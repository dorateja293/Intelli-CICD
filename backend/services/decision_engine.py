"""
Decision engine — combines ML failure probability and LLM risk level
to produce a final test execution decision.

Decisions:
  RUN_TESTS     — run the full CI test suite
  SKIP_TESTS    — safe to skip; low risk
  PARTIAL_TESTS — run only tests related to changed modules
"""
import json
import re
from dataclasses import dataclass

from backend.core.config import get_settings
from backend.services.llm_service import LLMResult

_settings = get_settings()

# Simple module → test-file mapping (extend as needed)
MODULE_TEST_MAP: dict[str, list[str]] = {
    "payment": ["tests/test_payment.py", "tests/test_transactions.py"],
    "auth": ["tests/test_auth.py", "tests/test_users.py"],
    "api": ["tests/test_api.py"],
    "database": ["tests/test_db.py"],
    "webhook": ["tests/test_webhook.py"],
}


@dataclass
class DecisionResult:
    decision: str               # RUN_TESTS | SKIP_TESTS | PARTIAL_TESTS
    failure_probability: float
    ml_confidence: float
    llm_risk_level: str
    llm_confidence: float
    affected_modules: list[str]
    partial_test_paths: list[str]
    reasoning: str


def _llm_risk_score(risk_level: str) -> float:
    """Convert LLM risk label to numeric score."""
    return {"LOW": 0.15, "MEDIUM": 0.50, "HIGH": 0.85}.get(risk_level.upper(), 0.50)


def _infer_partial_tests(modules: list[str]) -> list[str]:
    tests = []
    for mod in modules:
        for key, paths in MODULE_TEST_MAP.items():
            if key in mod.lower():
                tests.extend(paths)
    return list(dict.fromkeys(tests))  # deduplicate, preserve order


def make_decision(
    failure_probability: float,
    ml_confidence: float,
    llm_result: LLMResult,
) -> DecisionResult:
    """
    Fusion logic:
    - Weighted average: 60% ML + 40% LLM
    - Final score >= THRESHOLD_RUN   → RUN_TESTS
    - Final score >= THRESHOLD_PARTIAL → PARTIAL_TESTS
    - Otherwise                       → SKIP_TESTS
    """
    llm_score = _llm_risk_score(llm_result.risk_level)
    fused = 0.60 * failure_probability + 0.40 * llm_score

    partial_paths = _infer_partial_tests(llm_result.affected_modules)

    if fused >= _settings.DECISION_THRESHOLD_RUN:
        decision = "RUN_TESTS"
    elif fused >= _settings.DECISION_THRESHOLD_PARTIAL and partial_paths:
        decision = "PARTIAL_TESTS"
    elif fused >= _settings.DECISION_THRESHOLD_PARTIAL:
        decision = "RUN_TESTS"   # no targeted tests found — run all
    else:
        decision = "SKIP_TESTS"

    reasoning = (
        f"ML failure_prob={failure_probability:.2f} (confidence={ml_confidence:.2f}), "
        f"LLM risk={llm_result.risk_level} (confidence={llm_result.confidence:.2f}), "
        f"fused_score={fused:.2f} → {decision}"
    )

    return DecisionResult(
        decision=decision,
        failure_probability=failure_probability,
        ml_confidence=ml_confidence,
        llm_risk_level=llm_result.risk_level,
        llm_confidence=llm_result.confidence,
        affected_modules=llm_result.affected_modules,
        partial_test_paths=partial_paths,
        reasoning=reasoning,
    )
