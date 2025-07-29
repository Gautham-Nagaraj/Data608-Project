import pytest
import uuid
from datetime import datetime
from app import crud, models, schemas
from tests.conftest import override_get_db


def test_unsold_shares_storage_and_retrieval(override_get_db):
    """Test that unsold shares are properly stored and can be retrieved."""
    db = next(override_get_db())
    
    # Create a test player
    player = crud.create_player(db, schemas.PlayerCreate(nickname="TestTrader"))
    
    # Create a test session
    session_data = schemas.SessionCreate(
        player_id=player.id,
        started_at=datetime.utcnow(),
        status="active",
        balance=10000.0
    )
    session = crud.create_session(db, session_data)
    
    # Create test stocks
    stock1 = crud.create_stock(db, schemas.StockCreate(
        symbol="TEST1",
        company_name="Test Company 1",
        category="popular"
    ))
    stock2 = crud.create_stock(db, schemas.StockCreate(
        symbol="TEST2", 
        company_name="Test Company 2",
        category="volatile"
    ))
    
    # Create trades that will result in unsold shares
    # Buy 100 shares of TEST1 at $50
    trade1 = schemas.TradeCreate(
        session_id=session.session_id,
        timestamp=datetime.utcnow(),
        symbol="TEST1",
        action="buy",
        qty=100,
        price=50.0
    )
    crud.record_trade(db, trade1)
    
    # Buy 50 shares of TEST2 at $30
    trade2 = schemas.TradeCreate(
        session_id=session.session_id,
        timestamp=datetime.utcnow(),
        symbol="TEST2",
        action="buy",
        qty=50,
        price=30.0
    )
    crud.record_trade(db, trade2)
    
    # Sell only 30 shares of TEST1 at $55 (leaving 70 unsold)
    trade3 = schemas.TradeCreate(
        session_id=session.session_id,
        timestamp=datetime.utcnow(),
        symbol="TEST1",
        action="sell",
        qty=30,
        price=55.0
    )
    crud.record_trade(db, trade3)
    
    # Calculate score (this should store unsold shares)
    score = crud.calculate_score(db, session.session_id)
    
    # Verify score calculation
    assert score.total_trades == 3
    assert score.total_profit == 150.0  # (55-50) * 30 = 150
    assert score.total_score == 4  # 3 trades + 1 bonus for profit
    
    # Verify unsold shares were stored
    unsold_shares = crud.get_unsold_shares(db, session.session_id)
    assert len(unsold_shares) == 2  # Two unsold positions
    
    # Verify unsold shares details
    unsold_by_symbol = {share.symbol: share for share in unsold_shares}
    
    # TEST1: Should have 70 shares left
    assert "TEST1" in unsold_by_symbol
    test1_unsold = unsold_by_symbol["TEST1"]
    assert test1_unsold.quantity == 70
    assert test1_unsold.purchase_price == 50.0
    assert test1_unsold.total_cost == 3500.0  # 70 * 50
    
    # TEST2: Should have all 50 shares left
    assert "TEST2" in unsold_by_symbol  
    test2_unsold = unsold_by_symbol["TEST2"]
    assert test2_unsold.quantity == 50
    assert test2_unsold.purchase_price == 30.0
    assert test2_unsold.total_cost == 1500.0  # 50 * 30


def test_session_summary_with_feedback(override_get_db):
    """Test session summary generation with feedback messages."""
    db = next(override_get_db())
    
    # Create test data similar to above
    player = crud.create_player(db, schemas.PlayerCreate(nickname="SummaryTestTrader"))
    session_data = schemas.SessionCreate(
        player_id=player.id,
        started_at=datetime.utcnow(),
        status="completed",
        balance=10000.0
    )
    session = crud.create_session(db, session_data)
    
    # Create a stock and some trades with unsold shares
    stock = crud.create_stock(db, schemas.StockCreate(
        symbol="SUMM",
        company_name="Summary Test Company",
        category="popular"
    ))
    
    # Buy 100, sell 60, leaving 40 unsold
    buy_trade = schemas.TradeCreate(
        session_id=session.session_id,
        timestamp=datetime.utcnow(),
        symbol="SUMM",
        action="buy",
        qty=100,
        price=25.0
    )
    crud.record_trade(db, buy_trade)
    
    sell_trade = schemas.TradeCreate(
        session_id=session.session_id,
        timestamp=datetime.utcnow(),
        symbol="SUMM",
        action="sell",
        qty=60,
        price=30.0
    )
    crud.record_trade(db, sell_trade)
    
    # Calculate score
    crud.calculate_score(db, session.session_id)
    
    # Get session summary
    summary = crud.get_session_summary(db, session.session_id)
    
    assert summary is not None
    assert summary.session.session_id == session.session_id
    assert summary.score is not None
    assert summary.unsold_count == 1
    assert summary.total_unsold_value == 1000.0  # 40 * 25
    
    # Check feedback messages
    assert len(summary.feedback_messages) > 0
    
    # Should contain feedback about unsold shares
    unsold_feedback = [msg for msg in summary.feedback_messages if "unsold" in msg.lower()]
    assert len(unsold_feedback) > 0
    
    # Should contain feedback about profit
    profit_feedback = [msg for msg in summary.feedback_messages if "profit" in msg.lower() or "$" in msg]
    assert len(profit_feedback) > 0


def test_unsold_shares_summary(override_get_db):
    """Test the unsold shares summary aggregation."""
    db = next(override_get_db())
    
    # Create test data
    player = crud.create_player(db, schemas.PlayerCreate(nickname="AggregateTestTrader"))
    session_data = schemas.SessionCreate(
        player_id=player.id,
        started_at=datetime.utcnow(),
        status="active",
        balance=10000.0
    )
    session = crud.create_session(db, session_data)
    
    # Create a stock
    stock = crud.create_stock(db, schemas.StockCreate(
        symbol="AGG",
        company_name="Aggregate Test Company", 
        category="popular"
    ))
    
    # Create multiple buy orders for the same stock at different prices
    buy1 = schemas.TradeCreate(
        session_id=session.session_id,
        timestamp=datetime.utcnow(),
        symbol="AGG",
        action="buy",
        qty=50,
        price=20.0
    )
    crud.record_trade(db, buy1)
    
    buy2 = schemas.TradeCreate(
        session_id=session.session_id,
        timestamp=datetime.utcnow(),
        symbol="AGG",
        action="buy",
        qty=30,
        price=25.0
    )
    crud.record_trade(db, buy2)
    
    # Calculate score (creates unsold shares)
    crud.calculate_score(db, session.session_id)
    
    # Get summary
    summary = crud.get_unsold_shares_summary(db, session.session_id)
    
    assert len(summary) == 1  # One symbol
    agg_summary = summary[0]
    
    assert agg_summary['symbol'] == 'AGG'
    assert agg_summary['total_quantity'] == 80  # 50 + 30
    assert agg_summary['total_cost'] == 1750.0  # 50*20 + 30*25
    assert agg_summary['average_price'] == 21.875  # 1750/80
    assert agg_summary['positions'] == 2  # Two buy orders
