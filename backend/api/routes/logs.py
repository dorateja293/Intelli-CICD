"""
POST /analyze-logs  — Analyze CI log text and classify the error.
POST /fix-error     — Alias / convenience endpoint, same logic.
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from backend.ai.log_analyzer import analyze_log, suggest_fix
from backend.core.security import get_current_user_id

router = APIRouter(tags=["logs"])


class LogRequest(BaseModel):
    log_text: str = Field(..., max_length=500_000)


class LogAnalysisResponse(BaseModel):
    error_type: str
    root_cause: str
    suggested_fix: str
    confidence: float
    severity: str
    matched_lines: list[str]


@router.post("/analyze-logs", response_model=LogAnalysisResponse)
async def analyze_logs(body: LogRequest, _uid: str = Depends(get_current_user_id)):
    """Analyze raw CI log text and return a classified error with suggested fix."""
    if not body.log_text.strip():
        return LogAnalysisResponse(
            error_type="unknown_error",
            root_cause="Empty log provided",
            suggested_fix="Please provide non-empty CI log text.",
            confidence=0.0,
            severity="low",
            matched_lines=[],
        )
    result = analyze_log(body.log_text)
    return LogAnalysisResponse(
        error_type=result.error_type,
        root_cause=result.root_cause,
        suggested_fix=result.suggested_fix,
        confidence=result.confidence,
        severity=result.severity,
        matched_lines=result.matched_lines,
    )


@router.post("/fix-error", response_model=LogAnalysisResponse)
async def fix_error(body: LogRequest, _uid: str = Depends(get_current_user_id)):
    """Alias for /analyze-logs — accepts CI log text and returns step-by-step fix."""
    return await analyze_logs(body, _uid)
