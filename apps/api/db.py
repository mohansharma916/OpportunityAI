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
        await conn.run_sync(_add_missing_columns)
        await conn.run_sync(_purge_stored_credentials)


def _add_missing_columns(sync_conn) -> None:
    """create_all never alters existing tables; add new nullable columns to older databases."""
    from sqlalchemy import inspect, text

    inspector = inspect(sync_conn)
    existing_tables = set(inspector.get_table_names())
    for table in Base.metadata.sorted_tables:
        if table.name not in existing_tables:
            continue
        present = {c["name"] for c in inspector.get_columns(table.name)}
        for column in table.columns:
            if column.name in present or not column.nullable:
                continue
            col_type = column.type.compile(dialect=sync_conn.dialect)
            sync_conn.execute(text(f'ALTER TABLE {table.name} ADD COLUMN "{column.name}" {col_type}'))


def _purge_stored_credentials(sync_conn) -> None:
    """
    Logins now live only in the candidate's own browser profile.
    Drop any passwords / session cookies that older versions stored in the database.
    """
    from sqlalchemy import inspect, text

    inspector = inspect(sync_conn)
    tables = inspector.get_table_names()
    if "account_credentials" in tables:
        sync_conn.execute(text("DROP TABLE account_credentials"))
    if "scraping_platforms" in tables:
        columns = {c["name"] for c in inspector.get_columns("scraping_platforms")}
        for col in ("auth_password", "auth_username"):
            if col in columns:
                sync_conn.execute(text(f"ALTER TABLE scraping_platforms DROP COLUMN {col}"))
