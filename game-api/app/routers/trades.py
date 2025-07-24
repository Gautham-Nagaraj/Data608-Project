from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app import crud, schemas
from app.core.db import get_db

router = APIRouter()

@router.post("/", response_model=schemas.Trade)
def post_trade(trade_in: schemas.TradeCreate, db: Session = Depends(get_db)):
    return crud.record_trade(db, trade_in)

@router.get("/session/{session_id}", response_model=List[schemas.Trade])
def list_trades(session_id: UUID, db: Session = Depends(get_db)):
    return crud.get_trades(db, session_id)