"""
Database Seeder for Intelli-CI

Populates realistic organizations, users, repositories, pipelines,
stages/jobs, security findings, and AI suggestions for demo and testing.
"""
import asyncio
import json
import uuid
from datetime import datetime, timedelta, timezone
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import get_settings
from shared.database import async_session_factory, engine, init_db
from shared.models import (
    AISuggestion,
    Job,
    Organization,
    Pipeline,
    Repository,
    SecurityFinding,
    SecurityPolicy,
    User,
)
from shared.security import hash_password

settings = get_settings()
logger = structlog.get_logger()


async def seed():
    print("Initializing database schema...")
    await init_db()

    async with async_session_factory() as db:
        # Check if already seeded
        existing_org = await db.execute(select(Organization).limit(1))
        if existing_org.scalar_one_or_none():
            print("Database already contains data. Skipping re-seed.")
            return

        print("Seeding initial dataset...")

        # 1. Organization
        org_id = uuid.uuid4()
        org = Organization(
            id=org_id,
            name="Intelli-CI Engineering Org",
            slug="intelli-ci-eng",
        )
        db.add(org)

        # 2. Security Policy
        policy = SecurityPolicy(
            id=uuid.uuid4(),
            org_id=org_id,
            block_on_critical=True,
            block_on_high=False,
            block_on_secrets=True,
            max_critical_allowed=0,
            max_high_allowed=3,
        )
        db.add(policy)

        # 3. Users
        admin_user = User(
            id=uuid.uuid4(),
            email="admin@intelli-ci.dev",
            name="Platform Admin",
            hashed_password=hash_password("AdminPass123!"),
            organization_id=org_id,
            role="admin",
            is_active=True,
            is_verified=True,
        )
        dev_user = User(
            id=uuid.uuid4(),
            email="developer@intelli-ci.dev",
            name="Sarah Jenkins",
            hashed_password=hash_password("DevPass123!"),
            organization_id=org_id,
            role="developer",
            is_active=True,
            is_verified=True,
        )
        db.add_all([admin_user, dev_user])

        # 4. Repositories
        repos_data = [
            ("intelli-ci/core-platform", "https://github.com/intelli-ci/core-platform", "main"),
            ("intelli-ci/api-gateway", "https://github.com/intelli-ci/api-gateway", "main"),
            ("intelli-ci/frontend-dashboard", "https://github.com/intelli-ci/frontend-dashboard", "main"),
            ("intelli-ci/ml-pipeline", "https://github.com/intelli-ci/ml-pipeline", "master"),
        ]

        repos = []
        for name, url, branch in repos_data:
            r = Repository(
                id=uuid.uuid4(),
                organization_id=org_id,
                name=name,
                url=url,
                provider="github",
                default_branch=branch,
                webhook_secret=str(uuid.uuid4()),
            )
            repos.append(r)
            db.add(r)

        await db.flush()

        # 5. Pipeline Runs
        now = datetime.now(timezone.utc)
        pipeline_configs = [
            # (repo_idx, branch, commit, message, author, status, duration, files, added, deleted, prob, decision, saved)
            (0, "main", "7f8b9a1", "feat(api): optimize Redis cache hit ratio and TTL policies", "Sarah Jenkins", "SUCCESS", 112, 6, 140, 25, 0.18, "SKIP_TESTS", 18),
            (0, "main", "3c4d5e6", "fix(db): add connection pooling with retry backoff", "Alex Rivera", "SUCCESS", 135, 3, 65, 12, 0.12, "SKIP_TESTS", 18),
            (0, "feature/auth-jwt", "9a8b7c6", "feat(auth): integrate asymmetric RS256 token verification", "Sarah Jenkins", "SUCCESS", 154, 8, 220, 45, 0.28, "PARTIAL_TESTS", 9),
            (0, "bugfix/kafka-fallback", "1b2c3d4", "fix: handle missing broker with graceful local queue fallback", "Dev", "FAILED", 88, 14, 380, 95, 0.78, "RUN_TESTS", 0),
            (1, "main", "4d5e6f7", "perf(gateway): implement token bucket rate limiting", "Sarah Jenkins", "SUCCESS", 95, 4, 85, 10, 0.15, "SKIP_TESTS", 18),
            (1, "feature/cors-headers", "8e9f0a1", "chore(config): allow dynamic origin resolution", "Alex Rivera", "SUCCESS", 82, 2, 30, 5, 0.08, "SKIP_TESTS", 18),
            (1, "main", "2c3d4e5", "refactor(routes): streamline pipeline status queries", "Dev", "SUCCESS", 104, 5, 110, 35, 0.22, "PARTIAL_TESTS", 9),
            (2, "main", "6a7b8c9", "feat(ui): add real-time ML risk predictor and charts", "Sarah Jenkins", "SUCCESS", 145, 12, 310, 80, 0.32, "PARTIAL_TESTS", 9),
            (2, "bugfix/vite-proxy", "5f6e7d8", "fix(vite): adjust proxy target for container networking", "Alex Rivera", "SUCCESS", 72, 1, 15, 2, 0.05, "SKIP_TESTS", 18),
            (2, "feature/log-viewer", "0b1c2d3", "feat(logs): add ANSI color highlights and copy action", "Dev", "FAILED", 64, 18, 540, 160, 0.86, "RUN_TESTS", 0),
            (3, "master", "9f8e7d6", "train(ml): retrain RandomForest with 5000 balanced samples", "Alex Rivera", "SUCCESS", 210, 5, 190, 40, 0.20, "PARTIAL_TESTS", 9),
            (3, "master", "3a2b1c0", "feat(predictor): export confusion matrix and feature importances", "Sarah Jenkins", "SUCCESS", 180, 4, 130, 20, 0.14, "SKIP_TESTS", 18),
            (0, "main", "8b7c6d5", "docs: update system architecture diagram and README", "Alex Rivera", "SUCCESS", 45, 2, 80, 10, 0.02, "SKIP_TESTS", 18),
            (1, "bugfix/timeout", "6e5d4c3", "fix(http): increase upstream timeout for heavy analytics", "Sarah Jenkins", "SUCCESS", 90, 3, 40, 8, 0.10, "SKIP_TESTS", 18),
            (0, "feature/anomaly-detector", "5a4b3c2", "feat(ai): add Isolation Forest pipeline duration anomaly check", "Dev", "FAILED", 160, 22, 620, 190, 0.91, "RUN_TESTS", 0),
        ]

        for i, (r_idx, branch, sha, msg, author, status, duration, files, added, deleted, prob, decision, saved) in enumerate(pipeline_configs):
            pipe_id = uuid.uuid4()
            pipe_created = now - timedelta(hours=(len(pipeline_configs) - i) * 3, minutes=15)
            meta = {
                "files_changed": files,
                "lines_added": added,
                "lines_deleted": deleted,
                "churn": added + deleted,
                "failure_probability": prob,
                "decision": decision,
                "time_saved_minutes": saved,
            }

            p = Pipeline(
                id=pipe_id,
                repo_id=repos[r_idx].id,
                trigger_type="push",
                commit_sha=f"{sha}000000000000000000000000000000000"[:40],
                branch=branch,
                commit_message=msg,
                author_name=author,
                author_email=f"{author.lower().replace(' ', '.')}@example.com",
                status=status,
                created_at=pipe_created,
                started_at=pipe_created + timedelta(seconds=5),
                completed_at=pipe_created + timedelta(seconds=duration + 5),
                duration_seconds=duration,
                config_yaml=json.dumps(meta),
            )
            db.add(p)

            # Stages for each pipeline
            stages = [
                ("checkout", "checkout", 12, "SUCCESS", None),
                ("dependencies", "dependencies", 45, "SUCCESS", None),
                ("build", "build", int(duration * 0.35), "SUCCESS", None),
                ("test", "test", int(duration * 0.40), status, "AssertionError: Connection timeout to mock redis server on port 6379" if status == "FAILED" else None),
                ("security_scan", "security_scan", 25, "SUCCESS", None),
            ]
            if status == "SUCCESS":
                stages.append(("deploy", "deploy", 30, "SUCCESS", None))

            for w_idx, (j_name, j_stage, j_dur, j_status, j_err) in enumerate(stages):
                j = Job(
                    id=uuid.uuid4(),
                    pipeline_id=pipe_id,
                    name=j_name,
                    stage=j_stage,
                    status=j_status,
                    duration_seconds=j_dur,
                    wave_index=w_idx,
                    error_message=j_err,
                    exit_code=0 if j_status == "SUCCESS" else 1,
                    created_at=pipe_created,
                    started_at=pipe_created,
                    completed_at=pipe_created + timedelta(seconds=j_dur),
                )
                db.add(j)

                # Add AI suggestion for failures
                if j_status == "FAILED":
                    sug = AISuggestion(
                        id=uuid.uuid4(),
                        pipeline_id=pipe_id,
                        job_id=j.id,
                        error_fingerprint=f"ERR-{sha[:7]}",
                        error_type="DATABASE_CONNECTION_TIMEOUT",
                        error_message="AssertionError: Connection timeout to mock redis server on port 6379",
                        suggestion_text="1. Verify test fixture environment variables.\n2. Ensure Redis mock container or fakeredis is initialized in conftest.py.\n3. Increase socket timeout in Redis connection pool settings.",
                        confidence_score=0.92,
                        rule_id="RED001",
                        model_used="rule_engine",
                        created_at=pipe_created,
                    )
                    db.add(sug)

        await db.commit()
        print("✓ Database seeded successfully with 4 repositories and 15 complete pipeline runs.")


if __name__ == "__main__":
    asyncio.run(seed())
