from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, schemas
from app.core.db import get_db
from app.core.config import settings
import json
import ollama
from langchain_ollama import OllamaLLM
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser


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

    llm = OllamaLLM(
        model="qwen2.5:7b",
        base_url=settings.OLLAMA_BASE_URL,
        temperature=0.7,
        top_p=0.9,
        num_ctx=2048,
        num_predict=256
    )
    
    # Create parser based on the schema
    parser = PydanticOutputParser(pydantic_object=schemas.TradingAdviceResponse)
    
    prompt_template = PromptTemplate(
        input_variables=["symbols", "cutoff_date", "stock_data", "trades_data"],
        template="""You are a financial trading assistant in a stock simulation game, and your cutoff date is one day before of {cutoff_date}.

Your task: For each of these 3 stocks ({symbols}), choose one action (BUY, SELL, HOLD) and give a short reason.
Plan ahead for the next trading day, considering the current market conditions and the player's trades history.
Base your advice on the player's trade history, recent price movements, and day trading strategy, with the goal to maximize profit. Do not include disclaimers.

{format_instructions}

Stock data for analysis:
{stock_data}

Player's trade history:
{trades_data}""",
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )
    
    # Create the chain
    chain = prompt_template | llm | parser
    
    try:
        # Execute the chain
        result = chain.invoke({
            "symbols": ', '.join(symbols),
            "cutoff_date": session.started_at,
            "stock_data": json.dumps(game_data, separators=(',', ':')),
            "trades_data": json.dumps(trades_data, separators=(',', ':'))
        })
        
        # Return the Pydantic model directly (FastAPI will handle serialization)
        return result
    
    except Exception as e:
        # If anything fails, return a fallback response
        fallback_advice = []
        for symbol in symbols:
            fallback_advice.append(schemas.TradingAdviceItem(
                symbol=symbol,
                action="HOLD",
                reason="Unable to generate AI advice at this time. Consider holding your position."
            ))
        
        return schemas.TradingAdviceResponse(advice=fallback_advice)