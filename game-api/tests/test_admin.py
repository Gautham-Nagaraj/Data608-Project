import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.auth import hash_password
from app.models import AdminUser


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
            "/admin/login",
            data={"login": "testadmin", "password": "testpass123"}
        )
        assert response.status_code == 200
        assert response.json() == {"message": "Logged in"}
        assert "admin_session" in response.cookies

    def test_login_post_invalid_user(self, client: TestClient):
        """Test POST /admin/login with invalid username."""
        response = client.post(
            "/admin/login",
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
            "/admin/login",
            data={"login": "testadmin", "password": "wrongpassword"}
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid credentials"

    def test_login_post_missing_fields(self, client: TestClient):
        """Test POST /admin/login with missing form fields."""
        response = client.post("/admin/login", data={"login": "testadmin"})
        assert response.status_code == 422

        response = client.post("/admin/login", data={"password": "testpass123"})
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
            "/admin/login",
            data={"login": "testadmin", "password": "testpass123"}
        )
        assert login_response.status_code == 200

        # Access dashboard with session cookie
        response = client.get("/admin/dashboard")
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
        response = client.get("/admin/dashboard")
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"

    def test_dashboard_invalid_session(self, client: TestClient):
        """Test GET /admin/dashboard with invalid session cookie."""
        # Create a malformed cookie that will cause BadSignature
        client.cookies = {"admin_session": "invalid.cookie.format"}

        response = client.get("/admin/dashboard")
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"
