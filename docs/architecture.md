# Intelli-CI Architecture

## Overview

Intelli-CI is an AI-powered DevOps platform that predicts CI pipeline failures before they run,
saving compute time and developer feedback cycles. It combines a trained ML model with LLM-based
commit analysis to decide whether to **run all tests**, **run targeted tests**, or **skip tests entirely**.

---

## System Workflow

```
GitHub Push Event
       │
       ▼
┌──────────────────┐
│  POST /webhook   │  HMAC-SHA256 signature verified
│  (FastAPI)       │
└────────┬─────────┘
         │  extract commit metadata
         ▼
┌──────────────────────────────────────────────────────────┐
│                   Decision Pipeline                       │
│                                                          │
│  ┌─────────────────┐        ┌──────────────────────┐    │
│  │   ML Service    │        │    LLM Service        │    │
│  │ RandomForest    │        │  OpenAI / Ollama /    │    │
│  │ failure_prob    │        │  rule-based fallback  │    │
│  └────────┬────────┘        └──────────┬───────────┘    │
│           │  (prob, conf)              │  (risk, modules)│
│           └──────────────┬─────────────┘                │
│                          ▼                               │
│               ┌─────────────────┐                        │
│               │ Decision Engine │                        │
│               │  fused_score =  │                        │
│               │  0.6*ML+0.4*LLM │                        │
│               └────────┬────────┘                       │
└────────────────────────┼────────────────────────────────┘
                         ▼
              ┌──────────────────┐
              │    Decision      │
              │  RUN_TESTS       │  fused ≥ 0.55
              │  PARTIAL_TESTS   │  0.30 ≤ fused < 0.55
              │  SKIP_TESTS      │  fused < 0.30
              └──────────────────┘
                         │
                         ▼
              Stored in PostgreSQL
              Surfaced via React Dashboard
```

---

## Directory Structure

```
intelli-ci/
│
├── backend/                  # FastAPI application
│   ├── core/
│   │   ├── config.py         # Pydantic Settings (reads .env)
│   │   └── security.py       # JWT + HMAC webhook verification
│   ├── database/
│   │   └── connection.py     # SQLAlchemy async engine + session
│   ├── models/               # ORM models (mapped to PostgreSQL tables)
│   │   ├── user.py
│   │   ├── repository.py
│   │   ├── commit.py
│   │   ├── pipeline_run.py
│   │   └── prediction.py
│   ├── services/
│   │   ├── ml_service.py     # Loads joblib model; predict_failure_probability()
│   │   ├── llm_service.py    # OpenAI / Ollama / rule-based analyze_commit()
│   │   └── decision_engine.py# Fuses ML + LLM → RUN/PARTIAL/SKIP
│   ├── api/routes/
│   │   ├── auth.py           # POST /signup  POST /login
│   │   ├── predict.py        # POST /predict  GET /commits
│   │   ├── webhook.py        # POST /webhook/github
│   │   └── analytics.py      # GET /analytics/summary|timeline  GET /repositories
│   ├── main.py               # FastAPI app, CORS, lifespan, routers
│   ├── requirements.txt
│   └── .env.example
│
├── ml-engine/                # Offline training pipeline
│   ├── dataset/
│   │   └── generate_dataset.py  # Synthetic 5 000-row CSV
│   ├── training/
│   │   └── train.py             # RandomForestClassifier(n=300)
│   ├── predictor/
│   │   └── predict.py           # CLI + importable predict()
│   └── requirements.txt
│
├── llm-engine/               # Commit analysis helpers
│   ├── commit_analysis/
│   │   └── analyzer.py      # OpenAI / Ollama / rule-based async analyzer
│   └── risk_classifier/
│       └── classifier.py    # Maps risk + ML prob → test strategy
│
├── devops/
│   ├── docker/
│   │   ├── backend.Dockerfile
│   │   └── frontend.Dockerfile
│   ├── nginx/
│   │   └── nginx.conf        # SPA fallback, /api/ proxy
│   └── docker-compose.yml    # postgres + redis + backend + frontend
│
├── frontend/                 # Vite + React + Tailwind
│   ├── src/services/api.js   # Axios client → http://localhost:8000
│   └── .env.local            # VITE_API_URL=http://localhost:8000
│
├── .github/workflows/
│   └── ci.yml                # backend tests, ML train, frontend build, Docker smoke
│
└── docs/
    └── architecture.md       # (this file)
```

---

## Component Details

### Backend (FastAPI)

| File | Responsibility |
|------|----------------|
| `core/config.py` | Single `Settings` object; all env vars with typed defaults |
| `core/security.py` | `create_access_token`, `decode_access_token`, `verify_github_signature` |
| `database/connection.py` | `AsyncEngine`, `AsyncSession`, `get_db()` dependency |
| `models/` | 5 SQLAlchemy mapped classes auto-created on startup |
| `services/ml_service.py` | `predict_failure_probability(features) → (prob, confidence)` |
| `services/llm_service.py` | `analyze_commit(...) → LLMResult` — never crashes pipeline |
| `services/decision_engine.py` | `make_decision(prob, conf, llm) → DecisionResult` with score fusion |
| `api/routes/auth.py` | Stateless JWT signup/login |
| `api/routes/predict.py` | Core prediction endpoint; optionally persists to DB |
| `api/routes/webhook.py` | Idempotent push-event processor |
| `api/routes/analytics.py` | Aggregation queries for the dashboard |

### ML Engine

The ML engine is an **offline** training pipeline. The trained model artifact is mounted into the
backend container at runtime.

**Features (11 total)**

| Feature | Description |
|---------|-------------|
| `files_changed` | Number of files in the commit |
| `lines_added` | Total lines added |
| `lines_deleted` | Total lines removed |
| `code_churn` | lines_added + lines_deleted |
| `previous_failures` | Recent failure count for the repo |
| `test_coverage` | Repo test coverage % (0–100) |
| `is_merge_commit` | 0 or 1 |
| `commit_message_length` | Character count of message |
| `num_contributors_last_30d` | Active contributors window |
| `days_since_last_failure` | Staleness of last failure |
| `recent_failure_flag` | 1 if failure in last 7 days |

**Model:** `RandomForestClassifier(n_estimators=300, class_weight="balanced")`

### LLM Engine

Three providers selected via `LLM_PROVIDER` env var:

| Provider | Config |
|----------|--------|
| `openai` | `OPENAI_API_KEY` + `OPENAI_MODEL` (default `gpt-4o-mini`) |
| `ollama` | `OLLAMA_BASE_URL` (default `http://localhost:11434`) + `OLLAMA_MODEL` |
| `none` | Regex rule-based fallback — zero external dependencies |

The rule-based fallback tags commits mentioning `database`, `migration`, `auth`, `security`,
`payment`, `deploy`, `infrastructure` as **high risk**; `readme`, `docs`, `comment`, `typo` as
**low risk**; everything else as **medium risk**.

### Decision Engine

```
fused_score = 0.60 × ML_failure_probability + 0.40 × LLM_risk_score

LLM_risk_score mapping:
  high   → 0.85
  medium → 0.50
  low    → 0.15

Decision thresholds (configurable via env):
  fused_score ≥ DECISION_THRESHOLD_RUN     (0.55) → RUN_TESTS
  fused_score ≥ DECISION_THRESHOLD_PARTIAL (0.30) → PARTIAL_TESTS  (with targeted paths)
  fused_score <  DECISION_THRESHOLD_PARTIAL       → SKIP_TESTS
```

---

## API Reference

### Auth

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/signup` | None | Create account, returns JWT |
| POST | `/login` | None | Verify credentials, returns JWT |

### Prediction

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/predict` | Optional | Run ML+LLM+decision for a commit |
| GET | `/commits` | Required | Paginated commit+prediction history |

### Webhooks

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/webhook/github` | HMAC-SHA256 | GitHub push event handler |

### Analytics

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/analytics/summary` | Required | Aggregate counts + time saved |
| GET | `/analytics/timeline` | Required | Daily commit counts (last N days) |
| GET | `/repositories` | Required | User's linked repositories |

### System

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/health` | None | Liveness check |

---

## Local Development Quickstart

### Option A — Docker Compose (recommended)

```bash
# 1. Copy and fill env files
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local

# 2. Train the ML model first
cd ml-engine
pip install -r requirements.txt
python dataset/generate_dataset.py --out dataset/data.csv
python training/train.py --data dataset/data.csv --out models/model.pkl
cd ..

# 3. Start all services
cd devops
docker compose up --build
# → frontend: http://localhost
# → backend:  http://localhost:8000
# → API docs: http://localhost:8000/docs
```

### Option B — Individual processes

```bash
# Terminal 1 – PostgreSQL + Redis (via Docker)
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=intellici postgres:16-alpine
docker run -d -p 6379:6379 redis:7-alpine

# Terminal 2 – Backend
cd backend
pip install -r requirements.txt
cp .env.example .env   # edit values
uvicorn main:app --reload --port 8000

# Terminal 3 – Frontend
cd frontend
npm install
cp .env.example .env.local
npx vite --port 3000
```

### Train and smoke-test the ML model

```bash
cd ml-engine
python dataset/generate_dataset.py --samples 5000 --out dataset/data.csv
python training/train.py --data dataset/data.csv --out models/model.pkl
python predictor/predict.py --files_changed 12 --lines_added 400 --lines_deleted 50 \
  --code_churn 450 --previous_failures 3 --test_coverage 60 \
  --is_merge_commit 0 --commit_message_length 80 \
  --num_contributors_last_30d 5 --days_since_last_failure 2 --recent_failure_flag 1 \
  --model models/model.pkl
```

---

## GitHub Webhook Setup

1. In your GitHub repo → **Settings → Webhooks → Add webhook**
2. Payload URL: `https://your-domain.com/webhook/github`
3. Content type: `application/json`
4. Secret: value of `GITHUB_WEBHOOK_SECRET` in your backend `.env`
5. Events: **Just the push event**

---

## CI/CD Pipeline (`.github/workflows/ci.yml`)

| Job | Trigger | What it does |
|-----|---------|--------------|
| `backend` | All pushes/PRs | pytest against real Postgres service container |
| `ml-engine` | All pushes/PRs | Generate dataset → train → smoke predict → upload artifact |
| `frontend` | All pushes/PRs | `npm ci` → `npm run build` |
| `docker` | Push to `main` only | `docker compose up --build -d` smoke test |
