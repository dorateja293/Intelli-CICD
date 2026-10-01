"""
Pipeline Orchestrator Service

Consumes pipeline.trigger events from Kafka, parses and validates pipeline
YAML configuration, builds a job dependency DAG, creates pipeline/job records
in PostgreSQL, enqueues jobs to Redis Streams, and manages the pipeline
state machine throughout execution.
"""

import asyncio
import random
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Optional

import httpx
import structlog
import yaml
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, ValidationError, field_validator
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import get_settings
from shared.database import get_db, get_db_context, init_db
from shared.kafka import (
    TOPIC_ALERTS,
    TOPIC_JOB_EVENTS,
    TOPIC_PIPELINE_TRIGGER,
    KafkaConsumerLoop,
    publish_message,
)
from shared.logging import configure_logging
from shared.models import Job, Pipeline, PipelineEventLog, Repository
from shared.redis_client import get_redis_client
from shared.schemas import AlertEvent, JobEventMessage, PipelineTriggerEvent

settings = get_settings()
configure_logging("pipeline-orchestrator")
logger = structlog.get_logger()


# ================================
# Pipeline YAML Config Models
# ================================

class RetryConfig(BaseModel):
    """Retry configuration."""

    max_attempts: int = 3
    backoff: str = "exponential"
    backoff_base_seconds: int = 30
    retry_on_exit_codes: list[int] = [1, 2]


class ArtifactsConfig(BaseModel):
    """Artifacts configuration."""

    paths: list[str] = []
    expire_in: str = "7d"


class CacheConfig(BaseModel):
    """Cache configuration."""

    key: str
    paths: list[str] = []


class RuleConfig(BaseModel):
    """Rule configuration."""

    condition: Optional[str] = None
    when: str = "always"

    class Config:
        populate_by_name = True


class JobConfig(BaseModel):
    """Job configuration from YAML."""

    stage: str
    image: str = "ubuntu:22.04"
    commands: list[str]
    depends_on: list[str] = []
    allow_failure: bool = False
    timeout: int = 3600
    retry: Optional[RetryConfig] = None
    artifacts: Optional[ArtifactsConfig] = None
    cache: Optional[CacheConfig] = None
    rules: list[RuleConfig] = []
    environment: Optional[str] = None


class DefaultsConfig(BaseModel):
    """Default configuration."""

    image: str = "ubuntu:22.04"
    timeout: int = 3600
    retry: Optional[RetryConfig] = None


class PipelineConfig(BaseModel):
    """Full pipeline configuration from YAML."""

    version: str
    stages: list[str]
    jobs: dict[str, JobConfig]
    defaults: Optional[DefaultsConfig] = None

    @field_validator("jobs")
    @classmethod
    def validate_stage_references(cls, jobs: dict[str, JobConfig], info) -> dict[str, JobConfig]:
        """Validate that all jobs reference valid stages."""
        # Get stages from the model being validated
        stages = info.data.get("stages", [])
        for name, job in jobs.items():
            if job.stage not in stages:
                raise ValueError(f"Job '{name}' references unknown stage '{job.stage}'")
        return jobs


# ================================
# DAG Builder
# ================================

def build_dag(jobs: dict[str, JobConfig], stages: list[str]) -> list[list[str]]:
    """
    Build job execution waves from dependencies and stages.
    Returns jobs grouped by execution wave (topological sort).
    Each inner list can be executed in parallel.
    Raises ValueError on circular dependencies.
    """
    in_degree: dict[str, int] = {name: 0 for name in jobs}
    graph: dict[str, list[str]] = defaultdict(list)

    # Build dependency graph
    for name, job in jobs.items():
        for dep in job.depends_on:
            if dep not in jobs:
                raise ValueError(f"Job '{name}' depends on unknown job '{dep}'")
            graph[dep].append(name)
            in_degree[name] += 1

    # Add implicit stage dependencies
    stage_jobs: dict[str, list[str]] = defaultdict(list)
    for name, job in jobs.items():
        stage_jobs[job.stage].append(name)

    for i, stage in enumerate(stages[1:], 1):
        prev_stage = stages[i - 1]
        for job_name in stage_jobs[stage]:
            job = jobs[job_name]
            # If job has no explicit dependencies, depend on all jobs from previous stage
            if not job.depends_on:
                for prev_job in stage_jobs[prev_stage]:
                    if prev_job not in job.depends_on:
                        graph[prev_job].append(job_name)
                        in_degree[job_name] += 1

    # Topological sort using Kahn's algorithm
    queue = deque([n for n, deg in in_degree.items() if deg == 0])
    waves: list[list[str]] = []
    visited = 0

    while queue:
        wave = list(queue)
        waves.append(wave)
        queue.clear()
        for node in wave:
            visited += 1
            for neighbor in graph[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

    if visited != len(jobs):
        raise ValueError("Circular dependency detected in pipeline configuration")

    return waves


# ================================
# Retry Backoff Calculation
# ================================

def compute_backoff(attempt: int, base: int, strategy: str) -> float:
    """Compute retry backoff delay."""
    if strategy == "fixed":
        return float(base)
    elif strategy == "exponential":
        delay = base * (2 ** (attempt - 1))
        jitter = random.uniform(0, delay * 0.1)  # 10% jitter
        return min(delay + jitter, 300)  # cap at 5 minutes
    elif strategy == "linear":
        return float(base * attempt)
    return float(base)


# ================================
# Pipeline Config Fetcher
# ================================

async def fetch_pipeline_config(repo_url: str, commit_sha: str, provider: str) -> str:
    """Fetch .intelli-ci.yml from the repository at the given commit."""
    # Extract repo path from URL
    if provider == "github":
        # https://github.com/owner/repo.git -> owner/repo
        repo_path = repo_url.replace("https://github.com/", "").replace(".git", "")
        raw_url = f"https://raw.githubusercontent.com/{repo_path}/{commit_sha}/.intelli-ci.yml"
    elif provider == "gitlab":
        repo_path = repo_url.replace("https://gitlab.com/", "").replace(".git", "")
        raw_url = f"https://gitlab.com/{repo_path}/-/raw/{commit_sha}/.intelli-ci.yml"
    else:
        # Bitbucket
        repo_path = repo_url.replace("https://bitbucket.org/", "").replace(".git", "")
        raw_url = f"https://bitbucket.org/{repo_path}/raw/{commit_sha}/.intelli-ci.yml"

    async with httpx.AsyncClient() as client:
        resp = await client.get(raw_url, timeout=10.0, follow_redirects=True)
        resp.raise_for_status()
        return resp.text


def parse_pipeline_config(yaml_str: str) -> PipelineConfig:
    """Parse and validate pipeline YAML configuration."""
    raw = yaml.safe_load(yaml_str)
    return PipelineConfig(**raw)


# ================================
# Database Operations
# ================================

async def create_pipeline_and_jobs(
    db: AsyncSession,
    event: PipelineTriggerEvent,
    config: PipelineConfig,
    waves: list[list[str]],
    config_yaml: str,
) -> Pipeline:
    """Create pipeline and job records in database."""
    pipeline = Pipeline(
        repo_id=event.repo_id,
        trigger_type=event.trigger_type,
        commit_sha=event.commit_sha,
        branch=event.branch,
        commit_message=event.commit_message,
        author_email=event.author_email,
        author_name=event.author_name,
        pr_number=event.pr_number,
        status="PENDING",
        config_yaml=config_yaml,
    )
    db.add(pipeline)
    await db.flush()  # Get pipeline.id

    for wave_index, wave in enumerate(waves):
        for job_name in wave:
            job_cfg = config.jobs[job_name]
            job = Job(
                pipeline_id=pipeline.id,
                name=job_name,
                stage=job_cfg.stage,
                status="PENDING",
                config=job_cfg.model_dump(),
                wave_index=wave_index,
            )
            db.add(job)

    await db.commit()
    await db.refresh(pipeline)
    return pipeline


async def update_pipeline_status(
    db: AsyncSession,
    pipeline_id: str,
    status: str,
    blocked_reason: Optional[str] = None,
) -> None:
    """Update pipeline status."""
    update_data: dict[str, Any] = {"status": status, "updated_at": datetime.utcnow()}

    if status == "RUNNING" and not blocked_reason:
        update_data["started_at"] = datetime.utcnow()
    elif status in ("SUCCESS", "FAILED", "CANCELLED"):
        update_data["completed_at"] = datetime.utcnow()
    if blocked_reason:
        update_data["blocked_reason"] = blocked_reason

    await db.execute(update(Pipeline).where(Pipeline.id == pipeline_id).values(**update_data))
    await db.commit()


async def update_job_status(
    db: AsyncSession,
    job_id: str,
    status: str,
    exit_code: Optional[int] = None,
    error_message: Optional[str] = None,
    runner_id: Optional[str] = None,
) -> None:
    """Update job status."""
    import uuid

    update_data: dict[str, Any] = {"status": status, "updated_at": datetime.utcnow()}

    if status == "RUNNING":
        update_data["started_at"] = datetime.utcnow()
    elif status in ("SUCCESS", "FAILED", "SKIPPED", "CANCELLED"):
        update_data["completed_at"] = datetime.utcnow()
    if exit_code is not None:
        update_data["exit_code"] = exit_code
    if error_message:
        update_data["error_message"] = error_message
    if runner_id:
        update_data["runner_id"] = runner_id

    await db.execute(update(Job).where(Job.id == uuid.UUID(job_id)).values(**update_data))
    await db.commit()


async def get_jobs_by_wave(db: AsyncSession, pipeline_id: str, wave_index: int) -> list[Job]:
    """Get all jobs in a specific wave."""
    import uuid

    result = await db.execute(
        select(Job).where(Job.pipeline_id == uuid.UUID(pipeline_id), Job.wave_index == wave_index)
    )
    return list(result.scalars().all())


async def get_pending_jobs_in_wave(db: AsyncSession, pipeline_id: str, wave_index: int) -> list[Job]:
    """Get pending jobs in a wave."""
    import uuid

    result = await db.execute(
        select(Job).where(
            Job.pipeline_id == uuid.UUID(pipeline_id),
            Job.wave_index == wave_index,
            Job.status == "PENDING",
        )
    )
    return list(result.scalars().all())


async def get_max_wave_index(db: AsyncSession, pipeline_id: str) -> int:
    """Get the maximum wave index for a pipeline."""
    import uuid
    from sqlalchemy import func

    result = await db.execute(
        select(func.max(Job.wave_index)).where(Job.pipeline_id == uuid.UUID(pipeline_id))
    )
    return result.scalar() or 0


async def get_pipeline_with_jobs(db: AsyncSession, pipeline_id: str) -> Optional[Pipeline]:
    """Get pipeline with all its jobs."""
    import uuid
    from sqlalchemy.orm import selectinload

    result = await db.execute(
        select(Pipeline)
        .options(selectinload(Pipeline.jobs))
        .where(Pipeline.id == uuid.UUID(pipeline_id))
    )
    return result.scalar_one_or_none()


async def get_repository(db: AsyncSession, repo_id: str) -> Optional[Repository]:
    """Get repository by ID."""
    import uuid

    result = await db.execute(select(Repository).where(Repository.id == uuid.UUID(repo_id)))
    return result.scalar_one_or_none()


# ================================
# Job Queue Operations
# ================================

async def enqueue_jobs(pipeline_id: str, jobs: list[Job]) -> None:
    """Enqueue jobs to Redis Stream."""
    redis = get_redis_client()

    for job in jobs:
        message = {
            "pipeline_id": str(pipeline_id),
            "job_id": str(job.id),
            "job_name": job.name,
            "image": job.config.get("image", "ubuntu:22.04"),
            "commands": job.config.get("commands", []),
            "timeout": job.config.get("timeout", 3600),
            "retry_policy": job.config.get("retry"),
        }
        await redis.xadd("job.queue", message, maxlen=10000)
        logger.info("Job enqueued", job_id=str(job.id), job_name=job.name, pipeline_id=str(pipeline_id))


# ================================
# Alert Publishing
# ================================

async def publish_pipeline_alert(
    pipeline: Pipeline,
    repo: Repository,
    event_type: str,
    message: str,
) -> None:
    """Publish alert for pipeline state change."""
    severity_map = {
        "pipeline_failed": "ERROR",
        "pipeline_succeeded": "INFO",
        "pipeline_cancelled": "WARN",
        "security_critical": "CRITICAL",
    }

    alert = AlertEvent(
        event_type=event_type,
        org_id=str(repo.organization_id),
        repo_id=str(repo.id),
        pipeline_id=str(pipeline.id),
        severity=severity_map.get(event_type, "INFO"),
        title=f"Pipeline {event_type.replace('_', ' ').title()}",
        message=message,
        metadata={
            "branch": pipeline.branch,
            "commit_sha": pipeline.commit_sha,
            "author": pipeline.author_name,
        },
        timestamp=datetime.utcnow().isoformat() + "Z",
    )

    await publish_message(TOPIC_ALERTS, key=str(pipeline.id), value=alert)


# ================================
# Pipeline Trigger Handler
# ================================

async def handle_pipeline_trigger(event: PipelineTriggerEvent) -> None:
    """Handle incoming pipeline trigger event."""
    logger.info(
        "Processing pipeline trigger",
        repo_id=event.repo_id,
        commit_sha=event.commit_sha,
        trigger_type=event.trigger_type,
    )

    async with get_db_context() as db:
        # Get repository
        repo = await get_repository(db, event.repo_id)
        if not repo:
            logger.error("Repository not found", repo_id=event.repo_id)
            return

        try:
            # Fetch pipeline config
            config_yaml = await fetch_pipeline_config(repo.url, event.commit_sha, event.provider)
            config = parse_pipeline_config(config_yaml)

            # Build DAG
            waves = build_dag(config.jobs, config.stages)

            # Create pipeline and jobs
            pipeline = await create_pipeline_and_jobs(db, event, config, waves, config_yaml)

            logger.info(
                "Pipeline created",
                pipeline_id=str(pipeline.id),
                job_count=len(config.jobs),
                wave_count=len(waves),
            )

            # Enqueue wave-0 jobs
            wave0_jobs = await get_jobs_by_wave(db, str(pipeline.id), 0)
            await enqueue_jobs(str(pipeline.id), wave0_jobs)

            # Update job statuses to QUEUED
            for job in wave0_jobs:
                await update_job_status(db, str(job.id), "QUEUED")

            # Update pipeline status
            await update_pipeline_status(db, str(pipeline.id), "QUEUED")

        except httpx.HTTPStatusError as e:
            logger.error("Config fetch failed", error=str(e), status_code=e.response.status_code)
            # Create failed pipeline
            pipeline = Pipeline(
                repo_id=event.repo_id,
                trigger_type=event.trigger_type,
                commit_sha=event.commit_sha,
                branch=event.branch,
                status="FAILED",
                config_error="CONFIG_NOT_FOUND",
                blocked_reason="Pipeline configuration file not found",
            )
            db.add(pipeline)
            await db.commit()
            await publish_pipeline_alert(pipeline, repo, "pipeline_failed", "Configuration file not found")

        except (yaml.YAMLError, ValidationError, ValueError) as e:
            logger.error("Config parse failed", error=str(e))
            pipeline = Pipeline(
                repo_id=event.repo_id,
                trigger_type=event.trigger_type,
                commit_sha=event.commit_sha,
                branch=event.branch,
                status="FAILED",
                config_error="CONFIG_PARSE_ERROR",
                blocked_reason=str(e),
            )
            db.add(pipeline)
            await db.commit()
            await publish_pipeline_alert(pipeline, repo, "pipeline_failed", f"Configuration error: {e}")


# ================================
# Job Completion Handler
# ================================

async def handle_job_completion(event: JobEventMessage) -> None:
    """Handle job completion event."""
    logger.info(
        "Processing job completion",
        job_id=event.job_id,
        pipeline_id=event.pipeline_id,
        status=event.status,
    )

    async with get_db_context() as db:
        # Update job status
        await update_job_status(
            db,
            event.job_id,
            event.status,
            exit_code=event.exit_code,
            runner_id=event.runner_id,
        )

        # Get pipeline with jobs
        pipeline = await get_pipeline_with_jobs(db, event.pipeline_id)
        if not pipeline:
            logger.error("Pipeline not found", pipeline_id=event.pipeline_id)
            return

        repo = await get_repository(db, str(pipeline.repo_id))

        # Find the job that completed
        completed_job = next((j for j in pipeline.jobs if str(j.id) == event.job_id), None)
        if not completed_job:
            logger.error("Job not found", job_id=event.job_id)
            return

        wave_index = completed_job.wave_index
        max_wave = await get_max_wave_index(db, event.pipeline_id)

        # Check if all jobs in current wave are complete
        wave_jobs = [j for j in pipeline.jobs if j.wave_index == wave_index]
        wave_complete = all(j.status in ("SUCCESS", "FAILED", "SKIPPED") for j in wave_jobs)

        if not wave_complete:
            # Update pipeline to RUNNING if not already
            if pipeline.status != "RUNNING":
                await update_pipeline_status(db, event.pipeline_id, "RUNNING")
            return

        # Wave complete - check for failures
        failed_jobs = [j for j in wave_jobs if j.status == "FAILED" and not j.config.get("allow_failure", False)]

        if failed_jobs:
            # Skip remaining jobs and fail pipeline
            remaining_jobs = [j for j in pipeline.jobs if j.status == "PENDING"]
            for job in remaining_jobs:
                await update_job_status(db, str(job.id), "SKIPPED")

            await update_pipeline_status(db, event.pipeline_id, "FAILED")
            if repo:
                await publish_pipeline_alert(
                    pipeline,
                    repo,
                    "pipeline_failed",
                    f"Pipeline failed: job '{failed_jobs[0].name}' failed",
                )
            return

        # Check if this was the last wave
        if wave_index >= max_wave:
            # All waves complete - success!
            await update_pipeline_status(db, event.pipeline_id, "SUCCESS")
            if repo:
                await publish_pipeline_alert(
                    pipeline,
                    repo,
                    "pipeline_succeeded",
                    f"Pipeline completed successfully",
                )
            return

        # Enqueue next wave
        next_wave_jobs = await get_pending_jobs_in_wave(db, event.pipeline_id, wave_index + 1)
        if next_wave_jobs:
            await enqueue_jobs(event.pipeline_id, next_wave_jobs)
            for job in next_wave_jobs:
                await update_job_status(db, str(job.id), "QUEUED")


# ================================
# Kafka Consumer Message Handler
# ================================

async def handle_kafka_message(msg: Any) -> None:
    """Route Kafka messages to appropriate handlers."""
    topic = msg.topic()
    value = msg.value().decode("utf-8")

    if topic == TOPIC_PIPELINE_TRIGGER:
        event = PipelineTriggerEvent.model_validate_json(value)
        await handle_pipeline_trigger(event)
    elif topic == TOPIC_JOB_EVENTS:
        event = JobEventMessage.model_validate_json(value)
        await handle_job_completion(event)


# ================================
# FastAPI App for Internal APIs
# ================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting pipeline orchestrator")
    await init_db()

    # Start Kafka consumers in background
    trigger_consumer = KafkaConsumerLoop(
        "pipeline-orchestrator",
        [TOPIC_PIPELINE_TRIGGER, TOPIC_JOB_EVENTS],
    )
    consumer_task = asyncio.create_task(trigger_consumer.start(handle_kafka_message))

    yield

    logger.info("Shutting down pipeline orchestrator")
    trigger_consumer.stop()
    consumer_task.cancel()


app = FastAPI(
    title="Intelli-CI Pipeline Orchestrator",
    description="Pipeline orchestration and job scheduling service",
    version="1.0.0",
    lifespan=lifespan,
)


@app.post("/pipelines/{pipeline_id}/cancel")
async def cancel_pipeline(
    pipeline_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Cancel a running pipeline."""
    pipeline = await get_pipeline_with_jobs(db, pipeline_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    if pipeline.status not in ("PENDING", "QUEUED", "RUNNING"):
        raise HTTPException(status_code=400, detail=f"Cannot cancel pipeline in {pipeline.status} state")

    # Cancel pending/queued jobs
    for job in pipeline.jobs:
        if job.status in ("PENDING", "QUEUED"):
            await update_job_status(db, str(job.id), "CANCELLED")

    await update_pipeline_status(db, pipeline_id, "CANCELLED")

    repo = await get_repository(db, str(pipeline.repo_id))
    if repo:
        await publish_pipeline_alert(pipeline, repo, "pipeline_cancelled", "Pipeline cancelled by user")

    return {"status": "cancelled", "pipeline_id": pipeline_id}


@app.post("/pipelines/{pipeline_id}/retry")
async def retry_pipeline(
    pipeline_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Retry failed/skipped jobs in a pipeline."""
    pipeline = await get_pipeline_with_jobs(db, pipeline_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    if pipeline.status not in ("FAILED", "CANCELLED"):
        raise HTTPException(status_code=400, detail=f"Cannot retry pipeline in {pipeline.status} state")

    # Reset failed/skipped jobs
    jobs_to_retry = [j for j in pipeline.jobs if j.status in ("FAILED", "SKIPPED")]
    for job in jobs_to_retry:
        await update_job_status(db, str(job.id), "PENDING")
        # Increment retry count
        await db.execute(update(Job).where(Job.id == job.id).values(retry_count=job.retry_count + 1))
    await db.commit()

    # Find minimum wave of jobs to retry
    min_wave = min(j.wave_index for j in jobs_to_retry) if jobs_to_retry else 0

    # Enqueue the minimum wave jobs
    wave_jobs = [j for j in jobs_to_retry if j.wave_index == min_wave]
    await enqueue_jobs(pipeline_id, wave_jobs)
    for job in wave_jobs:
        await update_job_status(db, str(job.id), "QUEUED")

    await update_pipeline_status(db, pipeline_id, "QUEUED")

    return {"status": "retrying", "pipeline_id": pipeline_id, "jobs_retrying": len(jobs_to_retry)}


@app.get("/pipelines/{pipeline_id}/status")
async def get_pipeline_status(
    pipeline_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get pipeline status with job details."""
    pipeline = await get_pipeline_with_jobs(db, pipeline_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    return {
        "id": str(pipeline.id),
        "status": pipeline.status,
        "branch": pipeline.branch,
        "commit_sha": pipeline.commit_sha,
        "jobs": [
            {
                "id": str(j.id),
                "name": j.name,
                "stage": j.stage,
                "status": j.status,
                "wave_index": j.wave_index,
            }
            for j in pipeline.jobs
        ],
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

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.service.orchestrator_port,
        reload=True,
    )
