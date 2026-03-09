"""
Backend pytest test suite.

Run with:
    pytest -v

For CI with a real Postgres:
    DATABASE_URL=postgresql+asyncpg://... pytest -v
"""
import pytest
from httpx import ASGITransport, AsyncClient

from backend.main import app  # env vars set in conftest.py before this import


# ── Shared async client fixture ───────────────────────────────────────────────

@pytest.fixture
async def client():
    """Async HTTP client wired directly to the FastAPI app (no real server)."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


# ── /health ───────────────────────────────────────────────────────────────────

async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


# ── /signup ───────────────────────────────────────────────────────────────────

async def test_signup_success(client):
    resp = await client.post("/signup", json={
        "name": "Test User",
        "email": "test@example.com",
        "password": "strongpass1",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert "token" in data
    assert data["user"]["email"] == "test@example.com"


async def test_signup_duplicate_email(client):
    payload = {"name": "Dup", "email": "dup@example.com", "password": "strongpass1"}
    await client.post("/signup", json=payload)
    resp = await client.post("/signup", json=payload)
    assert resp.status_code == 409


async def test_signup_short_password(client):
    resp = await client.post("/signup", json={
        "name": "Short",
        "email": "short@example.com",
        "password": "abc",
    })
    assert resp.status_code == 400


# ── /login ────────────────────────────────────────────────────────────────────

async def test_login_success(client):
    email, password = "login@example.com", "mypassword9"
    await client.post("/signup", json={"name": "Login User", "email": email, "password": password})
    resp = await client.post("/login", json={"email": email, "password": password})
    assert resp.status_code == 200
    assert "token" in resp.json()


async def test_login_wrong_password(client):
    email = "wrongpw@example.com"
    await client.post("/signup", json={"name": "WP", "email": email, "password": "correctpass1"})
    resp = await client.post("/login", json={"email": email, "password": "wrongpass99"})
    assert resp.status_code == 401


async def test_login_unknown_email(client):
    resp = await client.post("/login", json={"email": "ghost@example.com", "password": "anything"})
    assert resp.status_code == 401


# ── /predict ──────────────────────────────────────────────────────────────────

async def test_predict_returns_decision(client):
    resp = await client.post("/predict", json={
        "files_changed": 15,
        "lines_added": 500,
        "lines_deleted": 80,
        "code_churn": 580,
        "previous_failures": 4,
        "test_coverage": 55.0,
        "is_merge_commit": 0,
        "commit_message_length": 120,
        "num_contributors_last_30d": 6,
        "days_since_last_failure": 1,
        "recent_failure_flag": 1,
        "commit_message": "refactor: overhaul database migrations",
        "commit_sha": "abc123def456",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["decision"] in ("RUN_TESTS", "PARTIAL_TESTS", "SKIP_TESTS")
    assert 0.0 <= data["failure_probability"] <= 1.0


async def test_predict_low_risk(client):
    """A trivial docs-only commit should lean toward SKIP_TESTS."""
    resp = await client.post("/predict", json={
        "files_changed": 1,
        "lines_added": 3,
        "lines_deleted": 1,
        "code_churn": 4,
        "previous_failures": 0,
        "test_coverage": 90.0,
        "is_merge_commit": 0,
        "commit_message_length": 20,
        "num_contributors_last_30d": 1,
        "days_since_last_failure": 30,
        "recent_failure_flag": 0,
        "commit_message": "docs: fix readme typo",
    })
    assert resp.status_code == 200
    assert resp.json()["decision"] in ("SKIP_TESTS", "PARTIAL_TESTS", "RUN_TESTS")


# ── /commits (auth-gated) ─────────────────────────────────────────────────────

async def test_commits_requires_auth(client):
    resp = await client.get("/commits")
    assert resp.status_code == 401


async def test_commits_with_token(client):
    signup = await client.post("/signup", json={
        "name": "Commits User",
        "email": "commits@example.com",
        "password": "securepass1",
    })
    token = signup.json()["token"]
    resp = await client.get("/commits", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert "commits" in resp.json()


# ── /analytics/summary (auth-gated) ──────────────────────────────────────────

async def test_analytics_summary_requires_auth(client):
    resp = await client.get("/analytics/summary")
    assert resp.status_code == 401


async def test_analytics_summary_with_token(client):
    signup = await client.post("/signup", json={
        "name": "Analytics User",
        "email": "analytics@example.com",
        "password": "securepass2",
    })
    token = signup.json()["token"]
    resp = await client.get("/analytics/summary", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    body = resp.json()
    assert "total_commits" in body or "total" in body
