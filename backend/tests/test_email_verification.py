from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient
from models.models import User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from tests.test_auth import _login_user, _register_user

VALID_PASSWORD = "Str0ng!Pass"
VALID_EMAIL = "alice@example.com"
VALID_DISPLAY_NAME = "Alice"

class TestEmailVerification:
    """Tests to make sure email verification functions correctly"""

    @pytest.mark.anyio
    async def test_register_creates_unverified_user_and_sends_email(
        self, client: AsyncClient, db_session: AsyncSession, mock_email_send: AsyncMock
    ) -> None:
        await _register_user(
            client=client,
            email=VALID_EMAIL,
            password=VALID_PASSWORD,
            display_name=VALID_DISPLAY_NAME
        )

        result = await db_session.execute( select( User ).where( User.email == VALID_EMAIL ) )

        user_row = result.scalar_one_or_none( )

        assert user_row is not None
        assert user_row.email_verified_at is None

        mock_email_send[ "verification" ].assert_awaited_once( )
        sent = mock_email_send[ "verification" ].call_args.kwargs
        assert sent[ "to" ] == VALID_EMAIL
        assert sent[ "display_name" ] == VALID_DISPLAY_NAME
        assert "raw_token" in sent

    @pytest.mark.anyio
    async def test_login_blocked_before_verification(
        self, client: AsyncClient, mock_email_send: AsyncMock
    ) -> None:
        await _register_user(
            client=client,
            email=VALID_EMAIL,
            password=VALID_PASSWORD,
            display_name=VALID_DISPLAY_NAME
        )

        response = await _login_user(
            client=client,
            email=VALID_EMAIL,
            password=VALID_PASSWORD
        )

        assert response.status_code == 403
        assert response.json( )[ "detail" ] == "Email has not been verified."

    @pytest.mark.anyio
    async def test_wrong_password_still_returns_401_when_unverified(
        self, client: AsyncClient, mock_email_send: AsyncMock
    ) -> None:
        await _register_user(
            client=client,
            email=VALID_EMAIL,
            password=VALID_PASSWORD,
            display_name=VALID_DISPLAY_NAME
        )

        response = await _login_user(
            client=client,
            email=VALID_EMAIL,
            password="wrong-password"
        )

        assert response.status_code == 401

    @pytest.mark.anyio
    async def test_full_verification_flow(
        self, client: AsyncClient, mock_email_send: AsyncMock
    ) -> None:
        await _register_user(
            client=client,
            email=VALID_EMAIL,
            password=VALID_PASSWORD,
            display_name=VALID_DISPLAY_NAME
        )

        verify_token = mock_email_send[ "verification" ].call_args.kwargs[ "raw_token" ]

        response = await client.get( f"/auth/verify-email?token={ verify_token }" )

        assert response.status_code == 200

        login_response = await _login_user(
            client=client,
            email=VALID_EMAIL,
            password=VALID_PASSWORD
        )

        assert login_response.status_code == 200

    @pytest.mark.anyio
    async def test_verify_email_rejects_unknown_token(
        self, client: AsyncClient, mock_email_send: AsyncMock
    ) -> None:
        response = await client.get( "/auth/verify-email?token=random" )

        assert response.status_code == 400

    @pytest.mark.anyio
    async def test_verify_email_token_cannot_be_reused(
        self, client: AsyncClient, mock_email_send: AsyncMock
    ) -> None:
        await _register_user(
            client=client,
            email=VALID_EMAIL,
            password=VALID_PASSWORD,
            display_name=VALID_DISPLAY_NAME
        )

        verify_token = mock_email_send[ "verification" ].call_args.kwargs[ "raw_token" ]

        response = await client.get( f"/auth/verify-email?token={ verify_token }" )
        assert response.status_code == 200

        reuse_response = await client.get( f"/auth/verify-email?token={ verify_token }" )
        assert reuse_response.status_code == 400

    @pytest.mark.anyio
    async def test_verify_email_rejects_expired_token(
        self, client: AsyncClient, db_session: AsyncSession, mock_email_send: AsyncMock
    ) -> None:
        from datetime import datetime, timedelta, timezone

        from models.models import EmailVerificationToken
        from sqlalchemy import update

        await _register_user(
            client=client,
            email=VALID_EMAIL,
            password=VALID_PASSWORD,
            display_name=VALID_DISPLAY_NAME
        )
        raw_token = mock_email_send[ "verification" ].call_args.kwargs[ "raw_token" ]

        from auth.security import hash_token
        await db_session.execute(
            update( EmailVerificationToken )
            .where( EmailVerificationToken.token_hash == hash_token( raw_token ) )
            .values( expires_at=datetime.now( timezone.utc ) - timedelta( minutes=1 ) )
        )
        await db_session.commit()

        response = await client.get( "/auth/verify-email", params={ "token": raw_token } )
        assert response.status_code == 400

    @pytest.mark.anyio
    async def test_resend_verification_invalidates_previous_token(
        self, client: AsyncClient, mock_email_send: AsyncMock
    ) -> None:
        await _register_user(
            client=client,
            email=VALID_EMAIL,
            password=VALID_PASSWORD,
            display_name=VALID_DISPLAY_NAME
        )
        old_token = mock_email_send[ "verification" ].call_args.kwargs[ "raw_token" ]

        resend_response = await client.post(
            "/auth/resend-verification", json={ "email": VALID_EMAIL }
        )
        assert resend_response.status_code == 200

        new_token = mock_email_send[ "verification" ].call_args.kwargs[ "raw_token" ]
        assert new_token != old_token

        old_result = await client.get( "/auth/verify-email", params={ "token": old_token } )
        assert old_result.status_code == 400

        new_result = await client.get( "/auth/verify-email", params={ "token": new_token } )
        assert new_result.status_code == 200

    @pytest.mark.anyio
    async def test_resend_verification_is_enumeration_safe(
        self, client: AsyncClient, mock_email_send: AsyncMock
    ) -> None:
        unregistered = await client.post(
            "/auth/resend-verification", json={ "email": "nobody@example.com" }
        )

        await _register_user(
            client=client,
            email=VALID_EMAIL,
            password=VALID_PASSWORD,
            display_name=VALID_DISPLAY_NAME
        )
        raw_token = mock_email_send[ "verification" ].call_args.kwargs[ "raw_token" ]
        await client.get( "/auth/verify-email", params={ "token": raw_token } )

        already_verified = await client.post(
            "/auth/resend-verification", json={ "email": VALID_EMAIL }
        )

        assert unregistered.status_code == already_verified.status_code
        assert unregistered.json( ) == already_verified.json( )

    @pytest.mark.anyio
    async def test_resend_verification_does_not_email_unregistered_or_verified(
        self, client: AsyncClient, mock_email_send: AsyncMock
    ) -> None:
        await client.post( "/auth/resend-verification", json={ "email": "nobody@example.com" } )
        mock_email_send[ "verification" ].assert_not_called( )

        await _register_user(
            client=client,
            email=VALID_EMAIL,
            password=VALID_PASSWORD,
            display_name=VALID_DISPLAY_NAME
        )
        raw_token = mock_email_send[ "verification" ].call_args.kwargs[ "raw_token" ]
        await client.get( "/auth/verify-email", params={ "token": raw_token } )

        calls_before = mock_email_send[ "verification" ].await_count
        await client.post( "/auth/resend-verification", json={ "email": VALID_EMAIL } )
        assert mock_email_send[ "verification" ].await_count == calls_before

    @pytest.mark.anyio
    async def test_forgot_password_sends_reset_email(
        self, client: AsyncClient, mock_email_send: AsyncMock
    ) -> None:
        await _register_user(
            client=client,
            email=VALID_EMAIL,
            password=VALID_PASSWORD,
            display_name=VALID_DISPLAY_NAME
        )

        response = await client.post(
            "/auth/forgot-password", json={ "email": VALID_EMAIL }
        )
        assert response.status_code == 200

        mock_email_send[ "reset" ].assert_awaited_once( )
        sent = mock_email_send[ "reset" ].call_args.kwargs
        assert sent[ "to" ] == VALID_EMAIL
        assert "raw_token" in sent