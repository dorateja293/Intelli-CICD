"""
Database Connection Module

Provides async SQLAlchemy engine and session management.
Automatically normalises Render/Heroku-style postgres:// URLs to
the postgresql+asyncpg:// dialect required by SQLAlchemy async.
"""

import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from config.settings import get_settings

settings = get_settings()


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


def _normalise_db_url(url: str) -> str:
    """
    Normalise database URL for async SQLAlchemy usage.

    - postgres://...           → postgresql+asyncpg://...   (Render/Heroku style)
    - postgresql://...         → postgresql+asyncpg://...   (plain psycopg2 style)
    - postgresql+asyncpg://... → unchanged (already correct)
    - sqlite://...             → sqlite+aiosqlite://...
    - sqlite+aiosqlite://...   → unchanged
    """
    if url.startswith("postgres://"):
        return "postgresql+asyncpg://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        return "postgresql+asyncpg://" + url[len("postgresql://"):]
    if url.startswith("sqlite://") and not url.startswith("sqlite+aiosqlite://"):
        return "sqlite+aiosqlite://" + url[len("sqlite://"):]
    return url


def _sqlite_fallback_url() -> str:
    """Return a cross-platform writable SQLite URL for development fallback."""
    # /tmp is writable on Linux (Render) and macOS; use a relative path on Windows
    if os.name == "nt":
        return "sqlite+aiosqlite:///./test.db"
    return "sqlite+aiosqlite:////tmp/intellici.db"


def _create_engine(url: str | None = None):
    """Create database engine with appropriate settings based on database type."""
    raw_url = url or settings.database.database_url
    db_url = _normalise_db_url(raw_url)
    is_sqlite = db_url.startswith("sqlite")

    engine_kwargs = {
        "echo": settings.service.log_level == "DEBUG",
    }

    if not is_sqlite:
        engine_kwargs.update({
            "pool_size": settings.database.pool_size,
            "max_overflow": settings.database.max_overflow,
            "pool_timeout": settings.database.pool_timeout,
        })

    return create_async_engine(db_url, **engine_kwargs)


# Create async engine
engine = _create_engine()

# Session factory
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting database sessions with seamless fallback."""
    global engine, async_session_factory

    session = async_session_factory()
    if not str(engine.url).startswith("sqlite"):
        try:
            from sqlalchemy import text
            await session.execute(text("SELECT 1"))
        except Exception:
            fallback_url = _sqlite_fallback_url()
            engine = create_async_engine(fallback_url, echo=False)
            async_session_factory = async_sessionmaker(
                engine, class_=AsyncSession, expire_on_commit=False
            )
            await session.close()
            session = async_session_factory()

    try:
        yield session
    finally:
        await session.close()


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for database sessions (for non-FastAPI use)."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database tables with graceful SQLite fallback."""
    global engine, async_session_factory
    import shared.models.models  # noqa: F401
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception:
        # PostgreSQL unavailable — fall back to SQLite
        fallback_url = _sqlite_fallback_url()
        engine = create_async_engine(fallback_url, echo=False)
        async_session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close database connections."""
    await engine.dispose()
