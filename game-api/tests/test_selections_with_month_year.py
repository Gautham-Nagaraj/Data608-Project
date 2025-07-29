import uuid
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Player, Session as SessionModel


class TestSelectionsWithMonthYear:
    """Test cases for selections router endpoints with month and year fields."""

    def test_create_selection_with_month_year_success(self, client: TestClient, db_session: Session):
        """Test POST /selections/{session_id} creates stock selections with month and year."""
        # Create test player first
        player = Player(nickname="TestPlayer")
        db_session.add(player)
        db_session.commit()
        db_session.refresh(player)
        
        # Create test session
        session = SessionModel(
            player_id=player.id,
            status="active",
            balance=10000.0,
            started_at=datetime.now()
        )
        db_session.add(session)
        db_session.commit()
        db_session.refresh(session)
        
        # Create a selection with month and year
        selection_data = {
            "popular_symbol": "AAPL",
            "volatile_symbol": "TSLA", 
            "sector_symbol": "MSFT",
            "month": 7,
            "year": 2025
        }
        
        response = client.post(
            f"/api/selections/{session.session_id}",
            json=selection_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["popular_symbol"] == "AAPL"
        assert data["volatile_symbol"] == "TSLA"
        assert data["sector_symbol"] == "MSFT"
        assert data["month"] == 7
        assert data["year"] == 2025
        assert data["session_id"] == str(session.session_id)

    def test_create_selection_invalid_month(self, client: TestClient, db_session: Session):
        """Test creating a selection with invalid month."""
        # Create test player first
        player = Player(nickname="TestPlayer2")
        db_session.add(player)
        db_session.commit()
        db_session.refresh(player)
        
        # Create test session
        session = SessionModel(
            player_id=player.id,
            status="active",
            balance=10000.0,
            started_at=datetime.now()
        )
        db_session.add(session)
        db_session.commit()
        db_session.refresh(session)
        
        # Try to create a selection with invalid month
        selection_data = {
            "popular_symbol": "AAPL",
            "volatile_symbol": "TSLA", 
            "sector_symbol": "MSFT",
            "month": 13,  # Invalid month
            "year": 2025
        }
        
        response = client.post(
            f"/api/selections/{session.session_id}",
            json=selection_data
        )
        
        assert response.status_code == 422  # Pydantic validation error
        assert "month" in response.json()["detail"][0]["loc"]

    def test_create_selection_invalid_year(self, client: TestClient, db_session: Session):
        """Test creating a selection with invalid year."""
        # Create test player first
        player = Player(nickname="TestPlayer3")
        db_session.add(player)
        db_session.commit()
        db_session.refresh(player)
        
        # Create test session
        session = SessionModel(
            player_id=player.id,
            status="active",
            balance=10000.0,
            started_at=datetime.now()
        )
        db_session.add(session)
        db_session.commit()
        db_session.refresh(session)
        
        # Try to create a selection with invalid year
        selection_data = {
            "popular_symbol": "AAPL",
            "volatile_symbol": "TSLA", 
            "sector_symbol": "MSFT",
            "month": 7,
            "year": 1800  # Invalid year
        }
        
        response = client.post(
            f"/api/selections/{session.session_id}",
            json=selection_data
        )
        
        assert response.status_code == 422  # Pydantic validation error
        assert "year" in response.json()["detail"][0]["loc"]

    def test_create_selection_nonexistent_session(self, client: TestClient, db_session: Session):
        """Test creating a selection for a nonexistent session."""
        random_session_id = uuid.uuid4()
        
        selection_data = {
            "popular_symbol": "AAPL",
            "volatile_symbol": "TSLA", 
            "sector_symbol": "MSFT",
            "month": 7,
            "year": 2025
        }
        
        response = client.post(
            f"/api/selections/{random_session_id}",
            json=selection_data
        )
        
        assert response.status_code == 404
        assert "Session not found" in response.json()["detail"]
