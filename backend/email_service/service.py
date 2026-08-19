from __future__ import annotations

from config import settings
from email_service.client import send_email
from email_service.templates import (
    change_email_verification_email,
    email_changed_email,
    password_reset_email,
    retention_warning_email,
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

async def send_retention_warning_email( *, to: str, display_name: str, download_url, deletion_date: str ) -> None:
    """
    Sends a deletion warning email to a user.
    Parameters:
        to (str): Address to send the email to.
        display_name (str): The display name to use in the email.
        download_url (str): The link to the download.
    """
    subject, html, text = retention_warning_email( display_name=display_name, download_url=download_url, deletion_date=deletion_date )
    await send_email( sender=settings.resend_general_email, to=to, subject=subject, html=html, text=text )

async def send_change_email_verification_email( *, to: str, display_name: str, raw_token: str ) -> None:
    """
    Sends a verification email to a user.
    Parameters:
        to (str): Address to send the email to.
        display_name (str): The display name to use in the email.
        raw_token (str): The unhashed email verification token.
    """
    subject, html, text = change_email_verification_email( display_name=display_name, raw_token=raw_token )
    await send_email( sender=settings.resend_verify_email, to=to, subject=subject, html=html, text=text )

async def send_email_changed_email( *, to: str, display_name: str, email: str ) -> None:
    """
    Sends an email notifying a user that their email has changed
    Parameters:
        to (str): Address to send the email to.
        display_name (str): The display name to use in the email.
        email (str): Users new email.
    """
    subject, html, text = email_changed_email( display_name=display_name, email=email )
    await send_email( sender=settings.support_email, to=to, subject=subject, html=html, text=text )