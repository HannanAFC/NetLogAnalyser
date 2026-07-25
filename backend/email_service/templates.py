from __future__ import annotations

from config import settings

# ── Design language (NetLogAnalyser · modern-minimal · cool-blue) ──────────
# Email-safe translation of the site's design tokens.  Inline styles only;
# email clients strip <style> blocks and ignore CSS custom properties.
#
# Palette
_COLOR_PAPER       = "#FCFCFD"
_COLOR_CARD        = "#FFFFFF"
_COLOR_TEXT        = "#1E2227"
_COLOR_TEXT_SOFT   = "#535A63"
_COLOR_TEXT_MUTED  = "#828993"
_COLOR_BORDER      = "#DEE1E6"
_COLOR_ACCENT      = "#2E6EC7"
_COLOR_ACCENT_HI   = "#1F4F99"

# Typography - system stack approximating Inter + IBM Plex Mono
_FONT_STACK  = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
_FONT_MONO   = "'SF Mono', 'Cascadia Code', 'IBM Plex Mono', ui-monospace, monospace"

# Layout
_WIDTH       = 520
_RADIUS      = "8px"


def _base_layout( *, title: str, body: str ) -> str:
    """Wrap *body* in a branded, mobile-friendly email shell."""
    return f"""\
        <!DOCTYPE html>
        <html lang="en">
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <meta name="color-scheme" content="light">
                <meta name="supported-color-schemes" content="light">
                <title>{ title }</title>
            </head>
            <body style="margin:0;padding:0;background:{_COLOR_PAPER};font-family:{_FONT_STACK};-webkit-font-smoothing:antialiased;">
                <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{_COLOR_PAPER};">
                    <tr>
                        <td align="center" style="padding:32px 16px 48px;">
                            {body}
                            <table role="presentation" width="{ _WIDTH }" cellpadding="0" cellspacing="0" style="margin:32px auto 0;">
                                <tr>
                                    <td style="border-top:1px solid {_COLOR_BORDER};padding-top:20px;">
                                        <p style="margin:0;font-family:{_FONT_MONO};font-size:10px;font-weight:500;letter-spacing:0.08em;text-transform:uppercase;color:{_COLOR_TEXT_MUTED};">
                                        NetLogAnalyser
                                        </p>
                                        <p style="margin:8px 0 0;font-size:12px;line-height:1.55;color:{_COLOR_TEXT_MUTED};">
                                        Real-time network log analysis &amp; monitoring
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
            </body>
        </html>
    """


def _card( *, content: str ) -> str:
    """A white card panel matching the site's panel component."""
    return f"""\
        <table role="presentation" width="{ _WIDTH }" cellpadding="0" cellspacing="0" style="
            background:{_COLOR_CARD};
            border:1px solid {_COLOR_BORDER};
            border-radius:{_RADIUS};
            margin:0 auto;
        ">
            <tr>
                <td style="padding:36px 32px;">
                    { content }
                </td>
            </tr>
        </table>
    """


def _button( *, label: str, href: str ) -> str:
    """CTA button - matches the site's mono-label + accent style."""
    return f"""\
        <table role="presentation" cellpadding="0" cellspacing="0" style="margin:28px 0 4px;">
            <tr>
                <td align="center" style="
                    background:{_COLOR_ACCENT};
                    border-radius:6px;
                ">
                    <a href="{ href }" target="_blank" rel="noopener" style="
                        display:inline-block;
                        padding:13px 32px;
                        font-family:{_FONT_MONO};
                        font-size:12px;
                        font-weight:600;
                        letter-spacing:0.02em;
                        color:#FFFFFF;
                        text-decoration:none;
                        white-space:nowrap;
                    ">{ label }</a>
                </td>
            </tr>
        </table>
    """


def _heading( *, text: str ) -> str:
    """Section heading - matches heading-2 from styles.css."""
    return f'<h2 style="margin:0 0 8px;font-size:20px;font-weight:600;line-height:1.2;letter-spacing:-0.02em;color:{_COLOR_TEXT};">{ text }</h2>'


def _body( *, text: str ) -> str:
    """Body copy - matches body-text from styles.css."""
    return f'<p style="margin:0 0 14px;font-size:15px;line-height:1.6;color:{_COLOR_TEXT_SOFT};">{ text }</p>'


def _muted( *, text: str ) -> str:
    """Small muted footnote."""
    return f'<p style="margin:0;font-size:12px;line-height:1.55;color:{_COLOR_TEXT_MUTED};">{ text }</p>'

def _link( *, text: str, href: str ) -> str:
    """Inline text link."""
    return f"""\
        <a href="'{ href } target="_blank" rel="noopener"
            style="
                text-decoration:underline;
                color:{_COLOR_ACCENT};"
        >
        { text }
        </a>
    """


# ═══════════════════════════════════════════════════════════════════════════════
#  Templates
# ═══════════════════════════════════════════════════════════════════════════════


def verification_email( *, display_name: str, raw_token: str ) -> tuple[str, str, str]:
    """Email verification - sent on registration and on resend."""
    link = f"{settings.frontend_url}/verify-email?token={raw_token}"

    subject = "Confirm your email - NetLogAnalyser"

    text = (
        f"Welcome to NetLogAnalyser, {display_name}.\n\n"
        f"Confirm your email address to activate your account:\n"
        f"{link}\n\n"
        f"This link expires in {settings.email_verification_token_expire_minutes} minutes.\n"
        f"If you didn't create a NetLogAnalyser account, you can ignore this email.\n\n"
        f"- The NetLogAnalyser team"
    )

    html = _base_layout(
        title=subject,
        body=_card(content=(
            _heading(text="Confirm your email")
            + _body(
                text=(
                    f"Hi {display_name}, thanks for signing up. "
                    f"Click the button below to verify your email address and activate your account."
                )
            )
            + _button(label="Confirm email address", href=link)
            + _muted(
                text=(
                    f"This link expires in {settings.email_verification_token_expire_minutes} minutes. "
                    f"If you didn't create a NetLogAnalyser account, you can ignore this email."
                )
            )
        )),
    )

    return subject, html, text


def password_reset_email( *, display_name: str, raw_token: str ) -> tuple[str, str, str]:
    """Password reset - sent from the forgot-password flow."""
    link = f"{settings.frontend_url}/reset-password?token={raw_token}"

    subject = "Reset your password - NetLogAnalyser"

    text = (
        f"Hi {display_name},\n\n"
        f"We received a request to reset your NetLogAnalyser password:\n"
        f"{link}\n\n"
        f"This link expires in {settings.password_reset_token_expire_minutes} minutes.\n"
        f"If you didn't request this, you can ignore this email - your password won't change.\n\n"
        f"- The NetLogAnalyser team"
    )

    html = _base_layout(
        title=subject,
        body=_card(content=(
            _heading(text="Reset your password")
            + _body(
                text=(
                    f"Hi {display_name}, we received a request to reset your password. "
                    f"Click the button below to choose a new one."
                )
            )
            + _button(label="Reset password", href=link)
            + _muted(
                text=(
                    f"This link expires in {settings.password_reset_token_expire_minutes} minutes. "
                    f"If you didn't request this, you can ignore this email - your password won't change."
                )
            )
        )),
    )

    return subject, html, text


def welcome_email( *, display_name: str ) -> tuple[str, str, str]:
    """Welcome email - sent after a user verifies their email address."""
    subject = "Welcome to NetLogAnalyser"

    text = (
        f"Hi {display_name},\n\n"
        f"Your email has been verified and your NetLogAnalyser account is now active.\n\n"
        f"Start ingesting your network logs by creating an API key in your dashboard:\n"
        f"{settings.frontend_url}/dashboard\n\n"
        f"If you need help getting started, check out our documentation or reply to this email.\n\n"
        f"- The NetLogAnalyser team"
    )

    html = _base_layout(
        title=subject,
        body=_card(content=(
            _heading(text="You're all set")
            + _body(
                text=(
                    f"Hi {display_name}, your email has been verified and your "
                    f"NetLogAnalyser account is ready to go."
                )
            )
            + _body(
                text=(
                    "To start ingesting network logs, create an API key from "
                    f"your dashboard and visit the { _link( text="API documentation", href=settings.backend_url ) }."
                )
            )
            + _button(label="Go to dashboard", href=f"{settings.frontend_url}/dashboard")
            + _muted(
                text=(
                    "If you have any questions, reply to this email or check "
                    "out the documentation in your dashboard."
                )
            )
        )),
    )

    return subject, html, text
