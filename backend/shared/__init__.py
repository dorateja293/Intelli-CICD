"""Shared module for common utilities."""

from shared.database import Base, get_db, get_db_context, init_db
from shared.kafka import (
    TOPIC_ALERTS,
    TOPIC_JOB_EVENTS,
    TOPIC_LOG_ERRORS,
    TOPIC_LOG_STREAM,
    TOPIC_PIPELINE_TRIGGER,
    publish_message,
)
from shared.logging import add_context, clear_context, configure_logging, get_logger
from shared.redis_client import RedisClient, get_redis_client

__all__ = [
    # Database
    "Base",
    "get_db",
    "get_db_context",
    "init_db",
    # Kafka
    "publish_message",
    "TOPIC_PIPELINE_TRIGGER",
    "TOPIC_JOB_EVENTS",
    "TOPIC_LOG_STREAM",
    "TOPIC_LOG_ERRORS",
    "TOPIC_ALERTS",
    # Redis
    "RedisClient",
    "get_redis_client",
    # Logging
    "configure_logging",
    "get_logger",
    "add_context",
    "clear_context",
]
