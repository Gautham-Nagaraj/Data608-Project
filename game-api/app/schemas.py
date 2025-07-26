from datetime import datetime, date
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ORMModel(BaseModel):
    model_config = {"from_attributes": True}


# Players
class PlayerBase(ORMModel):
    nickname: str = Field(..., example="TraderJoe")


class PlayerCreate(PlayerBase):
    pass


class Player(PlayerBase):
    id: int


# Stocks
class StockBase(ORMModel):
    symbol: str = Field(..., example="AAPL", max_length=10)
    company_name: str = Field(..., example="Apple Inc.")
    sector: Optional[str] = Field(None, example="Technology")
    category: str = Field(..., example="popular")  # popular, volatile, sector
    available_from: Optional[date] = None
    available_to: Optional[date] = None


class StockCreate(StockBase):
    pass


class Stock(StockBase):
    pass


# Admin Users
class AdminUserBase(ORMModel):
    login: str


class AdminUser(AdminUserBase):
    id: int


# Sessions
class SessionBase(BaseModel):
    player_id: int
    status: str = Field(..., example="active")
    balance: float = Field(..., example=10000.0)
    unsold_stocks: List[dict] = Field(default_factory=list)


class SessionCreate(SessionBase):
    started_at: datetime


class SessionUpdate(BaseModel):
    ended_at: Optional[datetime] = None
    status: Optional[str] = None
    balance: Optional[float] = None
    unsold_stocks: Optional[List[dict]] = None


class Session(SessionBase):
    session_id: UUID
    started_at: datetime
    ended_at: Optional[datetime]


# Selections
class SelectionCreate(ORMModel):
    popular_symbol: str = Field(..., min_length=1, example="AAPL")
    volatile_symbol: str = Field(..., min_length=1, example="TSLA")
    sector_symbol: str = Field(..., min_length=1, example="MSFT")


class Selection(SelectionCreate):
    id: int
    session_id: UUID


# Trades
class TradeBase(ORMModel):
    session_id: UUID
    symbol: str
    action: str = Field(..., example="buy")  # or "sell"
    qty: int
    price: float


class TradeCreate(TradeBase):
    timestamp: datetime


class Trade(TradeBase):
    trade_id: int
    timestamp: datetime

class Player(PlayerBase):
    id: int