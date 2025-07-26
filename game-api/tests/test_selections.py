import uuid
from datetime import datetime, date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Player, Session as SessionModel, Stock, SessionSelection


class TestSelectionsRouter:
    """Test cases for selections router endpoints."""

    def test_create_selection_success(self, client: TestClient, db_session: Session):
        """Test POST /selections/{session_id} creates stock selections."""
        # Create test player first
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

        # Create test stocks
        stocks = [
            Stock(symbol="AAPL", company_name="Apple Inc.", category="popular"),
            Stock(symbol="TSLA", company_name="Tesla Inc.", category="volatile"),
            Stock(symbol="MSFT", company_name="Microsoft Corp.", category="sector")
        ]
        for stock in stocks:
            db_session.add(stock)

        db_session.commit()

        selection_data = {
            "popular_symbol": "AAPL",
            "volatile_symbol": "TSLA",
            "sector_symbol": "MSFT"
        }

        response = client.post(f"/api/selections/{session_id}", json=selection_data)
        assert response.status_code == 200

        data = response.json()
        assert data["session_id"] == str(session_id)
        assert data["popular_symbol"] == "AAPL"
        assert data["volatile_symbol"] == "TSLA"
        assert data["sector_symbol"] == "MSFT"
        assert "id" in data

    def test_create_selection_invalid_uuid(self, client: TestClient):
        """Test POST /selections/{session_id} with invalid session UUID."""
        selection_data = {
            "popular_symbol": "AAPL",
            "volatile_symbol": "TSLA",
            "sector_symbol": "MSFT"
        }

        response = client.post("/api/selections/invalid-uuid", json=selection_data)
        assert response.status_code == 422

    def test_create_selection_missing_fields(self, client: TestClient):
        """Test POST /selections/{session_id} with missing required fields."""
        session_id = uuid.uuid4()

        # Missing popular_symbol
        incomplete_data = {
            "volatile_symbol": "TSLA",
            "sector_symbol": "MSFT"
        }

        response = client.post(f"/api/selections/{session_id}", json=incomplete_data)
        assert response.status_code == 422

    def test_create_selection_empty_symbols(self, client: TestClient):
        """Test POST /selections/{session_id} with empty symbol values."""
        session_id = uuid.uuid4()

        selection_data = {
            "popular_symbol": "",
            "volatile_symbol": "TSLA",
            "sector_symbol": "MSFT"
        }

        response = client.post(f"/api/selections/{session_id}", json=selection_data)
        assert response.status_code == 422

    def test_create_selection_nonexistent_session(self, client: TestClient):
        """Test POST /selections/{session_id} with non-existent session."""
        non_existent_session = uuid.uuid4()

        selection_data = {
            "popular_symbol": "AAPL",
            "volatile_symbol": "TSLA",
            "sector_symbol": "MSFT"
        }

        # This should fail because session doesn't exist
        response = client.post(f"/api/selections/{non_existent_session}", json=selection_data)
        assert response.status_code == 404  # Not found due to non-existent session

    def test_get_selection_success(self, client: TestClient, db_session: Session):
        """Test GET /selections/{session_id} retrieves selection."""
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

        # Create test stocks
        stocks = [
            Stock(symbol="AAPL", company_name="Apple Inc.", category="popular"),
            Stock(symbol="TSLA", company_name="Tesla Inc.", category="volatile"),
            Stock(symbol="MSFT", company_name="Microsoft Corp.", category="sector")
        ]
        for stock in stocks:
            db_session.add(stock)

        # Create selection
        selection = SessionSelection(
            session_id=session_id,
            popular_symbol="AAPL",
            volatile_symbol="TSLA",
            sector_symbol="MSFT"
        )
        db_session.add(selection)
        db_session.commit()

        response = client.get(f"/api/selections/{session_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["session_id"] == str(session_id)
        assert data["popular_symbol"] == "AAPL"
        assert data["volatile_symbol"] == "TSLA"
        assert data["sector_symbol"] == "MSFT"

    def test_get_selection_not_found(self, client: TestClient):
        """Test GET /selections/{session_id} with non-existent selection."""
        non_existent_session = uuid.uuid4()
        response = client.get(f"/api/selections/{non_existent_session}")
        assert response.status_code == 404

    def test_get_roulette_selection_success(self, client: TestClient, db_session: Session):
        """Test GET /selections/roulette with valid month and year."""
        # Create test stocks available for July 2025
        stocks = [
            Stock(
                symbol="AAPL", 
                company_name="Apple Inc.", 
                category="popular",
                sector="Technology",
                available_from=date(2025, 6, 1),
                available_to=date(2025, 8, 31)
            ),
            Stock(
                symbol="GOOGL", 
                company_name="Alphabet Inc.", 
                category="popular",
                sector="Technology",
                available_from=date(2025, 1, 1),
                available_to=None  # No end date
            ),
            Stock(
                symbol="TSLA", 
                company_name="Tesla Inc.", 
                category="volatile",
                sector="Automotive",
                available_from=date(2025, 7, 1),
                available_to=date(2025, 12, 31)
            ),
            Stock(
                symbol="GME", 
                company_name="GameStop Corp.", 
                category="volatile",
                sector="Retail",
                available_from=date(2025, 5, 1),
                available_to=date(2025, 9, 30)
            ),
            Stock(
                symbol="MSFT", 
                company_name="Microsoft Corp.", 
                category="sector",
                sector="Technology",
                available_from=date(2025, 1, 1),
                available_to=None
            ),
            Stock(
                symbol="JNJ", 
                company_name="Johnson & Johnson", 
                category="sector",
                sector="Healthcare",
                available_from=date(2025, 6, 15),
                available_to=date(2025, 8, 15)
            )
        ]
        
        for stock in stocks:
            db_session.add(stock)
        db_session.commit()

        response = client.get("/api/selections/roulette", params={"month": 7, "year": 2025})
        assert response.status_code == 200

        data = response.json()
        assert "popular_symbol" in data
        assert "volatile_symbol" in data
        assert "sector_symbol" in data
        assert data["popular_symbol"] in ["AAPL", "GOOGL"]
        assert data["volatile_symbol"] in ["TSLA", "GME"]
        assert data["sector_symbol"] in ["MSFT", "JNJ"]

    def test_get_roulette_selection_invalid_month(self, client: TestClient):
        """Test GET /selections/roulette with invalid month."""
        response = client.get("/api/selections/roulette", params={"month": 13, "year": 2025})
        assert response.status_code == 400
        assert "Month must be between 1 and 12" in response.json()["detail"]

        response = client.get("/api/selections/roulette", params={"month": 0, "year": 2025})
        assert response.status_code == 400

    def test_get_roulette_selection_invalid_year(self, client: TestClient):
        """Test GET /selections/roulette with invalid year."""
        response = client.get("/api/selections/roulette", params={"month": 7, "year": 1800})
        assert response.status_code == 400
        assert "Year must be between 1900 and 2100" in response.json()["detail"]

        response = client.get("/api/selections/roulette", params={"month": 7, "year": 2200})
        assert response.status_code == 400

    def test_get_roulette_selection_missing_params(self, client: TestClient):
        """Test GET /selections/roulette with missing parameters."""
        response = client.get("/api/selections/roulette")
        assert response.status_code == 422  # Validation error for missing required params

    def test_get_roulette_selection_no_stocks_available(self, client: TestClient, db_session: Session):
        """Test GET /selections/roulette when no stocks are available for the period."""
        # Create stocks that are not available in July 2025
        stocks = [
            Stock(
                symbol="AAPL", 
                company_name="Apple Inc.", 
                category="popular",
                sector="Technology",
                available_from=date(2025, 8, 1),  # Starts after July
                available_to=date(2025, 12, 31)
            ),
            Stock(
                symbol="TSLA", 
                company_name="Tesla Inc.", 
                category="volatile",
                sector="Automotive",
                available_from=date(2025, 1, 1),
                available_to=date(2025, 6, 30)  # Ends before July
            )
        ]
        
        for stock in stocks:
            db_session.add(stock)
        db_session.commit()

        response = client.get("/api/selections/roulette", params={"month": 7, "year": 2025})
        assert response.status_code == 404
        assert "Roulette selection not found" in response.json()["detail"]

    def test_get_roulette_selection_missing_category(self, client: TestClient, db_session: Session):
        """Test GET /selections/roulette when one category is missing."""
        # Create stocks but missing 'sector' category
        stocks = [
            Stock(
                symbol="AAPL", 
                company_name="Apple Inc.", 
                category="popular",
                sector="Technology",
                available_from=date(2025, 1, 1),
                available_to=None
            ),
            Stock(
                symbol="TSLA", 
                company_name="Tesla Inc.", 
                category="volatile",
                sector="Automotive",
                available_from=date(2025, 1, 1),
                available_to=None
            )
            # Missing 'sector' category stocks
        ]
        
        for stock in stocks:
            db_session.add(stock)
        db_session.commit()

        response = client.get("/api/selections/roulette", params={"month": 7, "year": 2025})
        assert response.status_code == 404
