"""
Notification Service

Consumes alert events from Kafka topic alerts, deduplicates to prevent
notification storms, routes to configured channels (Slack, email, PagerDuty,
MS Teams, custom webhooks), and provides API for managing notification
configurations.
"""

import asyncio
import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Optional

import httpx
import structlog
from fastapi import Depends, FastAPI, HTTPException
from jinja2 import Environment
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import get_settings
from shared.database import get_db, get_db_context, init_db
from shared.kafka import TOPIC_ALERTS, KafkaConsumerLoop
from shared.logging import configure_logging
from shared.models import NotificationConfig
from shared.redis_client import get_redis_client
from shared.schemas import AlertEvent, NotificationConfigCreate, NotificationConfigUpdate

settings = get_settings()
configure_logging("notification-service")
logger = structlog.get_logger()


# ================================
# Jinja2 Template Engine
# ================================

jinja_env = Environment()

TEMPLATES = {
    "pipeline_failed": {
        "title": "Pipeline Failed: {{ repo_name }} #{{ pipeline_id[:8] }}",
        "body": """
Pipeline **#{{ pipeline_id[:8] }}** on `{{ branch }}` failed.

**Commit:** `{{ commit_sha[:8] }}`
**Author:** {{ author }}

[View Pipeline]({{ dashboard_url }}/pipelines/{{ pipeline_id }})
        """.strip(),
    },
    "pipeline_succeeded": {
        "title": "Pipeline Passed: {{ repo_name }} #{{ pipeline_id[:8] }}",
        "body": "Pipeline `#{{ pipeline_id[:8] }}` on `{{ branch }}` completed successfully.",
    },
    "pipeline_cancelled": {
        "title": "Pipeline Cancelled: {{ repo_name }} #{{ pipeline_id[:8] }}",
        "body": "Pipeline `#{{ pipeline_id[:8] }}` on `{{ branch }}` was cancelled.",
    },
    "security_critical": {
        "title": "CRITICAL Security Alert: {{ repo_name }}",
        "body": """
**{{ critical_count }} CRITICAL** vulnerabilities found in pipeline #{{ pipeline_id[:8] }}.
Pipeline has been **BLOCKED**.

[View Security Report]({{ dashboard_url }}/pipelines/{{ pipeline_id }}/security)
        """.strip(),
    },
    "secret_detected": {
        "title": "Secret Detected: {{ repo_name }}",
        "body": """
**Secret detected** in pipeline #{{ pipeline_id[:8] }}.
Pipeline has been **BLOCKED**.

Please rotate any exposed credentials immediately.

[View Details]({{ dashboard_url }}/pipelines/{{ pipeline_id }}/security)
        """.strip(),
    },
    "job_failed": {
        "title": "Job Failed: {{ job_name }} in {{ repo_name }}",
        "body": "Job `{{ job_name }}` failed in pipeline #{{ pipeline_id[:8] }}.",
    },
    "slo_breach": {
        "title": "SLO Breach: {{ repo_name }}",
        "body": "Service Level Objective breached for {{ repo_name }}. Check metrics for details.",
    },
}


def render_template(event_type: str, context: dict[str, Any]) -> tuple[str, str]:
    """Render notification template."""
    template = TEMPLATES.get(event_type, {
        "title": f"Alert: {event_type}",
        "body": "{{ message }}",
    })
    title = jinja_env.from_string(template["title"]).render(**context)
    body = jinja_env.from_string(template["body"]).render(**context)
    return title, body


# ================================
# Deduplication
# ================================

ALWAYS_NOTIFY = {"security_critical", "secret_detected"}


async def is_duplicate_alert(event: AlertEvent) -> bool:
    """Check if alert should be deduplicated."""
    # Never deduplicate critical security events
    if event.event_type in ALWAYS_NOTIFY:
        return False

    redis = get_redis_client()
    dedup_key = f"notif:dedup:{event.org_id}:{event.repo_id}:{event.event_type}"
    result = await redis.set(dedup_key, "1", nx=True, ex=300)  # 5-minute TTL
    return result is None  # None = key existed = duplicate


# ================================
# Channel Dispatchers
# ================================

async def send_slack(webhook_url: str, title: str, body: str, severity: str) -> None:
    """Send notification to Slack."""
    color_map = {"INFO": "#36a64f", "WARN": "#f59e0b", "ERROR": "#ef4444", "CRITICAL": "#7c3aed"}
    payload = {
        "attachments": [
            {
                "color": color_map.get(severity, "#94a3b8"),
                "title": title,
                "text": body,
                "mrkdwn_in": ["text"],
                "footer": "Intelli-CI/CD",
                "ts": int(time.time()),
            }
        ]
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(webhook_url, json=payload, timeout=10.0)
        resp.raise_for_status()


async def send_email(recipients: list[str], title: str, body: str, smtp_config: dict) -> None:
    """Send notification via email."""
    try:
        import aiosmtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        msg = MIMEMultipart("alternative")
        msg["Subject"] = title
        msg["From"] = smtp_config.get("from_address", settings.smtp.from_address)
        msg["To"] = ", ".join(recipients)
        msg.attach(MIMEText(body, "plain"))

        # Simple HTML conversion
        html_body = f"<html><body><pre>{body}</pre></body></html>"
        msg.attach(MIMEText(html_body, "html"))

        await aiosmtplib.send(
            msg,
            hostname=smtp_config.get("host", settings.smtp.host),
            port=smtp_config.get("port", settings.smtp.port),
            username=smtp_config.get("username", settings.smtp.username),
            password=smtp_config.get("password", settings.smtp.password),
            use_tls=True,
        )
    except ImportError:
        logger.warning("aiosmtplib not installed, skipping email notification")


async def send_pagerduty(routing_key: str, title: str, body: str, severity: str, pipeline_id: str) -> None:
    """Send notification to PagerDuty."""
    severity_map = {"CRITICAL": "critical", "ERROR": "error", "WARN": "warning", "INFO": "info"}
    payload = {
        "routing_key": routing_key,
        "event_action": "trigger",
        "dedup_key": f"pipeline-{pipeline_id}",
        "payload": {
            "summary": title,
            "severity": severity_map.get(severity, "warning"),
            "source": "intelli-cicd",
            "custom_details": {"body": body},
        },
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://events.pagerduty.com/v2/enqueue",
            json=payload,
            timeout=10.0,
        )
        resp.raise_for_status()


async def send_teams(webhook_url: str, title: str, body: str, severity: str) -> None:
    """Send notification to MS Teams."""
    color_map = {"INFO": "00FF00", "WARN": "FFFF00", "ERROR": "FF0000", "CRITICAL": "800080"}
    payload = {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "themeColor": color_map.get(severity, "94a3b8"),
        "summary": title,
        "sections": [{"activityTitle": title, "activityText": body}],
    }
    async with httpx.AsyncClient() as client:
        await client.post(webhook_url, json=payload, timeout=10.0)


async def send_webhook(webhook_url: str, title: str, body: str, event: AlertEvent) -> None:
    """Send notification to custom webhook."""
    payload = {
        "title": title,
        "body": body,
        "event_type": event.event_type,
        "severity": event.severity,
        "pipeline_id": event.pipeline_id,
        "repo_id": event.repo_id,
        "timestamp": event.timestamp,
        "metadata": event.metadata,
    }
    async with httpx.AsyncClient() as client:
        await client.post(webhook_url, json=payload, timeout=10.0)


# ================================
# Notification Dispatcher
# ================================

async def dispatch_notification(
    config: NotificationConfig,
    title: str,
    body: str,
    event: AlertEvent,
) -> None:
    """Dispatch notification to configured channel with retry."""
    channel = config.channel
    cfg = config.config

    for attempt in range(1, 4):  # 3 attempts
        try:
            if channel == "slack":
                await send_slack(cfg["webhook_url"], title, body, event.severity)
            elif channel == "email":
                await send_email(cfg["recipients"], title, body, cfg)
            elif channel == "pagerduty":
                await send_pagerduty(cfg["routing_key"], title, body, event.severity, event.pipeline_id)
            elif channel == "teams":
                await send_teams(cfg["webhook_url"], title, body, event.severity)
            elif channel == "webhook":
                await send_webhook(cfg["webhook_url"], title, body, event)

            logger.info(
                "Notification sent",
                channel=channel,
                config_id=str(config.id),
                event_type=event.event_type,
            )
            return  # Success

        except Exception as e:
            if attempt == 3:
                logger.error(
                    "Notification delivery failed",
                    channel=channel,
                    config_id=str(config.id),
                    error=str(e),
                )
            else:
                await asyncio.sleep(2**attempt)  # Exponential backoff: 2s, 4s


# ================================
# Alert Handler
# ================================

async def handle_alert(event: AlertEvent) -> None:
    """Handle incoming alert event."""
    logger.info(
        "Processing alert",
        event_type=event.event_type,
        pipeline_id=event.pipeline_id,
        severity=event.severity,
    )

    # Check deduplication
    if await is_duplicate_alert(event):
        logger.info("Duplicate alert suppressed", event_type=event.event_type)
        return

    async with get_db_context() as db:
        import uuid

        # Get matching notification configs
        result = await db.execute(
            select(NotificationConfig).where(
                NotificationConfig.org_id == uuid.UUID(event.org_id),
                NotificationConfig.active == True,
            )
        )
        configs = result.scalars().all()

        # Filter configs by event type
        matching_configs = [c for c in configs if event.event_type in c.events]

        if not matching_configs:
            logger.debug("No notification configs match event", event_type=event.event_type)
            return

        # Build template context
        context = {
            "repo_name": event.metadata.get("repo_name", "Unknown"),
            "pipeline_id": event.pipeline_id,
            "branch": event.metadata.get("branch", "unknown"),
            "commit_sha": event.metadata.get("commit_sha", "unknown"),
            "author": event.metadata.get("author", "unknown"),
            "message": event.message,
            "dashboard_url": settings.service.dashboard_url,
            "critical_count": event.metadata.get("critical", 0),
            "job_name": event.metadata.get("job_name", "unknown"),
        }

        # Render template
        title, body = render_template(event.event_type, context)

        # Send to all matching configs
        for config in matching_configs:
            await dispatch_notification(config, title, body, event)


# ================================
# Kafka Message Handler
# ================================

async def handle_kafka_message(msg: Any) -> None:
    """Handle incoming Kafka messages."""
    try:
        event = AlertEvent.model_validate_json(msg.value())
        await handle_alert(event)
    except Exception as e:
        logger.error("Alert processing error", error=str(e))


# ================================
# FastAPI App
# ================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting notification service")
    await init_db()

    # Start Kafka consumer
    consumer = KafkaConsumerLoop("notification-service", [TOPIC_ALERTS])
    consumer_task = asyncio.create_task(consumer.start(handle_kafka_message))

    yield

    logger.info("Shutting down notification service")
    consumer.stop()
    consumer_task.cancel()


app = FastAPI(
    title="Intelli-CI Notification Service",
    description="Multi-channel notification delivery service",
    version="1.0.0",
    lifespan=lifespan,
)


# ================================
# API Endpoints
# ================================

@app.get("/api/v1/orgs/{org_id}/notifications")
async def list_notification_configs(
    org_id: str,
    db: AsyncSession = Depends(get_db),
):
    """List all notification configs for an organization."""
    import uuid

    result = await db.execute(
        select(NotificationConfig).where(NotificationConfig.org_id == uuid.UUID(org_id))
    )
    configs = result.scalars().all()

    return {
        "data": [
            {
                "id": str(c.id),
                "name": c.name,
                "channel": c.channel,
                "events": c.events,
                "active": c.active,
                "created_at": c.created_at.isoformat(),
            }
            for c in configs
        ]
    }


@app.post("/api/v1/orgs/{org_id}/notifications")
async def create_notification_config(
    org_id: str,
    config_data: NotificationConfigCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new notification config."""
    import uuid

    config = NotificationConfig(
        org_id=uuid.UUID(org_id),
        name=config_data.name,
        channel=config_data.channel,
        config=config_data.config,
        events=config_data.events,
        active=config_data.active,
    )
    db.add(config)
    await db.commit()
    await db.refresh(config)

    return {
        "data": {
            "id": str(config.id),
            "name": config.name,
            "channel": config.channel,
            "events": config.events,
            "active": config.active,
        }
    }


@app.put("/api/v1/orgs/{org_id}/notifications/{config_id}")
async def update_notification_config(
    org_id: str,
    config_id: str,
    update_data: NotificationConfigUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a notification config."""
    import uuid

    result = await db.execute(
        select(NotificationConfig).where(
            NotificationConfig.id == uuid.UUID(config_id),
            NotificationConfig.org_id == uuid.UUID(org_id),
        )
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(status_code=404, detail="Config not found")

    if update_data.name is not None:
        config.name = update_data.name
    if update_data.config is not None:
        config.config = update_data.config
    if update_data.events is not None:
        config.events = update_data.events
    if update_data.active is not None:
        config.active = update_data.active

    await db.commit()
    return {"status": "updated", "id": config_id}


@app.delete("/api/v1/orgs/{org_id}/notifications/{config_id}")
async def delete_notification_config(
    org_id: str,
    config_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a notification config."""
    import uuid

    result = await db.execute(
        select(NotificationConfig).where(
            NotificationConfig.id == uuid.UUID(config_id),
            NotificationConfig.org_id == uuid.UUID(org_id),
        )
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(status_code=404, detail="Config not found")

    await db.delete(config)
    await db.commit()
    return {"status": "deleted", "id": config_id}


@app.post("/api/v1/orgs/{org_id}/notifications/{config_id}/test")
async def test_notification_config(
    org_id: str,
    config_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Send a test notification."""
    import uuid

    result = await db.execute(
        select(NotificationConfig).where(
            NotificationConfig.id == uuid.UUID(config_id),
            NotificationConfig.org_id == uuid.UUID(org_id),
        )
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(status_code=404, detail="Config not found")

    # Create test event
    test_event = AlertEvent(
        event_type="pipeline_succeeded",
        org_id=org_id,
        repo_id="test-repo-id",
        pipeline_id="test-pipeline-id",
        severity="INFO",
        title="Test Notification",
        message="This is a test notification from Intelli-CI",
        metadata={"branch": "main", "commit_sha": "abc123", "author": "Test User"},
        timestamp=datetime.utcnow().isoformat() + "Z",
    )

    title, body = render_template("pipeline_succeeded", {
        "repo_name": "test-repo",
        "pipeline_id": "test-pipeline-id",
        "branch": "main",
        "commit_sha": "abc12345",
        "author": "Test User",
        "message": "Test notification",
        "dashboard_url": settings.service.dashboard_url,
    })

    try:
        await dispatch_notification(config, title, body, test_event)
        return {"status": "sent", "message": "Test notification sent successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send test notification: {e}")


@app.get("/health")
async def health():
    """Liveness probe."""
    return {"status": "ok"}


# ================================
# Entry Point
# ================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.service.notification_port,
        reload=True,
    )
