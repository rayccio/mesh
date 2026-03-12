import os
import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from httpx import AsyncClient, ASGITransport
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, patch

# Set environment variables before importing app modules
os.environ['HIVEBOT_DATA'] = '/tmp/hivebot_test'
os.environ['INTERNAL_API_KEY'] = 'test-internal-key'

# Import app modules after env vars are set
from app.main import app as fastapi_app  # rename to avoid confusion
from app.core.config import settings
from app.services.redis_service import redis_service
import app.core.database

TEST_DATABASE_URL = "postgresql+asyncpg://hivebot:hivebot@localhost/hivebot_test"

# -------------------------------------------------------------------
# Session‑scoped autouse fixture to set up the test database and
# replace the global AsyncSessionLocal before any service modules are used.
# -------------------------------------------------------------------
@pytest.fixture(scope="session", autouse=True)
async def setup_test_database():
    """Create the test engine and patch AsyncSessionLocal for all tests."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=NullPool)
    async with engine.begin() as conn:
        await conn.run_sync(app.core.database.Base.metadata.drop_all)
        await conn.run_sync(app.core.database.Base.metadata.create_all)

    # Create a sessionmaker bound to this test engine
    test_sessionmaker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Replace the global AsyncSessionLocal with our test sessionmaker
    app.core.database.AsyncSessionLocal = test_sessionmaker

    yield

    await engine.dispose()


# -------------------------------------------------------------------
# Function‑scoped fixtures
# -------------------------------------------------------------------
@pytest.fixture(scope="function")
def event_loop() -> Generator:
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a database session for tests that need it."""
    async with app.core.database.AsyncSessionLocal() as session:
        yield session
        await session.rollback()


# Autouse fixture to mock Redis for every test
@pytest.fixture(autouse=True)
def mock_redis():
    redis_mock = AsyncMock()
    redis_mock.ping = AsyncMock(return_value=True)
    redis_mock.publish = AsyncMock()
    redis_mock.get = AsyncMock(return_value=None)
    redis_mock.set = AsyncMock()
    redis_mock.delete = AsyncMock()
    redis_mock.client = redis_mock  # for direct attribute access

    with patch.object(redis_service, 'client', redis_mock):
        yield


# Autouse fixture to patch settings.secrets.get
@pytest.fixture(autouse=True)
def patch_settings():
    with patch.object(settings.secrets, 'get', side_effect=lambda key, default=None: 'test-internal-key' if key == 'INTERNAL_API_KEY' else default):
        yield


@pytest.fixture
async def client(session) -> AsyncGenerator:
    """Provide an HTTP client with the test session."""
    async def override_get_db():
        yield session

    fastapi_app.dependency_overrides[app.core.database.get_db] = override_get_db

    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    fastapi_app.dependency_overrides.clear()
