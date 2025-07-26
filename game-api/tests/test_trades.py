import uuid
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Player, Session as SessionModel, Stock, Trade


class TestTradesRouter:
    """Test cases for trades router endpoints."""

    def test_post_trade_success(self, client: TestClient, db_session: Session):
        """Test POST /trades/ creates a new trade."""
        # Create test player and session first
        player = Player(nickname="TestPlayer")
        db_session.add(player)
        db_session.commit()
        db_session.refresh(player)

        session_id = uuid.uuid4()
        session = SessionModel(
            session_id=session_id,
            player_id=player.id,
            started_at=datetime.now(),
            status="active",
            balance=10000.0,
            unsold_stocks=[]
        )
        db_session.add(session)

        # Create test stock
        stock = Stock(symbol="AAPL", company_name="Apple Inc.", category="popular")
        db_session.add(stock)
        db_session.commit()

        trade_data = {
            "session_id": str(session_id),
            "timestamp": "2025-07-25T10:30:00",
            "symbol": "AAPL",
            "action": "buy",
            "qty": 10,
            "price": 150.75
        }

        response = client.post("/trades/", json=trade_data)
        assert response.status_code == 200

        data = response.json()
        assert data["session_id"] == str(session_id)
        assert data["symbol"] == "AAPL"
        assert data["action"] == "buy"
        assert data["qty"] == 10
        assert data["price"] == 150.75
        assert "trade_id" in data
        assert "timestamp" in data

    def test_post_trade_sell_action(self, client: TestClient, db_session: Session):
        """Test POST /trades/ with sell action."""
        # Create test player and session
        player = Player(nickname="TestPlayer")
        db_session.add(player)
        db_session.commit()
        db_session.refresh(player)

        session_id = uuid.uuid4()
        session = SessionModel(
            session_id=session_id,
            player_id=player.id,
            started_at=datetime.now(),
            status="active",
            balance=10000.0,
            unsold_stocks=[]
        )
        db_session.add(session)

        # Create test stock
        stock = Stock(symbol="TSLA", company_name="Tesla Inc.", category="volatile")
        db_session.add(stock)
        db_session.commit()

        trade_data = {
            "session_id": str(session_id),
            "timestamp": "2025-07-25T11:30:00",
            "symbol": "TSLA",
            "action": "sell",
            "qty": 5,
            "price": 245.50
        }

        response = client.post("/trades/", json=trade_data)
        assert response.status_code == 200

        data = response.json()
        assert data["action"] == "sell"
        assert data["qty"] == 5
        assert data["price"] == 245.50

    def test_post_trade_invalid_data(self, client: TestClient):
        """Test POST /trades/ with invalid data."""
        invalid_data = {
            "session_id": "invalid-uuid",
            "timestamp": "invalid-date",
            "symbol": "AAPL",
            "action": "buy",
            "qty": "invalid",  # Should be int
            "price": "invalid"  # Should be float
        }

        response = client.post("/trades/", json=invalid_data)
        assert response.status_code == 422

    def test_post_trade_missing_fields(self, client: TestClient):
        """Test POST /trades/ with missing required fields."""
        incomplete_data = {
            "session_id": str(uuid.uuid4()),
            "symbol": "AAPL",
            "action": "buy"
            # Missing qty, price, timestamp
        }

        response = client.post("/trades/", json=incomplete_data)
        assert response.status_code == 422

    def test_post_trade_negative_values(self, client: TestClient, db_session: Session):
        """Test POST /trades/ with negative quantity and price."""
        # Create test setup
        player = Player(nickname="TestPlayer")
        db_session.add(player)
        db_session.commit()
        db_session.refresh(player)

        session_id = uuid.uuid4()
        session = SessionModel(
            session_id=session_id,
            player_id=player.id,
            started_at=datetime.now(),
            status="active",
            balance=10000.0,
            unsold_stocks=[]
        )
        db_session.add(session)

        stock = Stock(symbol="AAPL", company_name="Apple Inc.", category="popular")
        db_session.add(stock)
        db_session.commit()

        trade_data = {
            "session_id": str(session_id),
            "timestamp": "2025-07-25T10:30:00",
            "symbol": "AAPL",
            "action": "buy",
            "qty": -5,  # Negative quantity
            "price": -100.0  # Negative price
        }

        # This should either be rejected or handled by business logic
        response = client.post("/trades/", json=trade_data)
        # Accept either validation error or successful creation
        assert response.status_code in [200, 422]

    def test_list_trades_success(self, client: TestClient, db_session: Session):
        """Test GET /trades/session/{session_id} returns trades for session."""
        # Create test player and session
        player = Player(nickname="TestPlayer")
        db_session.add(player)
        db_session.commit()
        db_session.refresh(player)

        session_id = uuid.uuid4()
        session = SessionModel(
            session_id=session_id,
            player_id=player.id,
            started_at=datetime.now(),
            status="active",
            balance=10000.0,
            unsold_stocks=[]
        )
        db_session.add(session)

        # Create test stock
        stock = Stock(symbol="AAPL", company_name="Apple Inc.", category="popular")
        db_session.add(stock)

        # Create test trades
        trades = [
            Trade(
                session_id=session_id,
                timestamp=datetime.now(),
                symbol="AAPL",
                action="buy",
                qty=10,
                price=150.0
            ),
            Trade(
                session_id=session_id,
                timestamp=datetime.now(),
                symbol="AAPL",
                action="sell",
                qty=5,
                price=155.0
            )
        ]
        for trade in trades:
            db_session.add(trade)

        db_session.commit()

        response = client.get(f"/trades/session/{session_id}")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2

        # Check first trade
        assert data[0]["session_id"] == str(session_id)
        assert data[0]["symbol"] == "AAPL"
        assert data[0]["action"] in ["buy", "sell"]
        assert data[0]["qty"] in [10, 5]

    def test_list_trades_empty_session(self, client: TestClient, db_session: Session):
        """Test GET /trades/session/{session_id} with session that has no trades."""
        # Create test player and session
        player = Player(nickname="TestPlayer")
        db_session.add(player)
        db_session.commit()
        db_session.refresh(player)

        session_id = uuid.uuid4()
        session = SessionModel(
            session_id=session_id,
            player_id=player.id,
            started_at=datetime.now(),
            status="active",
            balance=10000.0,
            unsold_stocks=[]
        )
        db_session.add(session)
        db_session.commit()

        response = client.get(f"/trades/session/{session_id}")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_list_trades_invalid_uuid(self, client: TestClient):
        """Test GET /trades/session/{session_id} with invalid UUID."""
        response = client.get("/trades/session/invalid-uuid")
        assert response.status_code == 422

    def test_list_trades_nonexistent_session(self, client: TestClient):
        """Test GET /trades/session/{session_id} with non-existent session."""
        non_existent_id = uuid.uuid4()
        response = client.get(f"/trades/session/{non_existent_id}")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0  # Should return empty list for non-existent session
