import uuid
import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app import crud, models, schemas


class TestWebSocketRouter:
    
    def test_stream_prices_session_without_selection(self, db_session):
        """Test WebSocket with session that has no stock selection."""
        client = TestClient(app)
        
        # Create a player first
        player = crud.create_player(db_session, schemas.PlayerCreate(nickname="testplayer"))
        
        # Create a session without selection
        session_data = schemas.SessionCreate(
            player_id=player.id,
            started_at=datetime.now(),
            status="active",
            balance=10000.0
        )
        session = crud.create_session(db_session, session_data)
        
        with client.websocket_connect(f"/ws/prices/{session.session_id}") as websocket:
            data = websocket.receive_json()
            assert "error" in data
            assert "No stock selection found" in data["error"]
    
    def test_stream_prices_with_valid_session_and_selection(self, db_session):
        """Test WebSocket with valid session and selection but no price data."""
        client = TestClient(app)
        
        # Create test stocks
        stocks_data = [
            schemas.StockCreate(symbol="AAPL", company_name="Apple Inc.", category="popular"),
            schemas.StockCreate(symbol="TSLA", company_name="Tesla Inc.", category="volatile"),
            schemas.StockCreate(symbol="MSFT", company_name="Microsoft Corp.", category="sector", sector="Technology")
        ]
        
        for stock_data in stocks_data:
            crud.create_stock(db_session, stock_data)
        
        # Create stock prices
        price_data = [
            models.StockPrice(symbol="AAPL", date=datetime.now(), price=150.0),
            models.StockPrice(symbol="TSLA", date=datetime.now(), price=800.0),
            models.StockPrice(symbol="MSFT", date=datetime.now(), price=300.0)
        ]
        
        for price in price_data:
            db_session.add(price)
        db_session.commit()
        
        # Create a player
        player = crud.create_player(db_session, schemas.PlayerCreate(nickname="testplayer"))
        
        # Create a session
        session_data = schemas.SessionCreate(
            player_id=player.id,
            started_at=datetime.now(),
            status="active",
            balance=10000.0
        )
        session = crud.create_session(db_session, session_data)
        
        # Create a selection
        selection_data = schemas.SelectionCreate(
            popular_symbol="AAPL",
            volatile_symbol="TSLA",
            sector_symbol="MSFT",
            month=7,
            year=2025
        )
        crud.set_selection(db_session, session.session_id, selection_data)
        
        # Test WebSocket connection
        with client.websocket_connect(f"/ws/prices/{session.session_id}") as websocket:
            data = websocket.receive_json()
            
            # Should receive price data
            assert "session_id" in data
            assert "prices" in data
            assert "timestamp" in data
            assert data["session_id"] == str(session.session_id)
            
            # Should have 3 price entries
            assert len(data["prices"]) == 3
            
            # Check that we have prices for all selected symbols
            symbols = [price["symbol"] for price in data["prices"]]
            assert "AAPL" in symbols
            assert "TSLA" in symbols
            assert "MSFT" in symbols
            
            # Check price data structure
            for price in data["prices"]:
                assert "symbol" in price
                assert "price" in price
                assert "timestamp" in price
                assert isinstance(price["price"], (int, float))
