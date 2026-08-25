from __future__ import annotations

import resend
from config import settings

resend.api_key = settings.resend_api_key


async def send_email( *, sender: str, to: str, subject: str, html: str, text: str ) -> None:
    """
    Send an email via Resend. In development, if RESEND_API_KEY is unset, this logs the email instead
    of sending it.
    Parameters:
        to (str): Email recipient.
        subject (str): Email subject line.
        html (str): The HTML content of the email.
        text (str): Text alternative to the HTML content.
    """
    if not settings.email_verification_enabled or settings.resend_api_key == "" or settings.resend_api_key == "FAKE-KEY":
        print(
            f"Backup email logging: \nFrom: { sender } \nTo: { to } \nSubject: { subject } \n{ text }",
            "HTML:",
            html
        )
        return

    await resend.Emails.send_async(
    {
        "from": sender,
        "to": [ to ],
        "subject": subject,
        "html": html,
        "text": text
    } )
