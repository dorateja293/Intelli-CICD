"""
ML prediction service — loads the trained RandomForestClassifier and
returns a failure probability for a given feature vector.
"""
import os
from pathlib import Path
from typing import Optional

import joblib
import numpy as np

from backend.core.config import get_settings

_settings = get_settings()

FEATURE_COLUMNS = [
    "files_changed",
    "lines_added",
    "lines_deleted",
    "code_churn",
    "previous_failures",
    "test_coverage",
    "is_merge_commit",
    "commit_message_length",
    "num_contributors_last_30d",
    "days_since_last_failure",
    "recent_failure_flag",
]

_model = None


def _load_model():
    global _model
    if _model is not None:
        return _model

    path = Path(_settings.ML_MODEL_PATH) if _settings.ML_MODEL_PATH else Path()
    # Fallback to legacy Flask model location
    if not path.is_file():
        path = Path("model/intelli_ci_model.pkl")

    if path.is_file():
        _model = joblib.load(path)
    else:
        _model = None  # graceful degradation — will return 0.5

    return _model


def predict_failure_probability(features: dict) -> tuple[float, float]:
    """
    Returns (failure_probability, confidence).
    confidence is max class probability from the classifier.
    """
    model = _load_model()
    if model is None:
        return 0.5, 0.0

    row = [features.get(col, 0) for col in FEATURE_COLUMNS]
    X = np.array(row, dtype=float).reshape(1, -1)

    proba = model.predict_proba(X)[0]
    # Assume class index 1 = failure
    classes = list(model.classes_)
    if 1 in classes:
        failure_prob = float(proba[classes.index(1)])
    else:
        failure_prob = float(proba[-1])

    confidence = float(np.max(proba))
    return failure_prob, confidence
