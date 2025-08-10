from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from app.core.config import settings

"""
Database engine and session management.
"""
# Create async SQLAlchemy engine with increased pool size and overflow
async_engine = create_async_engine(
    str(settings.DATABASE_URL),
    pool_pre_ping=True,
    echo=False,
    pool_size=40,         # default is 5, increase as needed
    max_overflow=80,      # default is 10, increase as needed
    pool_timeout=15       # optional: fail faster if pool is exhausted
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Keep sync engine for migrations and admin tasks
sync_engine = create_engine(
    str(settings.DATABASE_URL).replace("postgresql+asyncpg://", "postgresql+psycopg://"),
    pool_pre_ping=True
)

# Sync session factory (for migrations)
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=sync_engine
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Async dependency that provides a database session and ensures it is closed after use.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_db_sync():
    """
    Sync dependency for backwards compatibility and migrations.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
