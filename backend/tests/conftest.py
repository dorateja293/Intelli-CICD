"""
Test configuration — sets up the SQLite test database before collection begins.

Environment variables MUST be set before any backend module is imported
(pydantic-settings caches Settings on first use via @lru_cache).
"""
import asyncio
import os

# ── Override env vars before any backend import ───────────────────────────────
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"
os.environ.setdefault("SECRET_KEY", "test-secret-key-32-chars-minimum!!")
os.environ.setdefault("LLM_PROVIDER", "none")
os.environ.setdefault("ML_MODEL_PATH", "")

import pytest  # noqa: E402

# Import engine/Base only after env vars are set so `get_settings()` cache
# is populated with the test values on first call.
from backend.database.connection import Base, engine  # noqa: E402
from backend.main import app  # noqa: E402, F401  (re-exported for test_api.py)


# ── Synchronous session-scoped DB setup (avoids event_loop scope conflicts) ──

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Drop and recreate all tables once per test session for a clean state."""

    async def _init():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)

    async def _cleanup():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    asyncio.run(_init())
    yield
    asyncio.run(_cleanup())
