"""
Unit tests for core API endpoints in Intelli-CI.
Validates authentication, health, ML predictions, AI log analysis, recommendations, and analytics.
"""
import pytest
from httpx import ASGITransport, AsyncClient
from services.api.main import app
from shared.database.connection import get_db
from shared.models import Organization, Repository, Pipeline


@pytest.fixture(autouse=True)
def override_db(db_session):
    """Override get_db dependency with test database session."""
    async def _override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_health_endpoint():
    """Test health status check returns healthy."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "services" in data
        assert data["services"]["api"] == "online"


@pytest.mark.asyncio
async def test_predict_endpoint():
    """Test RandomForest ML commit risk prediction endpoint."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {
            "files_changed": 3,
            "lines_added": 40,
            "lines_deleted": 10,
            "previous_failures": 0,
            "test_coverage": 85.0,
            "is_merge_commit": 0,
            "commit_message_length": 30,
            "num_contributors_last_30d": 2,
            "days_since_last_failure": 30,
        }
        response = await ac.post("/api/v1/predict", json=payload)
        assert response.status_code == 200
        data = response.json()["data"]
        assert "failure_probability" in data
        assert "risk_level" in data
        assert "decision" in data
        assert data["decision"] in ["RUN_TESTS", "PARTIAL_TESTS", "SKIP_TESTS"]
        assert "estimated_duration_seconds" in data
        assert "key_risk_drivers" in data


@pytest.mark.asyncio
async def test_ml_status_and_insights():
    """Test ML status and insights diagnostic endpoints."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res_status = await ac.get("/api/v1/ml/status")
        assert res_status.status_code == 200
        status_data = res_status.json()["data"]
        assert "status" in status_data
        assert "model_type" in status_data
        assert "features_count" in status_data
        assert status_data["features_count"] == 11

        res_insights = await ac.get("/api/v1/ml/insights")
        assert res_insights.status_code == 200
        insights_data = res_insights.json()["data"]
        assert "anomalies_detected" in insights_data


@pytest.mark.asyncio
async def test_analyze_logs_endpoint():
    """Test AI log parsing and error classification."""
    sample_log = """
    npm ERR! code ERESOLVE
    npm ERR! ERESOLVE could not resolve
    npm ERR! Conflicting peer dependency: react@18.2.0
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/analyze-logs", json={"logs": sample_log})
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["error_detected"] is True
        assert data["category"] == "dependencies"
        assert len(data["matches"]) > 0
        assert "npm" in data["recommended_fix"].lower()


@pytest.mark.asyncio
async def test_recommendations_endpoint(db_session):
    """Test optimization recommendations endpoint with empty and populated repository states."""
    # 1. Unregistered repository returns clean empty recommendations
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/recommendations")
        assert response.status_code == 200
        assert response.json()["data"] == []

    # 2. Registered repository with runs produces data-driven recommendations
    org = Organization(name="Rec Org", slug="rec-org")
    db_session.add(org)
    await db_session.flush()

    repo = Repository(
        organization_id=org.id,
        name="rec-repo",
        url="https://github.com/dorateja293/rec-repo",
        provider="github",
        default_branch="main",
    )
    db_session.add(repo)
    await db_session.flush()

    pipeline = Pipeline(
        repo_id=repo.id,
        trigger_type="push",
        commit_sha="c1234567890",
        branch="main",
        status="FAILED",
    )
    db_session.add(pipeline)
    await db_session.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get(f"/api/v1/recommendations?repository_id={repo.id}")
        assert response.status_code == 200
        data = response.json()["data"]
        assert isinstance(data, list)
        assert len(data) > 0
        assert "title" in data[0]
        assert "impact" in data[0]


@pytest.mark.asyncio
async def test_analytics_endpoints():
    """Test analytics duration, stage, failure, and trend endpoints."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        dur_res = await ac.get("/api/v1/analytics/durations")
        assert dur_res.status_code == 200
        assert "p50" in dur_res.json()["data"]

        stage_res = await ac.get("/api/v1/analytics/stages")
        assert stage_res.status_code == 200
        assert isinstance(stage_res.json()["data"], list)

        fail_res = await ac.get("/api/v1/analytics/failures")
        assert fail_res.status_code == 200
        assert "total_failures" in fail_res.json()["data"]

        trend_res = await ac.get("/api/v1/analytics/trends")
        assert trend_res.status_code == 200
        assert isinstance(trend_res.json()["data"], list)
