from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, schemas
from app.core.db import get_db
from app.core.config import settings
import json
import ollama
from langchain.prompts import PromptTemplate
import logging
import traceback
from langchain_ollama import ChatOllama
from pydantic import BaseModel

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/sessions/", response_model=schemas.Session)
async def start_session(session_in: schemas.SessionCreate, db: AsyncSession = Depends(get_db)):
    # Check if player exists
    player = await crud.get_player(db, session_in.player_id)
    if not player:
        raise HTTPException(status_code=400, detail="Player does not exist")

    return await crud.create_session(db, session_in)


@router.get("/sessions/{session_id}", response_model=schemas.Session)
async def read_session(session_id: UUID, db: AsyncSession = Depends(get_db)):
    db_session = await crud.get_session(db, session_id)
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
    return db_session


@router.patch("/sessions/{session_id}", response_model=schemas.Session)
async def modify_session(session_id: UUID, session_upd: schemas.SessionUpdate, db: AsyncSession = Depends(get_db)):
    updated = await crud.update_session(db, session_id, session_upd)
    if not updated:
        raise HTTPException(status_code=404, detail="Session not found")
    return updated

@router.post("/sessions/{session_id}/end", response_model=schemas.Score)
async def end_session(session_id: UUID, db: AsyncSession = Depends(get_db)):
    """End a session by marking it as ended."""
    session = await crud.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Update the session status to ended
    session.status = "ended"
    
    # Set the ended timestamp (timezone-naive for PostgreSQL)
    from datetime import datetime, timezone
    session.ended_at = datetime.now(timezone.utc).replace(tzinfo=None)
    
    await db.commit()
    await db.refresh(session)
    
    # Calculate and store the score
    db_score = await crud.calculate_score(db, session_id)

    return db_score


@router.post("/sessions/{session_id}/advise")
async def advise_player(session_id: UUID, db: AsyncSession = Depends(get_db)):
    """
    Provide buy/sell/hold advice for the current session using stock price history.
    """
    session = await crud.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    
    selection = await crud.get_selection(db, session_id)
    if not selection:
        raise HTTPException(status_code=400, detail="No stocks selected yet.")

    first_day = date(selection.year, selection.month, 1)
    # We need to get data for all selected stocks
    symbols = [selection.popular_symbol, selection.volatile_symbol, selection.sector_symbol]
    game_data = {}
    
    import calendar
    last_day_of_month = calendar.monthrange(selection.year, selection.month)[1]
    last_day = date(selection.year, selection.month, last_day_of_month)
    
    N = 5
    for symbol in symbols:
        prices = await crud.get_stock_prices(db, symbol, first_day, last_day)
        recent_prices = prices[-N:]  # Last N entries only
        game_data[symbol] = [{"date": p.date.isoformat(), "price": p.price} for p in recent_prices]

    if not game_data:
        raise HTTPException(status_code=500, detail="Price history missing for selected tickers.")

    trades = await crud.get_trades(db, session_id)
    
    # Convert Trade objects to dictionaries for JSON serialization
    trades_data = [
        {
            "trade_id": trade.trade_id,
            "session_id": str(trade.session_id),
            "timestamp": trade.timestamp.isoformat(),
            "symbol": trade.symbol,
            "action": trade.action,
            "qty": trade.qty,
            "price": trade.price
        }
        for trade in trades
    ]

    llm = ChatOllama(
        model="qwen3:latest",
        base_url=settings.OLLAMA_BASE_URL,
        temperature=0,
        top_p=0.9,
        num_ctx=2048,
        num_predict=256,
        format="json"
    )
    
    # Create parser based on the schema
    structured_llm  = llm.with_structured_output(schemas.TradingAdviceResponse)
    
    prompt_template = PromptTemplate(
        input_variables=["symbols", "cutoff_date", "stock_data", "trades_data"],
        template="""You are a financial trading assistant in a stock simulation game, and your cutoff date is one day before of {cutoff_date}.
Your task: For each of these 3 stocks ({symbols}), choose one action (BUY, SELL, HOLD) and give a short reason.
Plan ahead for the next trading day, considering the current market conditions and the player's trades history.
Base your advice on the player's trade history, recent price movements, and day trading strategy, with the goal to maximize profit. Do not include disclaimers.
Stock data for analysis:
{stock_data}
Player's trade history:
{trades_data}"""
    )
    
    # Create the chain
    chain = prompt_template | structured_llm 

    try:
        # Prepare prompt input
        prompt_input = {
            "symbols": ', '.join(symbols),
            "cutoff_date": session.started_at.isoformat(),
            "stock_data": json.dumps(game_data, separators=(',', ':')),
            "trades_data": json.dumps(trades_data, separators=(',', ':')),
        }

        logger.info("Generated prompt input for LLM:\n%s", prompt_input)

        # Execute the chain
        result = await chain.ainvoke(prompt_input, timeout=10)

        # Filter advice to only include selected symbols and ensure all are present
        selected_set = set(symbols)
        filtered_advice = []
        seen = set()
        for item in result.advice:
            if item.symbol in selected_set and item.symbol not in seen:
                filtered_advice.append(item)
                seen.add(item.symbol)

        # Add missing symbols with HOLD advice
        for symbol in symbols:
            if symbol not in seen:
                filtered_advice.append(
                    schemas.TradingAdviceItem(
                        symbol=symbol,
                        action="HOLD",
                        reason="No specific advice generated for this symbol. Consider holding."
                    )
                )
        result.advice = filtered_advice

        logger.info("LLM output parsed successfully:\n%s", result)

        # Return the Pydantic model directly (FastAPI will handle serialization)
        return result
    
    except Exception as e:
        logger.error("LLM generation or parsing failed: %s", str(e))
        logger.debug("Traceback:\n%s", traceback.format_exc())

        # Try to get raw LLM response (bypassing parser) for inspection
        try:
            prompt = await prompt_template.ainvoke(prompt_input)
            raw_output = await llm.ainvoke(prompt)
            logger.warning("Raw LLM response (unparsed):\n%s", raw_output)
        except Exception as raw_err:
            logger.error("Even raw LLM call failed: %s", raw_err)

        # Fallback response
        fallback_advice = [
            schemas.TradingAdviceItem(
                symbol=symbol,
                action="HOLD",
                reason="Unable to generate AI advice at this time. Consider holding your position."
            )
            for symbol in symbols
        ]

        return schemas.TradingAdviceResponse(advice=fallback_advice)
