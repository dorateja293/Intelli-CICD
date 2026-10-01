"""
Log Analyzer Service

Consumes error events from Kafka log.errors topic, uses the rule engine
to classify errors and generate suggestions, and stores results in PostgreSQL.
"""

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

import structlog
from fastapi import Depends, FastAPI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ai.rule_engine import get_rule_matcher
from config.settings import get_settings
from shared.database import get_db, get_db_context, init_db
from shared.kafka import TOPIC_LOG_ERRORS, KafkaConsumerLoop
from shared.logging import configure_logging
from shared.models import AISuggestion, Job
from shared.schemas import LogErrorEvent

settings = get_settings()
configure_logging("log-analyzer")
logger = structlog.get_logger()

rule_matcher = get_rule_matcher()


# ================================
# Error Analysis Handler
# ================================

async def analyze_and_store_suggestion(event: LogErrorEvent) -> None:
    """Analyze error event and store AI suggestion."""
    # Combine all error lines for analysis
    error_text = "\n".join(event.error_lines)

    # Get suggestion from rule engine
    result = rule_matcher.get_suggestion(error_text)

    if not result:
        logger.debug("No matching rule found", error_fingerprint=event.error_fingerprint)
        return

    async with get_db_context() as db:
        import uuid

        # Check if suggestion already exists for this error fingerprint
        existing = await db.execute(
            select(AISuggestion).where(
                AISuggestion.pipeline_id == uuid.UUID(event.pipeline_id),
                AISuggestion.error_fingerprint == event.error_fingerprint,
            )
        )
        if existing.scalar_one_or_none():
            logger.debug("Suggestion already exists", error_fingerprint=event.error_fingerprint)
            return

        # Get job_id if available
        job_id = None
        if event.job_id:
            try:
                job_id = uuid.UUID(event.job_id)
            except ValueError:
                pass

        # Create suggestion
        suggestion = AISuggestion(
            pipeline_id=uuid.UUID(event.pipeline_id),
            job_id=job_id,
            error_fingerprint=event.error_fingerprint,
            error_type=result["error_type"],
            error_message=error_text[:1000],  # Truncate if too long
            suggestion_text=result["suggestion"],
            confidence_score=result["confidence"],
            rule_id=result["rule_id"],
            model_used="rule_engine",
        )
        db.add(suggestion)
        await db.commit()

        logger.info(
            "AI suggestion stored",
            rule_id=result["rule_id"],
            error_type=result["error_type"],
            pipeline_id=event.pipeline_id,
        )


# ================================
# Kafka Message Handler
# ================================

async def handle_kafka_message(msg: Any) -> None:
    """Handle incoming error event from Kafka."""
    try:
        event = LogErrorEvent.model_validate_json(msg.value())
        await analyze_and_store_suggestion(event)
    except Exception as e:
        logger.error("Error processing message", error=str(e))


# ================================
# FastAPI App
# ================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting log analyzer")
    await init_db()

    # Start Kafka consumer
    consumer = KafkaConsumerLoop("log-analyzer", [TOPIC_LOG_ERRORS])
    consumer_task = asyncio.create_task(consumer.start(handle_kafka_message))

    yield

    logger.info("Shutting down log analyzer")
    consumer.stop()
    consumer_task.cancel()


app = FastAPI(
    title="Intelli-CI Log Analyzer",
    description="AI-powered error analysis and suggestion service",
    version="1.0.0",
    lifespan=lifespan,
)


@app.post("/api/v1/analyze")
async def analyze_text(
    error_text: str,
):
    """Analyze error text and return suggestions."""
    suggestions = rule_matcher.analyze_logs(error_text.split("\n"))
    return {"suggestions": suggestions}


@app.get("/api/v1/rules")
async def list_rules():
    """List all available rules."""
    return {
        "rules": [
            {
                "id": r.id,
                "error_type": r.error_type,
                "description": r.description,
                "category": r.category,
                "confidence": r.confidence,
            }
            for r in rule_matcher.rules
        ],
        "total": len(rule_matcher.rules),
    }


@app.get("/health")
async def health():
    """Liveness probe."""
    return {"status": "ok"}


# ================================
# Entry Point
# ================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8006, reload=True)
