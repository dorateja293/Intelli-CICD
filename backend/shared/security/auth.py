"""
Security Module

JWT authentication, password hashing, and RBAC utilities.
"""

import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Any, Optional

import structlog
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import get_settings
from shared.database import get_db
from shared.models import RefreshToken, User

logger = structlog.get_logger()
settings = get_settings()

# Direct bcrypt implementation (immune to passlib's bcrypt >= 4.0 / Python 3.14 wrap-bug detector crash)
import bcrypt

def hash_password(password: str) -> str:
    """Hash a password using bcrypt directly."""
    pwd_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a bcrypt hash."""
    try:
        pwd_bytes = plain_password.encode("utf-8")[:72]
        hash_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(pwd_bytes, hash_bytes)
    except Exception as e:
        logger.warning("Password verification failed", error=str(e))
        return False


# Bearer token scheme
bearer_scheme = HTTPBearer()


# ================================
# JWT Utilities

# ================================

def create_access_token(
    user_id: str,
    email: str,
    org_id: str,
    role: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a JWT access token."""
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.jwt.access_token_expire_minutes)

    expire = datetime.utcnow() + expires_delta
    payload = {
        "sub": user_id,
        "email": email,
        "org_id": org_id,
        "role": role,
        "type": "access",
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, settings.jwt.secret_key, algorithm=settings.jwt.algorithm)


def create_refresh_token(user_id: str) -> tuple[str, str, datetime]:
    """
    Create a refresh token.
    Returns (token, token_hash, expires_at).
    """
    expires_at = datetime.utcnow() + timedelta(days=settings.jwt.refresh_token_expire_days)
    payload = {
        "sub": user_id,
        "type": "refresh",
        "exp": expires_at,
        "iat": datetime.utcnow(),
        "jti": str(uuid.uuid4()),  # unique ID
    }
    token = jwt.encode(payload, settings.jwt.secret_key, algorithm=settings.jwt.algorithm)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    return token, token_hash, expires_at


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt.secret_key,
            algorithms=[settings.jwt.algorithm],
        )
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ================================
# Token Claims Model
# ================================

class TokenClaims:
    """Decoded JWT token claims."""

    def __init__(self, payload: dict[str, Any]):
        self.user_id = payload.get("sub")
        self.email = payload.get("email")
        self.org_id = payload.get("org_id")
        self.role = payload.get("role")
        self.token_type = payload.get("type")
        self.exp = payload.get("exp")
        self.iat = payload.get("iat")


# ================================
# Auth Dependencies
# ================================

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Get current authenticated user from JWT token."""
    token = credentials.credentials

    payload = decode_token(token)

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    result = await db.execute(
        select(User).where(User.id == uuid.UUID(user_id), User.is_active == True)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    return user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    ),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """Get current user if authenticated, None otherwise."""
    if not credentials:
        return None
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None


# ================================
# Role-Based Access Control
# ================================

ROLE_PERMISSIONS = {
    "admin": {
        "read:*",
        "write:*",
        "delete:*",
        "manage:users",
        "manage:organization",
        "manage:security_policy",
        "suppress:findings",
    },
    "developer": {
        "read:pipelines",
        "read:jobs",
        "read:logs",
        "read:security",
        "read:suggestions",
        "write:pipelines",
        "cancel:pipelines",
        "retry:jobs",
    },
    "viewer": {
        "read:pipelines",
        "read:jobs",
        "read:logs",
        "read:security",
        "read:suggestions",
    },
}


def has_permission(role: str, permission: str) -> bool:
    """Check if role has the required permission."""
    role_perms = ROLE_PERMISSIONS.get(role, set())

    # Check for wildcard permissions
    if "read:*" in role_perms and permission.startswith("read:"):
        return True
    if "write:*" in role_perms and permission.startswith("write:"):
        return True
    if "delete:*" in role_perms and permission.startswith("delete:"):
        return True

    return permission in role_perms


class RequirePermission:
    """Dependency factory for permission checking."""

    def __init__(self, permission: str):
        self.permission = permission

    async def __call__(self, user: User = Depends(get_current_user)) -> User:
        if not has_permission(user.role, self.permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {self.permission}",
            )
        return user


def require_permission(permission: str) -> RequirePermission:
    """Create a permission requirement dependency."""
    return RequirePermission(permission)


class RequireRole:
    """Dependency factory for role checking."""

    def __init__(self, *roles: str):
        self.roles = roles

    async def __call__(self, user: User = Depends(get_current_user)) -> User:
        if user.role not in self.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role required: {', '.join(self.roles)}",
            )
        return user


def require_role(*roles: str) -> RequireRole:
    """Create a role requirement dependency."""
    return RequireRole(*roles)


# ================================
# Resource Authorization
# ================================

async def authorize_resource(
    user: User,
    resource_org_id: uuid.UUID,
    permission: str,
) -> None:
    """
    Check if user can access a resource in an organization.
    Raises HTTPException if unauthorized.
    """
    if user.organization_id != resource_org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: resource belongs to different organization",
        )

    if not has_permission(user.role, permission):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied: {permission}",
        )


# ================================
# Refresh Token Management
# ================================

async def store_refresh_token(
    db: AsyncSession,
    user_id: uuid.UUID,
    token_hash: str,
    expires_at: datetime,
) -> RefreshToken:
    """Store refresh token in database."""
    refresh_token = RefreshToken(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at,
    )
    db.add(refresh_token)
    await db.commit()
    return refresh_token


async def validate_refresh_token(
    db: AsyncSession,
    token: str,
) -> Optional[User]:
    """Validate refresh token and return associated user."""
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked == False,
            RefreshToken.expires_at > datetime.utcnow(),
        )
    )
    refresh_token = result.scalar_one_or_none()

    if not refresh_token:
        return None

    result = await db.execute(
        select(User).where(User.id == refresh_token.user_id, User.is_active == True)
    )
    return result.scalar_one_or_none()


async def revoke_refresh_token(db: AsyncSession, token: str) -> bool:
    """Revoke a refresh token."""
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    refresh_token = result.scalar_one_or_none()

    if refresh_token:
        refresh_token.revoked = True
        refresh_token.revoked_at = datetime.utcnow()
        await db.commit()
        return True

    return False
