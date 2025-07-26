import asyncio
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, WebSocket
from sqlalchemy.orm import Session

from app import crud, schemas
from app.core.db import get_db

router = APIRouter()


@router.websocket("/prices/{session_id}")
async def stream_prices(websocket: WebSocket, session_id: str):
    await websocket.accept()
    while True:
        await websocket.send_json({"ticker": "AAPL", "price": 123.45})
        await asyncio.sleep(1)