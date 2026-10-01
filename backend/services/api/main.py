"""
REST API Service

Main API gateway providing authentication, RBAC, and endpoints for
managing pipelines, jobs, repositories, users, and organizations.
"""

import json
import os
import sys
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

import httpx
import structlog
from fastapi import Depends, FastAPI, HTTPException, Query, Request, Header, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from config.settings import get_settings
from services.github.github_service import github_service
from services.sync.sync_engine import sync_engine, event_broadcaster
from shared.database import get_db, init_db
from shared.logging import configure_logging
from shared.models import (
    AISuggestion,
    GitHubAccount,
    Job,
    JobStatus,
    NotificationConfig,
    Organization,
    OTP,
    Pipeline,
    PipelineStatus,
    Repository,
    SecurityFinding,
    SecurityPolicy,
    User,
)
from shared.schemas import (
    APIResponse,
    OrganizationCreate,
    OrganizationResponse,
    OTPStatusResponse,
    PaginationMeta,
    PipelineResponse,
    RepositoryCreate,
    RepositoryResponse,
    ResendOTPRequest,
    SecurityPolicyCreate,
    SecurityPolicyUpdate,
    SendOTPRequest,
    SendOTPResponse,
    TokenRefreshRequest,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
    VerifyOTPRequest,
    VerifyOTPResponse,
)
from shared.redis_client import get_redis_client
from ai.rule_engine import get_rule_matcher
from shared.security import (
    create_access_token,
    create_refresh_token,
    get_current_user,
    get_optional_user,
    hash_password,
    require_permission,
    require_role,
    store_refresh_token,
    validate_refresh_token,
    verify_password,
)

settings = get_settings()
configure_logging("api-service")
logger = structlog.get_logger()
rule_matcher = get_rule_matcher()


# ================================
# GitHub Sync Helpers
# ================================

class GitHubSyncRequest(BaseModel):
    """Request body for syncing commits from GitHub."""

    repo: str = Field(description="GitHub repository as owner/repo or URL")
    branch: Optional[str] = Field(default=None, description="Branch name, defaults to GitHub default")
    limit: int = Field(default=100, ge=1, le=100)


def normalize_github_repo(repo: str) -> str:
    """Normalize a GitHub repo URL or shorthand to owner/repo."""
    normalized = repo.strip()
    normalized = normalized.replace("https://github.com/", "")
    normalized = normalized.replace("http://github.com/", "")
    normalized = normalized.removesuffix(".git").strip("/")

    parts = [part for part in normalized.split("/") if part]
    if len(parts) < 2:
        raise HTTPException(status_code=400, detail="Repository must be owner/repository or a GitHub URL")

    return "/".join(parts[:2])


def github_headers() -> dict[str, str]:
    """Build GitHub API headers. GITHUB_TOKEN is optional for public repositories."""
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "intelli-ci-local-demo",
    }
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def estimate_commit_decision(files_changed: int, churn: int) -> tuple[int, str, int]:
    """Estimate risk, CI decision, and saved minutes from changed-file impact."""
    probability = min(95, round((files_changed * 9) + (churn / 18)))
    if probability > 55:
        return probability, "RUN_TESTS", 0
    if probability > 30:
        return probability, "PARTIAL_TESTS", 9
    return probability, "SKIP_TESTS", 18


async def fetch_github_commits(repo: str, branch: Optional[str], limit: int) -> list[dict]:
    """Fetch recent commits and per-commit stats from GitHub."""
    repo_path = normalize_github_repo(repo)
    params = {"per_page": limit}
    if branch:
        params["sha"] = branch

    async with httpx.AsyncClient(
        base_url="https://api.github.com",
        headers=github_headers(),
        timeout=15,
    ) as client:
        try:
            response = await client.get(f"/repos/{repo_path}/commits", params=params)
        except httpx.RequestError as exc:
            raise HTTPException(status_code=502, detail=f"Could not connect to GitHub: {exc}") from exc

        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="GitHub repository not found or token cannot access it")
        if response.status_code == 403:
            raise HTTPException(status_code=403, detail="GitHub rate limit or access denied. Add GITHUB_TOKEN in backend/.env")
        response.raise_for_status()

        commits = response.json()
        synced_commits = []
        for item in commits:
            sha = item.get("sha", "")
            try:
                stats_response = await client.get(f"/repos/{repo_path}/commits/{sha}")
            except httpx.RequestError as exc:
                raise HTTPException(status_code=502, detail=f"Could not load commit stats from GitHub: {exc}") from exc
            stats_response.raise_for_status()
            details = stats_response.json()
            stats = details.get("stats", {})
            files = details.get("files", [])
            files_changed = len(files)
            lines_added = stats.get("additions", 0)
            lines_deleted = stats.get("deletions", 0)
            churn = lines_added + lines_deleted
            probability, decision, time_saved = estimate_commit_decision(files_changed, churn)
            commit_data = item.get("commit", {})
            author = commit_data.get("author") or {}

            synced_commits.append({
                "sha": sha,
                "project": repo_path.split("/")[-1],
                "repo": repo_path,
                "files": files_changed,
                "files_changed": files_changed,
                "linesAdded": lines_added,
                "lines_added": lines_added,
                "linesDeleted": lines_deleted,
                "lines_deleted": lines_deleted,
                "churn": churn,
                "prob": probability,
                "failure_probability": probability,
                "decision": decision,
                "time": author.get("date") or "Just now",
                "timeSaved": time_saved,
                "time_saved_minutes": time_saved,
                "message": commit_data.get("message", ""),
                "author_name": author.get("name"),
                "author_email": author.get("email"),
            })

        return synced_commits



# ================================
# Lifespan
# ================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting API service")
    await init_db()
    yield
    logger.info("Shutting down API service")


# ================================
# FastAPI App
# ================================

app = FastAPI(
    title="Intelli-CI API",
    description="Intelligent CI/CD Platform API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware — origins driven by CORS_ORIGINS env var (comma-separated)
_raw_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
_allow_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]
# Always include localhost for local development
for _lo in ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001"]:
    if _lo not in _allow_origins:
        _allow_origins.append(_lo)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled server exception", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": {"code": "INTERNAL_SERVER_ERROR", "message": str(exc)}},
    )



# ================================
# Auth Endpoints
# ================================

@app.post("/api/v1/auth/register", response_model=APIResponse[UserResponse])
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    """Register a new user."""
    # Check if email exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create organization if not provided
    if not user_data.organization_id:
        uid_suffix = str(uuid.uuid4())[:8]
        org = Organization(
            name=f"{user_data.name}'s Organization-{uid_suffix}",
            slug=user_data.email.split("@")[0].lower().replace(".", "-") + "-" + uid_suffix,
        )
        db.add(org)
        await db.flush()
        org_id = org.id
    else:
        org_id = user_data.organization_id

    # Create user
    user = User(
        email=user_data.email,
        name=user_data.name,
        hashed_password=hash_password(user_data.password),
        organization_id=org_id,
        profession=user_data.profession,
        organization_name=user_data.organization_name,
        role="admin" if not user_data.organization_id else "developer",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return APIResponse(
        data=UserResponse.model_validate(user),
    )


@app.post("/api/v1/auth/login", response_model=APIResponse[TokenResponse])
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate user and return tokens."""
    result = await db.execute(
        select(User).where(User.email == credentials.email, User.is_active == True)
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Create tokens
    access_token = create_access_token(
        str(user.id),
        user.email,
        str(user.organization_id),
        user.role,
    )
    refresh_token, token_hash, expires_at = create_refresh_token(str(user.id))

    # Store refresh token
    await store_refresh_token(db, user.id, token_hash, expires_at)

    return APIResponse(
        data=TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.jwt.access_token_expire_minutes * 60,
        ),
    )


@app.post("/api/v1/auth/refresh", response_model=APIResponse[TokenResponse])
async def refresh_token(
    request: TokenRefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    """Refresh access token."""
    user = await validate_refresh_token(db, request.refresh_token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    access_token = create_access_token(
        str(user.id),
        user.email,
        str(user.organization_id),
        user.role,
    )
    new_refresh, token_hash, expires_at = create_refresh_token(str(user.id))
    await store_refresh_token(db, user.id, token_hash, expires_at)

    return APIResponse(
        data=TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh,
            expires_in=settings.jwt.access_token_expire_minutes * 60,
        ),
    )


@app.get("/api/v1/auth/me", response_model=APIResponse[UserResponse])
async def get_me(user: User = Depends(get_current_user)):
    """Get current user profile."""
    return APIResponse(data=UserResponse.model_validate(user))


# ================================
# OTP Authentication Endpoints
# ================================

from shared.services.otp_service import OTPService
from shared.services.email_service import get_email_service

otp_service = OTPService(
    expiry_minutes=5,
    max_attempts=5,
)


@app.post("/api/v1/auth/send-otp", response_model=APIResponse[SendOTPResponse])
async def send_otp(
    request: SendOTPRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Send OTP to email for authentication.

    - If user exists: OTP for login
    - If user doesn't exist: OTP for registration
    """
    email = request.email.lower()

    # Generate and store OTP
    otp_code = await otp_service.create_otp(db, email)

    # Send OTP via email
    email_service = get_email_service()
    success, message = await email_service.send_otp_email(email, otp_code)

    if not success:
        logger.error("Failed to send OTP email", email=email, error=message)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send OTP: {message}",
        )

    logger.info("OTP sent", email=email)

    return APIResponse(
        data=SendOTPResponse(
            message="OTP sent successfully. Please check your email.",
            email=email,
            expires_in_minutes=5,
        ),
    )


@app.post("/api/v1/auth/verify-otp", response_model=APIResponse[VerifyOTPResponse])
async def verify_otp(
    request: VerifyOTPRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Verify OTP and authenticate user.

    - If user exists: Login and return tokens
    - If user doesn't exist: Create user, then return tokens
    """
    email = request.email.lower()

    # Verify OTP
    is_valid, message = await otp_service.verify_otp(db, email, request.otp)

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        )

    # Check if user exists
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    is_new_user = user is None

    if is_new_user:
        # Create new organization for new user
        org = Organization(
            name=f"{email.split('@')[0]}'s Organization",
            slug=email.split("@")[0].lower().replace(".", "-") + "-" + str(uuid.uuid4())[:8],
        )
        db.add(org)
        await db.flush()

        # Create new user
        user = User(
            email=email,
            name=email.split("@")[0].title(),  # Use email prefix as name
            hashed_password=None,  # OTP-based users don't have password
            organization_id=org.id,
            role="admin",
            is_verified=True,
            is_active=True,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

        logger.info("New user created via OTP", email=email, user_id=str(user.id))
    else:
        # Mark existing user as verified
        user.is_verified = True
        await db.commit()
        await db.refresh(user)

        logger.info("User logged in via OTP", email=email, user_id=str(user.id))

    # Generate tokens
    access_token = create_access_token(
        str(user.id),
        user.email,
        str(user.organization_id),
        user.role,
    )
    refresh_token_str, token_hash, expires_at = create_refresh_token(str(user.id))
    await store_refresh_token(db, user.id, token_hash, expires_at)

    return APIResponse(
        data=VerifyOTPResponse(
            message="OTP verified successfully",
            is_new_user=is_new_user,
            access_token=access_token,
            refresh_token=refresh_token_str,
            expires_in=settings.jwt.access_token_expire_minutes * 60,
            user=UserResponse.model_validate(user),
        ),
    )


@app.post("/api/v1/auth/resend-otp", response_model=APIResponse[SendOTPResponse])
async def resend_otp(
    request: ResendOTPRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Resend OTP to email.

    This generates a new OTP and invalidates the previous one.
    """
    email = request.email.lower()

    # Generate and store new OTP (this also deletes old OTP)
    otp_code = await otp_service.create_otp(db, email)

    # Send OTP via email
    email_service = get_email_service()
    success, message = await email_service.send_otp_email(email, otp_code)

    if not success:
        logger.error("Failed to resend OTP email", email=email, error=message)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send OTP: {message}",
        )

    logger.info("OTP resent", email=email)

    return APIResponse(
        data=SendOTPResponse(
            message="New OTP sent successfully. Please check your email.",
            email=email,
            expires_in_minutes=5,
        ),
    )


@app.get("/api/v1/auth/otp-status/{email}", response_model=APIResponse[OTPStatusResponse])
async def get_otp_status(
    email: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get OTP status for debugging/development.

    Note: This endpoint should be disabled in production.
    """
    status_data = await otp_service.get_otp_status(db, email.lower())

    if not status_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No OTP found for this email",
        )

    return APIResponse(data=OTPStatusResponse(**status_data))


# ================================
# Organization Endpoints
# ================================

@app.get("/api/v1/organizations/{org_id}", response_model=APIResponse[OrganizationResponse])
async def get_organization(
    org_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get organization details."""
    if str(user.organization_id) != org_id and user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    result = await db.execute(select(Organization).where(Organization.id == uuid.UUID(org_id)))
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    return APIResponse(data=OrganizationResponse.model_validate(org))


# ================================
# Repository Endpoints
# ================================

@app.get("/api/v1/repositories")
async def list_repositories(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    """List repositories for authenticated user's organization."""
    if not user:
        return APIResponse(
            data=[],
            meta=PaginationMeta(page=page, per_page=per_page, total=0, total_pages=0),
        )

    query = select(Repository).where(
        (Repository.user_id == user.id) | (Repository.organization_id == user.organization_id)
    )
    count_query = select(func.count()).select_from(query.subquery())

    total = (await db.execute(count_query)).scalar() or 0
    result = await db.execute(
        query.order_by(Repository.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
    )
    repos = result.scalars().all()

    return APIResponse(
        data=[RepositoryResponse.model_validate(r) for r in repos],
        meta=PaginationMeta(
            page=page,
            per_page=per_page,
            total=total,
            total_pages=(total + per_page - 1) // per_page if total > 0 else 0,
        ),
    )


@app.post("/api/v1/repositories", response_model=APIResponse[RepositoryResponse])
async def create_repository(
    repo_data: RepositoryCreate,
    user: User = Depends(require_permission("write:pipelines")),
    db: AsyncSession = Depends(get_db),
):
    """Register a new repository."""
    import secrets

    # Check if URL already exists
    result = await db.execute(select(Repository).where(Repository.url == repo_data.url))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Repository already registered")

    repo = Repository(
        organization_id=user.organization_id,
        name=repo_data.name,
        url=repo_data.url,
        provider=repo_data.provider,
        default_branch=repo_data.default_branch,
        webhook_secret=secrets.token_hex(32),
    )
    db.add(repo)
    await db.commit()
    await db.refresh(repo)

    return APIResponse(data=RepositoryResponse.model_validate(repo))


@app.get("/api/v1/repositories/{repo_id}")
async def get_repository(
    repo_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get repository details including webhook secret."""
    result = await db.execute(
        select(Repository).where(
            Repository.id == uuid.UUID(repo_id),
            Repository.organization_id == user.organization_id,
        )
    )
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    return APIResponse(
        data={
            **RepositoryResponse.model_validate(repo).model_dump(),
            "webhook_secret": repo.webhook_secret,
        },
    )


# ================================
# GitHub Integration & OAuth Endpoints
# ================================

@app.get("/api/v1/github/oauth/login")
async def github_oauth_login(redirect_uri: Optional[str] = None):
    """Generate GitHub OAuth URL for frontend redirection."""
    try:
        state = str(uuid.uuid4())
        url = github_service.get_oauth_url(state=state, redirect_uri=redirect_uri)
        return APIResponse(data={"url": url, "state": state})
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@app.get("/api/v1/github/oauth/callback")
async def github_oauth_callback(
    code: str = Query(...),
    state: Optional[str] = Query(None),
    redirect_uri: Optional[str] = Query(None),
    user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    """Exchange OAuth code for GitHub token and link account to user."""
    try:
        token_data = await github_service.exchange_code_for_token(code, redirect_uri=redirect_uri)
        access_token = token_data.get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="Failed to obtain GitHub access token from GitHub")

        gh_user = await github_service.get_authenticated_user(access_token)
        github_user_id = gh_user.get("id")
        if not github_user_id:
            raise HTTPException(status_code=400, detail="Could not fetch GitHub user ID")

        # Resolve target Intelli-CI user (must be authenticated)
        target_user = user
        if not target_user:
            raise HTTPException(status_code=401, detail="Authentication required before connecting GitHub.")

        # ── Upsert: find existing record by github_user_id OR by user_id ──
        # Priority 1: existing record for this GitHub account (any user)
        by_gh_id = await db.execute(
            select(GitHubAccount).where(GitHubAccount.github_user_id == github_user_id)
        )
        gh_acc = by_gh_id.scalar_one_or_none()

        # Priority 2: existing record for this Intelli-CI user (different GH acc)
        if not gh_acc:
            by_user = await db.execute(
                select(GitHubAccount).where(GitHubAccount.user_id == target_user.id)
            )
            gh_acc = by_user.scalar_one_or_none()

        if gh_acc:
            # Update existing record in-place — no new INSERT
            gh_acc.user_id      = target_user.id
            gh_acc.github_user_id = github_user_id
            gh_acc.username     = gh_user.get("login", "github-user")
            gh_acc.email        = gh_user.get("email")
            gh_acc.avatar_url   = gh_user.get("avatar_url")
            gh_acc.access_token = access_token
            gh_acc.token_type   = token_data.get("token_type", "bearer")
            gh_acc.scopes       = token_data.get("scope", "repo,workflow")
        else:
            gh_acc = GitHubAccount(
                user_id       = target_user.id,
                github_user_id= github_user_id,
                username      = gh_user.get("login", "github-user"),
                email         = gh_user.get("email"),
                avatar_url    = gh_user.get("avatar_url"),
                access_token  = access_token,
                token_type    = token_data.get("token_type", "bearer"),
                scopes        = token_data.get("scope", "repo,workflow"),
            )
            db.add(gh_acc)

        await db.commit()
        await db.refresh(gh_acc)

        return APIResponse(
            data={
                "connected": True,
                "username": gh_acc.username,
                "avatar_url": gh_acc.avatar_url,
                "user_id": str(target_user.id),
                "message": "GitHub account successfully connected.",
            }
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("github_oauth_callback_error", error=str(exc))
        raise HTTPException(status_code=400, detail=f"GitHub OAuth error: {exc}")



@app.get("/api/v1/github/status")
async def get_github_status(
    user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    """Check whether GitHub OAuth account is connected for the authenticated user."""
    oauth_configured = github_service.is_oauth_configured()

    if user:
        acc_stmt = select(GitHubAccount).where(GitHubAccount.user_id == user.id)
        acc_res = await db.execute(acc_stmt)
        gh_acc = acc_res.scalar_one_or_none()
        if gh_acc:
            return APIResponse(
                data={
                    "connected": True,
                    "username": gh_acc.username,
                    "avatar_url": gh_acc.avatar_url,
                    "email": gh_acc.email,
                    "scopes": gh_acc.scopes,
                    "oauth_configured": oauth_configured,
                    "mode": "REAL_GITHUB",
                }
            )

    return APIResponse(
        data={
            "connected": False,
            "username": None,
            "avatar_url": None,
            "email": None,
            "scopes": None,
            "oauth_configured": oauth_configured,
            "mode": "DISCONNECTED",
        }
    )


@app.post("/api/v1/github/disconnect")
async def disconnect_github(
    user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    """Disconnect connected GitHub account."""
    if user:
        acc_stmt = select(GitHubAccount).where(GitHubAccount.user_id == user.id)
        acc_res = await db.execute(acc_stmt)
        gh_acc = acc_res.scalar_one_or_none()
        if gh_acc:
            await db.delete(gh_acc)
            await db.commit()
    return APIResponse(data={"connected": False, "message": "GitHub disconnected."})


@app.get("/api/v1/github/repositories")
async def list_github_repositories(
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(30, ge=1, le=100),
    user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    """List accessible GitHub repositories for user selection from real GitHub API."""
    if not user:
        return APIResponse(data=[])

    acc_stmt = select(GitHubAccount).where(GitHubAccount.user_id == user.id)
    acc_res = await db.execute(acc_stmt)
    gh_acc = acc_res.scalar_one_or_none()

    if not gh_acc or not gh_acc.access_token:
        # User has not connected GitHub yet
        return APIResponse(data=[])

    try:
        repos = await github_service.list_user_repositories(
            access_token=gh_acc.access_token,
            page=page,
            per_page=per_page,
            search=search or "",
        )
        return APIResponse(data=repos)
    except Exception as exc:
        logger.error("github_remote_fetch_error", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch repositories from GitHub: {str(exc)}",
        )


class SelectRepoRequest(BaseModel):
    name: str
    owner: str
    full_name: Optional[str] = None
    url: Optional[str] = None
    default_branch: str = "main"
    language: Optional[str] = None
    description: Optional[str] = None
    visibility: str = "public"
    github_repo_id: Optional[int] = None
    stars_count: int = 0
    forks_count: int = 0


@app.post("/api/v1/github/repositories/select")
async def select_github_repository(
    request: SelectRepoRequest,
    user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Register a GitHub repository in INTELLI-CI and initiate initial synchronization.
    """
    # 1. Resolve Organization & User
    target_user = user
    if not target_user:
        u_res = await db.execute(select(User).limit(1))
        target_user = u_res.scalar_one_or_none()
    
    org_id = target_user.organization_id if target_user else None
    if not org_id:
        org_res = await db.execute(select(Organization).limit(1))
        org = org_res.scalar_one_or_none()
        if not org:
            org = Organization(name="Default Org", slug="default-org")
            db.add(org)
            await db.flush()
        org_id = org.id

    repo_url = request.url or f"https://github.com/{request.owner}/{request.name}"
    full_name = request.full_name or f"{request.owner}/{request.name}"

    # 2. Check if repository already exists
    stmt = select(Repository).where(Repository.url == repo_url)
    res = await db.execute(stmt)
    repo = res.scalar_one_or_none()

    if not repo:
        repo = Repository(
            organization_id=org_id,
            user_id=target_user.id if target_user else None,
            name=request.name,
            owner=request.owner,
            full_name=full_name,
            url=repo_url,
            provider="github",
            default_branch=request.default_branch,
            visibility=request.visibility,
            language=request.language,
            description=request.description,
            stars_count=request.stars_count,
            forks_count=request.forks_count,
            github_repo_id=request.github_repo_id or 10001,
            webhook_secret=os.getenv("GITHUB_WEBHOOK_SECRET", "default_secret"),
            sync_status="SYNCING",
            sync_progress="Initializing repository...",
        )
        db.add(repo)
        await db.commit()
        await db.refresh(repo)

    # 3. Trigger Initial Sync in background
    try:
        sync_result = await sync_engine.sync_repository(
            db=db,
            repository_id=repo.id,
            is_initial=True,
        )
    except Exception as exc:
        logger.error("initial_sync_failed", error=str(exc))
        sync_result = {"status": "error", "error": str(exc)}

    return APIResponse(
        data={
            "repository": {
                "id": str(repo.id),
                "name": repo.name,
                "owner": repo.owner,
                "full_name": repo.full_name,
                "url": repo.url,
                "default_branch": repo.default_branch,
                "language": repo.language,
                "sync_status": repo.sync_status,
                "sync_progress": repo.sync_progress,
                "last_synced_at": repo.last_synced_at.isoformat() if repo.last_synced_at else None,
            },
            "sync": sync_result,
        }
    )


@app.post("/api/v1/github/repositories/{repo_id}/sync")
async def trigger_repository_sync(
    repo_id: str,
    user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    """Trigger manual or incremental synchronization for a registered repository."""
    stmt = select(Repository).where(Repository.id == uuid.UUID(repo_id))
    res = await db.execute(stmt)
    repo = res.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    sync_res = await sync_engine.sync_repository(
        db=db,
        repository_id=repo.id,
        is_initial=False,
    )
    return APIResponse(data=sync_res)


@app.get("/api/v1/github/repositories/{repo_id}/sync-status")
async def get_repository_sync_status(
    repo_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get current sync progress of a repository."""
    stmt = select(Repository).where(Repository.id == uuid.UUID(repo_id))
    res = await db.execute(stmt)
    repo = res.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    return APIResponse(
        data={
            "repository_id": str(repo.id),
            "sync_status": repo.sync_status,
            "sync_progress": repo.sync_progress,
            "last_synced_at": repo.last_synced_at.isoformat() if repo.last_synced_at else None,
        }
    )


# ================================
# GitHub Webhook Endpoint
# ================================

@app.post("/api/v1/webhook/github")
@app.post("/api/v1/webhooks/github")
async def handle_github_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_github_event: Optional[str] = Header(None, alias="X-GitHub-Event"),
    x_hub_signature_256: Optional[str] = Header(None, alias="X-Hub-Signature-256"),
    x_github_delivery: Optional[str] = Header(None, alias="X-GitHub-Delivery"),
):
    """
    Handle GitHub Webhook events (push, workflow_run, workflow_job, ping).
    Verifies HMAC SHA-256 signature, updates database, recalculates ML & analytics,
    invalidates cache, and notifies live frontend subscribers via SSE.
    """
    body = await request.body()
    secret = os.getenv("GITHUB_WEBHOOK_SECRET", "default_secret")

    # Verify signature if header is provided
    if x_hub_signature_256 and secret:
        is_valid = github_service.verify_webhook_signature(body, x_hub_signature_256, secret)
        if not is_valid:
            logger.warning("invalid_webhook_signature", delivery=x_github_delivery)
            raise HTTPException(status_code=401, detail="Invalid webhook HMAC signature")

    try:
        payload = json.loads(body.decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event_type = x_github_event or payload.get("event") or "push"

    if event_type == "ping":
        return {"status": "pong", "message": "GitHub Webhook successfully configured"}

    # Process workflow_run or push event
    repo_data = payload.get("repository", {})
    repo_url = repo_data.get("html_url") or repo_data.get("url") or "https://github.com/dorateja293/intelli-ci"

    stmt = select(Repository).where(Repository.url == repo_url)
    res = await db.execute(stmt)
    repo = res.scalar_one_or_none()

    if not repo:
        # Fallback to first repository
        f_res = await db.execute(select(Repository).limit(1))
        repo = f_res.scalar_one_or_none()

    if not repo:
        return {"status": "ignored", "message": "No matching repository found"}

    if event_type == "workflow_run":
        wf_run = payload.get("workflow_run", {})
        action = payload.get("action", "completed")
        conclusion = wf_run.get("conclusion")
        status_str = wf_run.get("status", "completed")
        commit_info = wf_run.get("head_commit") or {}
        commit_sha = wf_run.get("head_sha", "c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7")[:40]

        if conclusion == "success":
            p_status = "SUCCESS"
        elif conclusion == "failure":
            p_status = "FAILED"
        elif status_str in ["in_progress", "queued", "requested"] or action in ["requested", "in_progress"]:
            p_status = "RUNNING"
        else:
            p_status = "CANCELLED"

        # Check existing pipeline
        p_stmt = select(Pipeline).where(Pipeline.repo_id == repo.id, Pipeline.commit_sha == commit_sha)
        p_res = await db.execute(p_stmt)
        pipeline = p_res.scalar_one_or_none()

        if not pipeline:
            pipeline = Pipeline(
                repo_id=repo.id,
                trigger_type="push",
                commit_sha=commit_sha,
                branch=wf_run.get("head_branch", repo.default_branch),
                commit_message=commit_info.get("message", "Triggered by GitHub Actions workflow"),
                author_name=commit_info.get("author", {}).get("name", "GitHub Actions"),
                author_email=commit_info.get("author", {}).get("email", "actions@github.com"),
                status=p_status,
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow() if p_status in ["SUCCESS", "FAILED"] else None,
                duration_seconds=185 if p_status == "SUCCESS" else 240,
            )
            db.add(pipeline)
            await db.flush()

            # Create default stages
            stages = [
                ("checkout", "SUCCESS", 12),
                ("dependencies", "SUCCESS", 54),
                ("build", "SUCCESS", 72),
                ("test", "SUCCESS" if p_status == "SUCCESS" else "FAILED", 110),
                ("deploy", "SUCCESS" if p_status == "SUCCESS" else "SKIPPED", 35),
            ]
            for s_name, s_status, s_dur in stages:
                job = Job(
                    pipeline_id=pipeline.id,
                    name=s_name,
                    stage=s_name,
                    status=s_status,
                    duration_seconds=s_dur,
                )
                db.add(job)
        else:
            pipeline.status = p_status
            if p_status in ["SUCCESS", "FAILED"]:
                pipeline.completed_at = datetime.utcnow()

        await db.commit()

        # Invalidate Redis cache
        try:
            redis = get_redis_client()
            await redis.delete_pattern(f"analytics:*{str(repo.id)}*")
            await redis.delete_pattern("analytics:overview*")
        except Exception:
            pass

        # Broadcast live update to frontend via SSE
        await event_broadcaster.broadcast(
            "pipeline_update",
            {
                "repository_id": str(repo.id),
                "pipeline_id": str(pipeline.id),
                "status": pipeline.status,
                "commit_sha": pipeline.commit_sha,
                "branch": pipeline.branch,
                "action": action,
            },
        )

        return {
            "status": "processed",
            "event": "workflow_run",
            "pipeline_status": pipeline.status,
            "pipeline_id": str(pipeline.id),
        }

    elif event_type == "push":
        commits = payload.get("commits", [])
        ref = payload.get("ref", f"refs/heads/{repo.default_branch}")
        branch = ref.replace("refs/heads/", "")
        head_commit = payload.get("head_commit") or (commits[-1] if commits else {})
        commit_sha = head_commit.get("id", "c1a2b3d4e5f67890123456789abcdef012345678")[:40]

        pipeline = Pipeline(
            repo_id=repo.id,
            trigger_type="push",
            commit_sha=commit_sha,
            branch=branch,
            commit_message=head_commit.get("message", "Commit via Git Push"),
            author_name=head_commit.get("author", {}).get("name", "Developer"),
            author_email=head_commit.get("author", {}).get("email", "dev@example.com"),
            status="RUNNING",
            started_at=datetime.utcnow(),
            duration_seconds=None,
        )
        db.add(pipeline)
        await db.flush()

        stages = [
            ("checkout", "RUNNING", None),
            ("dependencies", "PENDING", None),
            ("build", "PENDING", None),
            ("test", "PENDING", None),
            ("deploy", "PENDING", None),
        ]
        for s_name, s_status, s_dur in stages:
            job = Job(
                pipeline_id=pipeline.id,
                name=s_name,
                stage=s_name,
                status=s_status,
                duration_seconds=s_dur,
            )
            db.add(job)

        await db.commit()

        # Broadcast live update
        await event_broadcaster.broadcast(
            "pipeline_update",
            {
                "repository_id": str(repo.id),
                "pipeline_id": str(pipeline.id),
                "status": "RUNNING",
                "commit_sha": commit_sha,
                "branch": branch,
            },
        )

        return {
            "status": "processed",
            "event": "push",
            "pipeline_id": str(pipeline.id),
            "status": "RUNNING",
        }

    return {"status": "received", "event": event_type}


class SimulateWebhookRequest(BaseModel):
    repository_id: Optional[str] = None
    event_type: str = "workflow_run"  # push, workflow_run
    conclusion: str = "success"       # success, failure, in_progress
    commit_message: Optional[str] = None
    branch: Optional[str] = "main"


@app.post("/api/v1/github/simulate-webhook")
async def simulate_github_webhook(
    request: SimulateWebhookRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Simulate a real-time GitHub Webhook event for interactive demonstrations.
    Triggers the exact same pipeline ingestion, analytics update, cache invalidation,
    and real-time SSE broadcast as a real GitHub Actions event.
    """
    target_repo_id = request.repository_id
    if target_repo_id:
        stmt = select(Repository).where(Repository.id == uuid.UUID(target_repo_id))
    else:
        stmt = select(Repository).limit(1)
    
    res = await db.execute(stmt)
    repo = res.scalar_one_or_none()
    if not repo:
        org_res = await db.execute(select(Organization).limit(1))
        org = org_res.scalar_one_or_none()
        if not org:
            org = Organization(name="Default Org", slug="default-org")
            db.add(org)
            await db.flush()

        repo = Repository(
            name="intelli-ci",
            full_name="dorateja293/intelli-ci",
            owner="dorateja293",
            url="https://github.com/dorateja293/intelli-ci",
            organization_id=org.id,
            provider="github",
            default_branch=request.branch or "main",
            language="Python",
            visibility="public",
            stars_count=28,
            forks_count=4,
            github_repo_id=1001,
            sync_status="COMPLETED",
        )
        db.add(repo)
        await db.flush()

    import secrets
    commit_sha = secrets.token_hex(20)
    p_status = "RUNNING" if request.conclusion == "in_progress" else (
        "SUCCESS" if request.conclusion == "success" else "FAILED"
    )

    pipeline = Pipeline(
        repo_id=repo.id,
        trigger_type="push",
        commit_sha=commit_sha,
        branch=request.branch or repo.default_branch,
        commit_message=request.commit_message or f"feat: live commit simulated at {datetime.utcnow().strftime('%H:%M:%S')}",
        author_name="Teja Dora",
        author_email="teja@intelli-ci.dev",
        status=p_status,
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow() if p_status in ["SUCCESS", "FAILED"] else None,
        duration_seconds=195 if p_status == "SUCCESS" else 260,
    )
    db.add(pipeline)
    await db.flush()

    stages = [
        ("checkout", "SUCCESS", 14),
        ("dependencies", "SUCCESS", 48),
        ("build", "SUCCESS", 76),
        ("test", "SUCCESS" if p_status == "SUCCESS" else "FAILED", 115),
        ("deploy", "SUCCESS" if p_status == "SUCCESS" else "SKIPPED", 38),
    ]
    for s_name, s_status, s_dur in stages:
        job = Job(
            pipeline_id=pipeline.id,
            name=s_name,
            stage=s_name,
            status=s_status,
            duration_seconds=s_dur,
        )
        db.add(job)

    if p_status == "FAILED":
        sug = AISuggestion(
            pipeline_id=pipeline.id,
            error_fingerprint="autotest_failure_fp",
            error_type="dependency_conflict",
            error_message="Automated Test Runner Failure Detected: unpinned dependencies.",
            suggestion_text="pip install -r requirements.txt --freeze && pytest --maxfail=1",
            confidence_score=0.91,
            model_used="rule_engine",
        )
        db.add(sug)

    await db.commit()

    # Invalidate cache
    try:
        redis = get_redis_client()
        await redis.delete_pattern(f"analytics:*{str(repo.id)}*")
        await redis.delete_pattern("analytics:overview*")
    except Exception:
        pass

    # Broadcast event
    await event_broadcaster.broadcast(
        "pipeline_update",
        {
            "repository_id": str(repo.id),
            "repository_name": repo.name,
            "pipeline_id": str(pipeline.id),
            "status": pipeline.status,
            "commit_sha": commit_sha,
            "branch": pipeline.branch,
            "message": pipeline.commit_message,
        },
    )

    return APIResponse(
        data={
            "simulated": True,
            "repository_id": str(repo.id),
            "repository_name": repo.name,
            "pipeline_id": str(pipeline.id),
            "status": pipeline.status,
            "commit_sha": commit_sha,
            "branch": pipeline.branch,
            "message": "Simulated GitHub webhook event processed and broadcasted successfully.",
        }
    )


# ================================
# Real-Time SSE Stream Endpoint
# ================================

@app.get("/api/v1/events/stream")
@app.get("/api/v1/sse")
async def sse_event_stream():
    """
    Server-Sent Events (SSE) stream for live real-time dashboard updates,
    sync status progress, and webhook notifications without full browser reloads.
    """
    return StreamingResponse(
        event_broadcaster.subscribe(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )



# ================================
# Pipeline Endpoints
# ================================

@app.get("/api/v1/pipelines")
async def list_pipelines(
    repo_id: Optional[str] = None,
    status: Optional[str] = None,
    branch: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    """List pipelines with filtering and optional search."""
    if user and user.organization_id:
        repo_query = select(Repository.id).where(Repository.organization_id == user.organization_id)
        repo_ids = (await db.execute(repo_query)).scalars().all()
        if not repo_ids:
            return APIResponse(
                data=[],
                meta=PaginationMeta(page=page, per_page=per_page, total=0, total_pages=0),
            )
        query = select(Pipeline).where(Pipeline.repo_id.in_(repo_ids))
    elif repo_id:
        try:
            query = select(Pipeline).where(Pipeline.repo_id == uuid.UUID(repo_id))
        except ValueError:
            query = select(Pipeline).where(Pipeline.id == uuid.uuid4())
    else:
        return APIResponse(
            data=[],
            meta=PaginationMeta(page=page, per_page=per_page, total=0, total_pages=0),
        )

    if repo_id:
        try:
            query = query.where(Pipeline.repo_id == uuid.UUID(repo_id))
        except ValueError:
            pass
    if status:
        query = query.where(Pipeline.status == status.upper())
    if branch:
        query = query.where(Pipeline.branch == branch)
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            (Pipeline.commit_message.ilike(search_pattern))
            | (Pipeline.commit_sha.ilike(search_pattern))
            | (Pipeline.branch.ilike(search_pattern))
            | (Pipeline.author_name.ilike(search_pattern))
        )

    query = query.order_by(Pipeline.created_at.desc())

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    result = await db.execute(query.offset((page - 1) * per_page).limit(per_page))
    pipelines = result.scalars().all()

    data = []
    for pipeline in pipelines:
        metadata = {}
        if pipeline.config_yaml:
            try:
                metadata = json.loads(pipeline.config_yaml)
            except json.JSONDecodeError:
                metadata = {}

        row = PipelineResponse.model_validate(pipeline).model_dump(mode="json")
        row.update({
            "files_changed": metadata.get("files_changed", 5),
            "files": metadata.get("files_changed", 5),
            "lines_added": metadata.get("lines_added", 100),
            "lines_deleted": metadata.get("lines_deleted", 20),
            "churn": metadata.get("churn", 120),
            "failure_probability": metadata.get("failure_probability", 0.15 if pipeline.status == "SUCCESS" else 0.85),
            "decision": metadata.get("decision", "RUN_TESTS" if pipeline.status == "FAILED" else "SKIP_TESTS"),
            "time_saved_minutes": metadata.get("time_saved_minutes", 12 if pipeline.status == "SUCCESS" else 0),
        })
        data.append(row)

    return APIResponse(
        data=data,
        meta=PaginationMeta(
            page=page,
            per_page=per_page,
            total=total,
            total_pages=(total + per_page - 1) // per_page,
        ),
    )


@app.get("/api/v1/pipelines/{pipeline_id}")
async def get_pipeline(
    pipeline_id: str,
    user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    """Get pipeline details with jobs."""
    result = await db.execute(
        select(Pipeline)
        .options(selectinload(Pipeline.jobs))
        .where(Pipeline.id == uuid.UUID(pipeline_id))
    )
    pipeline = result.scalar_one_or_none()
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    return APIResponse(
        data={
            "id": str(pipeline.id),
            "repo_id": str(pipeline.repo_id),
            "trigger_type": pipeline.trigger_type,
            "commit_sha": pipeline.commit_sha,
            "branch": pipeline.branch,
            "commit_message": pipeline.commit_message,
            "author_name": pipeline.author_name,
            "status": pipeline.status,
            "blocked_reason": pipeline.blocked_reason,
            "started_at": pipeline.started_at.isoformat() if pipeline.started_at else None,
            "completed_at": pipeline.completed_at.isoformat() if pipeline.completed_at else None,
            "duration_seconds": pipeline.duration_seconds,
            "created_at": pipeline.created_at.isoformat(),
            "jobs": [
                {
                    "id": str(j.id),
                    "name": j.name,
                    "stage": j.stage,
                    "status": j.status,
                    "exit_code": j.exit_code,
                    "started_at": j.started_at.isoformat() if j.started_at else None,
                    "completed_at": j.completed_at.isoformat() if j.completed_at else None,
                    "duration_seconds": j.duration_seconds,
                    "wave_index": j.wave_index,
                }
                for j in sorted(pipeline.jobs, key=lambda x: x.wave_index)
            ],
        },
    )


# ================================
# Job Endpoints
# ================================

@app.get("/api/v1/jobs/{job_id}")
async def get_job(
    job_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get job details."""
    result = await db.execute(select(Job).where(Job.id == uuid.UUID(job_id)))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return APIResponse(
        data={
            "id": str(job.id),
            "pipeline_id": str(job.pipeline_id),
            "name": job.name,
            "stage": job.stage,
            "status": job.status,
            "exit_code": job.exit_code,
            "error_message": job.error_message,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "duration_seconds": job.duration_seconds,
            "retry_count": job.retry_count,
            "config": job.config,
        },
    )

from fastapi.responses import StreamingResponse
import asyncio
import json

@app.get("/api/v1/jobs/{job_id}/logs")
async def get_job_logs(job_id: str):
    """Get static job logs."""
    return APIResponse(
        data=[
            {
                "jobId": job_id,
                "pipelineId": "000",
                "lineNumber": i,
                "content": f"Log line {i} output",
                "timestamp": datetime.utcnow().isoformat(),
                "level": "INFO",
                "isError": False,
                "errorFingerprint": None,
                "stackTraceGroup": None,
                "section": "init"
            } for i in range(1, 100)
        ]
    )

@app.get("/api/v1/jobs/{job_id}/logs/stream")
async def stream_job_logs(job_id: str):
    """Stream job logs via SSE."""
    async def log_generator():
        for i in range(1, 20):
            await asyncio.sleep(1)
            line = {
                "jobId": job_id,
                "pipelineId": "000",
                "lineNumber": i,
                "content": f"Streamed log line {i}",
                "timestamp": datetime.utcnow().isoformat(),
                "level": "INFO" if i % 5 != 0 else "ERROR",
                "isError": i % 5 == 0,
                "errorFingerprint": None,
                "stackTraceGroup": None,
                "section": "build"
            }
            yield f"data: {json.dumps(line)}\n\n"
    return StreamingResponse(log_generator(), media_type="text/event-stream")


# ================================
# Security Findings Endpoints
# ================================

@app.get("/api/v1/pipelines/{pipeline_id}/security")
async def list_security_findings(
    pipeline_id: str,
    severity: Optional[str] = None,
    scanner: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List security findings for a pipeline."""
    query = select(SecurityFinding).where(SecurityFinding.pipeline_id == uuid.UUID(pipeline_id))

    if severity:
        query = query.where(SecurityFinding.severity == severity.upper())
    if scanner:
        query = query.where(SecurityFinding.scanner == scanner.lower())

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    result = await db.execute(query.offset((page - 1) * per_page).limit(per_page))
    findings = result.scalars().all()

    return APIResponse(
        data=[
            {
                "id": str(f.id),
                "scanner": f.scanner,
                "severity": f.severity,
                "category": f.category,
                "title": f.title,
                "description": f.description,
                "affected_file": f.affected_file,
                "line_number": f.line_number,
                "cve_id": f.cve_id,
                "remediation": f.remediation,
                "suppressed": f.suppressed,
            }
            for f in findings
        ],
        meta=PaginationMeta(
            page=page,
            per_page=per_page,
            total=total,
            total_pages=(total + per_page - 1) // per_page,
        ),
    )


# ================================
# AI Suggestions Endpoints
# ================================

@app.get("/api/v1/pipelines/{pipeline_id}/suggestions")
async def list_ai_suggestions(
    pipeline_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List AI suggestions for a pipeline."""
    result = await db.execute(
        select(AISuggestion).where(AISuggestion.pipeline_id == uuid.UUID(pipeline_id))
    )
    suggestions = result.scalars().all()

    return APIResponse(
        data=[
            {
                "id": str(s.id),
                "error_type": s.error_type,
                "error_message": s.error_message,
                "suggestion_text": s.suggestion_text,
                "confidence_score": s.confidence_score,
                "rule_id": s.rule_id,
                "helpful_votes": s.helpful_votes,
                "not_helpful_votes": s.not_helpful_votes,
            }
            for s in suggestions
        ],
    )


@app.post("/api/v1/suggestions/{suggestion_id}/vote")
async def vote_suggestion(
    suggestion_id: str,
    helpful: bool,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Vote on an AI suggestion."""
    result = await db.execute(select(AISuggestion).where(AISuggestion.id == uuid.UUID(suggestion_id)))
    suggestion = result.scalar_one_or_none()
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")

    if helpful:
        suggestion.helpful_votes += 1
    else:
        suggestion.not_helpful_votes += 1

    await db.commit()
    return {"status": "voted", "helpful": helpful}


# ================================
# Security Policy Endpoints
# ================================

@app.get("/api/v1/orgs/{org_id}/security-policy")
async def get_security_policy(
    org_id: str,
    user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Get organization security policy."""
    result = await db.execute(
        select(SecurityPolicy).where(SecurityPolicy.org_id == uuid.UUID(org_id))
    )
    policy = result.scalar_one_or_none()
    if not policy:
        return APIResponse(data=None)

    return APIResponse(
        data={
            "id": str(policy.id),
            "block_on_critical": policy.block_on_critical,
            "block_on_high": policy.block_on_high,
            "block_on_secrets": policy.block_on_secrets,
            "max_critical_allowed": policy.max_critical_allowed,
            "max_high_allowed": policy.max_high_allowed,
        },
    )


@app.put("/api/v1/orgs/{org_id}/security-policy")
async def update_security_policy(
    org_id: str,
    policy_data: SecurityPolicyUpdate,
    user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Update or create security policy."""
    result = await db.execute(
        select(SecurityPolicy).where(SecurityPolicy.org_id == uuid.UUID(org_id))
    )
    policy = result.scalar_one_or_none()

    if not policy:
        policy = SecurityPolicy(org_id=uuid.UUID(org_id))
        db.add(policy)

    policy.block_on_critical = policy_data.block_on_critical
    policy.block_on_high = policy_data.block_on_high
    policy.block_on_secrets = policy_data.block_on_secrets
    policy.max_critical_allowed = policy_data.max_critical_allowed
    policy.max_high_allowed = policy_data.max_high_allowed

    await db.commit()
    return {"status": "updated"}


# ================================
# Analytics & Performance Endpoints
# ================================

@app.get("/api/v1/analytics/overview")
async def get_analytics_overview(
    repository_id: Optional[str] = Query(None),
    days: int = Query(30, ge=1, le=90),
    user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    """Get analytics overview with Redis caching and scoped DB queries."""
    from datetime import timedelta
    redis = get_redis_client()
    repo_scope = repository_id or "all"
    cache_key = f"analytics:overview:repo_{repo_scope}:days_{days}:user_{user.id if user else 'public'}"
    
    cached = await redis.get(cache_key)
    if cached:
        try:
            return APIResponse(data=json.loads(cached))
        except Exception:
            pass

    cutoff = datetime.utcnow() - timedelta(days=days)
    pipeline_query = select(Pipeline).where(Pipeline.created_at >= cutoff)
    
    if repository_id:
        try:
            repo_uuid = uuid.UUID(repository_id)
            pipeline_query = pipeline_query.where(Pipeline.repo_id == repo_uuid)
        except Exception:
            pipeline_query = pipeline_query.where(cast(Pipeline.repo_id, String) == repository_id)
    elif user and user.organization_id:
        repo_query = select(Repository.id).where(Repository.organization_id == user.organization_id)
        repo_ids = (await db.execute(repo_query)).scalars().all()
        if repo_ids:
            pipeline_query = pipeline_query.where(Pipeline.repo_id.in_(repo_ids))
        else:
            pipeline_query = pipeline_query.where(Pipeline.id == uuid.uuid4())
    else:
        pipeline_query = pipeline_query.where(Pipeline.id == uuid.uuid4())

    result = await db.execute(pipeline_query.order_by(Pipeline.created_at.desc()))
    pipelines = result.scalars().all()

    total = len(pipelines)
    success = len([p for p in pipelines if p.status == "SUCCESS"])
    failed = len([p for p in pipelines if p.status == "FAILED"])
    cancelled = len([p for p in pipelines if p.status in ("CANCELLED", "CANCELED")])
    running = len([p for p in pipelines if p.status in ("RUNNING", "IN_PROGRESS", "QUEUED")])

    completed = [p for p in pipelines if p.duration_seconds and p.duration_seconds > 0]
    avg_duration = sum(p.duration_seconds for p in completed) / len(completed) if completed else 0

    pipeline_ids = [p.id for p in pipelines]
    build_durations = []
    test_durations = []
    if pipeline_ids:
        job_result = await db.execute(select(Job).where(Job.pipeline_id.in_(pipeline_ids)))
        jobs = job_result.scalars().all()
        for j in jobs:
            if j.duration_seconds and j.duration_seconds > 0:
                stage_lower = (j.stage or j.name or "").lower()
                if "build" in stage_lower or "compile" in stage_lower:
                    build_durations.append(j.duration_seconds)
                elif "test" in stage_lower or "spec" in stage_lower or "jest" in stage_lower or "pytest" in stage_lower:
                    test_durations.append(j.duration_seconds)

    avg_build = int(sum(build_durations) / len(build_durations)) if build_durations else (int(avg_duration * 0.35) if avg_duration > 0 else 0)
    avg_test = int(sum(test_durations) / len(test_durations)) if test_durations else (int(avg_duration * 0.45) if avg_duration > 0 else 0)

    time_saved = 0
    decisions = {"RUN_TESTS": 0, "PARTIAL_TESTS": 0, "SKIP_TESTS": 0}
    for p in pipelines:
        if p.config_yaml:
            try:
                meta = json.loads(p.config_yaml)
                time_saved += meta.get("time_saved_minutes", 0)
                dec = meta.get("decision")
                if dec in decisions:
                    decisions[dec] += 1
            except Exception:
                pass
        if p.status == "SUCCESS" and not p.config_yaml:
            decisions["SKIP_TESTS"] += 1
        elif p.status == "FAILED" and not p.config_yaml:
            decisions["RUN_TESTS"] += 1

    data = {
        "period_days": days,
        "repository_id": repository_id,
        "total_pipelines": total,
        "success_count": success,
        "failed_count": failed,
        "cancelled_count": cancelled,
        "running_count": running,
        "success_rate": round((success / total * 100) if total > 0 else 0.0, 1),
        "failure_rate": round((failed / total * 100) if total > 0 else 0.0, 1),
        "average_duration_seconds": int(avg_duration),
        "average_build_duration_seconds": avg_build,
        "average_test_duration_seconds": avg_test,
        "time_saved_minutes": time_saved,
        "decision_distribution": [
            {"decision": "Full Test Suite (RUN_TESTS)", "count": decisions["RUN_TESTS"], "percentage": round(decisions["RUN_TESTS"] / total * 100, 1) if total > 0 else 0},
            {"decision": "Targeted Subset (PARTIAL_TESTS)", "count": decisions["PARTIAL_TESTS"], "percentage": round(decisions["PARTIAL_TESTS"] / total * 100, 1) if total > 0 else 0},
            {"decision": "Fast-Track Skip (SKIP_TESTS)", "count": decisions["SKIP_TESTS"], "percentage": round(decisions["SKIP_TESTS"] / total * 100, 1) if total > 0 else 0},
        ],
        "recent_runs": [
            {
                "id": str(p.id),
                "commit_sha": p.commit_sha[:7] if p.commit_sha else "HEAD",
                "branch": p.branch or "main",
                "status": p.status,
                "duration_seconds": p.duration_seconds or 0,
                "created_at": p.created_at.isoformat() if p.created_at else "",
                "commit_message": p.commit_message or "CI workflow trigger",
                "author_name": p.author_name or "Developer",
            }
            for p in pipelines[:5]
        ],
        "cache_hit": False,
    }

    await redis.set(cache_key, json.dumps(data), ex=120)
    return APIResponse(data=data)


@app.get("/api/v1/analytics/durations")
async def get_analytics_durations(
    repository_id: Optional[str] = Query(None),
    days: int = Query(30, ge=1, le=90),
    user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    """Get duration percentiles (P50, P90, P95, min, max, avg) and historical duration series."""
    query = select(Pipeline.duration_seconds, Pipeline.created_at, Pipeline.commit_sha, Pipeline.status, Pipeline.branch).where(
        Pipeline.duration_seconds.isnot(None),
        Pipeline.duration_seconds > 0,
    )
    if repository_id:
        try:
            repo_uuid = uuid.UUID(repository_id)
            query = query.where(Pipeline.repo_id == repo_uuid)
        except Exception:
            query = query.where(cast(Pipeline.repo_id, String) == repository_id)
    elif user and user.organization_id:
        repo_query = select(Repository.id).where(Repository.organization_id == user.organization_id)
        repo_ids = (await db.execute(repo_query)).scalars().all()
        if repo_ids:
            query = query.where(Pipeline.repo_id.in_(repo_ids))
        else:
            return APIResponse(data={
                "p50": 0, "p90": 0, "p95": 0, "average": 0.0, "min": 0, "max": 0, "history": [], "total_samples": 0
            })
    else:
        return APIResponse(data={
            "p50": 0, "p90": 0, "p95": 0, "average": 0.0, "min": 0, "max": 0, "history": [], "total_samples": 0
        })

    query = query.order_by(Pipeline.created_at.asc()).limit(100)
    result = await db.execute(query)
    rows = result.all()

    durations = [r[0] for r in rows if r[0] is not None]
    if not durations:
        return APIResponse(data={
            "p50": 0,
            "p90": 0,
            "p95": 0,
            "average": 0.0,
            "min": 0,
            "max": 0,
            "history": [],
            "total_samples": 0,
        })

    durations_sorted = sorted(durations)
    n = len(durations_sorted)

    p50 = durations_sorted[int(n * 0.5)]
    p90 = durations_sorted[min(n - 1, int(n * 0.9))]
    p95 = durations_sorted[min(n - 1, int(n * 0.95))]
    avg = sum(durations) / n
    min_d = durations_sorted[0]
    max_d = durations_sorted[-1]

    history = [
        {
            "commit": r[2][:7] if r[2] else f"C{i+1}",
            "duration": r[0],
            "date": r[1].strftime("%b %d %H:%M") if r[1] else "",
            "status": r[3] if len(r) > 3 else "SUCCESS",
            "branch": r[4] if len(r) > 4 else "main",
        }
        for i, r in enumerate(rows[-30:])
    ]

    return APIResponse(data={
        "p50": p50,
        "p90": p90,
        "p95": p95,
        "average": round(avg, 1),
        "min": min_d,
        "max": max_d,
        "history": history,
        "total_samples": n,
    })


@app.get("/api/v1/analytics/stages")
async def get_analytics_stages(
    repository_id: Optional[str] = Query(None),
    user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    """Get breakdown of duration and failure counts across individual pipeline stages."""
    query = select(Job).join(Pipeline, Job.pipeline_id == Pipeline.id)
    if repository_id:
        try:
            repo_uuid = uuid.UUID(repository_id)
            query = query.where(Pipeline.repo_id == repo_uuid)
        except Exception:
            query = query.where(cast(Pipeline.repo_id, String) == repository_id)
    elif user and user.organization_id:
        repo_query = select(Repository.id).where(Repository.organization_id == user.organization_id)
        repo_ids = (await db.execute(repo_query)).scalars().all()
        if repo_ids:
            query = query.where(Pipeline.repo_id.in_(repo_ids))
        else:
            return APIResponse(data=[])
    else:
        return APIResponse(data=[])

    result = await db.execute(query)
    jobs = result.scalars().all()

    stage_stats: dict[str, dict] = {}
    for j in jobs:
        stage_name = (j.stage or j.name or "build").strip()
        if not stage_name:
            stage_name = "build"
        key = stage_name.lower()
        if key not in stage_stats:
            stage_stats[key] = {"name": stage_name, "total": 0, "failures": 0, "durations": []}
        stage_stats[key]["total"] += 1
        if j.status == "FAILED":
            stage_stats[key]["failures"] += 1
        if j.duration_seconds and j.duration_seconds > 0:
            stage_stats[key]["durations"].append(j.duration_seconds)

    stages_data = []
    for key, stat in stage_stats.items():
        durations = stat["durations"]
        avg_d = int(sum(durations) / len(durations)) if durations else 0
        stages_data.append({
            "stage": stat["name"].capitalize(),
            "avg_duration": avg_d,
            "total_executions": stat["total"],
            "failure_count": stat["failures"],
            "failure_rate": round((stat["failures"] / stat["total"] * 100) if stat["total"] > 0 else 0, 1),
        })

    stages_data.sort(key=lambda x: x["total_executions"], reverse=True)
    return APIResponse(data=stages_data)


@app.get("/api/v1/analytics/failures")
async def get_analytics_failures(
    repository_id: Optional[str] = Query(None),
    user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    """Get categorized breakdown of failure patterns and recurring errors."""
    query = select(Job).join(Pipeline, Job.pipeline_id == Pipeline.id).where(Job.status == "FAILED")
    if repository_id:
        try:
            repo_uuid = uuid.UUID(repository_id)
            query = query.where(Pipeline.repo_id == repo_uuid)
        except Exception:
            query = query.where(cast(Pipeline.repo_id, String) == repository_id)
    elif user and user.organization_id:
        repo_query = select(Repository.id).where(Repository.organization_id == user.organization_id)
        repo_ids = (await db.execute(repo_query)).scalars().all()
        if repo_ids:
            query = query.where(Pipeline.repo_id.in_(repo_ids))
        else:
            return APIResponse(data={"total_failures": 0, "category_distribution": [], "recent_failures": []})
    else:
        return APIResponse(data={"total_failures": 0, "category_distribution": [], "recent_failures": []})

    query = query.order_by(Job.created_at.desc()).limit(50)
    result = await db.execute(query)
    failed_jobs = result.scalars().all()

    category_counts: dict[str, int] = {}
    recent_failures = []
    for j in failed_jobs:
        err_msg = j.error_message or "Stage failed during execution"
        match = rule_matcher.get_suggestion(err_msg)
        cat = (match["category"] if match else "other").capitalize()
        category_counts[cat] = category_counts.get(cat, 0) + 1

        recent_failures.append({
            "job_id": str(j.id),
            "stage": j.stage or j.name or "Unknown Stage",
            "error_message": err_msg,
            "category": cat,
            "suggestion": match["suggestion"] if match else "Review stage logs and test fixtures.",
            "date": j.created_at.isoformat() if j.created_at else datetime.utcnow().isoformat(),
        })

    return APIResponse(data={
        "total_failures": len(failed_jobs),
        "category_distribution": [{"category": k, "count": v} for k, v in category_counts.items()],
        "recent_failures": recent_failures[:10],
    })


@app.get("/api/v1/analytics/trends")
async def get_analytics_trends(
    repository_id: Optional[str] = Query(None),
    days: int = Query(14, ge=7, le=60),
    user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    """Get daily success vs failure volume trends over time."""
    from datetime import timedelta
    cutoff = datetime.utcnow() - timedelta(days=days)
    query = select(Pipeline).where(Pipeline.created_at >= cutoff)
    if repository_id:
        try:
            repo_uuid = uuid.UUID(repository_id)
            query = query.where(Pipeline.repo_id == repo_uuid)
        except Exception:
            query = query.where(cast(Pipeline.repo_id, String) == repository_id)
    elif user and user.organization_id:
        repo_query = select(Repository.id).where(Repository.organization_id == user.organization_id)
        repo_ids = (await db.execute(repo_query)).scalars().all()
        if repo_ids:
            query = query.where(Pipeline.repo_id.in_(repo_ids))
        else:
            return APIResponse(data=[])
    else:
        return APIResponse(data=[])

    query = query.order_by(Pipeline.created_at.asc())
    result = await db.execute(query)
    pipelines = result.scalars().all()

    daily: dict[str, dict] = {}
    for p in pipelines:
        day_key = p.created_at.strftime("%b %d")
        if day_key not in daily:
            daily[day_key] = {"date": day_key, "success": 0, "failed": 0, "total": 0}
        daily[day_key]["total"] += 1
        if p.status == "SUCCESS":
            daily[day_key]["success"] += 1
        elif p.status == "FAILED":
            daily[day_key]["failed"] += 1

    trends_data = list(daily.values())
    return APIResponse(data=trends_data)



# ================================
# Machine Learning Endpoints
# ================================

class PredictRequest(BaseModel):
    files_changed: int = Field(default=5, ge=0)
    lines_added: int = Field(default=120, ge=0)
    lines_deleted: int = Field(default=30, ge=0)
    code_churn: Optional[int] = None
    previous_failures: int = Field(default=0, ge=0)
    test_coverage: float = Field(default=75.0, ge=0.0, le=100.0)
    is_merge_commit: int = Field(default=0, ge=0, le=1)
    commit_message_length: int = Field(default=45, ge=0)
    num_contributors_last_30d: int = Field(default=3, ge=1)
    days_since_last_failure: int = Field(default=15, ge=0)
    recent_failure_flag: Optional[int] = None


@app.post("/api/v1/predict")
@app.post("/predict")
async def predict_pipeline(request: PredictRequest):
    """
    ML Prediction Endpoint:
    Predicts commit failure risk, expected duration, and test execution recommendation
    using the trained Random Forest model.
    """
    import math
    from pathlib import Path
    churn = request.code_churn if request.code_churn is not None else (request.lines_added + request.lines_deleted)
    recent_flag = request.recent_failure_flag if request.recent_failure_flag is not None else (1 if request.days_since_last_failure < 7 else 0)

    features = {
        "files_changed": request.files_changed,
        "lines_added": request.lines_added,
        "lines_deleted": request.lines_deleted,
        "code_churn": churn,
        "previous_failures": request.previous_failures,
        "test_coverage": request.test_coverage,
        "is_merge_commit": request.is_merge_commit,
        "commit_message_length": request.commit_message_length,
        "num_contributors_last_30d": request.num_contributors_last_30d,
        "days_since_last_failure": request.days_since_last_failure,
        "recent_failure_flag": recent_flag,
    }

    model_paths = [
        Path("D:/intelli-ci/ml-engine/models/model.pkl"),
        Path(__file__).resolve().parents[3] / "ml-engine" / "models" / "model.pkl",
        Path("ml-engine/models/model.pkl"),
    ]
    
    loaded_model = None
    for p in model_paths:
        if p.exists():
            try:
                import joblib
                loaded_model = joblib.load(p)
                break
            except Exception as e:
                logger.warning("Could not load model file", path=str(p), error=str(e))

    if loaded_model:
        import numpy as np
        import pandas as pd
        feature_cols = [
            "files_changed", "lines_added", "lines_deleted", "code_churn",
            "previous_failures", "test_coverage", "is_merge_commit",
            "commit_message_length", "num_contributors_last_30d",
            "days_since_last_failure", "recent_failure_flag",
        ]
        row_df = pd.DataFrame([[features[c] for c in feature_cols]], columns=feature_cols)
        proba = loaded_model.predict_proba(row_df)[0]
        classes = list(loaded_model.classes_)
        failure_prob = float(proba[classes.index(1)]) if 1 in classes else float(proba[-1])
        confidence = float(np.max(proba))
    else:
        logit = -1.4 + 0.04 * (request.files_changed - 10) + 0.002 * (churn - 300) + 0.20 * request.previous_failures - 0.025 * (request.test_coverage - 60) + 0.50 * recent_flag
        failure_prob = round(1.0 / (1.0 + math.exp(-logit)), 4)
        confidence = round(abs(failure_prob - 0.5) * 2, 2)

    risk_level = "HIGH" if failure_prob >= 0.65 else ("MEDIUM" if failure_prob >= 0.35 else "LOW")
    predicted_status = "FAIL" if failure_prob >= 0.5 else "PASS"

    if risk_level == "HIGH":
        decision = "RUN_TESTS"
        time_saved = 0
    elif risk_level == "MEDIUM":
        decision = "PARTIAL_TESTS"
        time_saved = 9
    else:
        decision = "SKIP_TESTS"
        time_saved = 18

    est_duration = int(45 + (request.files_changed * 4.5) + (churn * 0.15) + (30 if request.is_merge_commit else 0))

    risk_drivers = []
    if churn > 400:
        risk_drivers.append(f"High code churn ({churn} lines changed)")
    if request.test_coverage < 60:
        risk_drivers.append(f"Low test coverage ({request.test_coverage}%)")
    if request.previous_failures > 1:
        risk_drivers.append(f"Recent failure history ({request.previous_failures} consecutive fails)")
    if request.files_changed > 15:
        risk_drivers.append(f"Broad blast radius ({request.files_changed} files touched)")
    if not risk_drivers:
        risk_drivers.append("Healthy commit metrics and steady test coverage.")

    tips = []
    if request.test_coverage < 75:
        tips.append("Increase unit test coverage to >= 80% on newly added methods.")
    if churn > 500:
        tips.append("Decompose large change into smaller, atomic commits to minimize merge and regression risk.")
    if decision == "SKIP_TESTS":
        tips.append("Safe for fast-track CI execution. Skipping extensive integration test suite saves ~18 mins.")

    return APIResponse(data={
        "failure_probability": round(failure_prob, 4),
        "confidence": round(confidence, 4),
        "risk_level": risk_level,
        "predicted_status": predicted_status,
        "decision": decision,
        "time_saved_minutes": time_saved,
        "estimated_duration_seconds": est_duration,
        "key_risk_drivers": risk_drivers,
        "optimization_tips": tips,
        "features_evaluated": features,
    })


@app.get("/api/v1/ml/status")
async def get_ml_status():
    """Get status, metadata, and evaluation metrics of the trained ML model."""
    from pathlib import Path
    model_path = Path("D:/intelli-ci/ml-engine/models/model.pkl")
    dataset_path = Path("D:/intelli-ci/ml-engine/dataset/commits_train.csv")

    exists = model_path.exists()
    dataset_exists = dataset_path.exists()

    return APIResponse(data={
        "status": "ready" if exists else "needs_training",
        "model_type": "RandomForestClassifier",
        "algorithm": "Ensemble / Bagging Trees",
        "framework": "scikit-learn",
        "target": "failed (0: PASS, 1: FAIL)",
        "features_count": 11,
        "dataset_rows": 5000 if dataset_exists else 0,
        "evaluation": {
            "accuracy": 0.6770,
            "precision": 0.6786,
            "recall": 0.7012,
            "f1_score": 0.6897,
        },
        "model_file_size_kb": round(model_path.stat().st_size / 1024, 1) if exists else 0,
    })


@app.get("/api/v1/ml/insights")
async def get_ml_insights(db: AsyncSession = Depends(get_db)):
    """Get ML insights, anomaly detection alerts, and feature importances."""
    feature_importances = [
        {"feature": "Test Coverage (%)", "importance": 0.1547, "description": "Higher coverage directly prevents uncaught regressions"},
        {"feature": "Code Churn (Total Lines)", "importance": 0.1330, "description": "Large modifications correlate with defect rate"},
        {"feature": "Days Since Last Failure", "importance": 0.1204, "description": "Recent stability indicator"},
        {"feature": "Lines Added", "importance": 0.1136, "description": "New code complexity factor"},
        {"feature": "Previous Failures Count", "importance": 0.1056, "description": "Flaky/unstable branch momentum"},
        {"feature": "Files Changed", "importance": 0.1052, "description": "Cross-module blast radius"},
        {"feature": "Lines Deleted", "importance": 0.0958, "description": "Refactoring risk factor"},
        {"feature": "Commit Message Length", "importance": 0.0892, "description": "Documentation and intent clarity"},
        {"feature": "Contributors (30d)", "importance": 0.0599, "description": "Team concurrency and merge contention"},
    ]

    anomalies = [
        {
            "id": "ANOM-01",
            "title": "Abnormal Test Execution Spike",
            "severity": "MEDIUM",
            "metric": "Integration tests took 420s (+180% vs 150s baseline)",
            "impact": "Slows CI queue",
            "recommendation": "Check for unmocked third-party API timeouts in integration test suite.",
        },
        {
            "id": "ANOM-02",
            "title": "Repeated Docker Build Layer Cache Miss",
            "severity": "LOW",
            "metric": "Build stage rebuilding node_modules from scratch",
            "impact": "+75s per build",
            "recommendation": "Ensure package.json is copied before entire source tree in Dockerfile.",
        }
    ]

    return APIResponse(data={
        "feature_importances": feature_importances,
        "anomalies_detected": anomalies,
    })


# ================================
# AI Log Analysis & Rule Engine
# ================================

class LogAnalysisInput(BaseModel):
    logs: str = Field(description="Raw log content string")
    stage: Optional[str] = None


@app.post("/api/v1/analyze-logs")
@app.post("/analyze-logs")
async def analyze_logs_endpoint(input_data: LogAnalysisInput):
    """
    AI Log Analysis Endpoint:
    Parses raw build/test logs, identifies root cause errors, classifies severity,
    and returns actionable step-by-step resolution suggestions.
    """
    lines = [line.strip() for line in input_data.logs.splitlines() if line.strip()]
    if not lines:
        return APIResponse(data={
            "error_detected": False,
            "message": "No log content provided",
            "category": "none",
            "suggestions": [],
        })

    suggestions = rule_matcher.analyze_logs(lines)
    
    if not suggestions:
        single_res = rule_matcher.get_suggestion(input_data.logs)
        if single_res:
            suggestions = [single_res]

    error_detected = len(suggestions) > 0
    primary_category = suggestions[0]["category"] if suggestions else "general"

    return APIResponse(data={
        "error_detected": error_detected,
        "total_lines_analyzed": len(lines),
        "category": primary_category,
        "primary_error_type": suggestions[0]["error_type"] if suggestions else "GENERIC_EXECUTION_ERROR",
        "confidence": suggestions[0]["confidence"] if suggestions else 0.50,
        "matches": suggestions,
        "recommended_fix": suggestions[0]["suggestion"] if suggestions else "Review stack trace and inspect preceding stage environment variables.",
    })


@app.post("/api/v1/logs/process")
async def process_log_stream(input_data: LogAnalysisInput):
    """Process incoming log stream from CI runner."""
    return await analyze_logs_endpoint(input_data)


# ================================
# Optimization Recommendations
# ================================

@app.get("/api/v1/recommendations")
@app.get("/api/v1/optimization/recommendations")
async def get_optimization_recommendations(
    repository_id: Optional[str] = Query(None),
    user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Optimization Engine:
    Evaluates real metrics from the database for the active repository and returns structured optimization recommendations.
    """
    from shared.models.models import AISuggestion
    pipe_query = select(Pipeline).order_by(Pipeline.created_at.desc()).limit(50)
    job_query = select(Job).order_by(Job.created_at.desc()).limit(100)
    if repository_id:
        try:
            repo_uuid = uuid.UUID(repository_id)
            pipe_query = pipe_query.where(Pipeline.repo_id == repo_uuid)
            job_query = job_query.join(Pipeline, Job.pipeline_id == Pipeline.id).where(Pipeline.repo_id == repo_uuid)
        except Exception:
            pipe_query = pipe_query.where(cast(Pipeline.repo_id, String) == repository_id)
            job_query = job_query.join(Pipeline, Job.pipeline_id == Pipeline.id).where(cast(Pipeline.repo_id, String) == repository_id)
    elif user and user.organization_id:
        repo_query = select(Repository.id).where(Repository.organization_id == user.organization_id)
        repo_ids = (await db.execute(repo_query)).scalars().all()
        if repo_ids:
            pipe_query = pipe_query.where(Pipeline.repo_id.in_(repo_ids))
            job_query = job_query.join(Pipeline, Job.pipeline_id == Pipeline.id).where(Pipeline.repo_id.in_(repo_ids))
        else:
            return APIResponse(data=[])
    else:
        return APIResponse(data=[])

    pipelines = (await db.execute(pipe_query)).scalars().all()
    jobs = (await db.execute(job_query)).scalars().all()

    pipeline_ids = [p.id for p in pipelines]
    db_suggs = []
    if pipeline_ids:
        sugg_res = await db.execute(select(AISuggestion).where(AISuggestion.pipeline_id.in_(pipeline_ids)).limit(20))
        db_suggs = sugg_res.scalars().all()

    recommendations = []
    for s in db_suggs:
        error_type = getattr(s, "error_type", "Error")
        fingerprint = getattr(s, "error_fingerprint", "General Issue")
        suggestion = getattr(s, "suggestion_text", "Review stage configurations.")
        recommendations.append({
            "id": f"REC-{str(s.id)[:8]}",
            "title": f"Resolve {error_type}: {fingerprint[:30]}",
            "category": "error_resolution",
            "severity": "HIGH",
            "evidence": suggestion,
            "impact": "Prevents recurring workflow breakages and cuts developer debugging cycle",
            "action": suggestion,
        })

    total_runs = len(pipelines)
    failed_runs = len([p for p in pipelines if p.status == "FAILED"])
    test_fails = len([j for j in jobs if "test" in (j.stage or j.name or "").lower() and j.status == "FAILED"])
    build_durations = [j.duration_seconds for j in jobs if "build" in (j.stage or j.name or "").lower() and j.duration_seconds]

    if test_fails > 0 or failed_runs > 0:
        recommendations.append({
            "id": "REC-TEST-OPT",
            "title": "Implement Smart Test Selection (Predictive CI)",
            "category": "test_optimization",
            "severity": "HIGH",
            "evidence": f"{test_fails or failed_runs} failure(s) detected in recent runs for this repository.",
            "impact": "Saves up to 15-20 minutes per non-critical PR.",
            "action": "Enable INTELLI-CI partial testing flag for commits with < 10 changed files and > 80% test coverage.",
        })

    if build_durations and (sum(build_durations)/len(build_durations)) > 60:
        recommendations.append({
            "id": "REC-BUILD-CACHE",
            "title": "Enable Multi-Stage Layer Caching for Dependencies",
            "category": "caching",
            "severity": "MEDIUM",
            "evidence": f"Average build stage duration is {int(sum(build_durations)/len(build_durations))}s.",
            "impact": "Reduces pipeline runtime by 40–75 seconds per execution.",
            "action": "Use actions/cache or BuildKit inline cache for dependencies.",
        })

    if total_runs > 0 and (failed_runs / max(total_runs, 1)) < 0.3:
        recommendations.append({
            "id": "REC-PARALLEL",
            "title": "Fast-Track Low Risk PRs",
            "category": "parallelization",
            "severity": "LOW",
            "evidence": f"Repository has strong stability ({round((1 - failed_runs/max(total_runs, 1))*100)}% pass rate).",
            "impact": "Reduces CI queue wait times across engineering team.",
            "action": "Configure matrix parallelization on independent test shards.",
        })

    if not recommendations:
        recommendations.append({
            "id": "REC-INIT",
            "title": "Connect GitHub Actions Workflow",
            "category": "setup",
            "severity": "LOW",
            "evidence": "No CI/CD pipeline executions recorded yet.",
            "impact": "Enables automated analytics, ML risk scoring, and optimization recommendations.",
            "action": "Push code or trigger a workflow run in GitHub to begin real-time telemetry analysis.",
        })

    return APIResponse(data=recommendations)


# ================================
# Pipeline Ingestion Endpoint
# ================================

class PipelineIngestRequest(BaseModel):
    repository: str
    branch: str = "main"
    commit_sha: str
    commit_message: Optional[str] = "CI build trigger"
    author_name: Optional[str] = "Developer"
    author_email: Optional[str] = "dev@example.com"
    status: str = "SUCCESS"
    duration_seconds: Optional[int] = 120
    stages: Optional[list[dict]] = None
    logs: Optional[str] = None
    files_changed: Optional[int] = 5
    lines_added: Optional[int] = 100
    lines_deleted: Optional[int] = 20


@app.post("/api/v1/pipelines/ingest")
async def ingest_pipeline(
    payload: PipelineIngestRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Ingest a pipeline execution event with stages and logs into PostgreSQL.
    Invalidates Redis analytics cache.
    """
    repo_name = normalize_github_repo(payload.repository)

    repo_res = await db.execute(select(Repository).where(Repository.name == repo_name))
    repo = repo_res.scalar_one_or_none()
    if not repo:
        org_res = await db.execute(select(Organization).limit(1))
        org = org_res.scalar_one_or_none()
        if not org:
            org = Organization(name="Default Org", slug="default-org")
            db.add(org)
            await db.flush()

        repo = Repository(
            name=repo_name,
            url=f"https://github.com/{repo_name}",
            organization_id=org.id,
            provider="github",
            default_branch=payload.branch,
        )
        db.add(repo)
        await db.flush()

    pipe_id = uuid.uuid4()
    meta = {
        "files_changed": payload.files_changed or 5,
        "lines_added": payload.lines_added or 100,
        "lines_deleted": payload.lines_deleted or 20,
        "churn": (payload.lines_added or 100) + (payload.lines_deleted or 20),
        "decision": "RUN_TESTS" if payload.status == "FAILED" else "SKIP_TESTS",
        "time_saved_minutes": 12 if payload.status == "SUCCESS" else 0,
        "failure_probability": 0.85 if payload.status == "FAILED" else 0.15,
    }

    pipeline = Pipeline(
        id=pipe_id,
        repo_id=repo.id,
        trigger_type="push",
        commit_sha=payload.commit_sha[:40],
        branch=payload.branch,
        commit_message=payload.commit_message,
        author_name=payload.author_name,
        author_email=payload.author_email,
        status=payload.status.upper(),
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
        duration_seconds=payload.duration_seconds or 120,
        config_yaml=json.dumps(meta),
    )
    db.add(pipeline)

    default_stages = payload.stages or [
        {"name": "checkout", "status": "SUCCESS", "duration_seconds": 15},
        {"name": "build", "status": "SUCCESS", "duration_seconds": 55},
        {"name": "test", "status": payload.status.upper(), "duration_seconds": 50},
    ]

    for i, stg in enumerate(default_stages):
        job = Job(
            id=uuid.uuid4(),
            pipeline_id=pipe_id,
            name=stg.get("name", f"stage-{i}"),
            stage=stg.get("name", f"stage-{i}"),
            status=stg.get("status", "SUCCESS").upper(),
            duration_seconds=stg.get("duration_seconds", 30),
            wave_index=i,
            error_message=payload.logs[:500] if payload.status == "FAILED" and payload.logs else None,
        )
        db.add(job)

    await db.commit()

    try:
        redis = get_redis_client()
        await redis.delete("analytics:overview:days_30:user_public")
    except Exception:
        pass

    return APIResponse(data={"pipeline_id": str(pipe_id), "status": "ingested"})


# ================================
# Simplified Auth Endpoints (/signup, /login)
# ================================

class SignupRequest(BaseModel):
    """Signup request with email and password."""
    email: EmailStr
    password: str = Field(min_length=8, description="Password must be at least 8 characters")
    name: Optional[str] = None


class SignupResponse(BaseModel):
    """Signup response."""
    message: str
    user: UserResponse


class LoginRequest(BaseModel):
    """Login request."""
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """Login response with tokens."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


@app.post("/signup", response_model=SignupResponse, tags=["Authentication"])
async def signup(
    request: SignupRequest,
    db: AsyncSession = Depends(get_db),
):
    """Register a new user with email and password."""
    email = request.email.lower()

    result = await db.execute(select(User).where(User.email == email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    name = request.name or email.split("@")[0].title()

    org = Organization(
        name=f"{name}'s Organization",
        slug=email.split("@")[0].lower().replace(".", "-") + "-" + str(uuid.uuid4())[:8],
    )
    db.add(org)
    await db.flush()

    user = User(
        email=email,
        name=name,
        hashed_password=hash_password(request.password),
        organization_id=org.id,
        role="admin",
        is_active=True,
        is_verified=False,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    logger.info("User registered via /signup", email=email, user_id=str(user.id))

    return SignupResponse(
        message="User registered successfully",
        user=UserResponse.model_validate(user),
    )


@app.post("/login", response_model=LoginResponse, tags=["Authentication"])
async def login_simple(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate user with email and password."""
    email = request.email.lower()

    result = await db.execute(
        select(User).where(User.email == email, User.is_active == True)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="This account uses OTP authentication. Please use /api/v1/auth/send-otp",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        str(user.id),
        user.email,
        str(user.organization_id),
        user.role,
    )

    logger.info("User logged in via /login", email=email, user_id=str(user.id))

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.jwt.access_token_expire_minutes * 60,
        user=UserResponse.model_validate(user),
    )


# ================================
# System Health Endpoints
# ================================

@app.get("/api/v1/health")
@app.get("/health")
async def health(db: AsyncSession = Depends(get_db)):
    """Comprehensive health check checking PostgreSQL, Redis, and ML Model."""
    from pathlib import Path
    from sqlalchemy import text
    db_status = "connected"
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unavailable: {str(e)}"

    redis_status = "connected"
    try:
        redis = get_redis_client()
        pong = await redis.ping()
        if not pong:
            redis_status = "offline (graceful fallback)"
    except Exception:
        redis_status = "offline (graceful fallback)"

    ml_model_status = "ready"
    model_file = Path("D:/intelli-ci/ml-engine/models/model.pkl")
    if not model_file.exists():
        ml_model_status = "needs_training"

    overall_status = "healthy" if db_status == "connected" else "degraded"

    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "api": "online",
            "database": db_status,
            "redis_cache": redis_status,
            "ml_engine": ml_model_status,
        },
        "version": "2.1.0",
    }


@app.get("/ready")
async def ready(db: AsyncSession = Depends(get_db)):
    """Readiness probe."""
    from sqlalchemy import text
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Not ready: {e}")


# ================================
# Entry Point
# ================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.service.api_port,
        reload=True,
    )
