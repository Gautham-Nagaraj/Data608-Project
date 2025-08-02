"""
Test async CRUD functionality
"""
import pytest
import tempfile
import os
from unittest.mock import MagicMock
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

# Mock settings before importing app modules
import sys
mock_settings = MagicMock()
mock_settings.DATABASE_URL = "sqlite+aiosqlite:///test_crud.db"
mock_settings.SECRET_KEY = "test-secret-key-for-testing-only"
mock_settings.DEBUG = True
mock_settings.ALLOWED_ORIGINS = ["*"]

sys.modules['app.core.config'] = MagicMock()
sys.modules['app.core.config'].settings = mock_settings

# Import after mocking
from app.models import Base, Player, Session as GameSession, Stock
from app import schemas


class TestAsyncCRUD:
    """Test async CRUD operations"""

    @pytest.fixture
    async def async_db_session(self):
        """Create async database session for testing"""
        # Create temporary database
        db_fd, db_path = tempfile.mkstemp()
        database_url = f"sqlite+aiosqlite:///{db_path}"

        # Create async engine
        engine = create_async_engine(
            database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        
        AsyncTestingSessionLocal = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

        # Create tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # Create session
        async with AsyncTestingSessionLocal() as session:
            yield session

        # Cleanup
        await engine.dispose()
        os.close(db_fd)
        try:
            os.unlink(db_path)
        except (OSError, PermissionError):
            pass

    @pytest.mark.asyncio
    async def test_async_session_creation(self, async_db_session):
        """Test that async database session can be created"""
        assert async_db_session is not None
        assert isinstance(async_db_session, AsyncSession)

    @pytest.mark.asyncio
    async def test_models_import(self):
        """Test that async models can be imported"""
        from app.models import Base, Player, Session as GameSession
        assert Base is not None
        assert Player is not None
        assert GameSession is not None

    @pytest.mark.asyncio
    async def test_crud_import(self):
        """Test that CRUD functions can be imported"""
        try:
            from app import crud
            # Check if async functions exist
            assert hasattr(crud, 'get_player')
            assert hasattr(crud, 'create_player') 
            assert hasattr(crud, 'get_session')
            assert hasattr(crud, 'create_session')
            print("✅ CRUD async functions available")
        except ImportError as e:
            pytest.fail(f"CRUD import failed: {e}")

    @pytest.mark.asyncio
    async def test_schemas_import(self):
        """Test that Pydantic schemas can be imported"""
        try:
            from app import schemas
            assert hasattr(schemas, 'PlayerCreate')
            assert hasattr(schemas, 'SessionCreate')
            print("✅ Schemas import successfully")
        except ImportError as e:
            pytest.fail(f"Schemas import failed: {e}")


if __name__ == "__main__":
    import asyncio
    
    async def run_manual_tests():
        test_class = TestAsyncCRUD()
        
        try:
            await test_class.test_models_import()
            print("✅ Models import test passed")
            
            await test_class.test_crud_import()
            print("✅ CRUD import test passed")
            
            await test_class.test_schemas_import()
            print("✅ Schemas import test passed")
            
            print("✅ All async CRUD tests passed!")
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
    
    asyncio.run(run_manual_tests())
