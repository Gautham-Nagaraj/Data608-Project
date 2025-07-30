import datetime
from datetime import timezone
from decimal import Decimal
import uuid
import logging

from sqlalchemy.orm import Session
from sqlalchemy import text, func, desc, extract

from app import models, schemas
from collections import defaultdict
from datetime import date

# Set up logger for this module
logger = logging.getLogger(__name__)

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
    db_stock = models.Stock(**stock.model_dump())
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


# Admin-specific functions for management

def get_sessions_with_filters(db: Session, player_id: int = None, status: str = None, 
                            start_date = None, end_date = None, limit: int = 100, offset: int = 0):
    """Get sessions with optional filters for admin dashboard"""
    query = db.query(models.Session)
    
    if player_id:
        query = query.filter(models.Session.player_id == player_id)
    
    if status:
        query = query.filter(models.Session.status == status)
    
    if start_date:
        query = query.filter(models.Session.started_at >= start_date)
    
    if end_date:
        # Add one day to include sessions started on end_date
        from datetime import timedelta
        end_datetime = datetime.combine(end_date, datetime.min.time()) + timedelta(days=1)
        query = query.filter(models.Session.started_at < end_datetime)
    
    # Order by most recent first
    query = query.order_by(models.Session.started_at.desc())
    
    if offset:
        query = query.offset(offset)
    
    if limit:
        query = query.limit(limit)
    
    sessions = query.all()
    
    # Enrich with player nicknames and score data
    result = []
    for session in sessions:
        player = db.query(models.Player).filter(models.Player.id == session.player_id).first()
        score = db.query(models.Score).filter(models.Score.session_id == session.session_id).first()
        
        session_data = {
            "session_id": str(session.session_id),
            "player_id": session.player_id,
            "player_nickname": player.nickname if player else "Unknown",
            "started_at": session.started_at,
            "ended_at": session.ended_at,
            "status": session.status,
            "balance": session.balance,
            "total_score": score.total_score if score else 0,
            "total_profit": float(score.total_profit) if score else 0.0,
            "total_trades": score.total_trades if score else 0
        }
        result.append(session_data)
    
    return result


def get_leaderboard(db: Session, top_n: int = 10, sort_by: str = "total_score"):
    """Get top N players sorted by specified metric"""
    
    # Build query to aggregate player statistics
    query = db.query(
        models.Player.id.label("player_id"),
        models.Player.nickname,
        func.sum(models.Score.total_score).label("total_score"),
        func.sum(models.Score.total_profit).label("total_profit"),
        func.sum(models.Score.total_trades).label("total_trades")
    ).join(
        models.Score, models.Player.id == models.Score.player_id
    ).group_by(
        models.Player.id, models.Player.nickname
    )
    
    # Apply sorting
    if sort_by == "total_score":
        query = query.order_by(desc("total_score"))
    elif sort_by == "total_profit":
        query = query.order_by(desc("total_profit"))
    else:
        query = query.order_by(desc("total_score"))  # Default fallback
    
    players = query.limit(top_n).all()
    
    # Format results
    result = []
    for player in players:
        result.append({
            "player_id": player.player_id,
            "nickname": player.nickname,
            "total_score": float(player.total_score or 0),
            "total_profit": float(player.total_profit or 0),
            "total_trades": int(player.total_trades or 0)
        })
    
    return result


def get_player_statistics(db: Session):
    """Get comprehensive player statistics"""
    
    # Overall statistics
    total_players = db.query(func.count(models.Player.id)).scalar()
    total_sessions = db.query(func.count(models.Session.session_id)).scalar()
    total_trades = db.query(func.sum(models.Score.total_trades)).scalar() or 0
    
    # Average statistics
    avg_score = db.query(func.avg(models.Score.total_score)).scalar() or 0
    avg_profit = db.query(func.avg(models.Score.total_profit)).scalar() or 0
    avg_trades_per_session = db.query(func.avg(models.Score.total_trades)).scalar() or 0
    
    # Active players (players with sessions in last 30 days)
    from datetime import timedelta
    thirty_days_ago = datetime.datetime.now(timezone.utc) - timedelta(days=30)
    active_players = db.query(func.count(func.distinct(models.Session.player_id))).filter(
        models.Session.started_at >= thirty_days_ago
    ).scalar()
    
    return {
        "total_players": total_players,
        "total_sessions": total_sessions,
        "total_trades": total_trades,
        "active_players_30d": active_players,
        "average_score_per_session": round(float(avg_score), 2),
        "average_profit_per_session": round(float(avg_profit), 2),
        "average_trades_per_session": round(float(avg_trades_per_session), 2)
    }


def delete_session_data(db: Session, session_id: uuid.UUID):
    """Delete a session and all related data"""
    try:
        # Delete in correct order to handle foreign key constraints
        
        # 1. Delete unsold shares
        db.query(models.UnsoldShare).filter(models.UnsoldShare.session_id == session_id).delete()
        
        # 2. Delete scores
        db.query(models.Score).filter(models.Score.session_id == session_id).delete()
        
        # 3. Delete trades
        db.query(models.Trade).filter(models.Trade.session_id == session_id).delete()
        
        # 4. Delete session selections
        db.query(models.SessionSelection).filter(models.SessionSelection.session_id == session_id).delete()
        
        # 5. Finally delete the session
        session_deleted = db.query(models.Session).filter(models.Session.session_id == session_id).delete()
        
        db.commit()
        return session_deleted > 0
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting session {session_id}: {e}")
        raise


def archive_session(db: Session, session_id: uuid.UUID):
    """Archive a session by updating its status"""
    try:
        session = db.query(models.Session).filter(models.Session.session_id == session_id).first()
        if session:
            session.status = "archived"
            if not session.ended_at:
                session.ended_at = datetime.datetime.now(timezone.utc)
            db.commit()
            return True
        return False
    except Exception as e:
        db.rollback()
        logger.error(f"Error archiving session {session_id}: {e}")
        raise


def reset_all_session_data(db: Session):
    """Reset all session-related data - DANGEROUS OPERATION"""
    try:
        # Delete in correct order
        db.query(models.UnsoldShare).delete()
        db.query(models.Score).delete() 
        db.query(models.Trade).delete()
        db.query(models.SessionSelection).delete()
        db.query(models.Session).delete()
        
        db.commit()
        logger.warning("All session data has been reset by admin")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error resetting all data: {e}")
        raise


def export_database_snapshot(db: Session, tables: list = None):
    """Export database snapshot - placeholder implementation"""
    # This would need to be implemented based on specific requirements
    # Could use SQLAlchemy reflection to get table structures
    # and export data in various formats
    
    exported_tables = []
    table_counts = {}
    
    if not tables or "all" in tables:
        # Get counts of main tables
        table_counts = {
            "players": db.query(func.count(models.Player.id)).scalar(),
            "sessions": db.query(func.count(models.Session.session_id)).scalar(),
            "trades": db.query(func.count(models.Trade.trade_id)).scalar(),
            "scores": db.query(func.count(models.Score.id)).scalar(),
            "unsold_shares": db.query(func.count(models.UnsoldShare.id)).scalar(),
        }
        exported_tables = list(table_counts.keys())
    
    return {
        "exported_tables": exported_tables,
        "table_counts": table_counts,
        "export_timestamp": datetime.datetime.now(timezone.utc).isoformat(),
        "note": "This is a placeholder implementation. Full CSV export would be implemented based on requirements."
    }


# AI Agent Interactions

def create_agent_interaction(db: Session, interaction: schemas.AgentInteractionCreate):
    """Create a new agent interaction record"""
    db_interaction = models.AgentInteraction(
        session_id=interaction.session_id,
        interaction_type=interaction.interaction_type,
        content=interaction.content,
        interaction_metadata=interaction.metadata,
        timestamp=interaction.timestamp
    )
    db.add(db_interaction)
    db.commit()
    db.refresh(db_interaction)
    return db_interaction


def get_agent_interactions(db: Session, session_id: uuid.UUID = None, limit: int = 100):
    """Get agent interactions, optionally filtered by session"""
    query = db.query(models.AgentInteraction)
    
    if session_id:
        query = query.filter(models.AgentInteraction.session_id == session_id)
    
    query = query.order_by(models.AgentInteraction.timestamp.desc())
    
    if limit:
        query = query.limit(limit)
    
    return query.all()


def get_session_chat_log(db: Session, session_id: uuid.UUID):
    """Get all chat interactions for a specific session"""
    interactions = db.query(models.AgentInteraction).filter(
        models.AgentInteraction.session_id == session_id
    ).order_by(models.AgentInteraction.timestamp.asc()).all()
    
    return [{
        "id": interaction.id,
        "timestamp": interaction.timestamp,
        "type": interaction.interaction_type,
        "content": interaction.content,
        "metadata": interaction.interaction_metadata
    } for interaction in interactions]


# Admin Audit Logging

def create_audit_log(db: Session, admin_login: str, action: str, target_id: str = None, 
                    details: dict = None, ip_address: str = None):
    """Create an audit log entry for admin actions"""
    db_log = models.AdminAuditLog(
        admin_login=admin_login,
        action=action,
        target_id=target_id,
        details=details,
        ip_address=ip_address,
        timestamp=datetime.datetime.now(timezone.utc)
    )
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log


def get_audit_logs(db: Session, admin_login: str = None, action: str = None, 
                  start_date: datetime = None, end_date: datetime = None, 
                  limit: int = 100, offset: int = 0):
    """Get audit logs with optional filters"""
    query = db.query(models.AdminAuditLog)
    
    if admin_login:
        query = query.filter(models.AdminAuditLog.admin_login == admin_login)
    
    if action:
        query = query.filter(models.AdminAuditLog.action == action)
    
    if start_date:
        query = query.filter(models.AdminAuditLog.timestamp >= start_date)
    
    if end_date:
        query = query.filter(models.AdminAuditLog.timestamp <= end_date)
    
    query = query.order_by(models.AdminAuditLog.timestamp.desc())
    
    if offset:
        query = query.offset(offset)
    
    if limit:
        query = query.limit(limit)
    
    return query.all()


# Sessions

def create_session(db: Session, session: schemas.SessionCreate):
    db_session = models.Session(**session.model_dump())
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
    for field, value in session_update.model_dump(exclude_unset=True).items():
        setattr(db_session, field, value)
    db.commit()
    db.refresh(db_session)
    return db_session


# Selections

def set_selection(db: Session, session_id: uuid.UUID, selection: schemas.SelectionCreate):
    db_sel = models.SessionSelection(session_id=session_id, **selection.model_dump())
    db.add(db_sel)
    db.commit()
    db.refresh(db_sel)
    return db_sel

def get_selection(db: Session, session_id: uuid.UUID):
    return db.query(models.SessionSelection).filter(models.SessionSelection.session_id == session_id).first()

def update_selection(db: Session, session_id: uuid.UUID, session_update: schemas.SelectionUpdate):
    db_session = db.query(models.SessionSelection).filter(models.SessionSelection.session_id == session_id).first()
    if not db_session:
        return None
    for field, value in session_update.model_dump(exclude_unset=True).items():
        setattr(db_session, field, value)
    db.commit()
    db.refresh(db_session)
    return db_session

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
        sector_symbol=random.choice(sector_stocks_in_selected_sector).symbol,
        month=month,
        year=year
    )

# Trades

def record_trade(db: Session, trade: schemas.TradeCreate):
    db_trade = models.Trade(**trade.model_dump())
    db.add(db_trade)
    db.commit()
    db.refresh(db_trade)
    return db_trade


def get_trades(db: Session, session_id: uuid.UUID):
    return db.query(models.Trade).filter(models.Trade.session_id == session_id).all()

def get_eligible_dates(db: Session):
    """Get a list of eligible month and years for stock trading."""
    eligible_dates = db.query(models.Stock).filter(models.Stock.available_from <= datetime.date.today()).all()
    return [(date.available_from.month, date.available_from.year) for date in eligible_dates]

def get_eligible_dates_roulette(db: Session):
    """Get a random eligible month and year for roulette selections."""
    import random
    from datetime import date
    import calendar
    
    # Get all stocks with available_from dates
    stocks = db.query(models.Stock).filter(
        models.Stock.available_from.isnot(None),
        models.Stock.available_from <= datetime.date.today()
    ).all()
    
    if not stocks:
        return None
    
    # Get unique month/year combinations
    unique_dates = set()
    for stock in stocks:
        if stock.available_from:
            unique_dates.add((stock.available_from.month, stock.available_from.year))
    
    if not unique_dates:
        return None
    
    # Filter to only include dates where we have stocks from all three categories
    valid_dates = []
    for month, year in unique_dates:
        # Get the first and last day of the month
        month_start = date(year, month, 1)
        last_day = calendar.monthrange(year, month)[1]
        month_end = date(year, month, last_day)
        
        # Check if stocks from all categories are available in this month
        available_stocks = db.query(models.Stock).filter(
            (models.Stock.available_from <= month_start) &
            ((models.Stock.available_to >= month_end) | (models.Stock.available_to.is_(None)))
        ).all()
        
        categories = set(s.category for s in available_stocks if s.category)
        sectors = set(s.sector for s in available_stocks if s.sector and s.category == "sector")
        
        # Valid if we have all three categories and at least one sector
        if "popular" in categories and "volatile" in categories and "sector" in categories and sectors:
            valid_dates.append({"month": month, "year": year})

    if not valid_dates:
        return None
    
    # Return a random valid date
    return random.choice(valid_dates)

def get_stock_prices(db: Session, symbol: str, start_date: datetime.date, end_date: datetime.date):
    """Get stock prices for a given symbol within a date range."""
    # Convert dates to datetime objects for proper comparison with DateTime fields
    start_datetime = datetime.datetime.combine(start_date, datetime.time.min)
    end_datetime = datetime.datetime.combine(end_date, datetime.time.max)
    
    return db.query(models.StockPrice).filter(
        models.StockPrice.symbol == symbol,
        models.StockPrice.date >= start_datetime,
        models.StockPrice.date <= end_datetime
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

def get_latest_stock_prices(db: Session, symbols: list):
    """Get the latest stock prices for given symbols."""
    if not symbols:
        return []
    
    # Get the latest price for each symbol
    latest_prices = []
    for symbol in symbols:
        latest_price = db.query(models.StockPrice).filter(
            models.StockPrice.symbol == symbol
        ).order_by(models.StockPrice.date.desc()).first()
        
        if latest_price:
            latest_prices.append(latest_price)
    
    return latest_prices

def calculate_score(db: Session, session_id: uuid.UUID):
    """Calculate the score for a session based on trades."""
    logger.info(f"Starting score calculation for session {session_id}")
    
    trades = db.query(models.Trade).filter(models.Trade.session_id == session_id).order_by(models.Trade.timestamp).all()
    logger.info(f"Found {len(trades)} trades for session {session_id}")

    # Get session to access player_id
    session = db.query(models.Session).filter(models.Session.session_id == session_id).first()
    if not session:
        logger.error(f"Session {session_id} not found")
        raise ValueError(f"Session {session_id} not found")
    
    logger.info(f"Session belongs to player_id: {session.player_id}")
    
    if not trades:
        logger.info("No trades found, creating score record with zero values")
        # Create score record with zero values if no trades
        db_score = models.Score(
            session_id=session_id,
            player_id=session.player_id, 
            total_trades=0,
            total_profit=0.0,
            total_score=0.0
        )
        db.add(db_score)
        db.commit()
        db.refresh(db_score)
        logger.info("Created zero-value score record")
        return db_score
    
    # Organize by ticker: stack buys until we find sells
    buy_stack = defaultdict(list)
    total_score = 0
    total_profit = 0.0
    trade_count = len(trades)
    
    logger.info(f"Processing {trade_count} trades")
    
    for i, trade in enumerate(trades):
        symbol = trade.symbol
        action = trade.action.lower()
        qty = trade.qty
        price = trade.price

        logger.debug(f"Trade {i+1}/{trade_count}: {action.upper()} {qty} {symbol} @ {price}")

        # +1 for each action
        total_score += 1
        logger.debug(f"Score increased by 1 for trade action. Total score: {total_score}")

        if action == 'buy':
            buy_stack[symbol].append({'qty': qty, 'price': price})
            logger.debug(f"Added to buy stack for {symbol}. Stack size: {len(buy_stack[symbol])}")
            
        elif action == 'sell':
            qty_left = qty
            initial_qty = qty
            trade_profit = 0.0
            
            logger.debug(f"Processing sell of {qty} shares of {symbol}")
            
            while qty_left > 0 and buy_stack[symbol]:
                buy = buy_stack[symbol][0]
                matched_qty = min(qty_left, buy['qty'])
                profit_per_share = price - buy['price']
                profit_amount = profit_per_share * matched_qty
                profit_pct = (profit_per_share / buy['price']) * 100

                logger.debug(f"Matching {matched_qty} shares: bought at {buy['price']}, sold at {price}")
                logger.debug(f"Profit per share: {profit_per_share:.4f}, Profit %: {profit_pct:.2f}%")

                # Add to total profit
                total_profit += profit_amount
                trade_profit += profit_amount
                
                logger.debug(f"Profit amount: {profit_amount:.4f}, Total profit: {total_profit:.4f}")

                # Add profit bonus if positive
                if profit_pct > 0:
                    bonus_points = 0
                    if profit_pct <= 5:
                        bonus_points = 1
                    elif profit_pct <= 10:
                        bonus_points = 2
                    elif profit_pct <= 20:
                        bonus_points = 3
                    else:
                        bonus_points = 5
                    
                    total_score += bonus_points
                    logger.debug(f"Added {bonus_points} bonus points for {profit_pct:.2f}% profit. Total score: {total_score}")

                # Adjust buy stack
                buy['qty'] -= matched_qty
                if buy['qty'] == 0:
                    buy_stack[symbol].pop(0)
                    logger.debug(f"Removed exhausted buy order from stack for {symbol}")
                qty_left -= matched_qty

            if qty_left > 0:
                logger.warning(f"Could not match {qty_left} shares of {symbol} - insufficient buy orders")
            
            logger.debug(f"Completed sell trade. Matched {initial_qty - qty_left}/{initial_qty} shares. Trade profit: {trade_profit:.4f}")

    # Log and store unsold positions
    unsold_value = 0.0
    unsold_shares_list = []
    
    for symbol, buys in buy_stack.items():
        if buys:
            for buy_order in buys:
                if buy_order['qty'] > 0:
                    unsold_qty = buy_order['qty']
                    purchase_price = buy_order['price']
                    total_cost = unsold_qty * purchase_price
                    
                    # Create unsold share record
                    unsold_share = models.UnsoldShare(
                        session_id=session_id,
                        symbol=symbol,
                        quantity=unsold_qty,
                        purchase_price=purchase_price,
                        total_cost=total_cost
                    )
                    db.add(unsold_share)
                    unsold_shares_list.append(unsold_share)
                    
                    logger.info(f"Storing unsold position: {symbol} - {unsold_qty} shares at ${purchase_price:.2f}, total cost: ${total_cost:.2f}")
                    unsold_value += total_cost
    
    if unsold_value > 0:
        logger.info(f"Total unsold positions value: ${unsold_value:.2f} across {len(unsold_shares_list)} positions")
        logger.info("Recommendation: Complete trade cycles (buy → sell) for maximum scoring potential")
    else:
        logger.info("No unsold positions - excellent complete trading strategy!")

    logger.info(f"Final calculation results:")
    logger.info(f"  Total trades: {trade_count}")
    logger.info(f"  Total profit: ${total_profit:.2f}")
    logger.info(f"  Total score: {total_score}")
    logger.info(f"  Unsold positions value: ${unsold_value:.2f}")

    db_score = models.Score(
        session_id=session_id,
        player_id=session.player_id,
        total_trades=trade_count,
        total_profit=Decimal(total_profit),
        total_score=total_score
    )
    db.add(db_score)
    db.commit()
    db.refresh(db_score)
    
    logger.info(f"Score calculation completed for session {session_id}")
    return db_score


# Unsold Shares

def get_unsold_shares(db: Session, session_id: uuid.UUID):
    """Get all unsold shares for a session."""
    return db.query(models.UnsoldShare).filter(models.UnsoldShare.session_id == session_id).all()


def get_unsold_shares_summary(db: Session, session_id: uuid.UUID):
    """Get a summary of unsold shares by symbol for a session."""
    unsold_shares = get_unsold_shares(db, session_id)
    
    # Group by symbol and aggregate
    summary = {}
    for share in unsold_shares:
        if share.symbol not in summary:
            summary[share.symbol] = {
                'symbol': share.symbol,
                'total_quantity': 0,
                'total_cost': 0.0,
                'average_price': 0.0,
                'positions': 0
            }
        summary[share.symbol]['total_quantity'] += share.quantity
        summary[share.symbol]['total_cost'] += share.total_cost
        summary[share.symbol]['positions'] += 1
    
    # Calculate average prices
    for symbol_data in summary.values():
        if symbol_data['total_quantity'] > 0:
            symbol_data['average_price'] = symbol_data['total_cost'] / symbol_data['total_quantity']
    
    return list(summary.values())


def delete_unsold_shares(db: Session, session_id: uuid.UUID):
    """Delete all unsold shares for a session (useful for recalculation)."""
    db.query(models.UnsoldShare).filter(models.UnsoldShare.session_id == session_id).delete()
    db.commit()


# Session Summary and Feedback

def get_session_summary(db: Session, session_id: uuid.UUID):
    """Get comprehensive session summary including unsold shares and feedback."""
    # Get session details
    session = get_session(db, session_id)
    if not session:
        return None
    
    # Get score
    score = db.query(models.Score).filter(models.Score.session_id == session_id).first()
    
    # Get unsold shares
    unsold_shares = get_unsold_shares(db, session_id)
    
    # Calculate totals
    total_unsold_value = sum(share.total_cost for share in unsold_shares)
    unsold_count = len(unsold_shares)
    
    # Generate feedback messages
    feedback_messages = generate_feedback_messages(score, unsold_shares, total_unsold_value)
    
    return schemas.SessionSummary(
        session=session,
        score=score,
        unsold_shares=unsold_shares,
        total_unsold_value=total_unsold_value,
        unsold_count=unsold_count,
        feedback_messages=feedback_messages
    )


def generate_feedback_messages(score, unsold_shares, total_unsold_value):
    """Generate personalized feedback messages based on session performance."""
    feedback = []
    
    if not score:
        feedback.append("⚠️ No score calculated yet. Complete your trading session!")
        return feedback
    
    # Score-based feedback
    if score.total_score >= 50:
        feedback.append("🎉 Excellent trading performance! You're a natural trader!")
    elif score.total_score >= 30:
        feedback.append("👍 Good trading strategy! Keep it up!")
    elif score.total_score >= 15:
        feedback.append("📈 Decent performance, but there's room for improvement.")
    else:
        feedback.append("📚 Keep practicing! Trading takes time to master.")
    
    # Profit-based feedback
    if score.total_profit > 0:
        feedback.append(f"💰 Great job! You made ${score.total_profit:.2f} in profit!")
    elif score.total_profit == 0:
        feedback.append("⚖️ You broke even - not bad for practice!")
    else:
        feedback.append(f"📉 You had a loss of ${abs(score.total_profit):.2f}. Study market patterns!")
    
    # Unsold shares feedback
    if unsold_shares:
        unsold_summary = {}
        for share in unsold_shares:
            if share.symbol not in unsold_summary:
                unsold_summary[share.symbol] = 0
            unsold_summary[share.symbol] += share.quantity
        
        unsold_details = [f"{qty} shares of {symbol}" for symbol, qty in unsold_summary.items()]
        feedback.append(f"📦 You have unsold positions: {', '.join(unsold_details)}")
        feedback.append(f"💡 Tip: Complete trade cycles (buy → sell) to maximize your score!")
        feedback.append(f"🏦 Your unsold shares are worth ${total_unsold_value:.2f} at purchase price")
        
        if len(unsold_shares) > 5:
            feedback.append("🎯 Consider focusing on fewer stocks for better management")
    else:
        feedback.append("✅ Perfect! You completed all your trades - no unsold positions!")
        feedback.append("🌟 Complete trading cycles lead to maximum scoring potential!")
    
    # Trade activity feedback
    if score.total_trades >= 20:
        feedback.append("⚡ Very active trader! High activity can lead to great rewards.")
    elif score.total_trades >= 10:
        feedback.append("📊 Good trading activity level.")
    elif score.total_trades >= 5:
        feedback.append("🔄 Moderate trading activity - consider more strategic moves.")
    else:
        feedback.append("🐌 Low trading activity - be more active to increase your score!")
    
    return feedback

def get_selected_tickers_for_session(session_id: str, db: Session) -> list[str]:
    # Query your selections table (e.g. Selections model)
    selections = db.query(models.Selection).filter(
        models.Selection.session_id == session_id
    ).all()
    return [s.symbol for s in selections]

