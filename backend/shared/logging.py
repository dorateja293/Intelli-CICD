"""
Structured Logging Module

Provides JSON-formatted structured logging using structlog.
"""

import logging
import sys
from typing import Any

import structlog

from config.settings import get_settings

settings = get_settings()


def configure_logging(service_name: str | None = None) -> None:
    """Configure structured logging for the application."""
    log_level = getattr(logging, settings.service.log_level, logging.INFO)

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    # Suppress noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.BoundLogger:
    """Get a configured logger instance."""
    logger = structlog.get_logger(name)
    return logger.bind(service=settings.service.service_name)


def add_context(**kwargs: Any) -> None:
    """Add context variables to current logging context."""
    structlog.contextvars.bind_contextvars(**kwargs)


def clear_context() -> None:
    """Clear current logging context."""
    structlog.contextvars.clear_contextvars()
