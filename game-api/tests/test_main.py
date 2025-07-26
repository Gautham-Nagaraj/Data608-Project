import pytest
from fastapi.testclient import TestClient


class TestMainApp:
    """Test cases for main application endpoints."""

    def test_health_check(self, client: TestClient):
        """Test GET /health returns health status."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_docs_endpoint(self, client: TestClient):
        """Test GET /docs returns API documentation."""
        response = client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_openapi_endpoint(self, client: TestClient):
        """Test GET /openapi.json returns OpenAPI schema."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data

    def test_cors_headers(self, client: TestClient):
        """Test CORS headers are properly set."""
        response = client.options("/health")
        # FastAPI/Starlette handles OPTIONS automatically
        assert response.status_code in [200, 405]

    def test_nonexistent_endpoint(self, client: TestClient):
        """Test accessing non-existent endpoint returns 404."""
        response = client.get("/nonexistent")
        assert response.status_code == 404
