import os
import tempfile
from typing import AsyncGenerator
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Mock the settings class for testing to accept any DATABASE_URL
# Create a mock settings object that bypasses PostgresDsn validation
mock_settings = MagicMock()
mock_settings.DATABASE_URL = "sqlite+aiosqlite:///test.db"
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
async def async_test_db():
    """Create a temporary async SQLite database for testing."""
    # Create a temporary database file
    db_fd, db_path = tempfile.mkstemp()
    database_url = f"sqlite+aiosqlite:///{db_path}"

    # Create async engine
    async_engine = create_async_engine(
        database_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    AsyncTestingSessionLocal = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    # Create tables
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with AsyncTestingSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    yield AsyncTestingSessionLocal

    # Cleanup
    app.dependency_overrides.clear()
    await async_engine.dispose()
    os.close(db_fd)

    # Try to remove the file, but don't fail if it's still locked on Windows
    try:
        os.unlink(db_path)
    except (OSError, PermissionError):
        # On Windows, sometimes the file is still locked, that's okay
        pass


@pytest.fixture(scope="function")
def test_db():
    """Create a temporary SQLite database for testing (sync version for compatibility)."""
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


@pytest.fixture(scope="function")
def admin_user_with_session(db_session):
    """Create an admin user, player, and session for testing."""
    from app.models import AdminUser, Player, Session as GameSession
    from app.core.auth import hash_password
    import uuid
    from datetime import datetime
    
    # Create admin user
    admin = AdminUser(
        login="testadmin",
        password_hash=hash_password("testpass123")
    )
    db_session.add(admin)
    
    # Create player
    player = Player(nickname="TestPlayer")
    db_session.add(player)
    db_session.flush()  # Get the player ID
    
    # Create session
    session = GameSession(
        session_id=uuid.uuid4(),
        player_id=player.id,
        started_at=datetime.utcnow(),
        status="active",
        balance=10000.0
    )
    db_session.add(session)
    db_session.commit()
    
    return admin, player, session
