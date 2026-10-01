"""
GitHub Service Layer for Intelli-CI.
Handles OAuth2 token exchange, live GitHub REST API requests, real repository discovery,
workflow runs, jobs, logs, and webhook verification with comprehensive error handling.
"""
import hashlib
import hmac
import os
from typing import Any, Dict, List, Optional
import httpx
import structlog
from config.settings import get_settings

logger = structlog.get_logger()

GITHUB_API_BASE = "https://api.github.com"
GITHUB_OAUTH_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_OAUTH_TOKEN_URL = "https://github.com/login/oauth/access_token"

DEFAULT_SCOPES = "repo,workflow,read:user,user:email"
PLACEHOLDER_CLIENT_IDS = {"", "INTELLI_CI_OAUTH_CLIENT", "YOUR_GITHUB_CLIENT_ID", "DEMO_CLIENT_ID"}


class GitHubService:
    """Dedicated service for interacting with GitHub REST APIs and OAuth."""

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        redirect_uri: Optional[str] = None,
    ):
        settings = get_settings()
        self.client_id = client_id or os.getenv("GITHUB_CLIENT_ID", settings.github.client_id)
        self.client_secret = client_secret or os.getenv("GITHUB_CLIENT_SECRET", settings.github.client_secret)
        self.redirect_uri = redirect_uri or os.getenv("GITHUB_REDIRECT_URI", settings.github.redirect_uri)
        self.webhook_secret = os.getenv("GITHUB_WEBHOOK_SECRET", settings.github.webhook_secret)

    def _get_active_client_id(self) -> str:
        return (os.getenv("GITHUB_CLIENT_ID") or self.client_id or get_settings().github.client_id).strip()

    def _get_active_client_secret(self) -> str:
        return (os.getenv("GITHUB_CLIENT_SECRET") or self.client_secret or get_settings().github.client_secret).strip()

    def _get_active_redirect_uri(self) -> str:
        return (
            os.getenv("GITHUB_REDIRECT_URI")
            or self.redirect_uri
            or get_settings().github.redirect_uri
            or "http://localhost:3000/auth/github/callback"
        ).strip()

    def is_oauth_configured(self) -> bool:
        """Check if real GitHub OAuth credentials are configured."""
        cid = self._get_active_client_id()
        csec = self._get_active_client_secret()
        if not cid or cid in PLACEHOLDER_CLIENT_IDS:
            return False
        if not csec or csec in {"", "YOUR_GITHUB_CLIENT_SECRET", "DEMO_SECRET"}:
            return False
        return True

    def _resolve_token(self, token: Optional[str] = None) -> Optional[str]:
        """Resolve valid GitHub token from arguments or environment."""
        if token and not token.startswith("gho_demo_token_"):
            return token.strip()
        env_token = os.getenv("GITHUB_TOKEN") or get_settings().github.token
        if env_token and env_token.strip():
            return env_token.strip()
        return None

    def get_oauth_url(self, state: str, redirect_uri: Optional[str] = None) -> str:
        """Generate GitHub OAuth authorization URL."""
        if not self.is_oauth_configured():
            raise ValueError(
                "GitHub OAuth is not configured. Please configure GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET in backend/.env"
            )
        client_id = self._get_active_client_id()
        redirect = redirect_uri or self._get_active_redirect_uri()
        return (
            f"{GITHUB_OAUTH_AUTHORIZE_URL}"
            f"?client_id={client_id}"
            f"&redirect_uri={redirect}"
            f"&scope={DEFAULT_SCOPES}"
            f"&state={state}"
        )

    async def exchange_code_for_token(self, code: str, redirect_uri: Optional[str] = None) -> Dict[str, Any]:
        """Exchange GitHub OAuth authorization code for an access token."""
        if not self.is_oauth_configured():
            # If GITHUB_TOKEN exists in environment, permit local dev token linkage
            env_token = self._resolve_token()
            if env_token:
                logger.info("using_env_token_for_oauth_exchange")
                return {
                    "access_token": env_token,
                    "token_type": "bearer",
                    "scope": DEFAULT_SCOPES,
                }
            raise ValueError("GitHub OAuth is not configured. Please configure GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET.")

        async with httpx.AsyncClient(timeout=10.0) as client:
            headers = {"Accept": "application/json"}
            data = {
                "client_id": self._get_active_client_id(),
                "client_secret": self._get_active_client_secret(),
                "code": code,
                "redirect_uri": redirect_uri or self._get_active_redirect_uri(),
            }
            res = await client.post(GITHUB_OAUTH_TOKEN_URL, headers=headers, json=data)
            if res.status_code != 200:
                raise ValueError(f"Failed to exchange code: {res.text}")
            payload = res.json()
            if "error" in payload:
                raise ValueError(f"GitHub OAuth error: {payload.get('error_description', payload.get('error'))}")
            return payload

    async def get_authenticated_user(self, access_token: Optional[str] = None) -> Dict[str, Any]:
        """Fetch authenticated GitHub user profile from GitHub API."""
        token = self._resolve_token(access_token)
        if not token:
            raise PermissionError("No valid GitHub access token provided")

        async with httpx.AsyncClient(timeout=10.0) as client:
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "User-Agent": "Intelli-CI-App",
            }
            res = await client.get(f"{GITHUB_API_BASE}/user", headers=headers)
            if res.status_code == 401:
                raise PermissionError("Invalid or expired GitHub access token")
            if res.status_code != 200:
                raise ValueError(f"GitHub API error ({res.status_code}): {res.text}")
            return res.json()

    async def list_user_repositories(
        self,
        access_token: Optional[str] = None,
        page: int = 1,
        per_page: int = 30,
        search: str = "",
        visibility: str = "all",
    ) -> List[Dict[str, Any]]:
        """List repositories accessible to the user from GitHub REST API."""
        token = self._resolve_token(access_token)
        if not token:
            return []

        async with httpx.AsyncClient(timeout=15.0) as client:
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "User-Agent": "Intelli-CI-App",
            }
            params = {
                "page": page,
                "per_page": per_page,
                "sort": "updated",
                "direction": "desc",
                "visibility": visibility,
            }
            res = await client.get(f"{GITHUB_API_BASE}/user/repos", headers=headers, params=params)
            if res.status_code == 401:
                raise PermissionError("Unauthorized GitHub API request. Token is invalid or expired.")
            if res.status_code != 200:
                logger.warning("failed_to_fetch_github_repos", status=res.status_code, body=res.text[:200])
                return []

            repos = res.json()
            if search:
                s = search.lower()
                repos = [r for r in repos if s in r.get("name", "").lower() or s in (r.get("description") or "").lower()]
            return repos

    async def get_repository(self, access_token: Optional[str], owner: str, repo: str) -> Dict[str, Any]:
        """Fetch single repository metadata from GitHub."""
        token = self._resolve_token(access_token)
        if not token:
            raise PermissionError("No GitHub token configured")

        async with httpx.AsyncClient(timeout=10.0) as client:
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "User-Agent": "Intelli-CI-App",
            }
            res = await client.get(f"{GITHUB_API_BASE}/repos/{owner}/{repo}", headers=headers)
            if res.status_code != 200:
                raise ValueError(f"Repository not found on GitHub: {res.text}")
            return res.json()

    async def get_workflow_runs(
        self,
        access_token: Optional[str],
        owner: str,
        repo: str,
        per_page: int = 20,
    ) -> List[Dict[str, Any]]:
        """Fetch recent real GitHub Actions workflow runs from GitHub API."""
        token = self._resolve_token(access_token)
        if not token:
            return []

        async with httpx.AsyncClient(timeout=15.0) as client:
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "User-Agent": "Intelli-CI-App",
            }
            res = await client.get(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/actions/runs?per_page={per_page}",
                headers=headers,
            )
            if res.status_code != 200:
                logger.info("no_workflow_runs_found_or_error", status=res.status_code)
                return []
            return res.json().get("workflow_runs", [])

    async def get_workflow_run_jobs(
        self,
        access_token: Optional[str],
        owner: str,
        repo: str,
        run_id: int,
    ) -> List[Dict[str, Any]]:
        """Fetch jobs for a specific GitHub Actions workflow run from GitHub API."""
        token = self._resolve_token(access_token)
        if not token:
            return []

        async with httpx.AsyncClient(timeout=15.0) as client:
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "User-Agent": "Intelli-CI-App",
            }
            res = await client.get(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/actions/runs/{run_id}/jobs",
                headers=headers,
            )
            if res.status_code != 200:
                return []
            return res.json().get("jobs", [])

    async def get_job_logs(
        self,
        access_token: Optional[str],
        owner: str,
        repo: str,
        job_id: int,
    ) -> Optional[str]:
        """Download raw log content for a specific GitHub Actions job."""
        token = self._resolve_token(access_token)
        if not token:
            return None

        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "User-Agent": "Intelli-CI-App",
            }
            res = await client.get(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/actions/jobs/{job_id}/logs",
                headers=headers,
            )
            if res.status_code == 200:
                return res.text
            return None

    def verify_webhook_signature(
        self,
        payload_body: bytes,
        signature_header: Optional[str],
        secret: Optional[str] = None,
    ) -> bool:
        """Verify GitHub X-Hub-Signature-256 HMAC signature."""
        key = secret or self.webhook_secret or "default_secret"
        if not signature_header:
            return False

        expected_sig = "sha256=" + hmac.new(
            key.encode("utf-8"),
            payload_body,
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(expected_sig, signature_header)


# Singleton instance
github_service = GitHubService()
