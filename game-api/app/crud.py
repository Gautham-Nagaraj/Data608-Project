import datetime
import uuid

from sqlalchemy.orm import Session
from sqlalchemy import text

from app import models, schemas


# Players

def get_player(db: Session, player_id: int):
    return db.query(models.Player).filter(models.Player.id == player_id).first()


def create_player(db: Session, player: schemas.PlayerCreate):
    db_player = models.Player(nickname=player.nickname)
    db.add(db_player)
    db.commit()
    db.refresh(db_player)
    return db_player


def get_players(db: Session, nickname: str = None, limit: int = None, offset: int = 0):
    query = db.query(models.Player)
    
    # Apply nickname filter if provided
    if nickname:
        query = query.filter(models.Player.nickname.ilike(f"%{nickname}%"))
    
    # Apply pagination
    if offset:
        query = query.offset(offset)
    if limit:
        query = query.limit(limit)
    
    return query.all()


# Stocks

def get_stock_by_symbol(db: Session, symbol: str):
    return db.query(models.Stock).filter(models.Stock.symbol == symbol).first()


def create_stock(db: Session, stock: schemas.StockCreate):
    db_stock = models.Stock(**stock.dict())
    db.add(db_stock)
    db.commit()
    db.refresh(db_stock)
    return db_stock


def get_stocks(db: Session, category: str = None, sector: str = None, limit: int = None, offset: int = 0):
    query = db.query(models.Stock)
    
    # Apply filters if provided
    if category:
        query = query.filter(models.Stock.category == category)
    if sector:
        query = query.filter(models.Stock.sector == sector)
    
    # Apply pagination
    if offset:
        query = query.offset(offset)
    if limit:
        query = query.limit(limit)
    
    return query.all()


# Admin Users

def get_admin_user(db: Session, login: str):
    return db.query(models.AdminUser).filter(models.AdminUser.login == login).first()


# Sessions

def create_session(db: Session, session: schemas.SessionCreate):
    db_session = models.Session(**session.dict())
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session


# Helper to fetch a session by ID

def get_session(db: Session, session_id: uuid.UUID):
    return db.query(models.Session).filter(models.Session.session_id == session_id).first()


def update_session(db: Session, session_id: uuid.UUID, session_update: schemas.SessionUpdate):
    db_session = db.query(models.Session).filter(models.Session.session_id == session_id).first()
    if not db_session:
        return None
    for field, value in session_update.dict(exclude_unset=True).items():
        setattr(db_session, field, value)
    db.commit()
    db.refresh(db_session)
    return db_session


# Selections

def set_selection(db: Session, session_id: uuid.UUID, selection: schemas.SelectionCreate):
    db_sel = models.SessionSelection(session_id=session_id, **selection.dict())
    db.add(db_sel)
    db.commit()
    db.refresh(db_sel)
    return db_sel

def get_selection(db: Session, session_id: uuid.UUID):
    return db.query(models.SessionSelection).filter(models.SessionSelection.session_id == session_id).first()

def get_roulette_selection(db: Session, month: int, year: int):
    """Get the roulette selection for a specific month and year."""
    from datetime import date
    import calendar
    
    # Get the first and last day of the specified month
    month_start = date(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    month_end = date(year, month, last_day)
    
    # Get stocks available within the given month
    # A stock is available in the month if:
    # - It starts before or at the beginning of the month AND
    # - It ends after the month or has no end date
    available_stocks = db.query(models.Stock).filter(
        (models.Stock.available_from <= month_start) &
        ((models.Stock.available_to >= month_end) | (models.Stock.available_to.is_(None)))
    ).all()
    
    if not available_stocks:
        return None
    
    # Filter by categories
    popular_stocks = [s for s in available_stocks if s.category == "popular"]
    volatile_stocks = [s for s in available_stocks if s.category == "volatile"]
    sector_stocks = [s for s in available_stocks if s.category == "sector"]
    
    if not (popular_stocks and volatile_stocks and sector_stocks):
        return None
    
    # Randomly select one stock from each category
    import random
    
    # For sector_symbol: first get a random sector, then get a random stock from that sector
    available_sectors = list(set(s.sector for s in sector_stocks if s.sector))
    if not available_sectors:
        return None
    
    selected_sector = random.choice(available_sectors)
    sector_stocks_in_selected_sector = [s for s in sector_stocks if s.sector == selected_sector]
    
    return schemas.Selection(
        id=0,  # This is a virtual selection
        session_id=uuid.uuid4(),  # This is a virtual session_id
        popular_symbol=random.choice(popular_stocks).symbol,
        volatile_symbol=random.choice(volatile_stocks).symbol,
        sector_symbol=random.choice(sector_stocks_in_selected_sector).symbol
    )

# Trades

def record_trade(db: Session, trade: schemas.TradeCreate):
    db_trade = models.Trade(**trade.dict())
    db.add(db_trade)
    db.commit()
    db.refresh(db_trade)
    return db_trade


def get_trades(db: Session, session_id: uuid.UUID):
    return db.query(models.Trade).filter(models.Trade.session_id == session_id).all()

def get_eligible_dates(db: Session):
    """Get a list of eligible month and years for stock trading."""
    eligible_dates = db.query(models.Stock).filter(models.Stock.available_from <= datetime.now()).all()
    return [(date.available_from.month, date.available_from.year) for date in eligible_dates]

def get_stock_prices(db: Session, symbol: str, start_date: datetime.date, end_date: datetime.date):
    """Get stock prices for a given symbol within a date range."""
    return db.query(models.StockPrice).filter(
        models.StockPrice.symbol == symbol,
        models.StockPrice.date >= start_date,
        models.StockPrice.date <= end_date
    ).all()

def get_stock_sectors(db: Session):
    """Get a list of unique stock sectors from the stock_sectors view."""
    try:
        # Try to query the view first
        result = db.execute(text("SELECT sector FROM stock_sectors ORDER BY sector"))
        return [row[0] for row in result.fetchall()]
    except Exception:
        # Fallback to querying stocks table directly if view doesn't exist
        result = db.execute(text("SELECT DISTINCT sector FROM stocks WHERE sector IS NOT NULL ORDER BY sector"))
        return [row[0] for row in result.fetchall()]