"""
GET /analytics/summary — Aggregated KPIs scoped to the authenticated user.
GET /analytics/timeline — Daily commit counts for the last N days.
GET /repositories — List repositories linked to the authenticated user.
"""
from datetime import datetime, timedelta, timezone
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import Date, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.security import get_current_user_id
from backend.database.connection import get_db
from backend.models.commit import Commit
from backend.models.prediction import Prediction
from backend.models.repository import Repository

router = APIRouter(tags=["analytics"])


@router.get("/analytics/summary")
async def analytics_summary(
    db: AsyncSession = Depends(get_db),
    uid: str = Depends(get_current_user_id),
):
    user_uuid = uuid.UUID(uid)
    # Count predictions belonging to this user directly (manual + webhook via user_id)
    total_result = await db.execute(
        select(func.count()).select_from(Prediction).where(Prediction.user_id == user_uuid)
    )
    total = total_result.scalar() or 0

    skipped_result = await db.execute(
        select(func.count()).select_from(Prediction).where(
            Prediction.user_id == user_uuid,
            Prediction.decision == "SKIP_TESTS",
        )
    )
    skipped = skipped_result.scalar() or 0

    partial_result = await db.execute(
        select(func.count()).select_from(Prediction).where(
            Prediction.user_id == user_uuid,
            Prediction.decision == "PARTIAL_TESTS",
        )
    )
    partial = partial_result.scalar() or 0

    executed = total - skipped

    avg_prob_result = await db.execute(
        select(func.avg(Prediction.failure_probability)).where(Prediction.user_id == user_uuid)
    )
    avg_prob = float(avg_prob_result.scalar() or 0)

    return {
        "total": total,
        "skipped": skipped,
        "partial": partial,
        "executed": executed,
        "time_saved": skipped * 10,   # est. 10 min per skipped run
        "avg_failure_probability": round(avg_prob, 4),
    }


@router.get("/analytics/timeline")
async def analytics_timeline(
    days: int = 30,
    db: AsyncSession = Depends(get_db),
    uid: str = Depends(get_current_user_id),
):
    user_uuid = uuid.UUID(uid)
    since = datetime.now(timezone.utc) - timedelta(days=days)

    day_col = cast(Commit.created_at, Date).label("day")

    result = await db.execute(
        select(day_col, func.count().label("commits"))
        .join(Repository, Commit.repository_id == Repository.id)
        .where(
            Repository.owner_id == user_uuid,
            Commit.created_at >= since,
        )
        .group_by(day_col)
        .order_by(day_col)
    )

    rows = result.all()
    timeline = []
    for row in rows:
        d = row.day
        # SQLite returns a string; PostgreSQL returns a datetime.date
        if isinstance(d, str):
            d = datetime.strptime(d, "%Y-%m-%d")
        timeline.append({
            "date": d.strftime("%b %d") if d else "",
            "commits": row.commits,
        })
    return {"timeline": timeline}


@router.get("/repositories")
async def list_repositories(
    db: AsyncSession = Depends(get_db),
    uid: str = Depends(get_current_user_id),
):
    result = await db.execute(
        select(Repository)
        .where(Repository.owner_id == uuid.UUID(uid))
        .order_by(Repository.created_at.desc())
        .limit(100)
    )
    repos = result.scalars().all()
    return {
        "repositories": [
            {
                "id": str(r.id),
                "full_name": r.full_name,
                "default_branch": r.default_branch,
                "description": r.description,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in repos
        ]
    }
