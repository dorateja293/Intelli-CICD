# Intelli-CICD

Intelli-CICD is a Flask-based CI decision service that predicts failure probability for a commit and decides whether to run the full pytest suite or skip it.

## Current Architecture

The project has four main parts:

- `app.py`: local prediction API backed by the trained model in `model/intelli_ci_model.pkl`
- `github_ci_runner.py`: GitHub and PostgreSQL integration script for collecting commit metadata and storing decisions
- `.github/workflows/intelli-ci.yml`: GitHub Actions workflow that validates the checked-out code and uses the local app for CI decisions
- `schema.sql`: PostgreSQL bootstrap schema for `commit_history`

## Prediction Contract

`POST /predict` expects these 11 numeric features:

- `files_changed`
- `lines_added`
- `lines_deleted`
- `code_churn`
- `commit_hour`
- `commit_day`
- `historical_failure_rate`
- `is_weekend`
- `large_commit_flag`
- `recent_failure_flag`
- `execution_time`

The API returns:

```json
{
  "failure_probability": 0.23,
  "decision": "SKIP_TESTS"
}
```

The current decision threshold in code is `0.4`. If `failure_probability > 0.4`, the API returns `RUN_FULL_TESTS`; otherwise it returns `SKIP_TESTS`.

## Local Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Start the API:

```bash
python app.py
```

4. Optionally run the smoke test script:

```bash
python test_api.py
```

By default, `test_api.py` uses `http://127.0.0.1:5000/predict`. Override it with `PREDICT_API_URL` when needed.

## Environment Variables

`github_ci_runner.py` requires:

- `GITHUB_TOKEN`
- `REPO_NAME`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `DB_HOST`
- `DB_PORT`

Optional:

- `PREDICT_API_URL`: defaults to `https://intelli-cicd.onrender.com/predict` in the runner

## Database Setup

Create the PostgreSQL table before running `github_ci_runner.py`:

```bash
psql -f schema.sql
```

The schema stores one row per commit SHA and updates the row if the same commit is processed again.

## CI Workflow

The GitHub Actions workflow now:

- installs project dependencies
- compiles the Python files
- extracts commit-level file and churn metrics
- calls the local Flask app via its test client
- runs `pytest` only when the prediction says `RUN_FULL_TESTS`

## Deployment

`Procfile` is configured for Gunicorn:

```bash
web: gunicorn app:app
```

## Known Gap

The model file was serialized with `scikit-learn 1.6.1`. If your local environment uses a different sklearn version, you may see compatibility warnings until the environment is rebuilt with `requirements.txt`.
