from __future__ import annotations

import base64
import json
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient, Response
from models.models import User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# ═══════════════════════════════════════════════════════════════════
# Helpers — auth / setup
# ═══════════════════════════════════════════════════════════════════

VALID_EMAIL        = "logs-tester@example.com"
VALID_PASSWORD     = "Str0ng!Pass"
VALID_DISPLAY_NAME = "Logs Tester"
VALID_KEY_LABEL    = "Logs Test Key"


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
    payload = _build_register_payload(
        email=email, password=password, display_name=display_name
    )
    return await client.post( "/auth/register", json=payload )


async def _login_user(
    client:   AsyncClient,
    email:    str = VALID_EMAIL,
    password: str = VALID_PASSWORD
) -> Response:
    return await client.post(
        "/auth/login",
        json={ "email": email, "password": password }
    )


async def _register_and_login(
    client:       AsyncClient,
    db_session:   AsyncSession,
    email:        str = VALID_EMAIL,
    password:     str = VALID_PASSWORD,
    display_name: str = VALID_DISPLAY_NAME
) -> Response:
    """Register, verify email, then login, returning the login response."""
    await _register_user( client, email=email, password=password, display_name=display_name )
    await _verify_user_email( db_session, email=email )
    return await _login_user( client, email=email, password=password )


async def _verify_user_email(
    db_session: AsyncSession,
    email:      str = VALID_EMAIL
) -> None:
    """Mark a user's email as verified directly in the database."""
    from models.models import EmailVerificationToken

    result = await db_session.execute(
        select( User ).where( User.email == email.lower( ) )
    )
    user = result.scalar_one_or_none( )
    assert user is not None, f"No user found with email { email }"

    from sqlalchemy import update

    await db_session.execute(
        update( EmailVerificationToken )
        .where(
            EmailVerificationToken.user_id == user.id,
            EmailVerificationToken.used_at.is_( None )
        )
        .values( used_at=datetime.now( UTC ) )
    )

    user.email_verified_at = datetime.now( UTC )
    await db_session.commit( )


async def _create_api_key(
    client:       AsyncClient,
    access_token: str,
    label:        str = VALID_KEY_LABEL
) -> Response:
    return await client.post(
        "/api-keys",
        json={ "label": label },
        headers={ "Authorization": f"Bearer { access_token }" }
    )


async def _setup_user_with_key(
    client:     AsyncClient,
    db_session: AsyncSession,
    email:      str = VALID_EMAIL
) -> tuple[ str, str, str, str ]:
    """Register, login, create an API key. Returns (access_token, api_key_id, raw_api_key, user_id)."""
    response     = await _register_and_login( client, db_session, email=email )
    data         = response.json( )
    access_token = data[ "access_token" ]
    user_id      = data[ "user" ][ "id" ]

    key_response = await _create_api_key( client, access_token )
    key_data     = key_response.json( )
    api_key_id   = key_data[ "id" ]
    raw_api_key  = key_data[ "api_key" ]

    return access_token, api_key_id, raw_api_key, user_id


# ═══════════════════════════════════════════════════════════════════
# Helpers — log entry creation
# ═══════════════════════════════════════════════════════════════════

def _iso_now( ) -> str:
    return datetime.now( UTC ).isoformat( )


def _valid_entry( **overrides ) -> dict:
    entry = {
        "src_ip":            "192.168.1.10",
        "dst_ip":            "10.0.0.5",
        "src_port":          443,
        "dst_port":          51820,
        "protocol":          "TCP",
        "packet_size_bytes": 1500,
        "flags":             "SYN,ACK",
        "raw_payload":       { "note": "test entry" },
        "captured_at":       _iso_now( )
    }
    entry.update( overrides )
    return entry


def _batch_payload( entries: list[ dict ] ) -> dict:
    return { "entries": entries }


async def _ingest(
    client:  AsyncClient,
    raw_key: str,
    entries: list[ dict ]
) -> Response:
    return await client.post(
        "/ingest",
        json=_batch_payload( entries ),
        headers={ "X-API-Key": raw_key }
    )


async def _ingest_entries(
    client:     AsyncClient,
    raw_key:    str,
    count:      int,
    *,
    base_time:  datetime | None = None,
    start_port: int = 443
) -> None:
    """Ingest *count* log entries, each with a unique captured_at and dst_port."""
    if base_time is None:
        base_time = datetime.now( UTC )

    for i in range( count ):
        entry = _valid_entry(
            dst_port=start_port + i,
            captured_at=base_time.isoformat( )
        )
        # Advance base_time by 1 second per entry so each has a distinct ordering key
        base_time = base_time.replace( microsecond=0 )  # strip microseconds for clean ordering
        await _ingest( client, raw_key, [ entry ] )


# ═══════════════════════════════════════════════════════════════════
# Helpers — cursor manipulation (for tampering tests)
# ═══════════════════════════════════════════════════════════════════

def _decode_cursor( cursor: str ) -> dict:
    """Decode a base64 cursor back to a dict for inspection."""
    json_str = base64.urlsafe_b64decode( cursor.encode( ) ).decode( )
    return json.loads( json_str )


def _make_tampered_cursor_missing_key( ) -> str:
    """Cursor with only 'id' but no 'captured_at'."""
    payload = { "id": 1 }
    return base64.urlsafe_b64encode( json.dumps( payload ).encode( ) ).decode( )


def _make_tampered_cursor_invalid_json( ) -> str:
    """Cursor that is valid base64 but not valid JSON."""
    return base64.urlsafe_b64encode( b"this is not json" ).decode( )


def _make_tampered_cursor_invalid_base64( ) -> str:
    """Cursor that is not valid base64 at all."""
    return "!!! not valid base64 !!!"


def _make_tampered_cursor_wrong_types( ) -> str:
    """Cursor with correct keys but wrong value types (invalid date string)."""
    payload = { "id": "not-an-int", "captured_at": "not-a-valid-iso-date" }
    return base64.urlsafe_b64encode( json.dumps( payload ).encode( ) ).decode( )


# ═══════════════════════════════════════════════════════════════════
# Happy path — basic retrieval
# ═══════════════════════════════════════════════════════════════════

class TestGetLogsHappyPath:
    """Basic retrieval tests for GET /logs."""

    @pytest.mark.anyio
    async def test_no_logs_returns_empty_list(
        self, client: AsyncClient, db_session: AsyncSession, mock_email_send: AsyncMock
    ) -> None:
        """A user with no log entries gets an empty list, no cursor, has_more=False."""
        response     = await _register_and_login( client, db_session )
        access_token = response.json( )[ "access_token" ]

        resp = await client.get(
            "/logs",
            headers={ "Authorization": f"Bearer { access_token }" }
        )

        assert resp.status_code == 200
        body = resp.json( )
        assert body[ "entries" ] == [ ]
        assert body[ "next_cursor" ] is None
        assert body[ "has_more" ] is False

    @pytest.mark.anyio
    async def test_retrieves_ingested_entries(
        self, client: AsyncClient, db_session: AsyncSession, mock_email_send: AsyncMock
    ) -> None:
        """Ingested log entries are visible via GET /logs."""
        access_token, _, raw_key, _ = await _setup_user_with_key( client, db_session )

        await _ingest_entries( client, raw_key, 3 )

        resp = await client.get(
            "/logs",
            headers={ "Authorization": f"Bearer { access_token }" }
        )

        assert resp.status_code == 200
        body = resp.json( )
        assert len( body[ "entries" ] ) == 3
        assert body[ "has_more" ] is False
        assert body[ "next_cursor" ] is None

        # Verify entry shape
        entry = body[ "entries" ][ 0 ]
        assert "id" in entry
        assert "src_ip" in entry
        assert "dst_ip" in entry
        assert "src_port" in entry
        assert "dst_port" in entry
        assert "protocol" in entry
        assert "packet_size_bytes" in entry
        assert "anomaly_score" in entry
        assert "anomaly_reasons" in entry
        assert "captured_at" in entry

    @pytest.mark.anyio
    async def test_entries_ordered_by_captured_at_desc(
        self, client: AsyncClient, db_session: AsyncSession, mock_email_send: AsyncMock
    ) -> None:
        """Entries must be returned in descending captured_at order (newest first)."""
        access_token, _, raw_key, _ = await _setup_user_with_key( client, db_session )

        # Ingest entries with distinct captured_at values
        base = datetime( 2026, 1, 1, 12, 0, 0, tzinfo=UTC )
        for i in range( 5 ):
            t     = base.replace( hour=12 + i )
            entry = _valid_entry( dst_port=100 + i, captured_at=t.isoformat( ) )
            await _ingest( client, raw_key, [ entry ] )

        resp = await client.get(
            "/logs",
            headers={ "Authorization": f"Bearer { access_token }" }
        )

        body    = resp.json( )
        entries = body[ "entries" ]
        assert len( entries ) == 5

        # Verify descending order: first entry should be the latest hour
        captured_ats = [ e[ "captured_at" ] for e in entries ]
        assert captured_ats == sorted( captured_ats, reverse=True ), (
            f"Expected descending order, got { captured_ats }"
        )

    @pytest.mark.anyio
    async def test_respects_explicit_limit(
        self, client: AsyncClient, db_session: AsyncSession, mock_email_send: AsyncMock
    ) -> None:
        """Passing limit=N returns at most N entries."""
        access_token, _, raw_key, _ = await _setup_user_with_key( client, db_session )

        await _ingest_entries( client, raw_key, 10 )

        resp = await client.get(
            "/logs",
            params={ "limit": 5 },
            headers={ "Authorization": f"Bearer { access_token }" }
        )

        body = resp.json( )
        assert len( body[ "entries" ] ) == 5
        assert body[ "has_more" ] is True
        assert body[ "next_cursor" ] is not None

    @pytest.mark.anyio
    async def test_requires_authentication(
        self, client: AsyncClient
    ) -> None:
        """Unauthenticated requests must be rejected."""
        resp = await client.get( "/logs" )
        assert resp.status_code in ( 401, 403 )


# ═══════════════════════════════════════════════════════════════════
# Pagination — boundary cases
# ═══════════════════════════════════════════════════════════════════

class TestGetLogsPagination:
    """Tests for cursor-based pagination edge cases."""

    @pytest.mark.anyio
    async def test_pagination_with_cursor_returns_next_page(
        self, client: AsyncClient, db_session: AsyncSession, mock_email_send: AsyncMock
    ) -> None:
        """Request page 1, use its cursor to get page 2 — verify no overlap."""
        access_token, _, raw_key, _ = await _setup_user_with_key( client, db_session )

        await _ingest_entries( client, raw_key, 10 )

        # Page 1
        resp1 = await client.get(
            "/logs",
            params={ "limit": 4 },
            headers={ "Authorization": f"Bearer { access_token }" }
        )
        body1  = resp1.json( )
        assert len( body1[ "entries" ] ) == 4
        assert body1[ "has_more" ] is True
        cursor = body1[ "next_cursor" ]
        assert cursor is not None

        # Page 2
        resp2 = await client.get(
            "/logs",
            params={ "limit": 4, "cursor": cursor },
            headers={ "Authorization": f"Bearer { access_token }" }
        )
        body2 = resp2.json( )
        assert len( body2[ "entries" ] ) == 4

        # Page 3 (last page — only 2 remaining)
        cursor2 = body2[ "next_cursor" ]
        assert cursor2 is not None
        resp3 = await client.get(
            "/logs",
            params={ "limit": 4, "cursor": cursor2 },
            headers={ "Authorization": f"Bearer { access_token }" }
        )
        body3 = resp3.json( )
        assert len( body3[ "entries" ] ) == 2
        assert body3[ "has_more" ] is False
        assert body3[ "next_cursor" ] is None

        # No overlap between pages
        ids_p1 = { e[ "id" ] for e in body1[ "entries" ] }
        ids_p2 = { e[ "id" ] for e in body2[ "entries" ] }
        ids_p3 = { e[ "id" ] for e in body3[ "entries" ] }
        assert ids_p1.isdisjoint( ids_p2 )
        assert ids_p1.isdisjoint( ids_p3 )
        assert ids_p2.isdisjoint( ids_p3 )

    @pytest.mark.anyio
    async def test_limit_1_minimum_boundary(
        self, client: AsyncClient, db_session: AsyncSession, mock_email_send: AsyncMock
    ) -> None:
        """limit=1 is the minimum and must return exactly 1 entry."""
        access_token, _, raw_key, _ = await _setup_user_with_key( client, db_session )

        await _ingest_entries( client, raw_key, 5 )

        resp = await client.get(
            "/logs",
            params={ "limit": 1 },
            headers={ "Authorization": f"Bearer { access_token }" }
        )

        body = resp.json( )
        assert len( body[ "entries" ] ) == 1
        assert body[ "has_more" ] is True
        assert body[ "next_cursor" ] is not None

    @pytest.mark.anyio
    async def test_limit_50_maximum_boundary(
        self, client: AsyncClient, db_session: AsyncSession, mock_email_send: AsyncMock
    ) -> None:
        """limit=50 is the maximum and must be accepted."""
        access_token, _, raw_key, _ = await _setup_user_with_key( client, db_session )

        await _ingest_entries( client, raw_key, 5 )

        resp = await client.get(
            "/logs",
            params={ "limit": 50 },
            headers={ "Authorization": f"Bearer { access_token }" }
        )

        assert resp.status_code == 200
        body = resp.json( )
        assert len( body[ "entries" ] ) == 5

    @pytest.mark.anyio
    async def test_limit_0_rejected(
        self, client: AsyncClient, db_session: AsyncSession, mock_email_send: AsyncMock
    ) -> None:
        """limit=0 is below the minimum (ge=1) and must return 422."""
        response     = await _register_and_login( client, db_session )
        access_token = response.json( )[ "access_token" ]

        resp = await client.get(
            "/logs",
            params={ "limit": 0 },
            headers={ "Authorization": f"Bearer { access_token }" }
        )

        assert resp.status_code == 422

    @pytest.mark.anyio
    async def test_limit_51_rejected(
        self, client: AsyncClient, db_session: AsyncSession, mock_email_send: AsyncMock
    ) -> None:
        """limit=51 is above the maximum (le=50) and must return 422."""
        response     = await _register_and_login( client, db_session )
        access_token = response.json( )[ "access_token" ]

        resp = await client.get(
            "/logs",
            params={ "limit": 51 },
            headers={ "Authorization": f"Bearer { access_token }" }
        )

        assert resp.status_code == 422

    @pytest.mark.anyio
    async def test_exactly_limit_entries_no_more(
        self, client: AsyncClient, db_session: AsyncSession, mock_email_send: AsyncMock
    ) -> None:
        """When entries equal limit, has_more=False and next_cursor=None."""
        access_token, _, raw_key, _ = await _setup_user_with_key( client, db_session )

        await _ingest_entries( client, raw_key, 5 )

        resp = await client.get(
            "/logs",
            params={ "limit": 5 },
            headers={ "Authorization": f"Bearer { access_token }" }
        )

        body = resp.json( )
        assert len( body[ "entries" ] ) == 5
        assert body[ "has_more" ] is False
        assert body[ "next_cursor" ] is None

    @pytest.mark.anyio
    async def test_limit_plus_one_entries_shows_has_more(
        self, client: AsyncClient, db_session: AsyncSession, mock_email_send: AsyncMock
    ) -> None:
        """When entries > limit, exactly *limit* are returned with has_more=True."""
        access_token, _, raw_key, _ = await _setup_user_with_key( client, db_session )

        await _ingest_entries( client, raw_key, 8 )

        resp = await client.get(
            "/logs",
            params={ "limit": 5 },
            headers={ "Authorization": f"Bearer { access_token }" }
        )

        body = resp.json( )
        assert len( body[ "entries" ] ) == 5
        assert body[ "has_more" ] is True
        assert body[ "next_cursor" ] is not None

    @pytest.mark.anyio
    async def test_cursor_past_all_entries_returns_empty(
        self, client: AsyncClient, db_session: AsyncSession, mock_email_send: AsyncMock
    ) -> None:
        """A cursor pointing past the last entry returns empty with has_more=False."""
        access_token, _, raw_key, _ = await _setup_user_with_key( client, db_session )

        await _ingest_entries( client, raw_key, 3 )

        # Build a cursor pointing to a time far in the past (before all entries)
        payload     = { "id": 0, "captured_at": "2000-01-01T00:00:00+00:00" }
        past_cursor = base64.urlsafe_b64encode(
            json.dumps( payload ).encode( )
        ).decode( )

        resp = await client.get(
            "/logs",
            params={ "limit": 5, "cursor": past_cursor },
            headers={ "Authorization": f"Bearer { access_token }" }
        )

        body = resp.json( )
        assert body[ "entries" ] == [ ]
        assert body[ "has_more" ] is False
        assert body[ "next_cursor" ] is None

    @pytest.mark.anyio
    async def test_default_limit_is_20(
        self, client: AsyncClient, db_session: AsyncSession, mock_email_send: AsyncMock
    ) -> None:
        """When no limit is specified, the default of 20 is used."""
        access_token, _, raw_key, _ = await _setup_user_with_key( client, db_session )

        await _ingest_entries( client, raw_key, 25 )

        resp = await client.get(
            "/logs",
            headers={ "Authorization": f"Bearer { access_token }" }
        )

        body = resp.json( )
        assert len( body[ "entries" ] ) == 20
        assert body[ "has_more" ] is True


# ═══════════════════════════════════════════════════════════════════
# Cursor security — tampering & cross-user isolation
# ═══════════════════════════════════════════════════════════════════

class TestGetLogsCursorSecurity:
    """Tests for cursor tampering and cross-user isolation."""

    # ── Tampered cursors ──────────────────────────────────────────

    @pytest.mark.anyio
    async def test_tampered_cursor_missing_key_returns_400(
        self, client: AsyncClient, db_session: AsyncSession, mock_email_send: AsyncMock
    ) -> None:
        """A cursor missing the 'captured_at' key must return 400."""
        response     = await _register_and_login( client, db_session )
        access_token = response.json( )[ "access_token" ]

        bad_cursor = _make_tampered_cursor_missing_key( )

        resp = await client.get(
            "/logs",
            params={ "cursor": bad_cursor },
            headers={ "Authorization": f"Bearer { access_token }" }
        )

        assert resp.status_code == 400
        assert "invalid cursor" in resp.json( )[ "detail" ].lower( )

    @pytest.mark.anyio
    async def test_tampered_cursor_invalid_json_returns_400(
        self, client: AsyncClient, db_session: AsyncSession, mock_email_send: AsyncMock
    ) -> None:
        """A cursor that decodes to non-JSON must return 400."""
        response     = await _register_and_login( client, db_session )
        access_token = response.json( )[ "access_token" ]

        bad_cursor = _make_tampered_cursor_invalid_json( )

        resp = await client.get(
            "/logs",
            params={ "cursor": bad_cursor },
            headers={ "Authorization": f"Bearer { access_token }" }
        )

        assert resp.status_code == 400
        assert "invalid cursor" in resp.json( )[ "detail" ].lower( )

    @pytest.mark.anyio
    async def test_tampered_cursor_invalid_base64_returns_400(
        self, client: AsyncClient, db_session: AsyncSession, mock_email_send: AsyncMock
    ) -> None:
        """A cursor that is not valid base64 must return 400."""
        response     = await _register_and_login( client, db_session )
        access_token = response.json( )[ "access_token" ]

        bad_cursor = _make_tampered_cursor_invalid_base64( )

        resp = await client.get(
            "/logs",
            params={ "cursor": bad_cursor },
            headers={ "Authorization": f"Bearer { access_token }" }
        )

        assert resp.status_code == 400
        assert "invalid cursor" in resp.json( )[ "detail" ].lower( )

    @pytest.mark.anyio
    async def test_tampered_cursor_wrong_types_returns_400(
        self, client: AsyncClient, db_session: AsyncSession, mock_email_send: AsyncMock
    ) -> None:
        """A cursor where 'captured_at' is not a valid ISO datetime must return 400."""
        response     = await _register_and_login( client, db_session )
        access_token = response.json( )[ "access_token" ]

        bad_cursor = _make_tampered_cursor_wrong_types( )

        resp = await client.get(
            "/logs",
            params={ "cursor": bad_cursor },
            headers={ "Authorization": f"Bearer { access_token }" }
        )

        assert resp.status_code == 400
        assert "invalid cursor" in resp.json( )[ "detail" ].lower( )

    @pytest.mark.anyio
    async def test_empty_cursor_rejected(
        self, client: AsyncClient, db_session: AsyncSession, mock_email_send: AsyncMock
    ) -> None:
        """An empty string cursor must be rejected (min_length=1)."""
        response     = await _register_and_login( client, db_session )
        access_token = response.json( )[ "access_token" ]

        resp = await client.get(
            "/logs",
            params={ "cursor": "" },
            headers={ "Authorization": f"Bearer { access_token }" }
        )

        assert resp.status_code == 422

    # ── Cross-user isolation ──────────────────────────────────────

    @pytest.mark.anyio
    async def test_user_a_cannot_see_user_b_entries(
        self, client: AsyncClient, db_session: AsyncSession, mock_email_send: AsyncMock
    ) -> None:
        """User A's GET /logs must never include User B's log entries."""
        # User A
        access_a, _, raw_a, _ = await _setup_user_with_key(
            client, db_session, email="user-a@example.com"
        )
        await _ingest_entries( client, raw_a, 5 )

        # User B — fresh session, separate user
        response_b = await _register_and_login(
            client, db_session, email="user-b@example.com"
        )
        access_b = response_b.json( )[ "access_token" ]

        # User B sees only their own entries (none)
        resp = await client.get(
            "/logs",
            headers={ "Authorization": f"Bearer { access_b }" }
        )

        body = resp.json( )
        assert body[ "entries" ] == [ ]
        assert body[ "has_more" ] is False

        # User A still sees their 5 entries
        resp_a = await client.get(
            "/logs",
            headers={ "Authorization": f"Bearer { access_a }" }
        )
        assert len( resp_a.json( )[ "entries" ] ) == 5

    @pytest.mark.anyio
    async def test_cross_user_cursor_does_not_leak_data(
        self, client: AsyncClient, db_session: AsyncSession, mock_email_send: AsyncMock
    ) -> None:
        """When User B uses a cursor obtained from User A's logs, User B must
        NOT see any of User A's log entries. The cursor is only a pagination
        anchor — the user_id filter still applies."""
        # User A: ingest entries and get a valid cursor
        access_a, _, raw_a, _ = await _setup_user_with_key(
            client, db_session, email="user-a-cursor@example.com"
        )
        await _ingest_entries( client, raw_a, 10 )

        resp_a = await client.get(
            "/logs",
            params={ "limit": 5 },
            headers={ "Authorization": f"Bearer { access_a }" }
        )
        body_a           = resp_a.json( )
        user_a_cursor    = body_a[ "next_cursor" ]
        assert user_a_cursor is not None
        user_a_entry_ids = { e[ "id" ] for e in body_a[ "entries" ] }

        # User B: ingest some entries too, then use User A's cursor
        response_b = await _register_and_login(
            client, db_session, email="user-b-cursor@example.com"
        )
        access_b = response_b.json( )[ "access_token" ]

        # Also give User B an API key and entries, so they have their own data
        key_resp_b = await _create_api_key( client, access_b )
        raw_b      = key_resp_b.json( )[ "api_key" ]
        await _ingest_entries( client, raw_b, 5 )

        # User B uses User A's cursor
        resp_b = await client.get(
            "/logs",
            params={ "limit": 10, "cursor": user_a_cursor },
            headers={ "Authorization": f"Bearer { access_b }" }
        )

        body_b = resp_b.json( )
        # User B must never see User A's entries
        b_ids = { e[ "id" ] for e in body_b[ "entries" ] }
        assert user_a_entry_ids.isdisjoint( b_ids ), (
            f"User B should not see User A's entries. "
            f"User A ids: { user_a_entry_ids }, User B saw: { b_ids }"
        )

    @pytest.mark.anyio
    async def test_forged_cursor_with_another_users_entry_id(
        self, client: AsyncClient, db_session: AsyncSession, mock_email_send: AsyncMock
    ) -> None:
        """A malicious user crafts a cursor pointing to another user's known
        entry id. The endpoint must still filter by user_id, returning only
        the attacker's own entries (or none)."""
        # User A: ingest entries
        _, _, raw_a, _ = await _setup_user_with_key(
            client, db_session, email="user-a-forge@example.com"
        )
        await _ingest_entries( client, raw_a, 3 )

        # Get User A's entry ids
        access_a_resp = await _login_user(
            client, email="user-a-forge@example.com"
        )
        access_a      = access_a_resp.json( )[ "access_token" ]
        resp_a        = await client.get(
            "/logs",
            headers={ "Authorization": f"Bearer { access_a }" }
        )
        user_a_entries = resp_a.json( )[ "entries" ]
        assert len( user_a_entries ) > 0
        # Pick the id and captured_at from User A's last (oldest) entry
        last_a = user_a_entries[ -1 ]

        # User B (attacker): craft a cursor pointing at User A's entry
        response_b = await _register_and_login(
            client, db_session, email="user-b-forge@example.com"
        )
        access_b = response_b.json( )[ "access_token" ]

        forged_payload = {
            "id":          last_a[ "id" ],
            "captured_at": last_a[ "captured_at" ]
        }
        forged_cursor = base64.urlsafe_b64encode(
            json.dumps( forged_payload ).encode( )
        ).decode( )

        resp_b = await client.get(
            "/logs",
            params={ "cursor": forged_cursor },
            headers={ "Authorization": f"Bearer { access_b }" }
        )

        # Must succeed (valid cursor shape) but return no User A data
        assert resp_b.status_code == 200
        body_b      = resp_b.json( )
        b_ids       = { e[ "id" ] for e in body_b[ "entries" ] }
        user_a_ids  = { e[ "id" ] for e in user_a_entries }
        assert b_ids.isdisjoint( user_a_ids ), (
            f"Forged cursor must not leak cross-user data. "
            f"User A ids: { user_a_ids }, User B saw: { b_ids }"
        )

    @pytest.mark.anyio
    async def test_cursor_tied_to_user_does_not_affect_isolation(
        self, client: AsyncClient, db_session: AsyncSession, mock_email_send: AsyncMock
    ) -> None:
        """Even when both users have entries, User B using User A's cursor
        only sees User B's own entries that fall within the cursor window."""
        # User A
        _, _, raw_a, _ = await _setup_user_with_key(
            client, db_session, email="user-a-iso@example.com"
        )
        await _ingest_entries( client, raw_a, 3 )

        # User B — also has entries
        response_b = await _register_and_login(
            client, db_session, email="user-b-iso@example.com"
        )
        access_b    = response_b.json( )[ "access_token" ]
        key_resp_b  = await _create_api_key( client, access_b )
        raw_b       = key_resp_b.json( )[ "api_key" ]
        await _ingest_entries( client, raw_b, 3 )

        # Get User A's first page cursor
        access_a_resp = await _login_user( client, email="user-a-iso@example.com" )
        access_a      = access_a_resp.json( )[ "access_token" ]
        resp_a        = await client.get(
            "/logs",
            params={ "limit": 1 },
            headers={ "Authorization": f"Bearer { access_a }" }
        )
        cursor_a     = resp_a.json( )[ "next_cursor" ]
        a_entry_ids  = { e[ "id" ] for e in resp_a.json( )[ "entries" ] }

        # User B uses User A's cursor
        resp_b = await client.get(
            "/logs",
            params={ "limit": 10, "cursor": cursor_a },
            headers={ "Authorization": f"Bearer { access_b }" }
        )

        body_b      = resp_b.json( )
        b_entry_ids = { e[ "id" ] for e in body_b[ "entries" ] }
        # Cross-user isolation: User B never sees User A's entries
        assert a_entry_ids.isdisjoint( b_entry_ids )


# ═══════════════════════════════════════════════════════════════════
# Edge cases
# ═══════════════════════════════════════════════════════════════════

class TestGetLogsEdgeCases:
    """Miscellaneous edge-case tests for GET /logs."""

    @pytest.mark.anyio
    async def test_cursor_with_future_timestamp_returns_empty(
        self, client: AsyncClient, db_session: AsyncSession, mock_email_send: AsyncMock
    ) -> None:
        """A cursor with a future captured_at returns empty (no entries match)."""
        response     = await _register_and_login( client, db_session )
        access_token = response.json( )[ "access_token" ]

        future_payload = {
            "id":          999999,
            "captured_at": "2099-01-01T00:00:00+00:00"
        }
        future_cursor = base64.urlsafe_b64encode(
            json.dumps( future_payload ).encode( )
        ).decode( )

        resp = await client.get(
            "/logs",
            params={ "cursor": future_cursor },
            headers={ "Authorization": f"Bearer { access_token }" }
        )

        assert resp.status_code == 200
        body = resp.json( )
        assert body[ "entries" ] == [ ]
        assert body[ "has_more" ] is False
        assert body[ "next_cursor" ] is None

    @pytest.mark.anyio
    async def test_multiple_pages_exhaust_all_entries(
        self, client: AsyncClient, db_session: AsyncSession, mock_email_send: AsyncMock
    ) -> None:
        """Walking through all pages with cursor must see every entry exactly once."""
        access_token, _, raw_key, _ = await _setup_user_with_key( client, db_session )

        total = 13
        await _ingest_entries( client, raw_key, total )

        seen_ids:  set[ int ]  = set( )
        cursor:    str | None  = None
        page_count = 0

        while True:
            params: dict = { "limit": 5 }
            if cursor:
                params[ "cursor" ] = cursor

            resp = await client.get(
                "/logs",
                params=params,
                headers={ "Authorization": f"Bearer { access_token }" }
            )
            body = resp.json( )
            page_count += 1

            for entry in body[ "entries" ]:
                assert entry[ "id" ] not in seen_ids, (
                    f"Duplicate entry id={ entry[ 'id' ] } on page { page_count }"
                )
                seen_ids.add( entry[ "id" ] )

            if not body[ "has_more" ]:
                break

            cursor = body[ "next_cursor" ]
            assert cursor is not None

        assert len( seen_ids ) == total
        assert page_count == 3  # 5 + 5 + 3
