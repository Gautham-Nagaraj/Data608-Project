import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Player


class TestPlayersRouter:
    """Test cases for players router endpoints."""

    def test_create_player_success(self, client: TestClient, db_session: Session):
        """Test POST /api/player creates a new player successfully."""
        player_data = {
            "nickname": "TestPlayer123"
        }

        response = client.post("/api/player", json=player_data)

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["nickname"] == "TestPlayer123"
        assert "id" in response_data
        assert isinstance(response_data["id"], int)

        # Verify player was actually created in database
        db_player = db_session.query(Player).filter(Player.nickname == "TestPlayer123").first()
        assert db_player is not None
        assert db_player.nickname == "TestPlayer123"

    def test_create_player_duplicate_nickname_allowed(self, client: TestClient, db_session: Session):
        """Test POST /api/player allows duplicate nicknames."""
        # Create a player first
        existing_player = Player(nickname="DuplicatePlayer")
        db_session.add(existing_player)
        db_session.commit()

        # Try to create another player with the same nickname - should now be allowed
        player_data = {
            "nickname": "DuplicatePlayer"
        }

        response = client.post("/api/player", json=player_data)

        # Should succeed since duplicates are now allowed
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["nickname"] == "DuplicatePlayer"
        assert "id" in response_data
        assert isinstance(response_data["id"], int)

    def test_create_player_missing_nickname(self, client: TestClient):
        """Test POST /api/player fails when nickname is missing."""
        player_data = {}

        response = client.post("/api/player", json=player_data)

        assert response.status_code == 422  # Validation error

    def test_create_player_empty_nickname(self, client: TestClient):
        """Test POST /api/player fails when nickname is empty."""
        player_data = {
            "nickname": ""
        }

        response = client.post("/api/player", json=player_data)

        assert response.status_code == 422  # Validation error

    def test_get_all_players_empty_database(self, client: TestClient):
        """Test GET /api/players returns empty list when no players exist."""
        response = client.get("/api/players")

        assert response.status_code == 200
        assert response.json() == []

    def test_get_all_players_success(self, client: TestClient, db_session: Session):
        """Test GET /api/players returns all players."""
        # Create test players
        players = [
            Player(nickname="Player1"),
            Player(nickname="Player2"),
            Player(nickname="Player3")
        ]
        for player in players:
            db_session.add(player)
        db_session.commit()

        response = client.get("/api/players")

        assert response.status_code == 200
        response_data = response.json()
        assert len(response_data) == 3
        
        # Check that all players are returned with correct data
        nicknames = [player["nickname"] for player in response_data]
        assert "Player1" in nicknames
        assert "Player2" in nicknames
        assert "Player3" in nicknames

        # Verify each player has required fields
        for player in response_data:
            assert "id" in player
            assert "nickname" in player
            assert isinstance(player["id"], int)
            assert isinstance(player["nickname"], str)

    def test_get_players_with_nickname_filter(self, client: TestClient, db_session: Session):
        """Test GET /api/players with nickname filter."""
        # Create test players
        players = [
            Player(nickname="TestUser1"),
            Player(nickname="TestUser2"),
            Player(nickname="AnotherPlayer"),
            Player(nickname="YetAnotherTest")
        ]
        for player in players:
            db_session.add(player)
        db_session.commit()

        # Test case-insensitive partial matching
        response = client.get("/api/players?nickname=test")

        assert response.status_code == 200
        response_data = response.json()
        assert len(response_data) == 3  # TestUser1, TestUser2, YetAnotherTest
        
        nicknames = [player["nickname"] for player in response_data]
        assert "TestUser1" in nicknames
        assert "TestUser2" in nicknames
        assert "YetAnotherTest" in nicknames
        assert "AnotherPlayer" not in nicknames

    def test_get_players_with_nickname_filter_no_matches(self, client: TestClient, db_session: Session):
        """Test GET /api/players with nickname filter that matches no players."""
        # Create test players
        players = [
            Player(nickname="Player1"),
            Player(nickname="Player2")
        ]
        for player in players:
            db_session.add(player)
        db_session.commit()

        response = client.get("/api/players?nickname=nonexistent")

        assert response.status_code == 200
        assert response.json() == []

    def test_get_players_with_limit(self, client: TestClient, db_session: Session):
        """Test GET /api/players with limit parameter."""
        # Create test players
        players = [
            Player(nickname=f"Player{i}") for i in range(5)
        ]
        for player in players:
            db_session.add(player)
        db_session.commit()

        response = client.get("/api/players?limit=3")

        assert response.status_code == 200
        response_data = response.json()
        assert len(response_data) == 3

    def test_get_players_with_offset(self, client: TestClient, db_session: Session):
        """Test GET /api/players with offset parameter."""
        # Create test players with predictable order
        players = [
            Player(nickname=f"Player{i:02d}") for i in range(5)
        ]
        for player in players:
            db_session.add(player)
        db_session.commit()

        # Get all players first to establish order
        all_response = client.get("/api/players")
        all_players = all_response.json()

        # Now test with offset
        offset_response = client.get("/api/players?offset=2")

        assert offset_response.status_code == 200
        offset_data = offset_response.json()
        assert len(offset_data) == 3  # 5 total - 2 offset = 3

    def test_get_players_with_limit_and_offset(self, client: TestClient, db_session: Session):
        """Test GET /api/players with both limit and offset parameters."""
        # Create test players
        players = [
            Player(nickname=f"Player{i:02d}") for i in range(10)
        ]
        for player in players:
            db_session.add(player)
        db_session.commit()

        response = client.get("/api/players?limit=3&offset=2")

        assert response.status_code == 200
        response_data = response.json()
        assert len(response_data) == 3

    def test_get_players_limit_boundary_values(self, client: TestClient, db_session: Session):
        """Test GET /api/players with boundary limit values."""
        # Create test players
        players = [
            Player(nickname=f"Player{i}") for i in range(5)
        ]
        for player in players:
            db_session.add(player)
        db_session.commit()

        # Test minimum limit
        response = client.get("/api/players?limit=1")
        assert response.status_code == 200
        assert len(response.json()) == 1

        # Test maximum limit
        response = client.get("/api/players?limit=100")
        assert response.status_code == 200
        assert len(response.json()) == 5  # Only 5 players exist

    def test_get_players_invalid_limit_values(self, client: TestClient):
        """Test GET /api/players with invalid limit values."""
        # Test limit too small
        response = client.get("/api/players?limit=0")
        assert response.status_code == 422

        # Test limit too large
        response = client.get("/api/players?limit=101")
        assert response.status_code == 422

        # Test negative limit
        response = client.get("/api/players?limit=-1")
        assert response.status_code == 422

    def test_get_players_invalid_offset_values(self, client: TestClient):
        """Test GET /api/players with invalid offset values."""
        # Test negative offset
        response = client.get("/api/players?offset=-1")
        assert response.status_code == 422

    def test_get_player_by_id_success(self, client: TestClient, db_session: Session):
        """Test GET /api/player/{player_id} returns specific player."""
        # Create a test player
        player = Player(nickname="SpecificPlayer")
        db_session.add(player)
        db_session.commit()
        db_session.refresh(player)

        response = client.get(f"/api/player/{player.id}")

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["id"] == player.id
        assert response_data["nickname"] == "SpecificPlayer"

    def test_get_player_by_id_not_found(self, client: TestClient):
        """Test GET /api/player/{player_id} returns 404 for non-existent player."""
        response = client.get("/api/player/99999")

        assert response.status_code == 404
        assert "Player not found" in response.json()["detail"]

    def test_get_player_by_id_invalid_id(self, client: TestClient):
        """Test GET /api/player/{player_id} with invalid player ID."""
        response = client.get("/api/player/invalid")

        assert response.status_code == 422  # Validation error for invalid integer

    def test_players_endpoint_integration(self, client: TestClient, db_session: Session):
        """Test complete workflow: create players, list them, get specific ones."""
        # Create multiple players
        player_data = [
            {"nickname": "Alice"},
            {"nickname": "Bob"},
            {"nickname": "Charlie"}
        ]

        created_players = []
        for data in player_data:
            response = client.post("/api/player", json=data)
            assert response.status_code == 200
            created_players.append(response.json())

        # List all players
        list_response = client.get("/api/players")
        assert list_response.status_code == 200
        all_players = list_response.json()
        assert len(all_players) == 3

        # Get each player individually
        for created_player in created_players:
            get_response = client.get(f"/api/player/{created_player['id']}")
            assert get_response.status_code == 200
            retrieved_player = get_response.json()
            assert retrieved_player["id"] == created_player["id"]
            assert retrieved_player["nickname"] == created_player["nickname"]

        # Test filtering
        filter_response = client.get("/api/players?nickname=alice")
        assert filter_response.status_code == 200
        filtered_players = filter_response.json()
        assert len(filtered_players) == 1
        assert filtered_players[0]["nickname"] == "Alice"

    def test_create_player_with_special_characters(self, client: TestClient, db_session: Session):
        """Test creating players with special characters in nickname."""
        special_nicknames = [
            "Player_123",
            "Player-456",
            "Player@789",
            "Player!",
            "Player#1"
        ]

        for nickname in special_nicknames:
            player_data = {"nickname": nickname}
            response = client.post("/api/player", json=player_data)
            
            # Should succeed (assuming no restrictions on special characters)
            assert response.status_code == 200
            assert response.json()["nickname"] == nickname

    def test_create_player_with_unicode_characters(self, client: TestClient, db_session: Session):
        """Test creating players with unicode characters in nickname."""
        unicode_nicknames = [
            "Player_中文",
            "Player_español",
            "Player_русский",
            "Player_🎮"
        ]

        for nickname in unicode_nicknames:
            player_data = {"nickname": nickname}
            response = client.post("/api/player", json=player_data)
            
            # Should succeed (assuming unicode support)
            assert response.status_code == 200
            assert response.json()["nickname"] == nickname
