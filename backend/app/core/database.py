from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from ..core.config import settings

# Construct database URL from environment (should be set in docker-compose)
POSTGRES_HOST = settings.POSTGRES_HOST or "postgres"
POSTGRES_USER = settings.POSTGRES_USER or "hivebot"
POSTGRES_PASSWORD = settings.POSTGRES_PASSWORD or "hivebot"
POSTGRES_DB = settings.POSTGRES_DB or "hivebot"

DATABASE_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}/{POSTGRES_DB}"

engine = create_async_engine(DATABASE_URL, echo=False, future=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
