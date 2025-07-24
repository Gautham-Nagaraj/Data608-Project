from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from datetime import datetime

# Players
class PlayerBase(BaseModel):
    nickname: str = Field(..., example="TraderJoe")

class PlayerCreate(PlayerBase):
    pass

class Player(PlayerBase):
    id: int

    class Config:
        orm_mode = True

# Admin Users
class AdminUserBase(BaseModel):
    login: str

class AdminUser(AdminUserBase):
    id: int

    class Config:
        orm_mode = True

# Sessions
class SessionBase(BaseModel):
    player_id: int
    status: str = Field(..., example="active")
    balance: float = Field(..., example=10000.0)
    unsold_stocks: List[dict] = Field(default_factory=list)

class SessionCreate(SessionBase):
    started_at: datetime

class SessionUpdate(BaseModel):
    ended_at: Optional[datetime]
    status: Optional[str]
    balance: Optional[float]
    unsold_stocks: Optional[List[dict]]

class Session(SessionBase):
    session_id: UUID
    started_at: datetime
    ended_at: Optional[datetime]

    class Config:
        orm_mode = True

# Selections
class SelectionCreate(BaseModel):
    popular_symbol: str
    volatile_symbol: str
    sector_symbol: str

class Selection(SelectionCreate):
    id: int
    session_id: UUID

    class Config:
        orm_mode = True

# Trades
class TradeBase(BaseModel):
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

    class Config:
        orm_mode = True