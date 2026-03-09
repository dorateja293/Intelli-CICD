# Intelli-CI/CD

> AI-powered CI/CD optimization platform — predict build failures before they happen, understand why commits break pipelines, and make smarter decisions about what to run.

[![Python](https://img.shields.io/badge/Python-3.12-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.11x-009688)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61DAFB)](https://react.dev)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-4-38BDF8)](https://tailwindcss.com)

---

## Features

| Feature | Description |
|---|---|
| **AI Failure Prediction** | ML model + LLM fusion predicts CI failure probability for every commit |
| **Log Analyzer** | Paste raw CI logs and get a structured root-cause explanation |
| **Analytics Dashboard** | Track failure rates, time saved, decision history and commit timelines |
| **Commit Analysis** | Per-commit risk scoring with churn, coverage and contributor signals |
| **GitHub Webhook** | Real-time ingestion of push events to auto-score incoming commits |
| **User Auth** | JWT-based registration / login with bcrypt password hashing |

---

## Tech Stack

### Backend
- **FastAPI** — async REST API
- **PostgreSQL + asyncpg** — primary database
- **SQLAlchemy 2 (async)** — ORM
- **Redis** — caching layer
- **JWT / bcrypt** — authentication & password security
- **scikit-learn** — RandomForest failure prediction model
- **Ollama / OpenAI** — LLM risk classification

### Frontend
- **React 19** with Vite
- **TailwindCSS v4** — utility-first styling
- **Recharts** — analytics charts
- **Lucide React** — icons
- **React Router v6** — client-side routing

---

## Project Structure

```
intelli-ci/
├── backend/                  # FastAPI application
│   ├── ai/                   # Log analysis AI module
│   ├── api/routes/           # REST endpoint handlers
│   │   ├── analytics.py
│   │   ├── auth.py
│   │   ├── logs.py
│   │   ├── predict.py
│   │   ├── profile.py
│   │   ├── system.py
│   │   └── webhook.py
│   ├── core/                 # Config, security helpers
│   ├── database/             # DB connection & session
│   ├── models/               # SQLAlchemy ORM models
│   ├── services/             # Business logic (ML, LLM, decision engine)
│   ├── tests/                # pytest test suite
│   ├── main.py               # FastAPI app entry point
│   ├── requirements.txt
│   └── .env.example          # Environment variable template
│
├── frontend/                 # React + Vite SPA
│   ├── public/
│   ├── src/
│   │   ├── components/       # Reusable UI components
│   │   ├── context/          # Auth & Sidebar React contexts
│   │   ├── layouts/          # DashboardLayout, AuthLayout
│   │   ├── pages/            # Full page components
│   │   └── services/         # Axios API client (api.js)
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
│
├── ml-engine/                # Training pipeline & predictor
│   ├── dataset/              # Training data (CSV)
│   ├── predictor/predict.py  # Inference helper
│   └── training/train.py     # Model training script
│
├── llm-engine/               # LLM commit analysis modules
│   ├── commit_analysis/
│   └── risk_classifier/
│
├── devops/                   # Docker & Nginx configs
│   ├── docker/
│   │   ├── backend.Dockerfile
│   │   └── frontend.Dockerfile
│   ├── nginx/nginx.conf
│   └── docker-compose.yml
│
├── docs/
│   └── architecture.md
│
├── .github/workflows/ci.yml  # GitHub Actions CI pipeline
├── pytest.ini
└── README.md
```

---

## Getting Started

### Prerequisites

- Python 3.12+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+
- *(Optional)* Ollama for local LLM inference

---

### 1. Clone the repository

```bash
git clone https://github.com/dorateja293/Intelli-CICD.git
cd Intelli-CICD
```

---

### 2. Backend setup

```bash
# Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux

# Install dependencies
pip install -r backend/requirements.txt

# Configure environment
cp backend/.env.example backend/.env
# Edit backend/.env with your database URL, secret key, etc.
```

#### Environment variables (`backend/.env`)

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string (`postgresql+asyncpg://...`) |
| `REDIS_URL` | Redis connection string (`redis://localhost:6379/0`) |
| `SECRET_KEY` | 32-char hex secret — generate with `python -c "import secrets; print(secrets.token_hex(32))"` |
| `ALGORITHM` | JWT algorithm (default: `HS256`) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime in minutes (default: `1440`) |
| `GITHUB_TOKEN` | GitHub personal access token for webhook validation |
| `GITHUB_WEBHOOK_SECRET` | Shared secret registered on GitHub webhook settings |
| `LLM_PROVIDER` | `openai` \| `ollama` \| `none` |
| `OPENAI_API_KEY` | OpenAI API key (only if `LLM_PROVIDER=openai`) |
| `OLLAMA_BASE_URL` | Ollama base URL (default: `http://localhost:11434`) |
| `OLLAMA_MODEL` | Ollama model name (default: `llama3.2`) |
| `ML_MODEL_PATH` | Path to trained `.pkl` model file |
| `DECISION_THRESHOLD_RUN` | Score above which CI always runs (default: `0.55`) |
| `DECISION_THRESHOLD_PARTIAL` | Score above which partial CI runs (default: `0.30`) |

#### Start the backend

```bash
python -m uvicorn backend.main:app --reload --port 8000
```

API docs available at: http://localhost:8000/docs

---

### 3. Train the ML model *(optional — skip if you have a pre-trained model)*

```bash
python ml-engine/training/train.py
# Outputs: ml-engine/models/model.pkl
```

---

### 4. Frontend setup

```bash
cd frontend
npm install

# Configure environment (create frontend/.env)
echo "VITE_API_URL=http://localhost:8000" > .env
```

#### Start the frontend dev server

```bash
npm run dev
# Runs on http://localhost:3000
```

#### Build for production

```bash
npm run build
# Output: frontend/dist/
```

---

## Running with Docker

```bash
# From the devops/ directory
cd devops
docker compose up --build
```

Services:
- Frontend: http://localhost:80
- Backend API: http://localhost:8000
- PostgreSQL: port 5432
- Redis: port 6379

---

## Running Tests

```bash
# Backend tests
pytest backend/tests/ -v

# Run with coverage
pytest backend/tests/ --cov=backend --cov-report=term-missing
```

---

## How the AI Prediction Works

Every commit is scored using a two-model fusion:

1. **ML model** — `RandomForestClassifier` trained on CI run history.  
   Input features: files changed, lines added/deleted, code churn, test coverage, commit message length, previous failures, contributor count, days since last failure, merge commit flag, recent failure flag.  
   Output: `failure_probability` (0.0 – 1.0)

2. **LLM analysis** — commit message + changed file list are sent to Ollama/OpenAI.  
   Output: `risk_level` (LOW / MEDIUM / HIGH → mapped to 0.1 / 0.5 / 0.9)

3. **Fusion formula:**
   ```
   final_score = (0.60 × ML_score) + (0.40 × LLM_score)
   ```

4. **Decision engine:**
   - `final_score > 0.55` → **RUN** full CI
   - `0.30 < final_score ≤ 0.55` → **PARTIAL** CI (fast checks only)
   - `final_score ≤ 0.30` → **SKIP** CI

---

## API Overview

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/auth/register` | Create a new user account |
| `POST` | `/api/auth/login` | Obtain a JWT access token |
| `GET` | `/api/analytics/summary` | Dashboard KPI summary |
| `GET` | `/api/analytics/timeline` | Commit failure timeline |
| `POST` | `/api/predict` | Score a commit (ML + LLM fusion) |
| `POST` | `/api/logs/analyze` | Analyze raw CI log output |
| `GET` | `/api/repositories` | List tracked repositories |
| `POST` | `/api/webhook/github` | GitHub push event webhook |
| `GET` | `/api/system/health` | Health check |

Full interactive docs: http://localhost:8000/docs

---

## License

MIT
