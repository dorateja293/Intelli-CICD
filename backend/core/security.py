import asyncio
import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt as _bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from backend.core.config import Settings, get_settings

bearer_scheme = HTTPBearer(auto_error=False)


# ── Password helpers ──────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    return _bcrypt.hashpw(plain.encode("utf-8"), _bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return _bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


async def hash_password_async(plain: str) -> str:
    """Off-load bcrypt (CPU-blocking) to a thread pool to avoid blocking the event loop."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, hash_password, plain)


async def verify_password_async(plain: str, hashed: str) -> bool:
    """Off-load bcrypt verify (CPU-blocking) to a thread pool."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, verify_password, plain, hashed)


# ── JWT ───────────────────────────────────────────────────────────────────────

def create_access_token(subject: str, settings: Settings) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {"sub": subject, "exp": expire, "iat": datetime.now(timezone.utc)}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str, settings: Settings) -> dict:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    settings: Settings = Depends(get_settings),
) -> str:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    payload = decode_access_token(credentials.credentials, settings)
    uid: Optional[str] = payload.get("sub")
    if uid is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    return uid


# ── GitHub webhook signature verification ────────────────────────────────────

def verify_github_signature(payload_body: bytes, signature_header: str, secret: str) -> bool:
    """Verify X-Hub-Signature-256 header from GitHub webhook."""
    if not secret:
        return True  # No secret configured — allow (dev mode)
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    expected = hmac.new(secret.encode(), payload_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature_header)


# ── Timing-safe token comparison ─────────────────────────────────────────────

def constant_time_compare(a: str, b: str) -> bool:
    return hmac.compare_digest(a.encode(), b.encode())
