import pytest
import asyncio
import asyncpg
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from httpx import AsyncClient
from typing import AsyncGenerator, Generator
from fastapi import FastAPI

from app.core.database import Base, get_db
from app.main import app
from app.core.config import settings
from app.services.redis_service import redis_service

# Use a separate test database
TEST_DATABASE_URL = "postgresql+asyncpg://hivebot:hivebot@localhost/hivebot_test"

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

@pytest.fixture
async def session(engine) -> AsyncGenerator[AsyncSession, None]:
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session

@pytest.fixture
async def client(session) -> AsyncGenerator:
    # Override dependency to use test session
    async def override_get_db():
        yield session
    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()

@pytest.fixture
async def redis_client():
    client = await redis.from_url("redis://localhost:6379/1", decode_responses=True)
    await client.flushdb()
    yield client
    await client.flushdb()
    await client.close()
