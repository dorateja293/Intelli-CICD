"""
Security Scanner Service

Runs three parallel security scanners (Trivy, Gitleaks, Semgrep) against
each pipeline's code and dependencies, normalizes findings into a canonical
schema, persists to PostgreSQL, publishes a summary to Kafka, and enforces
policy gates that block pipelines with CRITICAL findings.
"""

import asyncio
import json
import os
import tempfile
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Optional

import httpx
import structlog
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import get_settings
from shared.database import get_db, get_db_context, init_db
from shared.kafka import (
    TOPIC_ALERTS,
    TOPIC_PIPELINE_TRIGGER,
    TOPIC_SECURITY_RESULTS,
    KafkaConsumerLoop,
    publish_message,
)
from shared.logging import configure_logging
from shared.models import Pipeline, Repository, SecurityFinding, SecurityPolicy
from shared.schemas import AlertEvent, PipelineTriggerEvent, SecuritySummary

settings = get_settings()
configure_logging("security-scanner")
logger = structlog.get_logger()


# ================================
# Scanner: Trivy (Vulnerability Scanner)
# ================================

async def run_trivy(workspace_path: str, job_id: str) -> list[dict[str, Any]]:
    """Run Trivy vulnerability scanner."""
    cmd = [
        "trivy",
        "fs",
        "--format",
        "json",
        "--severity",
        "CRITICAL,HIGH,MEDIUM,LOW",
        "--exit-code",
        "0",
        "--quiet",
        workspace_path,
    ]

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()

        if process.returncode not in (0, 1):  # 1 = vulnerabilities found (expected)
            logger.error("Trivy execution failed", error=stderr.decode())
            return []

        data = json.loads(stdout.decode())
        return parse_trivy_output(data)

    except FileNotFoundError:
        logger.warning("Trivy not installed, skipping vulnerability scan")
        return []
    except json.JSONDecodeError as e:
        logger.error("Trivy output parse error", error=str(e))
        return []


def parse_trivy_output(data: dict) -> list[dict[str, Any]]:
    """Parse Trivy JSON output to canonical format."""
    findings: list[dict[str, Any]] = []

    for result in data.get("Results", []):
        for vuln in result.get("Vulnerabilities", []) or []:
            findings.append({
                "scanner": "trivy",
                "severity": vuln.get("Severity", "UNKNOWN").upper(),
                "category": "DEPENDENCY_VULNERABILITY",
                "title": f"{vuln.get('VulnerabilityID', 'UNKNOWN')}: {vuln.get('PkgName', 'unknown')}",
                "description": vuln.get("Description", ""),
                "affected_file": result.get("Target", ""),
                "cve_id": vuln.get("VulnerabilityID"),
                "cvss_score": vuln.get("CVSS", {}).get("nvd", {}).get("V3Score"),
                "remediation": f"Upgrade {vuln.get('PkgName', 'package')} to {vuln.get('FixedVersion', 'latest')}",
                "line_number": None,
            })

    return findings


# ================================
# Scanner: Gitleaks (Secret Detection)
# ================================

async def run_gitleaks(workspace_path: str) -> list[dict[str, Any]]:
    """Run Gitleaks secret detection scanner."""
    report_path = os.path.join(tempfile.gettempdir(), f"gitleaks-{os.getpid()}.json")

    cmd = [
        "gitleaks",
        "detect",
        "--source",
        workspace_path,
        "--report-format",
        "json",
        "--report-path",
        report_path,
        "--no-git",  # scan files, not git history
        "--exit-code",
        "0",
    ]

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await process.communicate()

        if os.path.exists(report_path):
            with open(report_path) as f:
                data = json.load(f)
            os.remove(report_path)
            return parse_gitleaks_output(data)

        return []

    except FileNotFoundError:
        logger.warning("Gitleaks not installed, skipping secret detection")
        return []
    except (json.JSONDecodeError, OSError) as e:
        logger.error("Gitleaks output parse error", error=str(e))
        return []


def parse_gitleaks_output(findings: list) -> list[dict[str, Any]]:
    """Parse Gitleaks JSON output to canonical format."""
    return [
        {
            "scanner": "gitleaks",
            "severity": "CRITICAL",  # All secrets are CRITICAL
            "category": "SECRET_LEAK",
            "title": f"Secret detected: {f.get('RuleID', 'unknown')}",
            "description": f"Potential secret in {f.get('File', 'unknown')}",
            "affected_file": f.get("File", ""),
            "cve_id": None,
            "cvss_score": None,
            "remediation": "Remove the secret, rotate credentials, add to .gitleaksignore if false positive",
            "line_number": f.get("StartLine"),
            "match": (f.get("Match", "")[:100] + "...") if len(f.get("Match", "")) > 100 else f.get("Match", ""),
        }
        for f in findings
    ]


# ================================
# Scanner: Semgrep (SAST)
# ================================

async def run_semgrep(workspace_path: str) -> list[dict[str, Any]]:
    """Run Semgrep static analysis scanner."""
    cmd = [
        "semgrep",
        "scan",
        "--config",
        "p/owasp-top-ten",
        "--config",
        "p/security-audit",
        "--json",
        "--quiet",
        workspace_path,
    ]

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        stdout, _ = await process.communicate()

        data = json.loads(stdout.decode())
        return parse_semgrep_output(data)

    except FileNotFoundError:
        logger.warning("Semgrep not installed, skipping SAST analysis")
        return []
    except json.JSONDecodeError as e:
        logger.error("Semgrep output parse error", error=str(e))
        return []


def parse_semgrep_output(data: dict) -> list[dict[str, Any]]:
    """Parse Semgrep JSON output to canonical format."""
    severity_map = {
        "ERROR": "HIGH",
        "WARNING": "MEDIUM",
        "INFO": "LOW",
    }

    return [
        {
            "scanner": "semgrep",
            "severity": severity_map.get(r.get("extra", {}).get("severity", ""), "MEDIUM"),
            "category": "SAST",
            "title": r.get("check_id", "unknown"),
            "description": r.get("extra", {}).get("message", ""),
            "affected_file": r.get("path", ""),
            "cve_id": r.get("extra", {}).get("metadata", {}).get("cve"),
            "cvss_score": None,
            "remediation": r.get("extra", {}).get("metadata", {}).get("fix", "Review and fix the identified issue"),
            "line_number": r.get("start", {}).get("line"),
        }
        for r in data.get("results", [])
    ]


# ================================
# Parallel Scanner Execution
# ================================

async def run_all_scanners(workspace_path: str, job_id: str) -> list[dict[str, Any]]:
    """Run all three scanners concurrently."""
    trivy_task = asyncio.create_task(run_trivy(workspace_path, job_id))
    gitleaks_task = asyncio.create_task(run_gitleaks(workspace_path))
    semgrep_task = asyncio.create_task(run_semgrep(workspace_path))

    results = await asyncio.gather(
        trivy_task,
        gitleaks_task,
        semgrep_task,
        return_exceptions=True,
    )

    all_findings: list[dict[str, Any]] = []
    scanner_names = ["trivy", "gitleaks", "semgrep"]

    for scanner_name, result in zip(scanner_names, results):
        if isinstance(result, Exception):
            logger.error(f"Scanner {scanner_name} failed", error=str(result))
        else:
            all_findings.extend(result)
            logger.info(f"Scanner {scanner_name} completed", finding_count=len(result))

    return all_findings


# ================================
# Database Operations
# ================================

async def persist_findings(
    db: AsyncSession,
    pipeline_id: str,
    findings: list[dict[str, Any]],
) -> None:
    """Persist security findings to database."""
    import uuid

    for f in findings:
        finding = SecurityFinding(
            pipeline_id=uuid.UUID(pipeline_id),
            scanner=f["scanner"],
            severity=f["severity"],
            category=f["category"],
            title=f["title"],
            description=f.get("description"),
            affected_file=f.get("affected_file"),
            line_number=f.get("line_number"),
            cve_id=f.get("cve_id"),
            cvss_score=f.get("cvss_score"),
            remediation=f.get("remediation"),
            suppressed=False,
        )
        db.add(finding)

    await db.commit()


async def get_security_policy(db: AsyncSession, org_id: str) -> Optional[SecurityPolicy]:
    """Get organization's security policy."""
    import uuid

    result = await db.execute(
        select(SecurityPolicy).where(SecurityPolicy.org_id == uuid.UUID(org_id))
    )
    return result.scalar_one_or_none()


# ================================
# Policy Gate
# ================================

async def evaluate_security_policy(
    db: AsyncSession,
    pipeline_id: str,
    org_id: str,
    findings: list[dict[str, Any]],
) -> tuple[bool, str]:
    """
    Evaluate findings against security policy.
    Returns (blocked: bool, reason: str).
    """
    policy = await get_security_policy(db, org_id)

    # Default policy if none exists
    block_on_critical = policy.block_on_critical if policy else True
    block_on_secrets = policy.block_on_secrets if policy else True

    critical = [f for f in findings if f["severity"] == "CRITICAL" and not f.get("suppressed")]
    secrets = [f for f in findings if f["category"] == "SECRET_LEAK" and not f.get("suppressed")]

    if secrets and block_on_secrets:
        return True, f"Pipeline blocked: {len(secrets)} secret(s) detected"

    if critical and block_on_critical:
        return True, f"Pipeline blocked: {len(critical)} CRITICAL vulnerability(s) found"

    return False, ""


# ================================
# Alert Publishing
# ================================

async def publish_security_alert(
    pipeline: Pipeline,
    org_id: str,
    findings: list[dict[str, Any]],
    blocked: bool,
    reason: str,
) -> None:
    """Publish security alert to notification service."""
    critical_count = len([f for f in findings if f["severity"] == "CRITICAL"])

    alert = AlertEvent(
        event_type="security_critical" if critical_count > 0 else "pipeline_failed",
        org_id=org_id,
        repo_id=str(pipeline.repo_id),
        pipeline_id=str(pipeline.id),
        severity="CRITICAL" if critical_count > 0 else "ERROR",
        title=f"Security Scan: {critical_count} Critical Issues",
        message=reason if blocked else f"Found {len(findings)} security issues",
        metadata={
            "critical": critical_count,
            "high": len([f for f in findings if f["severity"] == "HIGH"]),
            "medium": len([f for f in findings if f["severity"] == "MEDIUM"]),
            "low": len([f for f in findings if f["severity"] == "LOW"]),
            "blocked": blocked,
        },
        timestamp=datetime.utcnow().isoformat() + "Z",
    )

    await publish_message(TOPIC_ALERTS, key=str(pipeline.id), value=alert)


async def publish_security_summary(
    pipeline_id: str,
    findings: list[dict[str, Any]],
    blocked: bool,
) -> None:
    """Publish security scan summary."""
    summary = SecuritySummary(
        pipeline_id=pipeline_id,
        total_findings=len(findings),
        critical=len([f for f in findings if f["severity"] == "CRITICAL"]),
        high=len([f for f in findings if f["severity"] == "HIGH"]),
        medium=len([f for f in findings if f["severity"] == "MEDIUM"]),
        low=len([f for f in findings if f["severity"] == "LOW"]),
        blocked=blocked,
        timestamp=datetime.utcnow().isoformat() + "Z",
    )

    await publish_message(TOPIC_SECURITY_RESULTS, key=pipeline_id, value=summary)


# ================================
# Clone Repository
# ================================

async def clone_repository(repo_url: str, commit_sha: str, target_dir: str) -> bool:
    """Clone repository at specific commit."""
    try:
        # Clone with depth 1 for the specific commit
        clone_cmd = ["git", "clone", "--depth", "1", repo_url, target_dir]
        process = await asyncio.create_subprocess_exec(
            *clone_cmd,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await process.communicate()

        if process.returncode != 0:
            logger.error("Git clone failed", error=stderr.decode())
            return False

        # Checkout specific commit
        checkout_cmd = ["git", "-C", target_dir, "checkout", commit_sha]
        process = await asyncio.create_subprocess_exec(
            *checkout_cmd,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await process.communicate()

        return True

    except Exception as e:
        logger.error("Clone failed", error=str(e))
        return False


# ================================
# Security Scan Handler
# ================================

async def handle_security_scan(event: PipelineTriggerEvent) -> None:
    """Handle security scan for a pipeline trigger."""
    logger.info(
        "Starting security scan",
        repo_id=event.repo_id,
        commit_sha=event.commit_sha,
    )

    async with get_db_context() as db:
        import uuid

        # Get repository
        result = await db.execute(
            select(Repository).where(Repository.id == uuid.UUID(event.repo_id))
        )
        repo = result.scalar_one_or_none()
        if not repo:
            logger.error("Repository not found", repo_id=event.repo_id)
            return

        # Get or create pipeline record (it may already exist from orchestrator)
        result = await db.execute(
            select(Pipeline).where(
                Pipeline.repo_id == uuid.UUID(event.repo_id),
                Pipeline.commit_sha == event.commit_sha,
            )
        )
        pipeline = result.scalar_one_or_none()

        if not pipeline:
            # Create minimal pipeline record for security results
            pipeline = Pipeline(
                repo_id=uuid.UUID(event.repo_id),
                trigger_type=event.trigger_type,
                commit_sha=event.commit_sha,
                branch=event.branch,
                status="RUNNING",
            )
            db.add(pipeline)
            await db.flush()

        # Clone repository to temp directory
        with tempfile.TemporaryDirectory() as workspace:
            if not await clone_repository(repo.url, event.commit_sha, workspace):
                logger.error("Failed to clone repository for scanning")
                return

            # Run all scanners
            findings = await run_all_scanners(workspace, str(pipeline.id))

        logger.info(
            "Security scan completed",
            pipeline_id=str(pipeline.id),
            total_findings=len(findings),
        )

        # Persist findings
        await persist_findings(db, str(pipeline.id), findings)

        # Evaluate policy
        blocked, reason = await evaluate_security_policy(
            db,
            str(pipeline.id),
            str(repo.organization_id),
            findings,
        )

        if blocked:
            # Update pipeline status
            await db.execute(
                update(Pipeline)
                .where(Pipeline.id == pipeline.id)
                .values(status="FAILED", blocked_reason=reason)
            )
            await db.commit()

            # Publish alert
            await publish_security_alert(pipeline, str(repo.organization_id), findings, blocked, reason)

        # Publish summary
        await publish_security_summary(str(pipeline.id), findings, blocked)


# ================================
# Kafka Message Handler
# ================================

async def handle_kafka_message(msg: Any) -> None:
    """Handle incoming Kafka messages."""
    try:
        event = PipelineTriggerEvent.model_validate_json(msg.value())
        await handle_security_scan(event)
    except Exception as e:
        logger.error("Message processing error", error=str(e))


# ================================
# FastAPI App
# ================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting security scanner")
    await init_db()

    # Start Kafka consumer
    consumer = KafkaConsumerLoop("security-scanner", [TOPIC_PIPELINE_TRIGGER])
    consumer_task = asyncio.create_task(consumer.start(handle_kafka_message))

    yield

    logger.info("Shutting down security scanner")
    consumer.stop()
    consumer_task.cancel()


app = FastAPI(
    title="Intelli-CI Security Scanner",
    description="Security scanning service with Trivy, Gitleaks, and Semgrep",
    version="1.0.0",
    lifespan=lifespan,
)


# ================================
# API Endpoints
# ================================

@app.get("/api/v1/pipelines/{pipeline_id}/security")
async def get_pipeline_security_findings(
    pipeline_id: str,
    severity: Optional[str] = None,
    scanner: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """Get security findings for a pipeline."""
    import uuid

    query = select(SecurityFinding).where(SecurityFinding.pipeline_id == uuid.UUID(pipeline_id))

    if severity:
        query = query.where(SecurityFinding.severity == severity.upper())
    if scanner:
        query = query.where(SecurityFinding.scanner == scanner.lower())

    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    findings = result.scalars().all()

    return {
        "data": [
            {
                "id": str(f.id),
                "scanner": f.scanner,
                "severity": f.severity,
                "category": f.category,
                "title": f.title,
                "description": f.description,
                "affected_file": f.affected_file,
                "line_number": f.line_number,
                "cve_id": f.cve_id,
                "cvss_score": f.cvss_score,
                "remediation": f.remediation,
                "suppressed": f.suppressed,
            }
            for f in findings
        ],
        "meta": {"limit": limit, "offset": offset},
    }


@app.post("/api/v1/security/findings/{finding_id}/suppress")
async def suppress_finding(
    finding_id: str,
    reason: str,
    db: AsyncSession = Depends(get_db),
):
    """Suppress a security finding."""
    import uuid

    result = await db.execute(
        select(SecurityFinding).where(SecurityFinding.id == uuid.UUID(finding_id))
    )
    finding = result.scalar_one_or_none()

    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")

    finding.suppressed = True
    finding.suppressed_reason = reason
    finding.suppressed_at = datetime.utcnow()
    await db.commit()

    return {"status": "suppressed", "finding_id": finding_id}


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
        port=settings.service.security_scanner_port,
        reload=True,
    )
