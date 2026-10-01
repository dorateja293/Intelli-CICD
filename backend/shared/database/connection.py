"""
Database Connection Module

Provides async SQLAlchemy engine and session management.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from config.settings import get_settings

settings = get_settings()


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


def _create_engine():
    """Create database engine with appropriate settings based on database type."""
    db_url = settings.database.database_url
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
            fallback_url = "sqlite+aiosqlite:///D:/intelli-ci/backend/test.db"
            engine = create_async_engine(fallback_url, echo=False)
            async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
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
    except Exception as exc:
        # Switch to SQLite database on fallback
        fallback_url = "sqlite+aiosqlite:///D:/intelli-ci/backend/test.db"
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
