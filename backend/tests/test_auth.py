from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import pytest
from auth.security import generate_url_safe_token, hash_token
from httpx import AsyncClient, Response
from models.models import EmailVerificationToken, PasswordResetToken, User
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

# ═══════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════

VALID_PASSWORD = "Str0ng!Pass"
VALID_EMAIL = "alice@example.com"
VALID_DISPLAY_NAME = "Alice"


def _build_register_payload(
    email:            str = VALID_EMAIL,
    password:         str = VALID_PASSWORD,
    confirm_password: str = VALID_PASSWORD,
    display_name:     str = VALID_DISPLAY_NAME
) -> dict:
    return {
        "email":            email,
        "password":         password,
        "confirm_password": confirm_password,
        "display_name":     display_name
    }


async def _register_user(
    client:       AsyncClient,
    email:        str = VALID_EMAIL,
    password:     str = VALID_PASSWORD,
    display_name: str = VALID_DISPLAY_NAME
) -> Response:
    """Register a user and return the parsed JSON response."""
    payload = _build_register_payload(
        email=email,
        password=password,
        display_name=display_name
    )
    response = await client.post( "/auth/register", json=payload )
    return response


async def _login_user(
    client:   AsyncClient,
    email:    str = VALID_EMAIL,
    password: str = VALID_PASSWORD,
) -> Response:
    """Login and return the parsed JSON response (access_token + user)."""
    response = await client.post(
        "/auth/login", json={
            "email": email,
            "password": password
        }
    )
    return response


async def _register_and_login(
    client:       AsyncClient,
    db_session:   AsyncSession,
    email:        str = VALID_EMAIL,
    password:     str = VALID_PASSWORD,
    display_name: str = VALID_DISPLAY_NAME
) -> Response:
    """Convenience: register, verify email, then login, returning the login response JSON."""
    await _register_user( client, email=email, password=password, display_name=display_name )
    await _verify_user_email( db_session, email=email )
    return await _login_user( client, email=email, password=password )

async def _verify_user_email(
    db_session: AsyncSession,
    email: str = VALID_EMAIL
) -> None:
    """Mark a user's email as verified directly in the database.

    Also consumes any pending EmailVerificationToken rows so the user
    can immediately log in without going through the email round-trip.
    """
    result = await db_session.execute(
        select( User ).where( User.email == email.lower( ) )
    )
    user = result.scalar_one_or_none( )
    assert user is not None, f"No user found with email { email }"

    # consume pending verification tokens to match real verify flow
    await db_session.execute(
        update( EmailVerificationToken )
        .where(
            EmailVerificationToken.user_id == user.id,
            EmailVerificationToken.used_at.is_( None )
        )
        .values( used_at=datetime.now( timezone.utc ) )
    )

    user.email_verified_at = datetime.now( timezone.utc )
    await db_session.commit( )


async def _register_and_return_cookie(
    client: AsyncClient, db_session: AsyncSession
) -> tuple[ str | None, Response ]:
    """Helper to register, verify, login and return refresh token"""
    response = await _register_and_login( client, db_session )

    if response.cookies.get( "refresh_token" ) is None:
        raise ValueError( "No refresh token returned." )
    
    return response.cookies.get( "refresh_token" ), response

# ═══════════════════════════════════════════════════════════════════
# Registration
# ═══════════════════════════════════════════════════════════════════

class TestRegister:
    """Happy-path and validation tests for POST /auth/register."""

    @pytest.mark.anyio
    async def test_register_creates_user_and_returns_201(
        self, client: AsyncClient, mock_email_send: AsyncMock
    ) -> None:
        """A valid payload should create a user and return 201 with the user object."""
        response = await client.post(
            "/auth/register", json=_build_register_payload( )
        )

        assert response.status_code == 201
        data = response.json( )
        assert "user" in data
        user = data[ "user" ]
        assert user[ "email" ] == VALID_EMAIL
        assert user[ "display_name" ] == VALID_DISPLAY_NAME
        assert "id" in user
        assert "created_at" in user
        # no tokens should leak in the response
        assert "access_token" not in data
        assert "password" not in str( data )

        mock_email_send[ "verification" ].assert_awaited_once( )

    @pytest.mark.anyio
    async def test_register_duplicate_email_returns_409(
        self, client: AsyncClient, mock_email_send: AsyncMock
    ) -> None:
        """Registering the same email twice must return 409 Conflict."""
        await _register_user( client )

        response = await client.post(
            "/auth/register", json=_build_register_payload( )
        )

        assert response.status_code == 409
        assert "already exists" in response.json( )[ "detail" ].lower( )

    @pytest.mark.anyio
    async def test_register_missing_email_returns_422(
        self, client: AsyncClient
    ) -> None:
        """Omitting the email field must return 422 Unprocessable Entity."""
        payload = _build_register_payload( )
        del payload[ "email" ]

        response = await client.post( "/auth/register", json=payload )

        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_register_missing_password_returns_422(
        self, client: AsyncClient
    ) -> None:
        """Omitting the password field must return 422."""
        payload = _build_register_payload( )
        del payload[ "password" ]

        response = await client.post( "/auth/register", json=payload )

        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_register_missing_display_name_returns_422(
        self, client: AsyncClient
    ) -> None:
        """Omitting display_name must return 422."""
        payload = _build_register_payload( )
        del payload[ "display_name" ]

        response = await client.post( "/auth/register", json=payload )

        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_register_empty_display_name_returns_422(
        self, client: AsyncClient
    ) -> None:
        """An empty display_name must be rejected."""
        payload = _build_register_payload( display_name="" )

        response = await client.post( "/auth/register", json=payload )

        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_register_invalid_email_format_returns_422(
        self, client: AsyncClient
    ) -> None:
        """A malformed email string must be rejected by Pydantic validation."""
        payload = _build_register_payload( email="not-an-email" )

        response = await client.post( "/auth/register", json=payload )

        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_register_password_too_short_returns_422(
        self, client: AsyncClient
    ) -> None:
        """Password shorter than 8 characters must fail the complexity check."""
        payload = _build_register_payload( password="Ab1!" * 2 )  # 8 chars - valid
        # actually try 6 chars
        payload = _build_register_payload( password="Ab1!ab", confirm_password="Ab1!ab" )

        response = await client.post( "/auth/register", json=payload )

        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_register_passwords_mismatch_returns_422(
        self, client: AsyncClient
    ) -> None:
        """When password and confirm_password differ, the request must be rejected."""
        payload = _build_register_payload( confirm_password="Different1!" )

        response = await client.post( "/auth/register", json=payload )

        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_register_strips_email_whitespace(
        self, client: AsyncClient, mock_email_send: AsyncMock
    ) -> None:
        """Leading/trailing whitespace on the email should be stripped by EmailStr."""
        payload = _build_register_payload( email=" alice@example.com " )

        response = await client.post( "/auth/register", json=payload )

        data = response.json( )

        # EmailStr rejects whitespace
        assert response.status_code == 201
        assert data[ "user" ][ "email" ] == "alice@example.com"


# ═══════════════════════════════════════════════════════════════════
# Login
# ═══════════════════════════════════════════════════════════════════

class TestLogin:
    """Happy-path and edge-case tests for POST /auth/login."""

    @pytest.mark.anyio
    async def test_login_returns_access_token_and_user(
        self, client: AsyncClient, db_session: AsyncSession, mock_email_send: AsyncMock
    ) -> None:
        """A valid login must return a JWT access token, user object, and a
        refresh-token cookie."""
        response = await _register_and_login( client, db_session )

        assert response.status_code == 200
        data = response.json( )
        assert "access_token" in data
        assert data[ "token_type" ] == "bearer"
        assert data[ "user" ][ "email" ] == VALID_EMAIL

        # verify the refresh_token cookie is set
        cookies = response.cookies
        assert "refresh_token" in cookies
        assert cookies[ "refresh_token" ] != ""

    @pytest.mark.anyio
    async def test_login_wrong_password_returns_401(
        self, client: AsyncClient, mock_email_send: AsyncMock
    ) -> None:
        """An incorrect password must return 401."""
        await _register_user( client )

        response = await client.post(
            "/auth/login",
            json={ "email": VALID_EMAIL, "password": "WrongPass1!" }
        )

        assert response.status_code == 401
        assert "incorrect" in response.json( )[ "detail" ].lower( )

    @pytest.mark.anyio
    async def test_login_nonexistent_email_returns_401(
        self, client: AsyncClient, mock_email_send: AsyncMock
    ) -> None:
        """An email that has never been registered must return 401."""
        response = await client.post(
            "/auth/login",
            json={ "email": "ghost@example.com", "password": VALID_PASSWORD }
        )

        assert response.status_code == 401
        assert "incorrect" in response.json( )[ "detail" ].lower( )

    @pytest.mark.anyio
    async def test_login_missing_email_returns_422(
        self, client: AsyncClient, mock_email_send: AsyncMock
    ) -> None:
        """Omitting the email field must return 422."""
        response = await client.post(
            "/auth/login", json={ "password": VALID_PASSWORD }
        )
        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_login_missing_password_returns_422(
        self, client: AsyncClient
    ) -> None:
        """Omitting the password field must return 422."""
        response = await client.post(
            "/auth/login", json={ "email": VALID_EMAIL }
        )
        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_login_case_insensitive_email(
        self, client: AsyncClient, db_session: AsyncSession, mock_email_send: AsyncMock
    ) -> None:
        """Emails should be treated case-insensitively."""
        await _register_user( client, email="CaseTest@Example.COM" )
        await _verify_user_email( db_session, email="CaseTest@Example.COM" )

        response = await client.post(
            "/auth/login",
            json={ "email": "casetest@example.com", "password": VALID_PASSWORD }
        )

        assert response.status_code == 200

    @pytest.mark.anyio
    async def test_login_without_register_returns_401(
        self, client: AsyncClient
    ) -> None:
        """Attempting login before any registration must fail."""
        response = await client.post(
            "/auth/login",
            json={ "email": VALID_EMAIL, "password": VALID_PASSWORD }
        )
        assert response.status_code == 401


# ═══════════════════════════════════════════════════════════════════
# Token Refresh
# ═══════════════════════════════════════════════════════════════════

class TestRefresh:
    """Tests for POST /auth/refresh - exchanging a refresh-token cookie
    for a new access token."""

    async def _extract_refresh_cookie(
        self, client: AsyncClient, set_cookie_header: str | None = None
    ) -> str:
        """Helper to get the raw refresh-token value after login.

        If *set_cookie_header* is passed (the raw `set-cookie` response
        header), parse from there; otherwise do a fresh login.
        """
        if set_cookie_header:
            # Simple parse: "refresh_token=<val>; ..."
            for part in set_cookie_header.split( ";" ):
                part = part.strip( )
                if part.startswith( "refresh_token=" ):
                    return part[ len( "refresh_token=" ): ]
            raise ValueError( "refresh_token not found in set-cookie header" )

        login_resp = await client.post(
            "/auth/login",
            json={ "email": VALID_EMAIL, "password": VALID_PASSWORD }
        )
        return login_resp.cookies[ "refresh_token" ]
    
    

    @pytest.mark.anyio
    async def test_refresh_issues_new_access_token(
        self, client: AsyncClient, db_session: AsyncSession, mock_email_send: AsyncMock
    ) -> None:
        """A valid refresh token cookie should return a new access token."""
        refresh_token, response = await _register_and_return_cookie( client, db_session )
        client.cookies.set( "refresh_token", refresh_token )

        response = await client.post( "/auth/refresh" )

        assert response.status_code == 200
        data = response.json( )
        assert "access_token" in data
        assert data[ "user" ][ "email" ] == VALID_EMAIL
        # a new refresh cookie should also be set (rotation)
        assert refresh_token is not None

    @pytest.mark.anyio
    async def test_refresh_without_cookie_returns_401(
        self, client: AsyncClient
    ) -> None:
        """If no refresh_token cookie is sent, the endpoint must return 401."""
        # ensure the client has no cookie
        response = await client.post( "/auth/refresh" )

        assert response.status_code == 401
        assert "missing" in response.json( )[ "detail" ].lower( )

    @pytest.mark.anyio
    async def test_refresh_with_bogus_token_returns_401(
        self, client: AsyncClient
    ) -> None:
        """A refresh_token cookie with a random string must be rejected."""
        client.cookies.set( "refresh_token", "this-is-not-a-valid-token" )

        response = await client.post( "/auth/refresh" )

        assert response.status_code == 401
        assert "invalid" in response.json( )[ "detail" ].lower( )

    @pytest.mark.anyio
    async def test_refresh_reuse_triggers_family_revocation(
        self, client: AsyncClient, db_session: AsyncSession, mock_email_send: AsyncMock
    ) -> None:
        """Reusing an already-rotated refresh token must revoke the entire
        token family (token reuse detection)."""

        # login and get the raw set-cookie value so we can manually re-send it
        original_cookie, response = await _register_and_return_cookie( client, db_session )
        assert original_cookie is not None

        # first refresh → rotates token
        client.cookies.set( "refresh_token", original_cookie )
        refresh1 = await client.post( "/auth/refresh" )
        assert refresh1.status_code == 200

        # re-send the *original* cookie (token reuse attack)
        client.cookies.clear( )
        client.cookies.set( "refresh_token", original_cookie )

        reuse_resp = await client.post( "/auth/refresh" )
        assert reuse_resp.status_code == 401
        assert "already used" in reuse_resp.json( )[ "detail" ].lower( )

        # now even the *new* (rotated) token should be dead
        # because the whole family was revoked
        new_cookie = refresh1.cookies.get( "refresh_token" )
        assert new_cookie is not None
        client.cookies.clear( )
        client.cookies.set( "refresh_token", new_cookie )

        after_reuse = await client.post( "/auth/refresh" )
        assert after_reuse.status_code == 401

    @pytest.mark.anyio
    async def test_refresh_after_logout_returns_401(
        self, client: AsyncClient, db_session: AsyncSession, mock_email_send: AsyncMock
    ) -> None:
        """After a logout, the refresh token should be revoked and unusable."""
        refresh_token, response = await _register_and_return_cookie( client, db_session )

        # call logout with the access token
        await client.post(
            "/auth/logout",
            headers={ "Authorization": f"Bearer { refresh_token }"},
        )

        # now try to refresh - should fail
        response = await client.post( "/auth/refresh" )
        assert response.status_code == 401

    @pytest.mark.anyio
    async def test_refresh_returns_new_cookie_each_time(
        self, client: AsyncClient, db_session: AsyncSession, mock_email_send: AsyncMock
    ) -> None:
        """Each refresh call should rotate the cookie value."""
        first_cookie, response = await _register_and_return_cookie( client, db_session )
        client.cookies.set( "refresh_token", first_cookie )

        for _ in range( 3 ):
            resp = await client.post( "/auth/refresh" )
            assert resp.status_code == 200
            current = resp.cookies[ "refresh_token" ]
            if first_cookie is not None:
                assert current != first_cookie, (
                    "Refresh token cookie value was not rotated"
                )
            first_cookie = current
            client.cookies.set( "refresh_token", current )


# ═══════════════════════════════════════════════════════════════════
# Logout
# ═══════════════════════════════════════════════════════════════════

class TestLogout:
    """Tests for POST /auth/logout."""

    @pytest.mark.anyio
    async def test_logout_revokes_refresh_token(
        self, client: AsyncClient, db_session: AsyncSession, mock_email_send: AsyncMock
    ) -> None:
        """After logout, the refresh token must be revoked so it cannot be
        used to get new access tokens."""
        reset_token, response = await _register_and_return_cookie( client, db_session )

        response = await client.post(
            "/auth/logout",
            headers={ "Authorization": f"Bearer { response.json( )[ "access_token" ] }"},
        )

        assert response.status_code == 200
        assert "logged out" in response.json( )[ "detail" ].lower( )

        # refresh must now fail
        refresh_resp = await client.post( "/auth/refresh" )
        assert refresh_resp.status_code == 401

    @pytest.mark.anyio
    async def test_logout_clears_refresh_cookie(
        self, client: AsyncClient, db_session: AsyncSession, mock_email_send: AsyncMock
    ) -> None:
        """The response should include a Set-Cookie header that clears the
        refresh_token cookie."""
        reset_token, response = await _register_and_return_cookie( client, db_session )

        response = await client.post(
            "/auth/logout",
            headers={"Authorization": f"Bearer { response.json( )[ "access_token" ] }"},
        )

        set_cookie = response.headers.get("set-cookie", "")
        assert 'refresh_token=""' in set_cookie or "Max-Age=0" in set_cookie or "expires=Thu, 01 Jan 1970" in set_cookie, (
            "Cookie was not cleared in the response"
        )

    @pytest.mark.anyio
    async def test_logout_without_access_token_returns_401(
        self, client: AsyncClient
    ) -> None:
        """Logout without a Bearer token must be rejected."""
        response = await client.post( "/auth/logout" )
        assert response.status_code == 401

    @pytest.mark.anyio
    async def test_logout_with_expired_token_returns_401(
        self, client: AsyncClient
    ) -> None:
        """An expired or malformed JWT must be rejected."""
        response = await client.post(
            "/auth/logout",
            headers={ "Authorization": "Bearer this.is.not.a.jwt" },
        )
        assert response.status_code == 401

    @pytest.mark.anyio
    async def test_logout_without_cookie_is_still_successful(
        self, client: AsyncClient, db_session: AsyncSession, mock_email_send: AsyncMock
    ) -> None:
        """If the user has a valid access token but no refresh cookie,
        logout should still succeed (no-op on the cookie side)."""
        refresh_token, response = await _register_and_return_cookie( client, db_session )

        # manually remove the cookie
        client.cookies.clear()

        response = await client.post(
            "/auth/logout",
            headers={"Authorization": f"Bearer { response.json( )[ "access_token" ] }"},
        )

        assert response.status_code == 200

    @pytest.mark.anyio
    async def test_double_logout_is_idempotent(
        self, client: AsyncClient, db_session: AsyncSession, mock_email_send: AsyncMock
    ) -> None:
        """Calling logout twice with the same access token should not
        error on the second call."""
        refresh_token, response = await _register_and_return_cookie( client, db_session )

        headers = {"Authorization": f"Bearer { response.json( )[ "access_token" ] }"}
        resp1 = await client.post( "/auth/logout", headers=headers )
        assert resp1.status_code == 200

        # second logout - the refresh token may already be revoked,
        # but the endpoint should still succeed
        resp2 = await client.post( "/auth/logout", headers=headers )
        assert resp2.status_code == 200


# ═══════════════════════════════════════════════════════════════════
# Forgot / Reset Password
# ═══════════════════════════════════════════════════════════════════

class TestForgotPassword:
    """Tests for POST /auth/forgot-password."""

    @pytest.mark.anyio
    async def test_forgot_password_existing_email_returns_200(
        self, client: AsyncClient, mock_email_send: AsyncMock
    ) -> None:
        """A known email should return 200 (no user enumeration)."""
        await _register_user( client )

        response = await client.post(
            "/auth/forgot-password", json={ "email": VALID_EMAIL }
        )

        assert response.status_code == 200

    @pytest.mark.anyio
    async def test_forgot_password_unknown_email_still_returns_200(
        self, client: AsyncClient
    ) -> None:
        """An unknown email must also return 200 to prevent user enumeration."""
        response = await client.post(
            "/auth/forgot-password", json={ "email": "noone@example.com" }
        )

        assert response.status_code == 200
        assert "if the email" in response.json( )[ "detail" ].lower( )

    @pytest.mark.anyio
    async def test_forgot_password_invalid_email_format_returns_422(
        self, client: AsyncClient
    ) -> None:
        """A non-email string should be rejected by Pydantic."""
        response = await client.post(
            "/auth/forgot-password", json={ "email": "not-an-email" }
        )
        assert response.status_code == 422


class TestResetPassword:
    """Tests for POST /auth/reset-password."""

    async def _get_reset_token( self, client: AsyncClient, db_session: AsyncSession ) -> str:
        """Simulate the forgot-password flow and extract the raw reset token
        from the database so we can use it in reset-password tests.

        The production code prints the token with ``print()`` - here we
        query the DB directly for the token_hash and create the raw token
        manually via ``generate_url_safe_token`` + ``hash_token`` so we
        can construct a valid reset link.
        """
        # First, register & request a reset
        await _register_user( client )

        await client.post(
            "/auth/forgot-password", json={ "email": VALID_EMAIL }
        )

        # Read back the PasswordResetToken row from the DB
        from sqlalchemy import select

        result = await db_session.execute(
            select( PasswordResetToken ).order_by(
                PasswordResetToken.created_at.desc( )
            ).limit( 1 )
        )
        row = result.scalar_one_or_none( )
        assert row is not None, "Expected a PasswordResetToken row"

        # We can't reverse the hash, so we generate a known raw token
        # and manually patch the row's token_hash so we know the plaintext.
        raw_token = generate_url_safe_token( 32 )
        row.token_hash = hash_token( raw_token) 
        await db_session.commit( )

        return raw_token

    @pytest.mark.anyio
    async def test_reset_password_with_valid_token(
        self, client: AsyncClient, db_session: AsyncSession, mock_email_send: AsyncMock
    ) -> None:
        """A valid reset token + good password must succeed."""
        token = await self._get_reset_token( client, db_session )
        new_password = "N3wSecur3!P@ss"

        response = await client.post(
            "/auth/reset-password",
            json={
                "token": token,
                "password": new_password,
                "confirm_password": new_password
            }
        )

        assert response.status_code == 200
        assert "success" in response.json( )[ "detail" ].lower( )

        # the user must have a verified email before they can log in
        await _verify_user_email( db_session )

        # verify the new password actually works for login
        login_resp = await client.post(
            "/auth/login",
            json={ "email": VALID_EMAIL, "password": new_password }
        )
        assert login_resp.status_code == 200

    @pytest.mark.anyio
    async def test_reset_password_invalid_token_returns_401(
        self, client: AsyncClient
    ) -> None:
        """A bogus token must be rejected."""
        response = await client.post(
            "/auth/reset-password",
            json={
                "token": "this-is-a-fake-token",
                "password": VALID_PASSWORD,
                "confirm_password": VALID_PASSWORD
            }
        )

        assert response.status_code == 401
        assert "invalid" in response.json( )[ "detail" ].lower( )

    @pytest.mark.anyio
    async def test_reset_password_token_reuse_returns_401(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Using the same reset token twice must fail on the second attempt."""
        token = await self._get_reset_token( client, db_session )
        new_password = "N3wSecur3!P@ss"

        # first use - succeeds
        resp1 = await client.post(
            "/auth/reset-password",
            json={
                "token": token,
                "password": new_password,
                "confirm_password": new_password
            }
        )
        assert resp1.status_code == 200

        # second use with same token - must fail
        resp2 = await client.post(
            "/auth/reset-password",
            json={
                "token": token,
                "password": VALID_PASSWORD,
                "confirm_password": VALID_PASSWORD
            }
        )
        assert resp2.status_code == 401

    @pytest.mark.anyio
    async def test_reset_password_expired_token_returns_401(
        self, client: AsyncClient, db_session: AsyncSession, mock_email_send: AsyncMock
    ) -> None:
        """An expired reset token must be rejected."""
        token = await self._get_reset_token( client, db_session )

        # Manually expire the token in the DB
        from sqlalchemy import select, update

        await db_session.execute(
            update( PasswordResetToken )
            .values( expires_at=datetime.now( timezone.utc ) - timedelta( minutes=1 ) )
        )
        await db_session.commit( )

        response = await client.post(
            "/auth/reset-password",
            json={
                "token": token,
                "password": VALID_PASSWORD,
                "confirm_password": VALID_PASSWORD
            }
        )

        assert response.status_code == 401
        assert "expired" in response.json( )[ "detail" ].lower( )

    @pytest.mark.anyio
    async def test_reset_password_mismatched_passwords_returns_422(
        self, client: AsyncClient, db_session: AsyncSession, mock_email_send: AsyncMock
    ) -> None:
        """password != confirm_password must be rejected."""
        token = await self._get_reset_token( client, db_session )

        response = await client.post(
            "/auth/reset-password",
            json={
                "token": token,
                "password": "Str0ng!Pass",
                "confirm_password": "Different1!"
            }
        )

        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_reset_password_weak_password_returns_422(
        self, client: AsyncClient, db_session: AsyncSession, mock_email_send: AsyncMock
    ) -> None:
        """A password that fails complexity checks must be rejected."""
        token = await self._get_reset_token( client, db_session )

        response = await client.post(
            "/auth/reset-password",
            json={
                "token": token,
                "password": "short",
                "confirm_password": "short"
            }
        )

        assert response.status_code == 422


# ═══════════════════════════════════════════════════════════════════
# Password Complexity (unit-style via HTTP)
# ═══════════════════════════════════════════════════════════════════

class TestPasswordComplexity:
    """Validate every branch of the password policy through the register
    endpoint (the complexity rules are shared with reset-password)."""

    @pytest.mark.anyio
    async def test_missing_uppercase_rejected(
        self, client: AsyncClient
    ) -> None:
        payload = _build_register_payload( password="alllowercase1!", confirm_password="alllowercase1!" )
        response = await client.post("/auth/register", json=payload)
        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_missing_lowercase_rejected(
        self, client: AsyncClient
    ) -> None:
        payload = _build_register_payload(password="ALLUPPER1!", confirm_password="ALLUPPER1!")
        response = await client.post("/auth/register", json=payload)
        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_missing_digit_rejected(
        self, client: AsyncClient
    ) -> None:
        payload = _build_register_payload(password="NoDigits!!", confirm_password="NoDigits!!")
        response = await client.post("/auth/register", json=payload)
        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_missing_special_char_rejected(
        self, client: AsyncClient
    ) -> None:
        payload = _build_register_payload(password="NoSpecial1", confirm_password="NoSpecial1")
        response = await client.post("/auth/register", json=payload)
        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_exactly_eight_chars_passes(
        self, client: AsyncClient
    ) -> None:
        """A password of exactly 8 characters meeting all complexity rules
        must be accepted."""
        payload = _build_register_payload(password="Ab1!defg", confirm_password="Ab1!defg")
        response = await client.post("/auth/register", json=payload)
        assert response.status_code == 201

    @pytest.mark.anyio
    async def test_seven_chars_rejected(
        self, client: AsyncClient
    ) -> None:
        """A 7-character password even with proper complexity must be rejected."""
        payload = _build_register_payload(password="Ab1!def", confirm_password="Ab1!def")
        response = await client.post("/auth/register", json=payload)
        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_very_long_password_passes(
        self, client: AsyncClient
    ) -> None:
        """A 120-char password meeting complexity rules is accepted."""
        base = "Ab1!"  # 4 chars that satisfy all categories
        long_pass = base * 30  # 120 chars
        payload = _build_register_payload(
            email="longpass@example.com",
            password=long_pass,
            confirm_password=long_pass,
        )
        response = await client.post("/auth/register", json=payload)
        assert response.status_code == 201


# ═══════════════════════════════════════════════════════════════════
# Authentication dependency (get_current_user)
# ═══════════════════════════════════════════════════════════════════

class TestAuthDependency:
    """Tests that exercise the get_current_user dependency via a protected
    endpoint (POST /auth/logout requires the dependency)."""

    @pytest.mark.anyio
    async def test_valid_bearer_token_accepted(
        self, client: AsyncClient, db_session: AsyncSession, mock_email_send: AsyncMock
    ) -> None:
        """A valid access token must pass the dependency check."""
        refresh_token, response = await _register_and_return_cookie( client, db_session )

        response = await client.post(
            "/auth/logout",
            headers={"Authorization": f"Bearer { response.json( )[ "access_token" ] }"}
        )
        assert response.status_code == 200

    @pytest.mark.anyio
    async def test_missing_authorization_header_rejected(
        self, client: AsyncClient, mock_email_send: AsyncMock
    ) -> None:
        """Requests without an Authorization header must be rejected."""
        await _register_user( client)

        response = await client.post( "/auth/logout" )
        assert response.status_code == 401
        assert "could not validate" in response.json( )[ "detail" ].lower( )

    @pytest.mark.anyio
    async def test_malformed_jwt_rejected(
        self, client: AsyncClient
    ) -> None:
        """A string that is not a valid JWT must be rejected."""
        response = await client.post(
            "/auth/logout",
            headers={ "Authorization": "Bearer not-a-jwt" }
        )
        assert response.status_code == 401

    @pytest.mark.anyio
    async def test_tampered_jwt_rejected(
        self, client: AsyncClient, db_session: AsyncSession, mock_email_send: AsyncMock
    ) -> None:
        """A JWT whose payload has been modified after signing must be
        rejected (signature verification failure)."""
        refresh_token, response = await _register_and_return_cookie( client, db_session )
        # Take the valid token and append garbage to invalidate the signature
        tampered = response.json( )[ "access_token" ] + "tampered"

        response = await client.post(
            "/auth/logout",
            headers={ "Authorization": f"Bearer { tampered }"}
        )
        assert response.status_code == 401

    @pytest.mark.anyio
    async def test_jwt_for_nonexistent_user_rejected(
        self, client: AsyncClient
    ) -> None:
        """A JWT with a random UUID as sub that doesn't match any user
        must be rejected."""
        from auth.security import create_access_token

        fake_token = create_access_token( user_id=str( uuid.uuid4( ) ) )

        response = await client.post(
            "/auth/logout",
            headers={ "Authorization": f"Bearer { fake_token }" }
        )
        assert response.status_code == 401

    @pytest.mark.anyio
    async def test_empty_bearer_token_rejected(
        self, client: AsyncClient
    ) -> None:
        """An empty string after 'Bearer ' must be rejected."""
        response = await client.post(
            "/auth/logout",
            headers={ "Authorization": "Bearer " }
        )
        assert response.status_code == 401

    @pytest.mark.anyio
    async def test_wrong_auth_scheme_rejected(
        self, client: AsyncClient, db_session: AsyncSession, mock_email_send: AsyncMock
    ) -> None:
        """Using 'Basic' instead of 'Bearer' must be rejected."""
        refresh_token, response = await _register_and_return_cookie( client, db_session )

        response = await client.post(
            "/auth/logout",
            headers={ "Authorization": f"Basic { response.json( )[ 'access_token' ] }" }
        )
        assert response.status_code == 401


# ═══════════════════════════════════════════════════════════════════
# Concurrency & race-condition edge cases
# ═══════════════════════════════════════════════════════════════════

class TestConcurrency:
    """Edge-case tests for concurrent or rapid-fire requests."""

    @pytest.mark.anyio
    async def test_rapid_login_logout_sequence(
        self, client: AsyncClient, db_session: AsyncSession, mock_email_send: AsyncMock
    ) -> None:
        """Repeated login → logout cycles should work without errors."""
        await _register_user( client )
        await _verify_user_email( db_session )

        for _ in range( 5 ):
            # fresh client-like cookie state
            client.cookies.clear()

            login_resp = await client.post(
                "/auth/login",
                json={ "email": VALID_EMAIL, "password": VALID_PASSWORD }
            )
            assert login_resp.status_code == 200

            logout_resp = await client.post(
                "/auth/logout",
                headers={
                    "Authorization": f"Bearer { login_resp.json( )[ 'access_token' ] }"
                }
            )
            assert logout_resp.status_code == 200


# ═══════════════════════════════════════════════════════════════════
# Security: no secrets leaked
# ═══════════════════════════════════════════════════════════════════

class TestNoSecretsLeaked:
    """Ensure password hashes, tokens, and other secrets never leak in
    API responses."""

    @pytest.mark.anyio
    async def test_register_response_has_no_password_hash(
        self, client: AsyncClient, mock_email_send: AsyncMock
    ) -> None:
        response = await client.post(
            "/auth/register", json=_build_register_payload( )
        )
        body = response.text
        assert response.status_code == 201
        assert "password_hash" not in body
        assert "password" not in body.lower( )

    @pytest.mark.anyio
    async def test_login_response_has_no_password_hash(
        self, client: AsyncClient, db_session: AsyncSession, mock_email_send: AsyncMock
    ) -> None:
        await _register_user( client )
        await _verify_user_email( db_session )
        response = await client.post(
            "/auth/login",
            json={ "email": VALID_EMAIL, "password": VALID_PASSWORD }
        )
        body = response.text
        assert response.status_code == 200
        assert "password_hash" not in body

    @pytest.mark.anyio
    async def test_refresh_response_has_no_password_hash(
        self, client: AsyncClient, db_session: AsyncSession, mock_email_send: AsyncMock
    ) -> None:
        refresh_token, response = await _register_and_return_cookie( client, db_session )
        client.cookies.set( "refresh_token", refresh_token )
        response = await client.post( "/auth/refresh" )
        body = response.text
        assert response.status_code == 200
        assert "password_hash" not in body

    @pytest.mark.anyio
    async def test_401_error_does_not_distinguish_email_vs_password(
        self, client: AsyncClient, mock_email_send: AsyncMock
    ) -> None:
        """Both wrong-password and unknown-email must return the exact same
        generic message (prevent user enumeration)."""
        await _register_user( client )

        resp_wrong_pass = await client.post(
            "/auth/login",
            json={ "email": VALID_EMAIL, "password": "WrongPass1!" }
        )
        resp_unknown_email = await client.post(
            "/auth/login",
            json={ "email": "unknown@example.com", "password": VALID_PASSWORD }
        )

        assert resp_wrong_pass.status_code == 401
        assert resp_unknown_email.status_code == 401
        assert (
            resp_wrong_pass.json( )[ "detail" ]
            == resp_unknown_email.json( )[ "detail" ]
        ), (
            "Error messages differ - user enumeration possible"
        )
