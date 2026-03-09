"""
Risk classifier — maps CommitAnalysis results to a numeric risk score
and a recommended test strategy.

Can be chained after analyzer.py or used independently.
"""
from dataclasses import dataclass


@dataclass
class RiskClassification:
    risk_score: float         # 0.0 – 1.0
    test_strategy: str        # RUN_TESTS | PARTIAL_TESTS | SKIP_TESTS
    targeted_tests: list[str]
    explanation: str


# Module → test file mapping (extend for your codebase)
MODULE_TESTS: dict[str, list[str]] = {
    "auth":       ["tests/test_auth.py", "tests/test_users.py"],
    "payment":    ["tests/test_payment.py", "tests/test_transactions.py"],
    "api":        ["tests/test_api.py"],
    "database":   ["tests/test_db.py"],
    "webhook":    ["tests/test_webhook.py"],
    "models":     ["tests/test_models.py"],
    "services":   ["tests/test_services.py"],
}

RISK_THRESHOLDS = {
    "HIGH":   (0.75, "RUN_TESTS"),
    "MEDIUM": (0.45, "PARTIAL_TESTS"),
    "LOW":    (0.15, "SKIP_TESTS"),
}


def classify(
    risk_level: str,
    confidence: float,
    affected_modules: list[str],
    ml_failure_prob: float = 0.0,
) -> RiskClassification:
    """
    Combine LLM risk level and ML probability into a final classification.
    """
    base_score, default_strategy = RISK_THRESHOLDS.get(risk_level.upper(), (0.45, "PARTIAL_TESTS"))

    # Blend with ML probability (40% LLM, 60% ML)
    blended = 0.4 * base_score + 0.6 * ml_failure_prob

    # Override strategy based on blended score
    if blended >= 0.60:
        strategy = "RUN_TESTS"
    elif blended >= 0.30:
        strategy = "PARTIAL_TESTS"
    else:
        strategy = "SKIP_TESTS"

    # Targeted tests from affected modules
    targeted: list[str] = []
    for mod in affected_modules:
        for key, paths in MODULE_TESTS.items():
            if key in mod.lower():
                targeted.extend(paths)
    targeted = list(dict.fromkeys(targeted))  # deduplicate

    if strategy == "PARTIAL_TESTS" and not targeted:
        strategy = "RUN_TESTS"  # can't be partial without targets

    explanation = (
        f"LLM risk={risk_level} (base={base_score:.2f}), "
        f"ML prob={ml_failure_prob:.2f}, blended={blended:.2f} → {strategy}"
    )

    return RiskClassification(
        risk_score=round(blended, 4),
        test_strategy=strategy,
        targeted_tests=targeted,
        explanation=explanation,
    )
