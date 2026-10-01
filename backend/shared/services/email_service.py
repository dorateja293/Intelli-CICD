"""
Email Service Module

Provides email sending functionality for OTP delivery.
"""

import asyncio
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

import structlog

logger = structlog.get_logger()


class EmailService:
    """Service for sending emails."""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        username: str,
        password: str,
        from_address: str,
    ):
        """Initialize email service.

        Args:
            smtp_host: SMTP server hostname
            smtp_port: SMTP server port
            username: SMTP username (email)
            password: SMTP password (app password for Gmail)
            from_address: Sender email address
        """
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_address = from_address

    def _create_otp_email(self, to_email: str, otp: str) -> MIMEMultipart:
        """Create OTP email message.

        Args:
            to_email: Recipient email address
            otp: OTP code

        Returns:
            Email message object
        """
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Your Intelli-CI Verification Code"
        msg["From"] = self.from_address
        msg["To"] = to_email

        # Plain text version
        text = f"""
Your Intelli-CI Verification Code

Your verification code is: {otp}

This code will expire in 5 minutes.

If you didn't request this code, please ignore this email.

Best regards,
Intelli-CI Team
"""

        # HTML version
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
        .content {{ background: #f9f9f9; padding: 30px; border: 1px solid #ddd; border-top: none; }}
        .otp-code {{ font-size: 36px; font-weight: bold; letter-spacing: 8px; color: #667eea; text-align: center; padding: 20px; background: white; border-radius: 8px; margin: 20px 0; }}
        .footer {{ font-size: 12px; color: #666; text-align: center; margin-top: 20px; }}
        .warning {{ font-size: 14px; color: #e74c3c; margin-top: 15px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Intelli-CI</h1>
            <p>Email Verification</p>
        </div>
        <div class="content">
            <p>Hello,</p>
            <p>Your verification code is:</p>
            <div class="otp-code">{otp}</div>
            <p>This code will expire in <strong>5 minutes</strong>.</p>
            <p class="warning">If you didn't request this code, please ignore this email.</p>
        </div>
        <div class="footer">
            <p>&copy; 2024 Intelli-CI. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""

        msg.attach(MIMEText(text, "plain"))
        msg.attach(MIMEText(html, "html"))

        return msg

    async def send_otp_email(self, to_email: str, otp: str) -> tuple[bool, str]:
        """Send OTP email asynchronously.

        Args:
            to_email: Recipient email address
            otp: OTP code to send

        Returns:
            Tuple of (success: bool, message: str)
        """
        # Run SMTP in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._send_email_sync,
            to_email,
            otp,
        )

    def _send_email_sync(self, to_email: str, otp: str) -> tuple[bool, str]:
        """Send email synchronously (called from thread pool).

        Args:
            to_email: Recipient email address
            otp: OTP code

        Returns:
            Tuple of (success: bool, message: str)
        """
        if not self.username or not self.password:
            logger.warning("Email credentials not configured, OTP not sent", email=to_email)
            # For development, just log the OTP
            logger.info("OTP for development", email=to_email, otp=otp)
            return True, f"[DEV MODE] OTP: {otp} (Email not configured)"

        try:
            msg = self._create_otp_email(to_email, otp)

            # Create secure SSL context
            context = ssl.create_default_context()

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.username, self.password)
                server.sendmail(self.from_address, to_email, msg.as_string())

            logger.info("OTP email sent successfully", email=to_email)
            return True, "OTP sent successfully"

        except smtplib.SMTPAuthenticationError as e:
            logger.error("SMTP authentication failed", error=str(e))
            return False, "Email authentication failed. Please check SMTP credentials."

        except smtplib.SMTPRecipientsRefused as e:
            logger.error("Recipient refused", email=to_email, error=str(e))
            return False, "Invalid email address"

        except smtplib.SMTPException as e:
            logger.error("SMTP error", error=str(e))
            return False, f"Failed to send email: {str(e)}"

        except Exception as e:
            logger.error("Unexpected error sending email", error=str(e))
            return False, f"Failed to send email: {str(e)}"


def get_email_service() -> EmailService:
    """Get email service instance with settings from environment."""
    from config.settings import get_settings
    settings = get_settings()

    return EmailService(
        smtp_host=settings.smtp.host,
        smtp_port=settings.smtp.port,
        username=settings.smtp.username,
        password=settings.smtp.password,
        from_address=settings.smtp.from_address,
    )
