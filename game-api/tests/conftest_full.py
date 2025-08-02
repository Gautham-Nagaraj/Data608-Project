import os
import tempfile
from typing import Generator
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Mock the settings class for testing to accept any DATABASE_URL
# Create a mock settings object that bypasses PostgresDsn validation
mock_settings = MagicMock()
mock_settings.DATABASE_URL = "sqlite:///test.db"
mock_settings.SECRET_KEY = "test-secret-key-for-testing-only"
mock_settings.DEBUG = True
mock_settings.ALLOWED_ORIGINS = ["*"]

# Patch the settings import before any app modules are imported
import sys
sys.modules['app.core.config'] = MagicMock()
sys.modules['app.core.config'].settings = mock_settings

# Mock the async database parts
mock_db = MagicMock()
mock_db.AsyncSessionLocal = MagicMock()
mock_db.async_engine = MagicMock()
mock_db.get_db = MagicMock()

# Patch db module before importing app
sys.modules['app.core.db'] = mock_db

# Now we can safely import app modules
from app.main import app
from app.models import Base
from app.core.db import get_db


@pytest.fixture(scope="function")
def test_db():
    """Create a temporary SQLite database for testing."""
    # Create a temporary database file
    db_fd, db_path = tempfile.mkstemp()
    database_url = f"sqlite:///{db_path}"

    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Create tables
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    yield TestingSessionLocal

    # Cleanup - dispose engine first to release file locks
    app.dependency_overrides.clear()
    engine.dispose()  # This releases the database connections
    os.close(db_fd)

    # Try to remove the file, but don't fail if it's still locked on Windows
    try:
        os.unlink(db_path)
    except (OSError, PermissionError):
        # On Windows, sometimes the file is still locked, that's okay
        pass


@pytest.fixture(scope="function")
def client(test_db):
    """Create a test client."""
    with TestClient(app) as test_client:
        yield test_client


# Utility fixtures for test data
@pytest.fixture
def sample_player_data():
    """Sample player data for testing."""
    return {
        "nickname": "TestPlayer",
        "email": "test@example.com",
        "experience_level": "beginner"
    }


@pytest.fixture
def sample_session_data():
    """Sample session data for testing."""
    return {
        "player_id": 1,
        "balance": 10000.0,
        "status": "active"
    }


@pytest.fixture
def sample_stock_data():
    """Sample stock data for testing."""
    return {
        "symbol": "AAPL",
        "company_name": "Apple Inc.",
        "category": "popular",
        "sector": "Technology"
    }


@pytest.fixture
def sample_trade_data():
    """Sample trade data for testing."""
    return {
        "session_id": "550e8400-e29b-41d4-a716-446655440000",
        "symbol": "AAPL",
        "action": "buy",
        "shares": 10,
        "price": 150.0
    }


@pytest.fixture
def sample_selection_data():
    """Sample selection data for testing."""
    return {
        "session_id": "550e8400-e29b-41d4-a716-446655440000",
        "popular_symbol": "AAPL",
        "volatile_symbol": "TSLA",
        "sector_symbol": "MSFT",
        "month": 1,
        "year": 2024
    }
