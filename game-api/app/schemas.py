from datetime import datetime, date
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ORMModel(BaseModel):
    model_config = {"from_attributes": True}


# Players
class PlayerBase(ORMModel):
    nickname: str = Field(..., min_length=1, example="TraderJoe")


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
    month: int = Field(..., ge=1, le=12, example=7)
    year: int = Field(..., ge=1900, le=2100, example=2025)


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

class StockPrice(BaseModel):
    symbol: str
    price: float
    date: datetime

    class Config:
        from_attributes = True

class Score(BaseModel):
    session_id: UUID
    player_id: int
    created_at: datetime
    total_trades: int = Field(..., example=10)
    total_profit: float = Field(..., example=500.0)
    total_score: float = Field(..., example=1500.0)

    class Config:
        from_attributes = True


# Unsold Shares
class UnsoldShareBase(ORMModel):
    session_id: UUID
    symbol: str = Field(..., example="AAPL")
    quantity: int = Field(..., gt=0, example=10)
    purchase_price: float = Field(..., gt=0, example=150.0)
    total_cost: float = Field(..., gt=0, example=1500.0)


class UnsoldShareCreate(UnsoldShareBase):
    pass


class UnsoldShare(UnsoldShareBase):
    id: int
    created_at: datetime


# Session Summary for post-game analysis
class SessionSummary(BaseModel):
    session: Session
    score: Optional[Score] = None
    unsold_shares: List[UnsoldShare] = Field(default_factory=list)
    total_unsold_value: float = 0.0
    unsold_count: int = 0
    feedback_messages: List[str] = Field(default_factory=list)

    class Config:
        from_attributes = True


# AI Agent Interactions
class AgentInteractionBase(ORMModel):
    session_id: UUID
    interaction_type: str = Field(..., example="agent_suggestion")
    content: str = Field(..., example="Consider buying AAPL based on recent trends")
    metadata: Optional[dict] = None


class AgentInteractionCreate(AgentInteractionBase):
    timestamp: datetime


class AgentInteraction(AgentInteractionBase):
    id: int
    timestamp: datetime


# Admin Audit Log
class AdminAuditLogBase(ORMModel):
    admin_login: str
    action: str = Field(..., example="delete_session")
    target_id: Optional[str] = None
    details: Optional[dict] = None
    ip_address: Optional[str] = None


class AdminAuditLogCreate(AdminAuditLogBase):
    timestamp: datetime


class AdminAuditLog(AdminAuditLogBase):
    id: int
    timestamp: datetime


# Admin Dashboard Response Models
class SessionWithDetails(BaseModel):
    session_id: str
    player_id: int
    player_nickname: str
    started_at: datetime
    ended_at: Optional[datetime]
    status: str
    balance: float
    total_score: float
    total_profit: float
    total_trades: int

    class Config:
        from_attributes = True


class LeaderboardEntry(BaseModel):
    player_id: int
    nickname: str
    total_score: float
    total_profit: float
    total_trades: int

    class Config:
        from_attributes = True


class PlayerStatistics(BaseModel):
    total_players: int
    total_sessions: int
    total_trades: int
    active_players_30d: int
    average_score_per_session: float
    average_profit_per_session: float
    average_trades_per_session: float

    class Config:
        from_attributes = True