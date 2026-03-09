"""
POST /webhook/github — Receive GitHub push events, extract features, run
                       ML+LLM prediction, persist results.
"""
import hashlib
import hmac
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import get_settings, Settings
from backend.core.security import verify_github_signature
from backend.database.connection import get_db
from backend.models.commit import Commit
from backend.models.prediction import Prediction
from backend.models.repository import Repository
from backend.services.decision_engine import make_decision
from backend.services.llm_service import analyze_commit
from backend.services.ml_service import predict_failure_probability
from sqlalchemy import select

router = APIRouter(prefix="/webhook", tags=["webhook"])


def _extract_features(commit_payload: dict) -> dict:
    """Extract ML features from a single GitHub commit object."""
    added = commit_payload.get("added", [])
    removed = commit_payload.get("removed", [])
    modified = commit_payload.get("modified", [])
    all_files = added + removed + modified

    message = commit_payload.get("message", "")
    return {
        "files_changed": len(all_files),
        "lines_added": 0,        # GitHub push payload doesn't include line stats
        "lines_deleted": 0,      # Would need Commits API for that
        "code_churn": len(all_files) * 10,   # rough proxy
        "previous_failures": 0,
        "test_coverage": 0.0,
        "is_merge_commit": 1 if message.lower().startswith("merge") else 0,
        "commit_message_length": len(message),
        "num_contributors_last_30d": 1,
        "days_since_last_failure": 30,
        "recent_failure_flag": 0,
        # LLM extras
        "_message": message,
        "_files": all_files,
    }


@router.post("/github", status_code=status.HTTP_200_OK)
async def github_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
    x_hub_signature_256: str = Header(default=""),
    x_github_event: str = Header(default=""),
):
    raw_body = await request.body()

    # Signature verification
    if not verify_github_signature(raw_body, x_hub_signature_256, settings.GITHUB_WEBHOOK_SECRET):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    if x_github_event != "push":
        return {"status": "ignored", "event": x_github_event}

    try:
        payload = json.loads(raw_body)
    except (json.JSONDecodeError, ValueError):
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    repo_data = payload.get("repository", {})
    repo_full_name = repo_data.get("full_name", "unknown/unknown")
    github_repo_id = str(repo_data.get("id", "0"))

    # Upsert repository record
    result = await db.execute(
        select(Repository).where(Repository.github_repo_id == github_repo_id)
    )
    repo = result.scalar_one_or_none()
    if not repo:
        repo = Repository(
            github_repo_id=github_repo_id,
            full_name=repo_full_name,
            owner_id=None,   # no user linkage without OAuth
        )
        db.add(repo)
        await db.flush()

    processed = []
    for raw_commit in payload.get("commits", []):
        features = _extract_features(raw_commit)

        # Persist commit
        commit = Commit(
            repository_id=repo.id,
            sha=raw_commit.get("id", ""),
            author=raw_commit.get("author", {}).get("name", ""),
            message=features["_message"],
            files_changed=features["files_changed"],
            lines_added=features["lines_added"],
            lines_deleted=features["lines_deleted"],
            code_churn=features["code_churn"],
        )
        db.add(commit)
        await db.flush()

        # ML prediction
        failure_prob, ml_conf = predict_failure_probability(features)

        # LLM analysis
        llm_result = await analyze_commit(
            message=features["_message"],
            files=features["_files"],
            lines_added=features["lines_added"],
            lines_deleted=features["lines_deleted"],
        )

        # Decision
        decision_result = make_decision(failure_prob, ml_conf, llm_result)

        pred = Prediction(
            commit_id=commit.id,
            user_id=repo.owner_id,
            failure_probability=decision_result.failure_probability,
            ml_confidence=decision_result.ml_confidence,
            llm_risk_level=decision_result.llm_risk_level,
            llm_confidence=decision_result.llm_confidence,
            llm_affected_modules=",".join(decision_result.affected_modules),
            llm_reasoning=llm_result.reasoning,
            decision=decision_result.decision,
            partial_test_paths=json.dumps(decision_result.partial_test_paths),
        )
        db.add(pred)

        processed.append({
            "sha": commit.sha,
            "decision": decision_result.decision,
            "failure_probability": decision_result.failure_probability,
        })

    await db.commit()
    return {"status": "processed", "commits": processed}
