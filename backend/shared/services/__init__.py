"""Shared services module."""

from shared.services.otp_service import OTPService
from shared.services.email_service import EmailService

__all__ = [
    "OTPService",
    "EmailService",
]
