"""
GET  /system-health  — Detailed system health: DB, model, stats.
"""
import time
from pathlib import Path

from fastapi import APIRouter, Depends
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import get_settings
from backend.core.security import get_current_user_id
from backend.database.connection import get_db
from backend.models.commit import Commit
from backend.models.prediction import Prediction
from backend.models.user import User
from backend.services.ml_service import _load_model

router = APIRouter(tags=["system"])

_start_time = time.time()


@router.get("/system-health")
async def system_health(
    db: AsyncSession = Depends(get_db),
    settings=Depends(get_settings),
    _uid: str = Depends(get_current_user_id),
):
    # ── Database check ────────────────────────────────────────────────────────
    db_ok = False
    try:
        await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        pass

    # ── Model check ───────────────────────────────────────────────────────────
    model = _load_model()
    model_loaded = model is not None
    model_path = str(Path(settings.ML_MODEL_PATH))

    # ── DB stats ──────────────────────────────────────────────────────────────
    try:
        total_predictions = (await db.execute(select(func.count()).select_from(Prediction))).scalar() or 0
        total_commits     = (await db.execute(select(func.count()).select_from(Commit))).scalar() or 0
        total_users       = (await db.execute(select(func.count()).select_from(User))).scalar() or 0

        skipped = (
            await db.execute(
                select(func.count()).select_from(Prediction).where(Prediction.decision == "SKIP_TESTS")
            )
        ).scalar() or 0

        avg_prob = (await db.execute(select(func.avg(Prediction.failure_probability)))).scalar() or 0.0
    except Exception:
        total_predictions = total_commits = total_users = skipped = 0
        avg_prob = 0.0

    skip_rate = round(skipped / total_predictions, 4) if total_predictions > 0 else 0.0
    uptime_seconds = int(time.time() - _start_time)

    return {
        "status": "healthy" if db_ok else "degraded",
        "uptime_seconds": uptime_seconds,
        "uptime_human": _format_uptime(uptime_seconds),
        "database": {
            "connected": db_ok,
            "total_users": total_users,
            "total_commits": total_commits,
            "total_predictions": total_predictions,
        },
        "ml_model": {
            "loaded": model_loaded,
            "path": model_path,
            "provider": "RandomForestClassifier" if model_loaded else "none",
        },
        "ci_stats": {
            "tests_skipped": skipped,
            "skip_rate": skip_rate,
            "avg_failure_probability": round(float(avg_prob), 4),
            "estimated_minutes_saved": skipped * 10,
        },
        "llm": {
            "provider": settings.LLM_PROVIDER,
            "model": settings.OPENAI_MODEL if settings.LLM_PROVIDER == "openai" else settings.OLLAMA_MODEL,
        },
    }


def _format_uptime(seconds: int) -> str:
    if seconds < 60:
        return f"{seconds}s"
    if seconds < 3600:
        return f"{seconds // 60}m {seconds % 60}s"
    h = seconds // 3600
    m = (seconds % 3600) // 60
    return f"{h}h {m}m"
