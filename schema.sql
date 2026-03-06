CREATE TABLE IF NOT EXISTS commit_history (
    id BIGSERIAL PRIMARY KEY,
    commit_sha TEXT NOT NULL,
    files_changed INTEGER NOT NULL,
    code_churn INTEGER NOT NULL,
    historical_failure_rate DOUBLE PRECISION NOT NULL,
    failure_probability DOUBLE PRECISION NOT NULL,
    decision TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_commit_history_created_at
    ON commit_history (created_at DESC);

CREATE UNIQUE INDEX IF NOT EXISTS idx_commit_history_commit_sha
    ON commit_history (commit_sha);
