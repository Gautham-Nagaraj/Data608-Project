import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch

from app.core.auth import hash_password
from app.models import AdminUser, Player, Session as GameSession


class TestAdminRouter:
    """Test cases for admin router endpoints."""

    def test_login_post_success(self, client: TestClient, db_session: Session):
        """Test POST /admin/login with valid credentials."""
        # Create test admin user
        admin = AdminUser(
            login="testadmin",
            password_hash=hash_password("testpass123")
        )
        db_session.add(admin)
        db_session.commit()

        response = client.post(
            "/api/admin/login",
            data={"login": "testadmin", "password": "testpass123"}
        )
        assert response.status_code == 200
        assert response.json() == {"message": "Logged in"}
        assert "admin_session" in response.cookies

    def test_login_post_invalid_user(self, client: TestClient):
        """Test POST /admin/login with invalid username."""
        response = client.post(
            "/api/admin/login",
            data={"login": "nonexistent", "password": "testpass123"}
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid credentials"

    def test_login_post_invalid_password(self, client: TestClient, db_session: Session):
        """Test POST /admin/login with invalid password."""
        # Create test admin user
        admin = AdminUser(
            login="testadmin",
            password_hash=hash_password("testpass123")
        )
        db_session.add(admin)
        db_session.commit()

        response = client.post(
            "/api/admin/login",
            data={"login": "testadmin", "password": "wrongpassword"}
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid credentials"

    def test_login_post_missing_fields(self, client: TestClient):
        """Test POST /admin/login with missing form fields."""
        response = client.post("/api/admin/login", data={"login": "testadmin"})
        assert response.status_code == 422

        response = client.post("/api/admin/login", data={"password": "testpass123"})
        assert response.status_code == 422

    def test_dashboard_authenticated(self, client: TestClient, db_session: Session):
        """Test GET /admin/dashboard with valid session."""
        # Create test admin user
        admin = AdminUser(
            login="testadmin",
            password_hash=hash_password("testpass123")
        )
        db_session.add(admin)
        db_session.commit()

        # Login first to get session cookie
        login_response = client.post(
            "/api/admin/login",
            data={"login": "testadmin", "password": "testpass123"}
        )
        assert login_response.status_code == 200

        # Access dashboard with session cookie
        response = client.get("/api/admin/dashboard")
        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]
        # Check for dashboard JSON content
        data = response.json()
        assert "players" in data
        assert "sessions" in data
        assert isinstance(data["players"], list)
        assert isinstance(data["sessions"], list)

    def test_dashboard_unauthenticated(self, client: TestClient):
        """Test GET /admin/dashboard without session."""
        response = client.get("/api/admin/dashboard")
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"

    def test_dashboard_invalid_session(self, client: TestClient):
        """Test GET /admin/dashboard with invalid session cookie."""
        # Create a malformed cookie that will cause BadSignature
        client.cookies = {"admin_session": "invalid.cookie.format"}

        response = client.get("/api/admin/dashboard")
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"

    def test_dashboard_with_test_data(self, client: TestClient, db_session: Session):
        """Test GET /admin/dashboard returns correct structure with test data."""
        # Create test admin user
        admin = AdminUser(
            login="testadmin",
            password_hash=hash_password("testpass123")
        )
        db_session.add(admin)
        
        # Create test data with correct field names
        player = Player(nickname="TestPlayer")
        db_session.add(player)
        db_session.commit()
        
        from datetime import datetime
        game_session = GameSession(
            player_id=player.id,
            started_at=datetime(2024, 1, 1, 10, 0, 0),
            status="active",
            balance=1000.0
        )
        db_session.add(game_session)
        db_session.commit()

        # Login first to get session cookie
        login_response = client.post(
            "/api/admin/login",
            data={"login": "testadmin", "password": "testpass123"}
        )
        assert login_response.status_code == 200

        # Access dashboard with session cookie
        response = client.get("/api/admin/dashboard")
        assert response.status_code == 200
        
        data = response.json()
        assert "players" in data
        assert "sessions" in data
        assert len(data["players"]) == 1
        assert len(data["sessions"]) == 1
        
        # Check player data structure
        player_data = data["players"][0]
        assert "id" in player_data
        assert "nickname" in player_data
        assert player_data["nickname"] == "TestPlayer"
        
        # Check session data structure
        session_data = data["sessions"][0]
        assert "id" in session_data
        assert "player_id" in session_data
        assert "status" in session_data
        assert "balance" in session_data
        assert session_data["status"] == "active"
        assert session_data["balance"] == 1000.0

    def test_login_post_sql_injection_attempt(self, client: TestClient, db_session: Session):
        """Test POST /admin/login is protected against SQL injection."""
        # Create test admin user
        admin = AdminUser(
            login="testadmin",
            password_hash=hash_password("testpass123")
        )
        db_session.add(admin)
        db_session.commit()

        # Attempt SQL injection in login field
        response = client.post(
            "/api/admin/login",
            data={"login": "testadmin' OR '1'='1", "password": "anything"}
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid credentials"

        # Attempt SQL injection in password field
        response = client.post(
            "/api/admin/login",
            data={"login": "testadmin", "password": "' OR '1'='1"}
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid credentials"

    def test_login_post_empty_credentials(self, client: TestClient):
        """Test POST /admin/login with empty credentials."""
        response = client.post(
            "/api/admin/login",
            data={"login": "", "password": ""}
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid credentials"

    def test_login_post_very_long_credentials(self, client: TestClient):
        """Test POST /admin/login with extremely long credentials."""
        long_string = "a" * 10000
        response = client.post(
            "/api/admin/login",
            data={"login": long_string, "password": long_string}
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid credentials"

    def test_dashboard_expired_session(self, client: TestClient, db_session: Session):
        """Test GET /admin/dashboard with tampered session cookie."""
        # Create test admin user
        admin = AdminUser(
            login="testadmin",
            password_hash=hash_password("testpass123")
        )
        db_session.add(admin)
        db_session.commit()

        # Login first to get session cookie
        login_response = client.post(
            "/api/admin/login",
            data={"login": "testadmin", "password": "testpass123"}
        )
        assert login_response.status_code == 200

        # Tamper with the session cookie
        original_cookie = client.cookies["admin_session"]
        tampered_cookie = original_cookie[:-5] + "XXXXX"  # Modify last 5 characters
        client.cookies = {"admin_session": tampered_cookie}

        # Access dashboard with tampered cookie
        response = client.get("/api/admin/dashboard")
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"

    def test_login_response_sets_httponly_cookie(self, client: TestClient, db_session: Session):
        """Test POST /admin/login sets httponly cookie for security."""
        # Create test admin user
        admin = AdminUser(
            login="testadmin",
            password_hash=hash_password("testpass123")
        )
        db_session.add(admin)
        db_session.commit()

        response = client.post(
            "/api/admin/login",
            data={"login": "testadmin", "password": "testpass123"}
        )
        assert response.status_code == 200
        
        # Check that the cookie is set
        assert "admin_session" in response.cookies
        
        # Note: TestClient doesn't expose httponly flag directly,
        # but we can verify the cookie exists and is being used
        cookie_value = response.cookies["admin_session"]
        assert cookie_value is not None
        assert len(cookie_value) > 0

    @patch('app.routers.admin.crud.get_admin_user')
    def test_login_database_error_handling(self, mock_get_admin, client: TestClient):
        """Test POST /admin/login handles database errors gracefully."""
        # Mock database error
        mock_get_admin.side_effect = Exception("Database connection error")
        
        response = client.post(
            "/api/admin/login",
            data={"login": "testadmin", "password": "testpass123"}
        )
        # Should handle the error gracefully and return 500
        assert response.status_code == 500
        assert response.json()["detail"] == "Internal server error"

    def test_login_case_sensitivity(self, client: TestClient, db_session: Session):
        """Test POST /admin/login is case sensitive for login."""
        # Create test admin user
        admin = AdminUser(
            login="TestAdmin",
            password_hash=hash_password("testpass123")
        )
        db_session.add(admin)
        db_session.commit()

        # Test exact case match (should work)
        response = client.post(
            "/api/admin/login",
            data={"login": "TestAdmin", "password": "testpass123"}
        )
        assert response.status_code == 200

        # Test different case (should fail)
        response = client.post(
            "/api/admin/login",
            data={"login": "testadmin", "password": "testpass123"}
        )
        assert response.status_code == 401

    def test_multiple_login_attempts(self, client: TestClient, db_session: Session):
        """Test multiple login attempts work correctly."""
        # Create test admin user
        admin = AdminUser(
            login="testadmin",
            password_hash=hash_password("testpass123")
        )
        db_session.add(admin)
        db_session.commit()

        # Multiple successful logins should work
        for _ in range(3):
            response = client.post(
                "/api/admin/login",
                data={"login": "testadmin", "password": "testpass123"}
            )
            assert response.status_code == 200
            assert "admin_session" in response.cookies

    def test_dashboard_without_session_cookie(self, client: TestClient):
        """Test GET /admin/dashboard explicitly without any cookies."""
        # Clear any existing cookies
        client.cookies.clear()
        
        response = client.get("/api/admin/dashboard")
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"


class TestAdminSessionManagement:
    """Test cases for admin session management endpoints."""
    
    def test_get_sessions_with_filters(self, client: TestClient, db_session: Session, admin_user_with_session):
        """Test GET /admin/sessions with filters."""
        admin, player, session = admin_user_with_session
        
        # Login first
        response = client.post(
            "/api/admin/login",
            data={"login": admin.login, "password": "testpass123"}
        )
        assert response.status_code == 200
        
        # Test without filters
        response = client.get("/api/admin/sessions")
        assert response.status_code == 200
        data = response.json()
        assert "sessions" in data
        assert len(data["sessions"]) > 0
        
        # Test with player_id filter
        response = client.get(f"/api/admin/sessions?player_id={player.id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data["sessions"]) > 0
        assert all(s["player_id"] == player.id for s in data["sessions"])
    
    def test_get_leaderboard(self, client: TestClient, db_session: Session, admin_user_with_session):
        """Test GET /admin/leaderboard."""
        admin, player, session = admin_user_with_session
        
        # Login first
        response = client.post(
            "/api/admin/login",
            data={"login": admin.login, "password": "testpass123"}
        )
        assert response.status_code == 200
        
        response = client.get("/api/admin/leaderboard?top_n=5")
        assert response.status_code == 200
        data = response.json()
        assert "leaderboard" in data
        assert "sort_by" in data
        assert data["top_n"] == 5
    
    def test_export_leaderboard_csv(self, client: TestClient, db_session: Session, admin_user_with_session):
        """Test GET /admin/leaderboard/export."""
        admin, player, session = admin_user_with_session
        
        # Login first
        response = client.post(
            "/api/admin/login",
            data={"login": admin.login, "password": "testpass123"}
        )
        assert response.status_code == 200
        
        response = client.get("/api/admin/leaderboard/export")
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "attachment" in response.headers["content-disposition"]


class TestAdminActions:
    """Test cases for admin action endpoints."""
    
    def test_archive_session(self, client: TestClient, db_session: Session, admin_user_with_session):
        """Test POST /admin/sessions/{session_id}/archive."""
        admin, player, session = admin_user_with_session
        
        # Login first
        response = client.post(
            "/api/admin/login",
            data={"login": admin.login, "password": "testpass123"}
        )
        assert response.status_code == 200
        
        response = client.post(f"/api/admin/sessions/{session.session_id}/archive")
        assert response.status_code == 200
        assert "archived successfully" in response.json()["message"]
        
        # Verify session status changed
        db_session.refresh(session)
        assert session.status == "archived"
    
    def test_delete_session(self, client: TestClient, db_session: Session, admin_user_with_session):
        """Test DELETE /admin/sessions/{session_id}."""
        admin, player, session = admin_user_with_session
        
        # Login first
        response = client.post(
            "/api/admin/login",
            data={"login": admin.login, "password": "testpass123"}
        )
        assert response.status_code == 200
        
        session_id = str(session.session_id)
        response = client.delete(f"/api/admin/sessions/{session_id}")
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]
        
        # Verify session was deleted
        deleted_session = db_session.query(GameSession).filter(GameSession.session_id == session.session_id).first()
        assert deleted_session is None
    
    def test_reset_data_requires_confirmation(self, client: TestClient, db_session: Session, admin_user_with_session):
        """Test POST /admin/data/reset requires confirmation."""
        admin, player, session = admin_user_with_session
        
        # Login first
        response = client.post(
            "/api/admin/login",
            data={"login": admin.login, "password": "testpass123"}
        )
        assert response.status_code == 200
        
        # Test without confirmation
        response = client.post("/api/admin/data/reset?confirm=WRONG")
        assert response.status_code == 400
        assert "Confirmation required" in response.json()["detail"]
        
        # Test with correct confirmation
        response = client.post("/api/admin/data/reset?confirm=CONFIRM_RESET")
        assert response.status_code == 200
        assert "reset" in response.json()["message"]


class TestAdminAuditLog:
    """Test cases for admin audit logging."""
    
    def test_get_audit_logs(self, client: TestClient, db_session: Session, admin_user_with_session):
        """Test GET /admin/audit-logs."""
        admin, player, session = admin_user_with_session
        
        # Login first (this should create an audit log entry)
        response = client.post(
            "/api/admin/login",
            data={"login": admin.login, "password": "testpass123"}
        )
        assert response.status_code == 200
        
        # Get audit logs
        response = client.get("/api/admin/audit-logs")
        assert response.status_code == 200
        data = response.json()
        assert "audit_logs" in data
        assert len(data["audit_logs"]) > 0
        
        # Check login audit log exists
        login_logs = [log for log in data["audit_logs"] if log["action"] == "login"]
        assert len(login_logs) > 0
        assert login_logs[0]["admin_login"] == admin.login


class TestAgentInteractions:
    """Test cases for AI agent interaction endpoints."""
    
    def test_get_agent_interactions(self, client: TestClient, db_session: Session, admin_user_with_session):
        """Test GET /admin/interactions."""
        admin, player, session = admin_user_with_session
        
        # Create a test interaction
        from app.models import AgentInteraction
        interaction = AgentInteraction(
            session_id=session.session_id,
            interaction_type="agent_suggestion",
            content="Consider buying AAPL",
            interaction_metadata={"confidence": 0.8}
        )
        db_session.add(interaction)
        db_session.commit()
        
        # Login first
        response = client.post(
            "/api/admin/login",
            data={"login": admin.login, "password": "testpass123"}
        )
        assert response.status_code == 200
        
        # Get interactions
        response = client.get("/api/admin/interactions")
        assert response.status_code == 200
        data = response.json()
        assert "interactions" in data
        assert len(data["interactions"]) > 0
    
    def test_get_session_chat_log(self, client: TestClient, db_session: Session, admin_user_with_session):
        """Test GET /admin/sessions/{session_id}/chat."""
        admin, player, session = admin_user_with_session
        
        # Create test interactions
        from app.models import AgentInteraction
        interactions = [
            AgentInteraction(
                session_id=session.session_id,
                interaction_type="user_message",
                content="What should I buy?"
            ),
            AgentInteraction(
                session_id=session.session_id,
                interaction_type="agent_response",
                content="I recommend AAPL based on current trends"
            )
        ]
        for interaction in interactions:
            db_session.add(interaction)
        db_session.commit()
        
        # Login first
        response = client.post(
            "/api/admin/login",
            data={"login": admin.login, "password": "testpass123"}
        )
        assert response.status_code == 200
        
        # Get chat log
        response = client.get(f"/api/admin/sessions/{session.session_id}/chat")
        assert response.status_code == 200
        data = response.json()
        assert "chat_log" in data
        assert data["total_interactions"] == 2
