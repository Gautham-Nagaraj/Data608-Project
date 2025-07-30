from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, schemas
from app.core.db import get_db
import json
import ollama

router = APIRouter()


@router.post("/sessions/", response_model=schemas.Session)
def start_session(session_in: schemas.SessionCreate, db: Session = Depends(get_db)):
    # Check if player exists
    player = crud.get_player(db, session_in.player_id)
    if not player:
        raise HTTPException(status_code=400, detail="Player does not exist")

    return crud.create_session(db, session_in)


@router.get("/sessions/{session_id}", response_model=schemas.Session)
def read_session(session_id: UUID, db: Session = Depends(get_db)):
    db_session = crud.get_session(db, session_id)
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
    return db_session


@router.patch("/sessions/{session_id}", response_model=schemas.Session)
def modify_session(session_id: UUID, session_upd: schemas.SessionUpdate, db: Session = Depends(get_db)):
    updated = crud.update_session(db, session_id, session_upd)
    if not updated:
        raise HTTPException(status_code=404, detail="Session not found")
    return updated

@router.post("/sessions/{session_id}/end", response_model=schemas.Score)
def end_session(session_id: UUID, db: Session = Depends(get_db)):
    """End a session by marking it as ended."""
    session = crud.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Update the session status to ended
    session.status = "ended"
    
    # Set the ended timestamp
    from datetime import datetime, timezone
    session.ended_at = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(session)
    
    # Calculate and store the score
    db_score = crud.calculate_score(db, session_id)

    return db_score


@router.get("/sessions/{session_id}/summary", response_model=schemas.SessionSummary)
def get_session_summary(session_id: UUID, db: Session = Depends(get_db)):
    """Get comprehensive session summary with unsold shares and feedback."""
    summary = crud.get_session_summary(db, session_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Session not found")
    return summary


@router.get("/sessions/{session_id}/unsold-shares", response_model=list[schemas.UnsoldShare])
def get_unsold_shares(session_id: UUID, db: Session = Depends(get_db)):
    """Get all unsold shares for a session."""
    session = crud.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return crud.get_unsold_shares(db, session_id)


@router.get("/sessions/{session_id}/unsold-shares/summary")
def get_unsold_shares_summary(session_id: UUID, db: Session = Depends(get_db)):
    """Get aggregated summary of unsold shares by symbol."""
    session = crud.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return crud.get_unsold_shares_summary(db, session_id)

@router.post("/sessions/{session_id}/advise")
def advise_player(session_id: UUID, db: Session = Depends(get_db)):
    """
    Provide buy/sell/hold advice for the current session using stock price history.
    """
    session = crud.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    
    selection = crud.get_selection(db, session_id)
    if not selection:
        raise HTTPException(status_code=400, detail="No stocks selected yet.")

    first_day = date(selection.year, selection.month, 1)
    # We need to get data for all selected stocks
    symbols = [selection.popular_symbol, selection.volatile_symbol, selection.sector_symbol]
    game_data = {}
    
    import calendar
    last_day_of_month = calendar.monthrange(selection.year, selection.month)[1]
    last_day = date(selection.year, selection.month, last_day_of_month)
    
    for symbol in symbols:
        prices = crud.get_stock_prices(db, symbol, first_day, last_day)
        game_data[symbol] = [{"date": p.date.isoformat(), "price": p.price} for p in prices]

    if not game_data:
        raise HTTPException(status_code=500, detail="Price history missing for selected tickers.")

    trades = crud.get_trades(db, session_id)
    
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

    # Compose LLM prompt
    prompt = f"""
You are a financial trading assistant in a stock simulation game, and your cutoff date is one day before of {session.started_at}.

Your task: For each of these 3 stocks ({', '.join(symbols)}), choose one action (BUY, SELL, HOLD) and give a short reason.
Plan ahead for the next trading day, considering the current market conditions and the player's trades history.
Base your advice on the player's trade history, recent price movements, and day trading strategy, with the goal to maximize profit. Do not include disclaimers.

IMPORTANT: You must respond with ONLY valid JSON in this exact format, no additional text:
[
  {{
    "symbol": "TICKER",
    "action": "BUY",
    "reason": "Short explanation here"
  }},
  {{
    "symbol": "TICKER",
    "action": "SELL", 
    "reason": "Short explanation here"
  }},
  {{
    "symbol": "TICKER",
    "action": "HOLD",
    "reason": "Short explanation here"
  }}
]

Stock data for analysis:
{json.dumps(game_data, indent=2)}

Player's trade history:
{json.dumps(trades_data, indent=2)}
"""


    # Call local Ollama model
    client = ollama.Client(host="http://host.docker.internal:11434")
    response = client.chat(
        model="qwen2.5:7b",
        messages=[
            {"role": "system", "content": "You are a helpful trading assistant in a simulated stock trading game. Always respond with valid JSON only, no additional text or explanations."},
            {"role": "user", "content": prompt}
        ],
        options={
            "temperature": 0.7,
            "top_p": 0.9,
            "stop": ["</s>"]
        }
    )

    try:
        # Parse the JSON response from the LLM
        advice_content = response['message']['content']
        
        # Clean the content in case there are markdown code blocks
        if "```json" in advice_content:
            advice_content = advice_content.split("```json")[1].split("```")[0].strip()
        elif "```" in advice_content:
            advice_content = advice_content.split("```")[1].split("```")[0].strip()
        
        advice_data = json.loads(advice_content)
        
        # Validate that we have the expected format
        if not isinstance(advice_data, list):
            raise ValueError("Advice should be a list")
        
        for item in advice_data:
            if not all(key in item for key in ["symbol", "action", "reason"]):
                raise ValueError("Each advice item should have symbol, action, and reason")
        
        return {"advice": advice_data}
    
    except (json.JSONDecodeError, ValueError, KeyError) as e:
        # If parsing fails, return a fallback response
        fallback_advice = []
        for symbol in symbols:
            fallback_advice.append({
                "symbol": symbol,
                "action": "HOLD",
                "reason": "Unable to generate AI advice at this time. Consider holding your position."
            })
        
        return {"advice": fallback_advice}