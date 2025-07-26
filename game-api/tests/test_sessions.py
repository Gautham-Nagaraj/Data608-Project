import uuid
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Player, Session as SessionModel


class TestSessionsRouter:
    """Test cases for sessions router endpoints."""

    def test_create_session_success(self, client: TestClient, db_session: Session):
        """Test POST /sessions/ creates a new session."""
        # Create test player first
        player = Player(nickname="TestPlayer")
        db_session.add(player)
        db_session.commit()
        db_session.refresh(player)  # Get the generated ID

        session_data = {
            "player_id": player.id,
            "started_at": "2025-07-25T10:00:00",
            "status": "active",
            "balance": 10000.0,
            "unsold_stocks": []
        }

        response = client.post("/sessions/", json=session_data)
        assert response.status_code == 200

        data = response.json()
        assert data["player_id"] == player.id
        assert data["status"] == "active"
        assert data["balance"] == 10000.0
        assert data["unsold_stocks"] == []
        assert "session_id" in data
        assert "started_at" in data

    def test_create_session_invalid_data(self, client: TestClient):
        """Test POST /sessions/ with invalid data."""
        invalid_data = {
            "player_id": "invalid",  # Should be int
            "started_at": "invalid-date",
            "status": "active"
        }

        response = client.post("/sessions/", json=invalid_data)
        assert response.status_code == 422

    def test_create_session_nonexistent_player(self, client: TestClient):
        """Test POST /sessions/ with non-existent player_id."""
        session_data = {
            "player_id": 99999,  # Non-existent player
            "started_at": "2025-07-25T10:00:00",
            "status": "active",
            "balance": 10000.0,
            "unsold_stocks": []
        }

        response = client.post("/sessions/", json=session_data)
        # Should fail due to player validation
        assert response.status_code == 400  # Bad Request due to non-existent player

    def test_read_session_success(self, client: TestClient, db_session: Session):
        """Test GET /sessions/{session_id} returns session data."""
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

        response = client.get(f"/sessions/{session_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["session_id"] == str(session_id)
        assert data["player_id"] == player.id
        assert data["status"] == "active"
        assert data["balance"] == 10000.0

    def test_read_session_not_found(self, client: TestClient):
        """Test GET /sessions/{session_id} with non-existent session."""
        non_existent_id = uuid.uuid4()
        response = client.get(f"/sessions/{non_existent_id}")
        assert response.status_code == 404
        assert response.json()["detail"] == "Session not found"

    def test_read_session_invalid_uuid(self, client: TestClient):
        """Test GET /sessions/{session_id} with invalid UUID."""
        response = client.get("/sessions/invalid-uuid")
        assert response.status_code == 422

    def test_modify_session_success(self, client: TestClient, db_session: Session):
        """Test PATCH /sessions/{session_id} updates session."""
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

        update_data = {
            "status": "completed",
            "balance": 12500.0,
            "ended_at": "2025-07-25T15:00:00"
        }

        response = client.patch(f"/sessions/{session_id}", json=update_data)
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "completed"
        assert data["balance"] == 12500.0
        assert data["ended_at"] is not None

    def test_modify_session_not_found(self, client: TestClient):
        """Test PATCH /sessions/{session_id} with non-existent session."""
        non_existent_id = uuid.uuid4()
        update_data = {"status": "completed"}

        response = client.patch(f"/sessions/{non_existent_id}", json=update_data)
        assert response.status_code == 404
        assert response.json()["detail"] == "Session not found"

    def test_modify_session_partial_update(self, client: TestClient, db_session: Session):
        """Test PATCH /sessions/{session_id} with partial data."""
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

        # Update only status
        update_data = {"status": "paused"}
        response = client.patch(f"/sessions/{session_id}", json=update_data)
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "paused"
        assert data["balance"] == 10000.0  # Should remain unchanged
