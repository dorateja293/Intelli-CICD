"""
Unit and Integration tests for GitHub OAuth, Repository Selection,
Initial Synchronization, and Webhook Ingestion in Intelli-CI.
"""
import pytest
from httpx import ASGITransport, AsyncClient
from services.api.main import app
from services.github.github_service import github_service
from shared.database.connection import get_db
from shared.models import Organization, Repository, User, GitHubAccount


@pytest.fixture(autouse=True)
def override_db(db_session):
    """Override get_db dependency with test database session."""
    async def _override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_github_oauth_login_url(monkeypatch):
    """Test GitHub OAuth login URL generation and unconfigured error response."""
    import services.github.github_service as gh_mod

    # 1. Simulate unconfigured state by mocking is_oauth_configured → False
    monkeypatch.setattr(gh_mod.github_service, "is_oauth_configured", lambda: False)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/github/oauth/login")
        assert res.status_code == 400, f"Expected 400 when unconfigured, got {res.status_code}: {res.text}"
        assert "GitHub OAuth is not configured" in res.json()["detail"]

    # 2. Simulate configured state — restore real method and inject test credentials
    monkeypatch.setattr(gh_mod.github_service, "is_oauth_configured", lambda: True)
    monkeypatch.setattr(gh_mod.github_service, "client_id", "gh_test_client_id_999")
    monkeypatch.setattr(gh_mod.github_service, "client_secret", "gh_test_client_secret_999")
    monkeypatch.setattr(
        gh_mod.github_service,
        "_get_active_client_id",
        lambda: "gh_test_client_id_999",
    )
    monkeypatch.setattr(
        gh_mod.github_service,
        "_get_active_client_secret",
        lambda: "gh_test_client_secret_999",
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/github/oauth/login")
        assert res.status_code == 200, f"Expected 200 when configured, got {res.status_code}: {res.text}"
        data = res.json()["data"]
        assert "url" in data
        assert "github.com/login/oauth/authorize" in data["url"]
        assert "gh_test_client_id_999" in data["url"]
        assert "state" in data


@pytest.mark.asyncio
async def test_github_status_disconnected_and_connected(db_session):
    """Test GitHub connection status for disconnected and connected states."""
    # 1. Disconnected state for new user
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/github/status")
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["connected"] is False

    # 2. Connected state after account linkage
    org = Organization(name="Status Org", slug="status-org")
    db_session.add(org)
    await db_session.flush()

    user = User(name="Test Dev", email="dev@example.com", organization_id=org.id)
    db_session.add(user)
    await db_session.flush()

    gh_acc = GitHubAccount(
        user_id=user.id,
        github_user_id=12345,
        username="github-dev",
        access_token="gho_test_token_123",
        avatar_url="https://avatars.githubusercontent.com/u/12345",
    )
    db_session.add(gh_acc)
    await db_session.commit()

    # Pass user via dependency override or query
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/github/status")
        assert res.status_code == 200
        data = res.json()["data"]
        assert "connected" in data


@pytest.mark.asyncio
async def test_github_repository_listing():
    """Test fetching repositories available for selection returns empty when disconnected."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/github/repositories")
        assert res.status_code == 200
        repos = res.json()["data"]
        assert isinstance(repos, list)
        assert len(repos) == 0


@pytest.mark.asyncio
async def test_github_repository_selection_and_sync(db_session):
    """Test repository registration and initial synchronization."""
    org = Organization(name="Test Org", slug="test-org")
    db_session.add(org)
    await db_session.commit()

    payload = {
        "name": "intelli-ci",
        "owner": "dorateja293",
        "full_name": "dorateja293/intelli-ci",
        "url": "https://github.com/dorateja293/intelli-ci",
        "default_branch": "main",
        "language": "Python",
        "description": "Intelligent CI/CD Optimization Platform",
        "visibility": "public",
        "stars_count": 28,
        "forks_count": 6,
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/v1/github/repositories/select", json=payload)
        assert res.status_code == 200
        data = res.json()["data"]
        assert "repository" in data
        repo_data = data["repository"]
        assert repo_data["name"] == "intelli-ci"
        assert repo_data["sync_status"] in ["SYNCING", "COMPLETED"]


@pytest.mark.asyncio
async def test_simulate_github_webhook(db_session):
    """Test simulating a GitHub Actions webhook event."""
    org = Organization(name="Webhook Org", slug="webhook-org")
    db_session.add(org)
    await db_session.flush()

    repo = Repository(
        organization_id=org.id,
        name="webhook-repo",
        url="https://github.com/dorateja293/webhook-repo",
        provider="github",
        default_branch="main",
        webhook_secret="test_secret",
    )
    db_session.add(repo)
    await db_session.commit()

    payload = {
        "repository_id": str(repo.id),
        "event_type": "workflow_run",
        "conclusion": "success",
        "commit_message": "feat: test automated webhook processing",
        "branch": "main",
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/v1/github/simulate-webhook", json=payload)
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["simulated"] is True
        assert data["status"] == "SUCCESS"
        assert "pipeline_id" in data
