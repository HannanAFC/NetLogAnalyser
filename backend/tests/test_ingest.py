from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest
from config import settings
from fastapi import Request as FastAPIRequest
from fastapi import Response as FastAPIResponse
from fastapi_limiter.depends import RateLimiter
from httpx import AsyncClient, Response
from main import app
from models.models import EmailVerificationToken, LogEntry, User
from pyrate_limiter import Duration, Limiter, Rate
from rate_limiter import get_ingest_rate_limiter
from redis.asyncio import Redis
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

VALID_EMAIL = "ingest-tester@example.com"
VALID_PASSWORD = "Str0ng!Pass"
VALID_DISPLAY_NAME = "Ingest Tester"
VALID_KEY_LABEL = "Ingest Test Key"

def _build_strict_limiter( times: int, seconds: int ) -> RateLimiter:
    """Return an in-memory RateLimiter that allows only *times* requests."""
    return RateLimiter( Limiter( Rate( limit=times, interval=seconds * Duration.SECOND ) ) )

# ═══════════════════════════════════════════════════════════════════
# Helpers — auth / api key setup
# ═══════════════════════════════════════════════════════════════════

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
    client:     AsyncClient,
    db_session: AsyncSession,
    email:      str = VALID_EMAIL
) -> tuple[ str | None, Response ]:
    """Helper to register, verify, login and return refresh token"""
    response = await _register_and_login( client, db_session, email )

    if response.cookies.get( "refresh_token" ) is None:
        raise ValueError( "No refresh token returned." )
    
    return response.cookies.get( "refresh_token" ), response

async def _create_api_key(
    client: AsyncClient,
    access_token: str,
    label: str = VALID_KEY_LABEL
) -> Response:
    """Create an API key and return the response."""
    return await client.post(
        "/api-keys",
        json={ "label": label },
        headers={ "Authorization": f"Bearer { access_token }" }
    )

async def _revoke_api_key(
    client: AsyncClient,
    access_token: str,
    api_key_id: str
) -> None:
    response = await client.delete(
        f"/api-keys/{ api_key_id }",
        headers={ "Authorization": f"Bearer { access_token }" }
    )
    assert response.status_code in ( 200, 204 ), response.text


async def _setup_authenticated_key(
    client:       AsyncClient,
    db_session:   AsyncSession,
    email:        str = VALID_EMAIL
) -> tuple[ str, str, str ]:
    refresh_token, response = await _register_and_return_cookie( client, db_session, email )

    data = response.json( )
    assert refresh_token is not None
    access_token = data[ "access_token" ]

    key_response = await _create_api_key( client, access_token )
    key_data     = key_response.json( )
    print( key_data )
    id           = key_data[ "id" ]
    api_key      = key_data[ "api_key" ]

    return access_token, id, api_key

# ═══════════════════════════════════════════════════════════════════
# Helpers — building ingest payloads
# ═══════════════════════════════════════════════════════════════════

def _iso_now( ) -> str:
    return datetime.now( timezone.utc ).isoformat( )


def _valid_entry( **overrides ) -> dict:
    entry = {
        "src_ip":            "192.168.1.10",
        "dst_ip":             "10.0.0.5",
        "src_port":           443,
        "dst_port":           51820,
        "protocol":           "TCP",
        "packet_size_bytes":  1500,
        "flags":              "SYN,ACK",
        "raw_payload":        { "note": "test entry" },
        "captured_at":        _iso_now( )
    }
    entry.update( overrides )
    return entry


def _batch_payload( entries: list[ dict ] ) -> dict:
    return { "entries": entries }


async def _ingest(
    client: AsyncClient, raw_key: str, entries: list[ dict ]
) -> Response:
    return await client.post(
        "/ingest",
        json=_batch_payload( entries ),
        headers={ "X-API-Key": raw_key }
    )


async def _count_log_entries( db_session: AsyncSession, user_id: str ) -> int:
    result = await db_session.execute(
        select( func.count( ) ).select_from( LogEntry ).where( LogEntry.user_id == user_id )
    )
    return result.scalar_one( )


# ═══════════════════════════════════════════════════════════════════
# Authentication
# ═══════════════════════════════════════════════════════════════════

class TestIngestAuthentication:
    """Tests for the API-key auth boundary on POST /ingest."""

    @pytest.mark.anyio
    async def test_missing_api_key_header_rejected(
        self, client: AsyncClient
    ) -> None:
        """No X-API-Key header at all must be rejected before reaching the service."""
        response = await client.post( "/ingest", json=_batch_payload( [ _valid_entry( ) ] ) )
        assert response.status_code in ( 401, 403 )

    @pytest.mark.anyio
    async def test_unknown_api_key_rejected(
        self, client: AsyncClient, redis_client: Redis
    ) -> None:
        """A syntactically plausible but nonexistent key must return 401."""
        response = await _ingest( client, "nlak_" + uuid.uuid4( ).hex, [ _valid_entry( ) ] )
        assert response.status_code == 401

    @pytest.mark.anyio
    async def test_revoked_api_key_rejected(
        self, client: AsyncClient, redis_client: Redis, db_session: AsyncSession, mock_email_send: AsyncMock
    ) -> None:
        """A key that was valid must stop working immediately after revoke —
        this is the test that actually proves cache invalidation works,
        not just the happy path."""
        access_token, api_key_id, raw_key = await _setup_authenticated_key( client, db_session )

        # confirm it works first
        ok_response = await _ingest( client, raw_key, [ _valid_entry( dst_port=100 ) ] )
        assert ok_response.status_code == 207

        await _revoke_api_key( client, access_token, api_key_id )

        revoked_response = await _ingest( client, raw_key, [ _valid_entry( dst_port=100 ) ] )
        assert revoked_response.status_code == 401

    @pytest.mark.anyio
    async def test_valid_api_key_with_valid_batch_accepted(
        self, client: AsyncClient, redis_client: Redis, db_session: AsyncSession, mock_email_send: AsyncMock
    ) -> None:
        _, _, raw_key = await _setup_authenticated_key( client, db_session )

        response = await _ingest( client, raw_key, [ _valid_entry( ) ] )

        assert response.status_code == 207
        body = response.json( )
        assert body[ "accepted" ] == 1
        assert body[ "rejected" ] == 0
        assert body[ "errors" ] == [ ]


# ═══════════════════════════════════════════════════════════════════
# Partial acceptance
# ═══════════════════════════════════════════════════════════════════

class TestPartialAcceptance:
    """Tests for the accepted/rejected split behaviour of a mixed batch."""

    @pytest.mark.anyio
    async def test_all_valid_entries_all_accepted(
        self, client: AsyncClient, redis_client: Redis, db_session: AsyncSession, mock_email_send: AsyncMock
    ) -> None:
        _, _, raw_key = await _setup_authenticated_key( client, db_session )
        entries = [ _valid_entry( ) for _ in range( 5 ) ]

        response = await _ingest( client, raw_key, entries )

        body = response.json( )
        assert response.status_code == 207
        assert body[ "accepted" ] == 5
        assert body[ "rejected" ] == 0

    @pytest.mark.anyio
    async def test_mixed_valid_and_invalid_entries(
        self, client: AsyncClient, redis_client: Redis, db_session: AsyncSession, mock_email_send: AsyncMock
    ) -> None:
        _, _, raw_key = await _setup_authenticated_key( client, db_session )
        entries = [
            _valid_entry( ),
            _valid_entry( protocol="NOT_A_PROTOCOL" ),
            _valid_entry( ),
            _valid_entry( src_port=-1 ),
        ]

        response = await _ingest( client, raw_key, entries )

        body = response.json( )
        assert response.status_code == 207
        assert body[ "accepted" ] == 2
        assert body[ "rejected" ] == 2
        assert len( body[ "errors" ] ) == 2

    @pytest.mark.anyio
    async def test_all_invalid_entries_returns_zero_accepted(
        self, client: AsyncClient, redis_client: Redis, db_session: AsyncSession, mock_email_send: AsyncMock
    ) -> None:
        _, _, raw_key = await _setup_authenticated_key( client, db_session )
        entries = [
            _valid_entry( protocol="BOGUS" ),
            _valid_entry( dst_port=99999 ),
        ]

        response = await _ingest( client, raw_key, entries )

        body = response.json( )
        print( body )
        assert body[ "accepted" ] == 0
        assert body[ "rejected" ] == 2

    @pytest.mark.anyio
    async def test_error_index_matches_original_batch_position(
        self, client: AsyncClient, redis_client: Redis, db_session: AsyncSession, mock_email_send: AsyncMock
    ) -> None:
        """The invalid entry sits in the middle of the batch — this is the
        case that catches an off-by-one bug in how errors are indexed
        after invalid entries have already been filtered out elsewhere."""
        _, _, raw_key = await _setup_authenticated_key( client, db_session )
        entries = [
            _valid_entry( ),
            _valid_entry( ),
            _valid_entry( protocol="BOGUS" ),   # index 2
            _valid_entry( ),
        ]

        response = await _ingest( client, raw_key, entries )

        body = response.json( )
        assert body[ "accepted" ] == 3
        assert body[ "rejected" ] == 1
        assert body[ "errors" ][ 0 ][ "index" ] == 2


# ═══════════════════════════════════════════════════════════════════
# Per-entry validation
# ═══════════════════════════════════════════════════════════════════

class TestEntryValidation:
    """Field-level validation on individual log entries."""

    @pytest.mark.anyio
    async def test_invalid_protocol_rejected(
        self, client: AsyncClient, redis_client: Redis, db_session: AsyncSession, mock_email_send: AsyncMock
    ) -> None:
        _, _, raw_key = await _setup_authenticated_key( client, db_session )
        response = await _ingest( client, raw_key, [ _valid_entry( protocol="SCTP" ) ] )
        assert response.json( )[ "rejected" ] == 1

    @pytest.mark.anyio
    async def test_port_above_valid_range_rejected(
        self, client: AsyncClient, redis_client: Redis, db_session: AsyncSession, mock_email_send: AsyncMock
    ) -> None:
        _, _, raw_key = await _setup_authenticated_key( client, db_session )
        response = await _ingest( client, raw_key, [ _valid_entry( src_port=70000 ) ] )
        assert response.json( )[ "rejected" ] == 1

    @pytest.mark.anyio
    async def test_negative_port_rejected(
        self, client: AsyncClient, redis_client: Redis, db_session: AsyncSession, mock_email_send: AsyncMock
    ) -> None:
        _, _, raw_key = await _setup_authenticated_key( client, db_session )
        response = await _ingest( client, raw_key, [ _valid_entry( dst_port=-1 ) ] )
        assert response.json( )[ "rejected" ] == 1

    @pytest.mark.anyio
    async def test_negative_packet_size_rejected(
        self, client: AsyncClient, redis_client: Redis, db_session: AsyncSession, mock_email_send: AsyncMock
    ) -> None:
        _, _, raw_key = await _setup_authenticated_key( client, db_session )
        response = await _ingest( client, raw_key, [ _valid_entry( packet_size_bytes=-1 ) ] )
        assert response.json( )[ "rejected" ] == 1

    @pytest.mark.anyio
    async def test_invalid_ip_format_rejected(
        self, client: AsyncClient, redis_client: Redis, db_session: AsyncSession, mock_email_send: AsyncMock
    ) -> None:
        _, _, raw_key = await _setup_authenticated_key( client, db_session )
        response = await _ingest( client, raw_key, [ _valid_entry( src_ip="not-an-ip" ) ] )
        assert response.json( )[ "rejected" ] == 1

    @pytest.mark.anyio
    async def test_missing_required_field_rejected(
        self, client: AsyncClient, redis_client: Redis, db_session: AsyncSession, mock_email_send: AsyncMock
    ) -> None:
        _, _, raw_key = await _setup_authenticated_key( client, db_session )
        entry = _valid_entry( )
        del entry[ "protocol" ]
        response = await _ingest( client, raw_key, [ entry ] )
        assert response.json( )[ "rejected" ] == 1

    @pytest.mark.anyio
    async def test_client_supplied_anomaly_score_rejected(
        self, client: AsyncClient, redis_client: Redis, db_session: AsyncSession, mock_email_send: AsyncMock
    ) -> None:
        """A client must not be able to set its own anomaly score — this
        entry should be rejected outright (extra="forbid"), not silently
        accepted with the client's value stripped or overwritten."""
        _, _, raw_key = await _setup_authenticated_key( client, db_session )
        entry = _valid_entry( anomaly_score=0.0 )
        response = await _ingest( client, raw_key, [ entry ] )
        assert response.json( )[ "rejected" ] == 1

    @pytest.mark.anyio
    async def test_client_supplied_country_code_rejected(
        self, client: AsyncClient, redis_client: Redis, db_session: AsyncSession, mock_email_send: AsyncMock
    ) -> None:
        _, _, raw_key = await _setup_authenticated_key( client, db_session )
        entry = _valid_entry( country_code="US" )
        response = await _ingest( client, raw_key, [ entry ] )
        assert response.json( )[ "rejected" ] == 1


# ═══════════════════════════════════════════════════════════════════
# Batch size limits
# ═══════════════════════════════════════════════════════════════════

class TestBatchSizeLimits:
    """Tests around the whole-batch envelope, not individual entries."""

    @pytest.mark.anyio
    async def test_empty_entries_list_rejected_with_422(
        self, client: AsyncClient, redis_client: Redis, db_session: AsyncSession, mock_email_send: AsyncMock
    ) -> None:
        """min_length=1 on the request schema — this must fail the whole
        request at the schema layer, unlike per-entry validation failures."""
        _, _, raw_key = await _setup_authenticated_key( client, db_session )
        response = await _ingest( client, raw_key, [ ] )
        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_batch_at_max_size_accepted(
        self, client: AsyncClient, redis_client: Redis, db_session: AsyncSession, mock_email_send: AsyncMock
    ) -> None:
        _, _, raw_key = await _setup_authenticated_key( client, db_session )
        entries = [ _valid_entry( ) for _ in range( settings.ingest_max_batch_size ) ]

        response = await _ingest( client, raw_key, entries )

        assert response.status_code == 207
        assert response.json( )[ "accepted" ] == settings.ingest_max_batch_size

    @pytest.mark.anyio
    async def test_batch_exceeding_max_size_rejected_with_422(
        self, client: AsyncClient, redis_client: Redis, db_session: AsyncSession, mock_email_send: AsyncMock
    ) -> None:
        _, _, raw_key = await _setup_authenticated_key( client, db_session )
        entries = [ _valid_entry( ) for _ in range( settings.ingest_max_batch_size + 1 ) ]

        response = await _ingest( client, raw_key, entries )

        assert response.status_code == 422


# ═══════════════════════════════════════════════════════════════════
# Data integrity — server-derived fields, persistence
# ═══════════════════════════════════════════════════════════════════

class TestDataIntegrity:
    """Confirms accepted rows are persisted correctly and rejected rows
    aren't persisted at all."""

    @pytest.mark.anyio
    async def test_persisted_entry_uses_authenticated_user_and_api_key(
        self, client: AsyncClient, redis_client: Redis, db_session: AsyncSession, mock_email_send: AsyncMock
    ) -> None:
        access_token, api_key_id, raw_key = await _setup_authenticated_key( client, db_session )

        response = await _ingest( client, raw_key, [ _valid_entry( ) ] )
        assert response.json( )[ "accepted" ] == 1

        result = await db_session.execute(
            select( LogEntry ).order_by( LogEntry.id.desc( ) ).limit( 1 )
        )
        row = result.scalar_one( )
        assert str( row.api_key_id ) == api_key_id

    @pytest.mark.anyio
    async def test_rejected_entries_not_persisted(
        self, client: AsyncClient, redis_client: Redis, db_session: AsyncSession, mock_email_send: AsyncMock
    ) -> None:
        _, _, raw_key = await _setup_authenticated_key( client, db_session, email="persist@example.com" )

        response = await _ingest(
            client, raw_key,
            [ _valid_entry( ), _valid_entry( protocol="BOGUS" ) ]
        )
        assert response.json( )[ "accepted" ] == 1

        result = await db_session.execute( select( LogEntry ) )
        user_id = ( await db_session.execute(
            select( LogEntry.user_id ).limit( 1 )
        ) ).scalar_one( )
        count = await _count_log_entries( db_session, str( user_id ) )
        assert count == 1


# ═══════════════════════════════════════════════════════════════════
# Bulk-insert fallback path
# ═══════════════════════════════════════════════════════════════════

class TestBulkInsertFallback:
    """Exercises the DB-constraint-level failure path — cases where an
    entry passes Pydantic validation but still fails to insert.
    """

    @pytest.mark.anyio
    async def test_port_exceeding_smallint_range_falls_back_correctly(
        self, client: AsyncClient, redis_client: Redis, db_session: AsyncSession, mock_email_send: AsyncMock
    ) -> None:
        
        _, _, raw_key = await _setup_authenticated_key( client, db_session, email="fallback@example.com" )
        entries = [
            _valid_entry( ),
            _valid_entry( ),   # valid per schema, overflows SMALLINT
            _valid_entry( protocol="Not a valid one" ),
        ]

        response = await _ingest( client, raw_key, entries )

        body = response.json( )
        assert body[ "accepted" ] == 2, (
            "If this is 0, the bulk-insert fallback isn't catching the DB error."
        )
        assert body[ "rejected" ] == 1
        assert body[ "errors" ][ 0 ][ "index" ] == 2


# ═══════════════════════════════════════════════════════════════════
# Rate limiting
# ═══════════════════════════════════════════════════════════════════

class TestIngestRateLimiting:
    """Confirms the ingest rate limiter actually engages. Kept minimal —
    the bulk of rate-limiter behaviour likely belongs in
    test_rate_limiter.py; this just confirms it's wired up on this route."""

    @pytest.mark.anyio
    async def test_exceeding_rate_limit_returns_429(
        self, client: AsyncClient, redis_client: Redis, db_session: AsyncSession, mock_email_send: AsyncMock
    ) -> None:
        _, _, api_key = await _setup_authenticated_key( client, db_session )

        strict = _build_strict_limiter( 500, 60 )  # accounts for register call above

        async def _strict_auth( request: FastAPIRequest, response: FastAPIResponse ) -> None:
            await strict( request, response )

        app.dependency_overrides[ get_ingest_rate_limiter ] = _strict_auth

        statuses = [ ]
        for _ in range( 501 ):
            response = await _ingest( client, api_key, [ _valid_entry( ) ] )
            statuses.append( response.status_code )

        assert 429 in statuses