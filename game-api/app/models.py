from datetime import datetime, timezone
import uuid

from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


def utc_now():
    """Helper function to get current UTC datetime - replacement for deprecated datetime.utcnow()"""
    return datetime.now(timezone.utc)


class Player(Base):
    __tablename__ = 'players'
    id = Column(Integer, primary_key=True, index=True)
    nickname = Column(String, unique=False, nullable=False)


class AdminUser(Base):
    __tablename__ = 'admin_users'
    id = Column(Integer, primary_key=True, index=True)
    login = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)


class Session(Base):
    __tablename__ = 'sessions'
    session_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    player_id = Column(Integer, ForeignKey('players.id'), nullable=False)
    started_at = Column(DateTime, nullable=False)
    ended_at = Column(DateTime, nullable=True)
    status = Column(String, nullable=False)
    balance = Column(Float, nullable=False, default=0.0)
    unsold_stocks = Column(JSON, nullable=False, default=list)


class Stock(Base):
    __tablename__ = 'stocks'
    symbol = Column(String, primary_key=True, index=True)
    company_name = Column(String, nullable=False)
    sector = Column(String, nullable=True)
    category = Column(String, nullable=False)
    available_from = Column(Date, nullable=True)
    available_to = Column(Date, nullable=True)

class StockPrice(Base):
    __tablename__ = 'stock_prices'
    symbol = Column(String, ForeignKey('stocks.symbol'), primary_key=True, nullable=False)
    date = Column(DateTime, primary_key=True, nullable=False)
    price = Column(Float, nullable=False)

class SessionSelection(Base):
    __tablename__ = 'session_selections'
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey('sessions.session_id'), nullable=False)
    popular_symbol = Column(String, ForeignKey('stocks.symbol'), nullable=False)
    volatile_symbol = Column(String, ForeignKey('stocks.symbol'), nullable=False)
    sector_symbol = Column(String, ForeignKey('stocks.symbol'), nullable=False)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    current_date = Column(DateTime, nullable=True)


class Trade(Base):
    __tablename__ = 'trades'
    trade_id = Column(Integer, primary_key=True, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey('sessions.session_id'), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    symbol = Column(String, ForeignKey('stocks.symbol'), nullable=False)
    action = Column(String, nullable=False)
    qty = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)

class Score(Base):
    __tablename__ = 'scores'
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey('sessions.session_id'), nullable=False)
    player_id = Column(Integer, ForeignKey('players.id'), nullable=False)
    total_trades = Column(Integer, nullable=False)
    total_profit = Column(Float, nullable=False)
    total_score = Column(Float, nullable=False)
    created_at = Column(DateTime, nullable=False, default=utc_now)


class UnsoldShare(Base):
    __tablename__ = 'unsold_shares'
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey('sessions.session_id'), nullable=False)
    symbol = Column(String, ForeignKey('stocks.symbol'), nullable=False)
    quantity = Column(Integer, nullable=False)
    purchase_price = Column(Float, nullable=False)
    total_cost = Column(Float, nullable=False)
    created_at = Column(DateTime, nullable=False, default=utc_now)


class AgentInteraction(Base):
    __tablename__ = 'agent_interactions'
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey('sessions.session_id'), nullable=False)
    timestamp = Column(DateTime, nullable=False, default=utc_now)
    interaction_type = Column(String, nullable=False)  # 'user_message', 'agent_response', 'agent_suggestion'
    content = Column(String, nullable=False)
    interaction_metadata = Column(JSON, nullable=True)  # Additional context like suggested stocks, reasoning, etc.


class AdminAuditLog(Base):
    __tablename__ = 'admin_audit_log'
    id = Column(Integer, primary_key=True, index=True)
    admin_login = Column(String, nullable=False)
    action = Column(String, nullable=False)  # 'login', 'delete_session', 'export_data', etc.
    target_id = Column(String, nullable=True)  # ID of affected resource (session_id, player_id, etc.)
    details = Column(JSON, nullable=True)  # Additional details about the action
    timestamp = Column(DateTime, nullable=False, default=utc_now)
    ip_address = Column(String, nullable=True)