"""
Worker Agent Service

Pulls jobs from Redis Streams, provisions isolated execution environments
(Docker containers or Kubernetes Jobs), executes pipeline job commands,
streams logs to Kafka, and reports completion status.
"""

import asyncio
import json
import os
import re
import socket
import time
from datetime import datetime
from typing import Any, Optional

import structlog

from config.settings import get_settings
from shared.kafka import TOPIC_JOB_EVENTS, TOPIC_LOG_STREAM, get_producer, publish_message
from shared.logging import configure_logging
from shared.redis_client import get_redis_client

settings = get_settings()
configure_logging("worker-agent")
logger = structlog.get_logger()

# Stream configuration
STREAM_KEY = "job.queue"
CONSUMER_GROUP = "workers"
CONSUMER_NAME = f"worker-{socket.gethostname()}-{os.getpid()}"

# Log level detection patterns
LOG_LEVEL_PATTERNS = [
    (re.compile(r"\b(CRITICAL|FATAL)\b", re.I), "CRITICAL"),
    (re.compile(r"\b(ERROR|FAIL|FAILED|Exception|Error)\b", re.I), "ERROR"),
    (re.compile(r"\b(WARN|WARNING)\b", re.I), "WARN"),
    (re.compile(r"\b(DEBUG)\b", re.I), "DEBUG"),
]


def detect_log_level(line: str) -> str:
    """Detect log level from line content."""
    for pattern, level in LOG_LEVEL_PATTERNS:
        if pattern.search(line):
            return level
    return "INFO"


# ================================
# Log Streaming
# ================================

async def stream_logs(
    process: asyncio.subprocess.Process,
    job_id: str,
    pipeline_id: str,
) -> None:
    """Stream process output to Kafka."""
    line_number = 0

    async for raw_line in process.stdout:
        line = raw_line.decode("utf-8", errors="replace").rstrip()
        line_number += 1

        log_event = {
            "job_id": job_id,
            "pipeline_id": pipeline_id,
            "line_number": line_number,
            "content": line,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": detect_log_level(line),
        }

        await publish_message(
            TOPIC_LOG_STREAM,
            key=job_id,
            value=log_event,
        )


# ================================
# Job Execution
# ================================

async def execute_job_docker(
    job_id: str,
    pipeline_id: str,
    image: str,
    commands: list[str],
    timeout: int,
    env: dict[str, str],
) -> int:
    """Execute job commands in a Docker container."""
    # Build docker run command
    docker_cmd = [
        "docker",
        "run",
        "--rm",
        "--name",
        f"job-{job_id[:8]}",
        "--memory",
        "2g",
        "--cpus",
        "1.0",
        "--read-only",  # read-only root FS
        "--tmpfs",
        "/workspace:rw,size=1g",  # writable workspace
        "--security-opt",
        "no-new-privileges",
        "-w",
        "/workspace",
    ]

    # Add environment variables
    docker_cmd.extend(["-e", f"CI_JOB_ID={job_id}"])
    docker_cmd.extend(["-e", f"CI_PIPELINE_ID={pipeline_id}"])
    for key, value in env.items():
        docker_cmd.extend(["-e", f"{key}={value}"])

    # Add image and command
    docker_cmd.append(image)
    docker_cmd.extend(["sh", "-c", " && ".join(commands)])

    logger.info("Starting job execution", job_id=job_id, image=image, command_count=len(commands))

    process = await asyncio.create_subprocess_exec(
        *docker_cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,  # merge stderr into stdout
    )

    # Stream logs to Kafka
    await stream_logs(process, job_id, pipeline_id)

    try:
        await asyncio.wait_for(process.wait(), timeout=timeout)
    except asyncio.TimeoutError:
        logger.warning("Job execution timeout", job_id=job_id, timeout=timeout)
        process.kill()
        await process.wait()
        raise TimeoutError(f"Job exceeded {timeout}s timeout")

    return process.returncode or 0


async def execute_job_local(
    job_id: str,
    pipeline_id: str,
    image: str,
    commands: list[str],
    timeout: int,
    env: dict[str, str],
) -> int:
    """Execute job commands locally (for development)."""
    logger.info("Starting local job execution", job_id=job_id, command_count=len(commands))

    # Create combined command
    combined_cmd = " && ".join(commands)

    # Set up environment
    job_env = os.environ.copy()
    job_env["CI_JOB_ID"] = job_id
    job_env["CI_PIPELINE_ID"] = pipeline_id
    job_env.update(env)

    process = await asyncio.create_subprocess_shell(
        combined_cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        env=job_env,
    )

    # Stream logs
    await stream_logs(process, job_id, pipeline_id)

    try:
        await asyncio.wait_for(process.wait(), timeout=timeout)
    except asyncio.TimeoutError:
        process.kill()
        raise TimeoutError(f"Job exceeded {timeout}s timeout")

    return process.returncode or 0


# ================================
# Secret Resolution (Vault Mock)
# ================================

async def resolve_secrets(commands: list[str], pipeline_id: str) -> dict[str, str]:
    """
    Scan commands for ${{ secrets.KEY }} references and resolve from Vault.
    Returns env dict to inject into container.
    """
    pattern = re.compile(r"\$\{\{\s*secrets\.(\w+)\s*\}\}")
    secret_names: set[str] = set()
    for cmd in commands:
        secret_names.update(pattern.findall(cmd))

    env: dict[str, str] = {}
    for name in secret_names:
        # In production, this would fetch from HashiCorp Vault
        # For now, check environment variables as fallback
        env_value = os.getenv(name) or os.getenv(f"SECRET_{name}")
        if env_value:
            env[name] = env_value
        else:
            logger.warning("Secret not found", secret_name=name, pipeline_id=pipeline_id)

    return env


# ================================
# Job Completion Publishing
# ================================

async def publish_job_event(
    pipeline_id: str,
    job_id: str,
    status: str,
    exit_code: int,
    duration_seconds: int,
) -> None:
    """Publish job completion event to Kafka."""
    event = {
        "pipeline_id": pipeline_id,
        "job_id": job_id,
        "status": status,
        "exit_code": exit_code,
        "duration_seconds": duration_seconds,
        "runner_id": CONSUMER_NAME,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    await publish_message(TOPIC_JOB_EVENTS, key=pipeline_id, value=event)
    logger.info("Job event published", job_id=job_id, status=status, exit_code=exit_code)


# ================================
# Job Processing
# ================================

async def process_job(
    redis_client: Any,
    msg_id: str,
    fields: dict[str, Any],
    is_retry: bool = False,
) -> None:
    """Process a single job from the queue."""
    job_id = fields.get("job_id", "")
    pipeline_id = fields.get("pipeline_id", "")

    logger.info(
        "Processing job",
        job_id=job_id,
        pipeline_id=pipeline_id,
        is_retry=is_retry,
    )

    start_time = time.time()
    exit_code = 0
    status = "SUCCESS"

    try:
        # Parse job configuration
        commands = json.loads(fields.get("commands", "[]"))
        image = fields.get("image", "ubuntu:22.04")
        timeout = int(fields.get("timeout", settings.worker.default_timeout))

        # Resolve secrets
        env = await resolve_secrets(commands, pipeline_id)

        # Execute job
        try:
            # Try Docker first, fall back to local execution
            exit_code = await execute_job_docker(
                job_id,
                pipeline_id,
                image,
                commands,
                timeout,
                env,
            )
        except FileNotFoundError:
            # Docker not available, use local execution
            logger.warning("Docker not available, using local execution")
            exit_code = await execute_job_local(
                job_id,
                pipeline_id,
                image,
                commands,
                timeout,
                env,
            )

        status = "SUCCESS" if exit_code == 0 else "FAILED"

    except TimeoutError as e:
        status = "FAILED"
        exit_code = -1
        logger.error("Job timeout", job_id=job_id, error=str(e))

    except Exception as e:
        status = "FAILED"
        exit_code = -2
        logger.error("Job execution error", job_id=job_id, error=str(e))

    finally:
        duration = int(time.time() - start_time)

        # Publish completion event
        await publish_job_event(pipeline_id, job_id, status, exit_code, duration)

        # ACK message in Redis
        await redis_client.xack(STREAM_KEY, CONSUMER_GROUP, msg_id)
        logger.info(
            "Job completed",
            job_id=job_id,
            status=status,
            exit_code=exit_code,
            duration_seconds=duration,
        )


# ================================
# Abandoned Job Recovery
# ================================

async def claim_abandoned_jobs(redis_client: Any) -> None:
    """Reclaim jobs stuck in Pending Entry List (PEL) for >10 minutes."""
    try:
        pending = await redis_client.xpending_range(
            STREAM_KEY,
            CONSUMER_GROUP,
            "-",
            "+",
            10,
            idle=10 * 60 * 1000,  # 10 minutes in ms
        )

        for entry in pending:
            msg_id = entry.get("message_id") or entry.get("message-id") or str(entry.get(b"message_id", b""))
            if not msg_id:
                continue

            claimed = await redis_client.xclaim(
                STREAM_KEY,
                CONSUMER_GROUP,
                CONSUMER_NAME,
                10 * 60 * 1000,
                [msg_id],
            )

            for claimed_msg in claimed:
                if isinstance(claimed_msg, (list, tuple)) and len(claimed_msg) >= 2:
                    claimed_id, claimed_fields = claimed_msg[0], claimed_msg[1]
                    logger.info("Reclaimed abandoned job", msg_id=claimed_id)
                    await process_job(redis_client, claimed_id, claimed_fields, is_retry=True)

    except Exception as e:
        logger.error("Failed to claim abandoned jobs", error=str(e))


# ================================
# Main Worker Loop
# ================================

async def start_worker() -> None:
    """Main worker loop."""
    redis_client = get_redis_client()

    # Create consumer group if not exists
    await redis_client.xgroup_create(STREAM_KEY, CONSUMER_GROUP, mkstream=True)

    logger.info(
        "Worker started",
        consumer_name=CONSUMER_NAME,
        stream=STREAM_KEY,
        group=CONSUMER_GROUP,
    )

    while True:
        try:
            # Read messages from stream
            messages = await redis_client.xreadgroup(
                CONSUMER_GROUP,
                CONSUMER_NAME,
                {STREAM_KEY: ">"},  # ">" = undelivered messages only
                count=1,  # one job at a time
                block=5000,  # block 5s if no messages
            )

            if not messages:
                # No messages, check for abandoned jobs
                await claim_abandoned_jobs(redis_client)
                continue

            for stream, entries in messages:
                for msg_id, fields in entries:
                    # Decode fields if necessary
                    decoded_fields = {}
                    for k, v in fields.items():
                        key = k.decode("utf-8") if isinstance(k, bytes) else k
                        value = v.decode("utf-8") if isinstance(v, bytes) else v
                        decoded_fields[key] = value

                    await process_job(redis_client, msg_id, decoded_fields)

        except asyncio.CancelledError:
            logger.info("Worker shutdown requested")
            break
        except Exception as e:
            logger.error("Worker loop error", error=str(e))
            await asyncio.sleep(5)  # Brief pause before retry


# ================================
# Entry Point
# ================================

def main() -> None:
    """Main entry point."""
    asyncio.run(start_worker())


if __name__ == "__main__":
    main()
