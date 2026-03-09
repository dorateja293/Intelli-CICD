"""
Standalone predictor — can be used from the CLI or imported as a module.

Usage:
  python -m ml-engine.predictor.predict \
    --files_changed 5 --lines_added 200 --lines_deleted 50 \
    --previous_failures 2 --test_coverage 70
"""
import argparse
import json
from pathlib import Path

import joblib
import numpy as np

FEATURE_COLUMNS = [
    "files_changed", "lines_added", "lines_deleted", "code_churn",
    "previous_failures", "test_coverage", "is_merge_commit",
    "commit_message_length", "num_contributors_last_30d",
    "days_since_last_failure", "recent_failure_flag",
]

DEFAULT_MODEL = "ml-engine/models/model.pkl"


def load_model(path: str = DEFAULT_MODEL):
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Model not found at {p}. Run training first.")
    return joblib.load(p)


def predict(features: dict, model_path: str = DEFAULT_MODEL) -> dict:
    model = load_model(model_path)
    row = [features.get(c, 0) for c in FEATURE_COLUMNS]
    X = np.array(row, dtype=float).reshape(1, -1)

    proba = model.predict_proba(X)[0]
    classes = list(model.classes_)
    failure_prob = float(proba[classes.index(1)]) if 1 in classes else float(proba[-1])
    confidence = float(np.max(proba))

    return {
        "failure_probability": round(failure_prob, 4),
        "confidence": round(confidence, 4),
        "prediction": "FAIL" if failure_prob >= 0.5 else "PASS",
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Intelli-CI failure predictor")
    for col in FEATURE_COLUMNS:
        ap.add_argument(f"--{col}", type=float, default=0)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    args = vars(ap.parse_args())
    model_path = args.pop("model")

    result = predict(args, model_path)
    print(json.dumps(result, indent=2))
