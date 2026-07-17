from __future__ import annotations

from config import settings
from email_service.client import send_email
from email_service.templates import (
    password_reset_email,
    verification_email,
    welcome_email,
)


async def send_verification_email( *, to: str, display_name: str, raw_token: str ) -> None:
    """
    Sends a verification email to a user.
    Parameters:
        to (str): Address to send the email to.
        display_name (str): The display name to use in the email.
        raw_token (str): The unhashed email verification token.
    """
    subject, html, text = verification_email( display_name=display_name, raw_token=raw_token )
    await send_email( sender=settings.resend_verify_email, to=to, subject=subject, html=html, text=text )


async def send_password_reset_email( *, to: str, display_name: str, raw_token: str ) -> None:
    """
    Sends a password reset email to a user.
    Parameters:
        to (str): Address to send the email to.
        display_name (str): The display name to use in the email.
        raw_token (str): The unhashed password reset token.
    """
    subject, html, text = password_reset_email( display_name=display_name, raw_token=raw_token )
    await send_email( sender=settings.resend_recovery_email, to=to, subject=subject, html=html, text=text )


async def send_welcome_email( *, to: str, display_name: str ) -> None:
    """
    Sends a welcome email to a newly verified user.
    Parameters:
        to (str): Address to send the email to.
        display_name (str): The display name to use in the email.
    """
    subject, html, text = welcome_email( display_name=display_name )
    await send_email( sender=settings.resend_onboarding_email, to=to, subject=subject, html=html, text=text )
