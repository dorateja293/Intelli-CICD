"""
Generate a synthetic training dataset for the Intelli-CI RandomForest model.

Columns produced:
  files_changed, lines_added, lines_deleted, code_churn,
  previous_failures, test_coverage, is_merge_commit,
  commit_message_length, num_contributors_last_30d,
  days_since_last_failure, recent_failure_flag,
  failed  (target: 1=failure, 0=pass)
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
rng = np.random.default_rng(SEED)


def generate(n_samples: int = 5000) -> pd.DataFrame:
    files_changed = rng.integers(1, 40, n_samples)
    lines_added = rng.integers(0, 800, n_samples)
    lines_deleted = rng.integers(0, 400, n_samples)
    code_churn = lines_added + lines_deleted
    previous_failures = rng.integers(0, 10, n_samples)
    test_coverage = rng.uniform(20, 100, n_samples)
    is_merge_commit = rng.integers(0, 2, n_samples)
    commit_message_length = rng.integers(10, 200, n_samples)
    num_contributors = rng.integers(1, 20, n_samples)
    days_since_failure = rng.integers(0, 90, n_samples)
    recent_failure_flag = (days_since_failure < 7).astype(int)

    # Probabilistic label — realistic signal
    failure_score = (
        0.04 * files_changed
        + 0.002 * code_churn
        + 0.08 * previous_failures
        - 0.005 * test_coverage
        + 0.10 * recent_failure_flag
        - 0.003 * days_since_failure
        + rng.normal(0, 0.3, n_samples)
    )
    failed = (failure_score > 0.5).astype(int)

    return pd.DataFrame(
        {
            "files_changed": files_changed,
            "lines_added": lines_added,
            "lines_deleted": lines_deleted,
            "code_churn": code_churn,
            "previous_failures": previous_failures,
            "test_coverage": test_coverage.round(2),
            "is_merge_commit": is_merge_commit,
            "commit_message_length": commit_message_length,
            "num_contributors_last_30d": num_contributors,
            "days_since_last_failure": days_since_failure,
            "recent_failure_flag": recent_failure_flag,
            "failed": failed,
        }
    )


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--samples", type=int, default=5000)
    ap.add_argument("--out", default="ml-engine/dataset/commits.csv")
    args = ap.parse_args()

    df = generate(args.samples)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    print(f"Generated {len(df)} rows → {out}")
    print(df["failed"].value_counts().to_string())
