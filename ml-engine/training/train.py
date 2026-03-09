"""
Train the Intelli-CI RandomForestClassifier.

Usage:
  python -m ml-engine.training.train
  python -m ml-engine.training.train --data ml-engine/dataset/commits.csv --out ml-engine/models/model.pkl
"""
import argparse
import os
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    precision_recall_fscore_support,
)
from sklearn.model_selection import train_test_split

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
TARGET = "failed"

DEFAULT_DATA = "ml-engine/dataset/commits.csv"
DEFAULT_MODEL = "ml-engine/models/model.pkl"


def train(data_path: str = DEFAULT_DATA, model_path: str = DEFAULT_MODEL) -> None:
    df = pd.read_csv(data_path)
    print(f"Loaded {len(df)} rows from {data_path}")

    # Fill missing feature columns with sensible defaults
    defaults = {
        "lines_added": 0, "lines_deleted": 0, "code_churn": 0,
        "previous_failures": 0, "test_coverage": 0.0, "is_merge_commit": 0,
        "commit_message_length": 0, "num_contributors_last_30d": 1,
        "days_since_last_failure": 30, "recent_failure_flag": 0,
    }
    for col, val in defaults.items():
        if col not in df.columns:
            df[col] = val

    missing = [c for c in FEATURE_COLUMNS + [TARGET] if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    X, y = df[FEATURE_COLUMNS], df[TARGET]
    class_counts = y.value_counts()
    print("Class distribution:\n", class_counts.to_string())

    if class_counts.min() < 2 or len(df) < 20:
        X_train, X_test, y_train, y_test = X, y, X, y
        print("Dataset too small — training/evaluating on full set.")
    else:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

    model = RandomForestClassifier(
        n_estimators=300,
        max_depth=None,
        min_samples_split=10,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_test, preds, average="binary", zero_division=0
    )
    accuracy = accuracy_score(y_test, preds)

    print("\n── Evaluation ──────────────────────────────")
    print(f"  Accuracy : {accuracy:.4f}")
    print(f"  Precision: {precision:.4f}")
    print(f"  Recall   : {recall:.4f}")
    print(f"  F1 Score : {f1:.4f}")
    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, preds))
    print("\nClassification Report:")
    print(classification_report(y_test, preds, zero_division=0))

    importances = sorted(
        zip(FEATURE_COLUMNS, model.feature_importances_),
        key=lambda x: x[1],
        reverse=True,
    )
    print("\n── Feature Importances ─────────────────────")
    for feat, imp in importances:
        print(f"  {feat:<35} {imp:.4f}")

    # Atomic save
    out = Path(model_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = str(out) + ".tmp"
    joblib.dump(model, tmp)
    os.replace(tmp, out)
    print(f"\n✓ Model saved → {out}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=DEFAULT_DATA)
    ap.add_argument("--out", default=DEFAULT_MODEL)
    args = ap.parse_args()
    train(args.data, args.out)
