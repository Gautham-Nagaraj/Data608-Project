from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
import uuid

Base = declarative_base()

class Player(Base):
    __tablename__ = 'players'
    id = Column(Integer, primary_key=True, index=True)
    nickname = Column(String, unique=True, nullable=False)

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

class SessionSelection(Base):
    __tablename__ = 'session_selections'
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey('sessions.session_id'), nullable=False)
    popular_symbol = Column(String, ForeignKey('stocks.symbol'), nullable=False)
    volatile_symbol = Column(String, ForeignKey('stocks.symbol'), nullable=False)
    sector_symbol = Column(String, ForeignKey('stocks.symbol'), nullable=False)

class Trade(Base):
    __tablename__ = 'trades'
    trade_id = Column(Integer, primary_key=True, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey('sessions.session_id'), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    symbol = Column(String, ForeignKey('stocks.symbol'), nullable=False)
    action = Column(String, nullable=False)
    qty = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)