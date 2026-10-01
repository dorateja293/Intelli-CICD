"""
Log Processor Service

Consumes log events from Kafka topic log.stream, parses and enriches each
log line, detects error patterns, bulk-indexes to Elasticsearch, forwards
error events to the AI Engine via Kafka log.errors topic, and serves
real-time log streaming to the frontend via Server-Sent Events (SSE).
"""

import asyncio
import hashlib
import re
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

import structlog
from elasticsearch import AsyncElasticsearch
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import get_settings
from shared.database import get_db, get_db_context, init_db
from shared.kafka import (
    TOPIC_LOG_ERRORS,
    TOPIC_LOG_STREAM,
    KafkaConsumerLoop,
    publish_message,
)
from shared.logging import configure_logging
from shared.models import Job, Pipeline
from shared.redis_client import get_redis_client
from shared.schemas import EnrichedLogEvent, LogErrorEvent, RawLogEvent
from shared.security import get_current_user

settings = get_settings()
configure_logging("log-processor")
logger = structlog.get_logger()


# ================================
# Elasticsearch Client
# ================================

es_client: Optional[AsyncElasticsearch] = None


def get_elasticsearch() -> AsyncElasticsearch:
    """Get Elasticsearch client."""
    global es_client
    if es_client is None:
        es_client = AsyncElasticsearch(hosts=settings.elasticsearch.hosts.split(","))
    return es_client


# ================================
# Section Detection
# ================================

SECTION_PATTERNS = [
    re.compile(r"##\[section\](.+)"),  # GitHub Actions format
    re.compile(r"^\[SECTION\] (.+)"),
    re.compile(r"^==> (.+)"),
    re.compile(r"^\$ (.{5,60})$"),  # shell command lines
]


class SectionTracker:
    """Track current section from log lines."""

    def __init__(self):
        self.current: Optional[str] = None

    def detect(self, line: str) -> Optional[str]:
        """Detect section from line and return current section."""
        for pattern in SECTION_PATTERNS:
            match = pattern.match(line)
            if match:
                self.current = match.group(1).strip()[:100]  # Limit length
                return self.current
        return self.current


# ================================
# Stack Trace Aggregation
# ================================

STACK_TRACE_STARTS = [
    re.compile(r"Traceback \(most recent call last\):"),  # Python
    re.compile(r"Exception in thread"),  # Java
    re.compile(r"Error: .+ at .+:\d+"),  # Node.js
    re.compile(r"panic: "),  # Go
    re.compile(r"^\s*at \S+"),  # Generic stack frame
]

STACK_TRACE_CONTINUATION = re.compile(r"^\s+(at |File |from |\d+\.\s|\|)")


class StackTraceAggregator:
    """Aggregate multi-line stack traces."""

    def __init__(self):
        self.active_trace_id: Optional[str] = None
        self.in_trace: bool = False

    def process(self, line: str) -> Optional[str]:
        """Process line and return stack_trace_group UUID if part of trace."""
        if any(p.search(line) for p in STACK_TRACE_STARTS):
            self.active_trace_id = str(uuid4())
            self.in_trace = True
            return self.active_trace_id

        if self.in_trace and STACK_TRACE_CONTINUATION.match(line):
            return self.active_trace_id

        self.in_trace = False
        self.active_trace_id = None
        return None


# ================================
# Job Context Cache
# ================================

job_context_cache: dict[str, dict[str, Any]] = {}


async def get_job_context(job_id: str) -> dict[str, Any]:
    """Get job context (repo_id, pipeline_id) from cache or DB."""
    if job_id in job_context_cache:
        return job_context_cache[job_id]

    async with get_db_context() as db:
        import uuid

        result = await db.execute(
            select(Job, Pipeline)
            .join(Pipeline, Job.pipeline_id == Pipeline.id)
            .where(Job.id == uuid.UUID(job_id))
        )
        row = result.first()
        if row:
            job, pipeline = row
            context = {
                "repo_id": str(pipeline.repo_id),
                "pipeline_id": str(pipeline.id),
            }
            job_context_cache[job_id] = context
            return context

    return {"repo_id": "unknown", "pipeline_id": "unknown"}


# ================================
# Log Enrichment
# ================================

def enrich_log_event(
    raw: RawLogEvent,
    repo_id: str,
    section: Optional[str],
    stack_trace_group: Optional[str],
) -> EnrichedLogEvent:
    """Enrich raw log event with additional metadata."""
    is_error = raw.level in ("ERROR", "CRITICAL")
    fingerprint: Optional[str] = None

    if is_error:
        # Normalize error text for stable fingerprint
        normalized = re.sub(r"0x[0-9a-f]+", "0xADDR", raw.content)
        normalized = re.sub(r":\d+", ":N", normalized)
        normalized = re.sub(r"\d+", "N", normalized)
        fingerprint = hashlib.md5(normalized.encode()).hexdigest()[:12]

    return EnrichedLogEvent(
        job_id=raw.job_id,
        pipeline_id=raw.pipeline_id,
        repo_id=repo_id,
        line_number=raw.line_number,
        content=raw.content,
        timestamp=datetime.fromisoformat(raw.timestamp.replace("Z", "+00:00")),
        level=raw.level,
        is_error=is_error,
        error_fingerprint=fingerprint,
        stack_trace_group=stack_trace_group,
        section=section,
    )


# ================================
# Elasticsearch Indexing
# ================================

log_buffer: list[dict[str, Any]] = []
buffer_lock = asyncio.Lock()


async def flush_to_elasticsearch() -> None:
    """Flush log buffer to Elasticsearch."""
    global log_buffer

    async with buffer_lock:
        if not log_buffer:
            return

        buffer_copy = log_buffer.copy()
        log_buffer.clear()

    try:
        es = get_elasticsearch()
        actions: list[dict[str, Any]] = []

        for doc in buffer_copy:
            # Create daily index name
            timestamp_str = doc.get("timestamp", "")
            if isinstance(timestamp_str, datetime):
                date_str = timestamp_str.strftime("%Y-%m-%d")
            else:
                date_str = timestamp_str[:10] if timestamp_str else datetime.utcnow().strftime("%Y-%m-%d")

            index_name = f"logs-{doc.get('repo_id', 'unknown')}-{date_str}"
            actions.append({"index": {"_index": index_name}})
            actions.append(doc)

        if actions:
            response = await es.bulk(operations=actions)
            if response.get("errors"):
                failed = [item for item in response.get("items", []) if "error" in item.get("index", {})]
                logger.error("Elasticsearch bulk index partial failure", failed_count=len(failed))
            else:
                logger.debug("Flushed logs to Elasticsearch", count=len(buffer_copy))

    except Exception as e:
        logger.error("Elasticsearch flush error", error=str(e))
        # Re-add to buffer for retry
        async with buffer_lock:
            log_buffer.extend(buffer_copy)


async def periodic_flush() -> None:
    """Periodically flush log buffer."""
    while True:
        await asyncio.sleep(settings.elasticsearch.flush_interval)
        await flush_to_elasticsearch()


# ================================
# Redis Caching for SSE
# ================================

async def cache_log_line(job_id: str, line: EnrichedLogEvent) -> None:
    """Cache log line in Redis for SSE backlog."""
    redis = get_redis_client()
    key = f"logs:recent:{job_id}"

    await redis.rpush(key, line.model_dump_json())
    await redis.ltrim(key, -500, -1)  # Keep only last 500 lines
    await redis.expire(key, 3600)  # Expire after 1 hour

    # Publish to pub/sub channel for live streaming
    await redis.publish(f"logs:live:{job_id}", line.model_dump_json())


# ================================
# Error Event Publishing
# ================================

async def publish_error_event(enriched: EnrichedLogEvent) -> None:
    """Publish error event for AI Engine processing."""
    event = LogErrorEvent(
        job_id=enriched.job_id,
        pipeline_id=enriched.pipeline_id,
        repo_id=enriched.repo_id,
        error_lines=[enriched.content],
        error_fingerprint=enriched.error_fingerprint or "",
        stack_trace_group=enriched.stack_trace_group,
        timestamp=enriched.timestamp.isoformat(),
    )
    await publish_message(TOPIC_LOG_ERRORS, key=enriched.job_id, value=event)


# ================================
# Kafka Message Handler
# ================================

# Per-job trackers
section_trackers: dict[str, SectionTracker] = {}
stack_aggregators: dict[str, StackTraceAggregator] = {}


async def handle_log_message(msg: Any) -> None:
    """Handle incoming log message from Kafka."""
    try:
        raw = RawLogEvent.model_validate_json(msg.value())

        # Get or create trackers for this job
        if raw.job_id not in section_trackers:
            section_trackers[raw.job_id] = SectionTracker()
            stack_aggregators[raw.job_id] = StackTraceAggregator()

        section_tracker = section_trackers[raw.job_id]
        stack_aggregator = stack_aggregators[raw.job_id]

        # Get job context
        context = await get_job_context(raw.job_id)

        # Detect section and stack trace
        section = section_tracker.detect(raw.content)
        stack_trace_group = stack_aggregator.process(raw.content)

        # Enrich log event
        enriched = enrich_log_event(raw, context["repo_id"], section, stack_trace_group)

        # Add to buffer for ES indexing
        async with buffer_lock:
            log_buffer.append(enriched.model_dump(mode="json"))
            if len(log_buffer) >= settings.elasticsearch.bulk_size:
                await flush_to_elasticsearch()

        # Cache for SSE
        await cache_log_line(raw.job_id, enriched)

        # Publish error events
        if enriched.is_error:
            await publish_error_event(enriched)

    except Exception as e:
        logger.error("Log processing error", error=str(e))


# ================================
# FastAPI App
# ================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting log processor")
    await init_db()

    # Start Kafka consumer
    consumer = KafkaConsumerLoop("log-processor", [TOPIC_LOG_STREAM])
    consumer_task = asyncio.create_task(consumer.start(handle_log_message))

    # Start periodic flush
    flush_task = asyncio.create_task(periodic_flush())

    yield

    logger.info("Shutting down log processor")
    consumer.stop()
    consumer_task.cancel()
    flush_task.cancel()
    await flush_to_elasticsearch()  # Final flush

    if es_client:
        await es_client.close()


app = FastAPI(
    title="Intelli-CI Log Processor",
    description="Log processing and real-time streaming service",
    version="1.0.0",
    lifespan=lifespan,
)


# ================================
# SSE Endpoint
# ================================

@app.get("/api/v1/jobs/{job_id}/logs/stream")
async def stream_job_logs(
    job_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Stream job logs via Server-Sent Events."""
    # Verify job exists
    import uuid

    result = await db.execute(select(Job).where(Job.id == uuid.UUID(job_id)))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    async def event_generator():
        redis = get_redis_client()

        # 1. Send backlog (last 500 cached lines)
        cached = await redis.lrange(f"logs:recent:{job_id}", 0, -1)
        for line in cached:
            yield f"data: {line}\n\n"

        # 2. Subscribe for new lines
        pubsub = redis.pubsub()
        await pubsub.subscribe(f"logs:live:{job_id}")

        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    data = message["data"]
                    if isinstance(data, bytes):
                        data = data.decode("utf-8")
                    yield f"data: {data}\n\n"
        except asyncio.CancelledError:
            await pubsub.unsubscribe(f"logs:live:{job_id}")
        finally:
            await pubsub.close()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Disable NGINX buffering
            "Connection": "keep-alive",
        },
    )


# ================================
# Search Endpoint
# ================================

@app.get("/api/v1/logs/search")
async def search_logs(
    q: str,
    job_id: Optional[str] = None,
    pipeline_id: Optional[str] = None,
    repo_id: Optional[str] = None,
    level: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
):
    """Search logs in Elasticsearch."""
    es = get_elasticsearch()

    # Build query
    must: list[dict] = [{"query_string": {"query": q, "default_field": "content"}}]

    if job_id:
        must.append({"term": {"job_id": job_id}})
    if pipeline_id:
        must.append({"term": {"pipeline_id": pipeline_id}})
    if repo_id:
        must.append({"term": {"repo_id": repo_id}})
    if level:
        must.append({"term": {"level": level}})

    query = {
        "bool": {"must": must},
    }

    try:
        response = await es.search(
            index="logs-*",
            query=query,
            from_=offset,
            size=limit,
            sort=[{"timestamp": "desc"}],
        )

        hits = response.get("hits", {})
        return {
            "data": [hit["_source"] for hit in hits.get("hits", [])],
            "meta": {
                "total": hits.get("total", {}).get("value", 0),
                "limit": limit,
                "offset": offset,
            },
        }
    except Exception as e:
        logger.error("Search error", error=str(e))
        raise HTTPException(status_code=500, detail="Search failed")


# ================================
# Health Endpoint
# ================================

@app.get("/health")
async def health():
    """Liveness probe."""
    return {"status": "ok"}


@app.get("/ready")
async def ready():
    """Readiness probe."""
    try:
        es = get_elasticsearch()
        await es.ping()
        redis = get_redis_client()
        await redis.ping()
        return {"status": "ready"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Not ready: {e}")


# ================================
# Entry Point
# ================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.service.log_processor_port,
        reload=True,
    )
