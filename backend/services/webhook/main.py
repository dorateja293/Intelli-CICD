"""
Webhook Service

Receives webhook events from Git providers (GitHub, GitLab, Bitbucket),
validates authenticity via HMAC-SHA256, normalizes payloads into a
canonical schema, and publishes to Kafka for downstream processing.
"""

import hashlib
import hmac
import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Optional

import structlog
from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import get_settings
from shared.database import get_db, init_db
from shared.kafka import TOPIC_PIPELINE_TRIGGER, flush_producer, publish_message
from shared.logging import configure_logging
from shared.models import Repository
from shared.redis_client import get_redis_client
from shared.schemas import PipelineTriggerEvent, WebhookResponse

settings = get_settings()
configure_logging("webhook-service")
logger = structlog.get_logger()


# ================================
# Lifespan Management
# ================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting webhook service")
    await init_db()
    yield
    logger.info("Shutting down webhook service")
    flush_producer()


# ================================
# FastAPI App
# ================================

app = FastAPI(
    title="Intelli-CI Webhook Service",
    description="Webhook ingestion service for CI/CD triggers",
    version="1.0.0",
    lifespan=lifespan,
)


# ================================
# HMAC Signature Validation
# ================================

def validate_github_signature(payload: bytes, secret: str, signature_header: Optional[str]) -> bool:
    """Validate GitHub webhook signature (HMAC-SHA256)."""
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature_header)


def validate_gitlab_token(token_header: Optional[str], stored_secret: str) -> bool:
    """Validate GitLab webhook token (plain string comparison)."""
    return hmac.compare_digest(token_header or "", stored_secret)


def validate_bitbucket_signature(payload: bytes, secret: str, signature_header: Optional[str]) -> bool:
    """Validate Bitbucket webhook signature (HMAC-SHA256)."""
    if not signature_header:
        return False
    expected = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature_header)


# ================================
# Payload Normalization
# ================================

def normalize_github_push(payload: dict[str, Any], repo_id: str) -> PipelineTriggerEvent:
    """Normalize GitHub push event to canonical format."""
    return PipelineTriggerEvent(
        idempotency_key=f"{payload['repository']['id']}:{payload['after']}",
        trigger_type="push",
        provider="github",
        repo_id=repo_id,
        repo_url=payload["repository"]["clone_url"],
        branch=payload["ref"].replace("refs/heads/", ""),
        commit_sha=payload["after"],
        commit_message=payload.get("head_commit", {}).get("message", ""),
        author_email=payload.get("head_commit", {}).get("author", {}).get("email", ""),
        author_name=payload.get("head_commit", {}).get("author", {}).get("name", ""),
        triggered_at=datetime.utcnow(),
    )


def normalize_github_pr(payload: dict[str, Any], repo_id: str) -> PipelineTriggerEvent:
    """Normalize GitHub pull request event to canonical format."""
    pr = payload["pull_request"]
    return PipelineTriggerEvent(
        idempotency_key=f"{payload['repository']['id']}:{pr['head']['sha']}:pr{payload['number']}",
        trigger_type="pull_request",
        provider="github",
        repo_id=repo_id,
        repo_url=payload["repository"]["clone_url"],
        branch=pr["head"]["ref"],
        commit_sha=pr["head"]["sha"],
        commit_message=pr["title"],
        author_email=pr["user"].get("email", ""),
        author_name=pr["user"]["login"],
        pr_number=payload["number"],
        triggered_at=datetime.utcnow(),
    )


def normalize_gitlab_push(payload: dict[str, Any], repo_id: str) -> PipelineTriggerEvent:
    """Normalize GitLab push event to canonical format."""
    return PipelineTriggerEvent(
        idempotency_key=f"{payload['project']['id']}:{payload['after']}",
        trigger_type="push",
        provider="gitlab",
        repo_id=repo_id,
        repo_url=payload["project"]["git_http_url"],
        branch=payload["ref"].replace("refs/heads/", ""),
        commit_sha=payload["after"],
        commit_message=payload.get("commits", [{}])[0].get("message", "") if payload.get("commits") else "",
        author_email=payload.get("user_email", ""),
        author_name=payload.get("user_name", ""),
        triggered_at=datetime.utcnow(),
    )


def normalize_gitlab_mr(payload: dict[str, Any], repo_id: str) -> PipelineTriggerEvent:
    """Normalize GitLab merge request event to canonical format."""
    mr = payload["object_attributes"]
    return PipelineTriggerEvent(
        idempotency_key=f"{payload['project']['id']}:{mr['last_commit']['id']}:mr{mr['iid']}",
        trigger_type="pull_request",
        provider="gitlab",
        repo_id=repo_id,
        repo_url=payload["project"]["git_http_url"],
        branch=mr["source_branch"],
        commit_sha=mr["last_commit"]["id"],
        commit_message=mr["title"],
        author_email=mr["last_commit"].get("author", {}).get("email", ""),
        author_name=payload["user"]["username"],
        pr_number=mr["iid"],
        triggered_at=datetime.utcnow(),
    )


def normalize_bitbucket_push(payload: dict[str, Any], repo_id: str) -> PipelineTriggerEvent:
    """Normalize Bitbucket push event to canonical format."""
    change = payload["push"]["changes"][0]
    new_commit = change["new"]
    return PipelineTriggerEvent(
        idempotency_key=f"{payload['repository']['uuid']}:{new_commit['target']['hash']}",
        trigger_type="push",
        provider="bitbucket",
        repo_id=repo_id,
        repo_url=payload["repository"]["links"]["html"]["href"],
        branch=new_commit["name"],
        commit_sha=new_commit["target"]["hash"],
        commit_message=new_commit["target"].get("message", ""),
        author_email=new_commit["target"]["author"].get("raw", "").split("<")[-1].rstrip(">")
        if new_commit["target"].get("author")
        else "",
        author_name=new_commit["target"]["author"].get("user", {}).get("display_name", "")
        if new_commit["target"].get("author")
        else "",
        triggered_at=datetime.utcnow(),
    )


# ================================
# Repository Lookup
# ================================

async def get_repo_by_url(db: AsyncSession, url: str) -> Optional[Repository]:
    """Look up repository by clone URL."""
    # Try both HTTPS and SSH variations
    urls_to_check = [url, url.replace(".git", "")]
    if url.endswith(".git"):
        urls_to_check.append(url[:-4])
    else:
        urls_to_check.append(url + ".git")

    result = await db.execute(
        select(Repository).where(Repository.url.in_(urls_to_check))
    )
    return result.scalar_one_or_none()


async def get_repo_by_id(db: AsyncSession, repo_id: int, provider: str) -> Optional[Repository]:
    """Look up repository by provider's internal ID."""
    # This would require storing the provider's repo ID - simplified for this implementation
    return None


# ================================
# Rate Limiting
# ================================

async def check_rate_limit(repo_id: str, limit: int = 1000, window: int = 60) -> tuple[bool, int]:
    """Check rate limit for a repository."""
    redis = get_redis_client()
    return await redis.check_rate_limit(f"webhook:{repo_id}", limit, window)


# ================================
# Idempotency Check
# ================================

async def is_duplicate(idempotency_key: str) -> bool:
    """Check if this webhook event is a duplicate."""
    redis = get_redis_client()
    is_first = await redis.check_idempotency(f"webhook:{idempotency_key}", ttl=300)
    return not is_first


# ================================
# Webhook Endpoints
# ================================

@app.post("/webhooks/github", response_model=WebhookResponse)
async def github_webhook(
    request: Request,
    x_hub_signature_256: Optional[str] = Header(None),
    x_github_event: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """Handle GitHub webhook events."""
    start_time = time.time()
    payload_bytes = await request.body()

    # Parse payload
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # Get repository URL for lookup
    repo_url = payload.get("repository", {}).get("clone_url")
    if not repo_url:
        raise HTTPException(status_code=400, detail="Missing repository URL")

    # Look up repository
    repo = await get_repo_by_url(db, repo_url)
    if not repo:
        logger.warning("Webhook for unregistered repository", repo_url=repo_url)
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "REPO_NOT_REGISTERED", "message": f"Repository not registered: {repo_url}"}},
        )

    # Validate signature
    if not validate_github_signature(payload_bytes, repo.webhook_secret, x_hub_signature_256):
        logger.warning("Invalid webhook signature", repo_id=str(repo.id), provider="github")
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Check rate limit
    allowed, count = await check_rate_limit(str(repo.id))
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
            headers={"Retry-After": "60"},
        )

    # Normalize payload based on event type
    try:
        if x_github_event == "push":
            # Skip if this is a delete event (no commits)
            if payload.get("after") == "0000000000000000000000000000000000000000":
                return WebhookResponse(accepted=True, message="Branch delete event ignored")
            event = normalize_github_push(payload, str(repo.id))
        elif x_github_event == "pull_request" and payload.get("action") in ("opened", "synchronize", "reopened"):
            event = normalize_github_pr(payload, str(repo.id))
        else:
            return WebhookResponse(accepted=True, message=f"Event type '{x_github_event}' ignored")
    except (KeyError, TypeError) as e:
        logger.error("Payload normalization failed", error=str(e), provider="github")
        raise HTTPException(status_code=400, detail=f"Invalid payload structure: {e}")

    # Check idempotency
    if await is_duplicate(event.idempotency_key):
        logger.info("Duplicate webhook ignored", idempotency_key=event.idempotency_key)
        return WebhookResponse(accepted=True, message="Duplicate event ignored")

    # Publish to Kafka
    await publish_message(
        TOPIC_PIPELINE_TRIGGER,
        key=str(repo.id),
        value=event,
    )

    duration_ms = int((time.time() - start_time) * 1000)
    logger.info(
        "Webhook received",
        provider="github",
        repo_id=str(repo.id),
        commit_sha=event.commit_sha,
        trigger_type=event.trigger_type,
        duration_ms=duration_ms,
        status="published",
    )

    return WebhookResponse(
        accepted=True,
        message="Pipeline triggered",
    )


@app.post("/webhooks/gitlab", response_model=WebhookResponse)
async def gitlab_webhook(
    request: Request,
    x_gitlab_token: Optional[str] = Header(None),
    x_gitlab_event: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """Handle GitLab webhook events."""
    start_time = time.time()
    payload_bytes = await request.body()

    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # Get repository URL
    repo_url = payload.get("project", {}).get("git_http_url")
    if not repo_url:
        raise HTTPException(status_code=400, detail="Missing repository URL")

    # Look up repository
    repo = await get_repo_by_url(db, repo_url)
    if not repo:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "REPO_NOT_REGISTERED", "message": f"Repository not registered: {repo_url}"}},
        )

    # Validate token
    if not validate_gitlab_token(x_gitlab_token, repo.webhook_secret):
        logger.warning("Invalid webhook token", repo_id=str(repo.id), provider="gitlab")
        raise HTTPException(status_code=401, detail="Invalid token")

    # Check rate limit
    allowed, count = await check_rate_limit(str(repo.id))
    if not allowed:
        raise HTTPException(status_code=429, detail="Rate limit exceeded", headers={"Retry-After": "60"})

    # Normalize payload
    try:
        if x_gitlab_event == "Push Hook":
            if payload.get("after") == "0000000000000000000000000000000000000000":
                return WebhookResponse(accepted=True, message="Branch delete event ignored")
            event = normalize_gitlab_push(payload, str(repo.id))
        elif x_gitlab_event == "Merge Request Hook" and payload.get("object_attributes", {}).get("action") in (
            "open",
            "update",
            "reopen",
        ):
            event = normalize_gitlab_mr(payload, str(repo.id))
        else:
            return WebhookResponse(accepted=True, message=f"Event type '{x_gitlab_event}' ignored")
    except (KeyError, TypeError) as e:
        raise HTTPException(status_code=400, detail=f"Invalid payload structure: {e}")

    # Check idempotency
    if await is_duplicate(event.idempotency_key):
        return WebhookResponse(accepted=True, message="Duplicate event ignored")

    # Publish to Kafka
    await publish_message(TOPIC_PIPELINE_TRIGGER, key=str(repo.id), value=event)

    duration_ms = int((time.time() - start_time) * 1000)
    logger.info(
        "Webhook received",
        provider="gitlab",
        repo_id=str(repo.id),
        commit_sha=event.commit_sha,
        trigger_type=event.trigger_type,
        duration_ms=duration_ms,
        status="published",
    )

    return WebhookResponse(accepted=True, message="Pipeline triggered")


@app.post("/webhooks/bitbucket", response_model=WebhookResponse)
async def bitbucket_webhook(
    request: Request,
    x_hub_signature: Optional[str] = Header(None),
    x_event_key: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """Handle Bitbucket webhook events."""
    start_time = time.time()
    payload_bytes = await request.body()

    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # Get repository URL
    repo_url = payload.get("repository", {}).get("links", {}).get("html", {}).get("href")
    if not repo_url:
        raise HTTPException(status_code=400, detail="Missing repository URL")

    # Look up repository
    repo = await get_repo_by_url(db, repo_url)
    if not repo:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "REPO_NOT_REGISTERED", "message": f"Repository not registered: {repo_url}"}},
        )

    # Validate signature
    if not validate_bitbucket_signature(payload_bytes, repo.webhook_secret, x_hub_signature):
        logger.warning("Invalid webhook signature", repo_id=str(repo.id), provider="bitbucket")
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Check rate limit
    allowed, count = await check_rate_limit(str(repo.id))
    if not allowed:
        raise HTTPException(status_code=429, detail="Rate limit exceeded", headers={"Retry-After": "60"})

    # Normalize payload
    try:
        if x_event_key == "repo:push":
            event = normalize_bitbucket_push(payload, str(repo.id))
        else:
            return WebhookResponse(accepted=True, message=f"Event type '{x_event_key}' ignored")
    except (KeyError, TypeError, IndexError) as e:
        raise HTTPException(status_code=400, detail=f"Invalid payload structure: {e}")

    # Check idempotency
    if await is_duplicate(event.idempotency_key):
        return WebhookResponse(accepted=True, message="Duplicate event ignored")

    # Publish to Kafka
    await publish_message(TOPIC_PIPELINE_TRIGGER, key=str(repo.id), value=event)

    duration_ms = int((time.time() - start_time) * 1000)
    logger.info(
        "Webhook received",
        provider="bitbucket",
        repo_id=str(repo.id),
        commit_sha=event.commit_sha,
        trigger_type=event.trigger_type,
        duration_ms=duration_ms,
        status="published",
    )

    return WebhookResponse(accepted=True, message="Pipeline triggered")


# ================================
# Health Endpoints
# ================================

@app.get("/health")
async def health():
    """Liveness probe."""
    return {"status": "ok"}


@app.get("/ready")
async def ready(db: AsyncSession = Depends(get_db)):
    """Readiness probe - checks DB and Redis connectivity."""
    try:
        await db.execute(text("SELECT 1"))
        redis = get_redis_client()
        await redis.ping()
        return {"status": "ready"}
    except Exception as e:
        logger.error("Readiness check failed", error=str(e))
        raise HTTPException(status_code=503, detail="Service not ready")


# ================================
# Entry Point
# ================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.service.webhook_port,
        reload=True,
    )
