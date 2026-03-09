"""
GET  /profile          — Fetch current user's profile.
PUT  /profile          — Update current user's name.
PUT  /profile/password — Change password.
POST /connect-repository — Link a GitHub repository to the current user.
GET  /repositories     — List repositories linked to the authenticated user.
DELETE /repositories/{repo_id} — Remove a connected repository.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.security import (
    get_current_user_id,
    hash_password_async,
    verify_password_async,
)
from backend.database.connection import get_db
from backend.models.repository import Repository
from backend.models.user import User

router = APIRouter(tags=["profile"])


# ─── Schemas ──────────────────────────────────────────────────────────────────

class UpdateProfileRequest(BaseModel):
    name: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class ConnectRepositoryRequest(BaseModel):
    full_name: str           # "owner/repo"
    default_branch: str = "main"
    description: str = ""


# ─── Profile ──────────────────────────────────────────────────────────────────

@router.get("/profile")
async def get_profile(
    db: AsyncSession = Depends(get_db),
    uid: str = Depends(get_current_user_id),
):
    result = await db.execute(select(User).where(User.id == uid))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "id": str(user.id),
        "name": user.name,
        "email": user.email,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "updated_at": user.updated_at.isoformat() if user.updated_at else None,
    }


@router.put("/profile")
async def update_profile(
    body: UpdateProfileRequest,
    db: AsyncSession = Depends(get_db),
    uid: str = Depends(get_current_user_id),
):
    name = body.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Name cannot be empty")

    result = await db.execute(select(User).where(User.id == uid))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.name = name
    await db.commit()
    await db.refresh(user)
    return {
        "id": str(user.id),
        "name": user.name,
        "email": user.email,
        "updated_at": user.updated_at.isoformat() if user.updated_at else None,
    }


@router.put("/profile/password")
async def change_password(
    body: ChangePasswordRequest,
    db: AsyncSession = Depends(get_db),
    uid: str = Depends(get_current_user_id),
):
    if len(body.new_password) < 8:
        raise HTTPException(status_code=400, detail="New password must be at least 8 characters")

    result = await db.execute(select(User).where(User.id == uid))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not await verify_password_async(body.current_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    user.hashed_password = await hash_password_async(body.new_password)
    await db.commit()
    return {"message": "Password changed successfully"}


# ─── Repositories ─────────────────────────────────────────────────────────────

@router.post("/connect-repository", status_code=status.HTTP_201_CREATED)
async def connect_repository(
    body: ConnectRepositoryRequest,
    db: AsyncSession = Depends(get_db),
    uid: str = Depends(get_current_user_id),
):
    full_name = body.full_name.strip()
    if "/" not in full_name:
        raise HTTPException(status_code=400, detail="full_name must be in 'owner/repo' format")

    # Check if already linked for this user
    existing = await db.execute(
        select(Repository).where(
            Repository.full_name == full_name,
            Repository.owner_id == uid,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Repository already connected")

    # Use synthetic ID for manually connected repos (webhook uses GitHub repo ID)
    github_repo_id = f"manual-{uuid.uuid4().hex[:16]}"

    repo = Repository(
        github_repo_id=github_repo_id,
        full_name=full_name,
        default_branch=body.default_branch,
        description=body.description,
        owner_id=uid,
    )
    db.add(repo)
    await db.commit()
    await db.refresh(repo)

    return {
        "id": str(repo.id),
        "full_name": repo.full_name,
        "default_branch": repo.default_branch,
        "description": repo.description,
        "created_at": repo.created_at.isoformat() if repo.created_at else None,
    }


@router.delete("/repositories/{repo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_repository(
    repo_id: str,
    db: AsyncSession = Depends(get_db),
    uid: str = Depends(get_current_user_id),
):
    """Remove a connected repository owned by the current user."""
    try:
        repo_uuid = uuid.UUID(repo_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid repository ID")

    result = await db.execute(
        select(Repository).where(Repository.id == repo_uuid, Repository.owner_id == uid)
    )
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    await db.delete(repo)
    await db.commit()
