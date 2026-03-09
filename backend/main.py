"""
Intelli-CI FastAPI backend
Run locally:  uvicorn backend.main:app --reload --port 8000
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.api import (
    analytics_router,
    auth_router,
    logs_router,
    predict_router,
    profile_router,
    system_router,
    webhook_router,
)
from backend.core.config import get_settings
from backend.database.connection import Base, engine

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(name)s — %(message)s")
logger = logging.getLogger("intelli-ci")

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup (use Alembic migrations for production)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables ensured.")
    yield
    await engine.dispose()


app = FastAPI(
    title="Intelli-CI API",
    description="AI-powered CI/CD optimization — ML + LLM failure prediction",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ────────────────────────────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(predict_router)
app.include_router(analytics_router)
app.include_router(webhook_router)
app.include_router(logs_router)
app.include_router(system_router)
app.include_router(profile_router)


# ── Global exception handler ──────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s", request.url)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


@app.get("/health", tags=["system"])
async def health():
    return {"status": "ok", "service": "intelli-ci-backend"}
