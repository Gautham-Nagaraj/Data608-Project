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

# Now we can safely import app modules
from app.core.db import get_db
from app.main import app
from app.models import Base


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


@pytest.fixture(scope="function")
def db_session(test_db):
    """Create a database session for testing."""
    session = test_db()
    try:
        yield session
    finally:
        session.close()
