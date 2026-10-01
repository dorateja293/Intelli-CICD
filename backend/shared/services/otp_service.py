"""
OTP Service Module

Provides secure OTP generation, storage, and validation.
"""

import secrets
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models import OTP


class OTPService:
    """Service for OTP operations."""

    OTP_LENGTH = 6
    DEFAULT_EXPIRY_MINUTES = 5
    MAX_ATTEMPTS = 5

    def __init__(
        self,
        expiry_minutes: int = DEFAULT_EXPIRY_MINUTES,
        max_attempts: int = MAX_ATTEMPTS,
    ):
        """Initialize OTP service.

        Args:
            expiry_minutes: OTP validity duration in minutes
            max_attempts: Maximum verification attempts allowed
        """
        self.expiry_minutes = expiry_minutes
        self.max_attempts = max_attempts

    def generate_otp(self) -> str:
        """Generate a secure 6-digit OTP.

        Returns:
            6-digit OTP string
        """
        return "".join(secrets.choice("0123456789") for _ in range(self.OTP_LENGTH))

    async def create_otp(self, db: AsyncSession, email: str) -> str:
        """Create and store a new OTP for the given email.

        Args:
            db: Database session
            email: User's email address

        Returns:
            Generated OTP code
        """
        # Delete any existing OTPs for this email
        await db.execute(delete(OTP).where(OTP.email == email.lower()))

        # Generate new OTP
        otp_code = self.generate_otp()
        expires_at = datetime.utcnow() + timedelta(minutes=self.expiry_minutes)

        # Store OTP
        otp_record = OTP(
            email=email.lower(),
            otp_code=otp_code,
            expires_at=expires_at,
            attempts=0,
            is_verified=False,
        )
        db.add(otp_record)
        await db.commit()

        return otp_code

    async def verify_otp(
        self,
        db: AsyncSession,
        email: str,
        otp_code: str,
    ) -> tuple[bool, str]:
        """Verify the OTP for the given email.

        Args:
            db: Database session
            email: User's email address
            otp_code: OTP code to verify

        Returns:
            Tuple of (success: bool, message: str)
        """
        # Find OTP record
        result = await db.execute(
            select(OTP).where(OTP.email == email.lower())
        )
        otp_record = result.scalar_one_or_none()

        if not otp_record:
            return False, "No OTP found for this email. Please request a new OTP."

        # Check if already verified
        if otp_record.is_verified:
            return False, "OTP already used. Please request a new OTP."

        # Check expiry
        if datetime.utcnow() > otp_record.expires_at:
            return False, "OTP has expired. Please request a new OTP."

        # Check attempts
        if otp_record.attempts >= self.max_attempts:
            return False, f"Maximum attempts ({self.max_attempts}) exceeded. Please request a new OTP."

        # Increment attempts
        otp_record.attempts += 1

        # Verify OTP
        if otp_record.otp_code != otp_code:
            remaining = self.max_attempts - otp_record.attempts
            await db.commit()
            return False, f"Invalid OTP. {remaining} attempts remaining."

        # Mark as verified
        otp_record.is_verified = True
        await db.commit()

        return True, "OTP verified successfully."

    async def get_otp_status(
        self,
        db: AsyncSession,
        email: str,
    ) -> Optional[dict]:
        """Get OTP status for the given email.

        Args:
            db: Database session
            email: User's email address

        Returns:
            OTP status dict or None if no OTP exists
        """
        result = await db.execute(
            select(OTP).where(OTP.email == email.lower())
        )
        otp_record = result.scalar_one_or_none()

        if not otp_record:
            return None

        return {
            "email": otp_record.email,
            "expires_at": otp_record.expires_at.isoformat(),
            "attempts": otp_record.attempts,
            "max_attempts": self.max_attempts,
            "is_verified": otp_record.is_verified,
            "is_expired": datetime.utcnow() > otp_record.expires_at,
        }

    async def cleanup_expired(self, db: AsyncSession) -> int:
        """Clean up expired OTPs.

        Args:
            db: Database session

        Returns:
            Number of deleted records
        """
        result = await db.execute(
            delete(OTP).where(OTP.expires_at < datetime.utcnow())
        )
        await db.commit()
        return result.rowcount


# Default instance
otp_service = OTPService()
