"""
POST /predict — Direct ML + LLM prediction endpoint (used by the frontend
                and by the GitHub CI runner).
GET  /commits  — Return paginated commit history with predictions.
"""
import json
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.security import get_current_user_id
from backend.database.connection import get_db
from backend.models.commit import Commit
from backend.models.prediction import Prediction
from backend.models.repository import Repository
from backend.services.decision_engine import make_decision
from backend.services.llm_service import analyze_commit
from backend.services.ml_service import predict_failure_probability

router = APIRouter(tags=["predict"])


class PredictRequest(BaseModel):
    # ML features (validated ranges for production safety)
    files_changed: int = Field(default=0, ge=0, le=10_000)
    lines_added: int = Field(default=0, ge=0, le=1_000_000)
    lines_deleted: int = Field(default=0, ge=0, le=1_000_000)
    code_churn: int = Field(default=0, ge=0, le=2_000_000)
    previous_failures: int = Field(default=0, ge=0, le=10_000)
    test_coverage: float = Field(default=0.0, ge=0.0, le=100.0)
    is_merge_commit: int = Field(default=0, ge=0, le=1)
    commit_message_length: int = Field(default=0, ge=0, le=10_000)
    num_contributors_last_30d: int = Field(default=1, ge=1, le=10_000)
    days_since_last_failure: int = Field(default=30, ge=0, le=365)
    recent_failure_flag: int = Field(default=0, ge=0, le=1)
    # Optional LLM inputs
    commit_message: str = Field(default="", max_length=50_000)
    diff: str = Field(default="", max_length=500_000)
    changed_files: list[str] = Field(default_factory=list, max_length=5_000)


class PredictResponse(BaseModel):
    decision: str
    failure_probability: float
    ml_confidence: float
    llm_risk_level: str
    llm_confidence: float
    affected_modules: list[str]
    partial_test_paths: list[str]
    reasoning: str


@router.post("/predict", response_model=PredictResponse)
async def predict(
    body: PredictRequest,
    db: AsyncSession = Depends(get_db),
    uid: str = Depends(get_current_user_id),
):
    features = body.model_dump(
        include={
            "files_changed", "lines_added", "lines_deleted", "code_churn",
            "previous_failures", "test_coverage", "is_merge_commit",
            "commit_message_length", "num_contributors_last_30d",
            "days_since_last_failure", "recent_failure_flag",
        }
    )

    failure_prob, ml_conf = predict_failure_probability(features)

    llm_result = await analyze_commit(
        message=body.commit_message,
        files=body.changed_files,
        diff=body.diff,
        lines_added=body.lines_added,
        lines_deleted=body.lines_deleted,
    )

    result = make_decision(failure_prob, ml_conf, llm_result)

    # Persist manual prediction so it appears in analytics
    pred_record = Prediction(
        commit_id=None,
        user_id=uuid.UUID(uid),
        failure_probability=result.failure_probability,
        ml_confidence=result.ml_confidence,
        llm_risk_level=result.llm_risk_level,
        llm_confidence=result.llm_confidence,
        llm_affected_modules=",".join(result.affected_modules),
        llm_reasoning=result.reasoning,
        decision=result.decision,
        partial_test_paths=json.dumps(result.partial_test_paths),
    )
    db.add(pred_record)
    await db.commit()

    return PredictResponse(
        decision=result.decision,
        failure_probability=result.failure_probability,
        ml_confidence=result.ml_confidence,
        llm_risk_level=result.llm_risk_level,
        llm_confidence=result.llm_confidence,
        affected_modules=result.affected_modules,
        partial_test_paths=result.partial_test_paths,
        reasoning=result.reasoning,
    )


@router.get("/commits")
async def get_commits(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    uid: str = Depends(get_current_user_id),
):
    limit = min(max(1, limit), 500)
    offset = max(0, offset)
    user_uuid = uuid.UUID(uid)

    # Total count scoped to this user's repos
    total_result = await db.execute(
        select(func.count())
        .select_from(Commit)
        .join(Repository, Commit.repository_id == Repository.id)
        .where(Repository.owner_id == user_uuid)
    )
    total = total_result.scalar() or 0

    # Commits with their latest prediction — only from this user's repos
    result = await db.execute(
        select(Commit, Prediction)
        .join(Repository, Commit.repository_id == Repository.id)
        .outerjoin(Prediction, Prediction.commit_id == Commit.id)
        .where(Repository.owner_id == user_uuid)
        .order_by(desc(Commit.created_at))
        .limit(limit)
        .offset(offset)
    )
    rows = result.all()

    commits = []
    for commit, pred in rows:
        commits.append({
            "commit_sha": commit.sha,
            "author": commit.author,
            "message": commit.message,
            "files_changed": commit.files_changed,
            "code_churn": commit.code_churn,
            "failure_probability": pred.failure_probability if pred else None,
            "decision": pred.decision if pred else None,
            "llm_risk_level": pred.llm_risk_level if pred else None,
            "created_at": commit.created_at.isoformat() if commit.created_at else None,
        })

    return {"commits": commits, "total": total}
