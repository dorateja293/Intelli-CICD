from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Read from backend/.env first, fall back to root .env
        env_file=[".env", "backend/.env"],
        env_file_encoding="utf-8",
        # Ignore fields present in .env that are not declared here
        # (e.g. legacy DB_NAME, DB_USER vars from old Flask app)
        extra="ignore",
    )

    # App
    APP_NAME: str = "Intelli-CI"
    DEBUG: bool = False
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:80",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
    ]

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/intellici"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    SECRET_KEY: str = "change-me-in-production-use-32-char-secret"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # GitHub
    GITHUB_WEBHOOK_SECRET: str = ""
    GITHUB_TOKEN: str = ""

    # LLM — defaults to rule-based (no external calls needed out of the box)
    LLM_PROVIDER: str = "none"  # openai | ollama | none
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"

    # ML
    ML_MODEL_PATH: str = "ml-engine/models/model.pkl"
    DECISION_THRESHOLD_RUN: float = 0.55
    DECISION_THRESHOLD_PARTIAL: float = 0.30

    # Rate limiting (requests / window in seconds)
    RATE_LIMIT_REQUESTS: int = 60
    RATE_LIMIT_WINDOW: int = 60


@lru_cache
def get_settings() -> Settings:
    return Settings()
