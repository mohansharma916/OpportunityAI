"""
OpportunityOS — Async Database Engine & Session Factory
Supports SQLite (aiosqlite) for zero-setup local dev and PostgreSQL (asyncpg) for production.
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base

from apps.api.config import settings

# Adjust sqlite connect args if needed
connect_args = {}
if "sqlite" in settings.DATABASE_URL:
    connect_args = {"check_same_thread": False}

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    connect_args=connect_args,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    import apps.api.models  # noqa: F401 - Ensure all models are registered
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
