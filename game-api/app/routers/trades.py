from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, schemas
from app.core.db import get_db

router = APIRouter()


@router.post("/trades/", response_model=schemas.Trade)
async def post_trade(trade_in: schemas.TradeCreate, db: AsyncSession = Depends(get_db)):
    return await crud.record_trade(db, trade_in)


@router.get("/trades/session/{session_id}", response_model=List[schemas.Trade])
async def list_trades(session_id: UUID, db: AsyncSession = Depends(get_db)):
    return await crud.get_trades(db, session_id)
