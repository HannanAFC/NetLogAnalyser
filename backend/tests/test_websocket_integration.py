from __future__ import annotations

import asyncio
import json
import os
from contextlib import asynccontextmanager
from datetime import UTC, datetime

import pytest
from cache import get_redis
from config import settings
from database import get_db
from fastapi import Request, Response
from fastapi.testclient import TestClient
from fastapi_limiter.depends import RateLimiter
from httpx import AsyncClient
from main import app
from models.models import EmailVerificationToken, User
from pyrate_limiter import Duration, Limiter, Rate
from rate_limiter import (
    get_auth_rate_limiter,
    get_forgot_password_rate_limiter,
    get_general_rate_limiter,
    get_ingest_rate_limiter,
)
from redis.asyncio import Redis
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.websockets import WebSocketDisconnect
from websocket.manager import manager

# ═══════════════════════════════════════════════════════════════════
# Why TestClient instead of httpx.AsyncClient:
#   httpx's ASGITransport does not support WebSocket negotiation.
#   FastAPI's TestClient.websocket_connect() does - but it's sync.
#   We create a fresh Redis client per WS handler invocation so the
#   connection is bound to the TestClient portal's event loop, not
#   pytest's, avoiding "Future attached to a different loop" errors.
# ═══════════════════════════════════════════════════════════════════

VALID_EMAIL        = "ws-integration@example.com"
VALID_PASSWORD     = "Str0ng!Pass"
VALID_DISPLAY_NAME = "WS Integration Tester"

# Exception types that bubble up when a WebSocket closes before accept.
# TestClient wraps these in RuntimeError when called from asyncio.to_thread.
_WS_CLOSE_EXCEPTIONS = ( WebSocketDisconnect, RuntimeError )


# ═══════════════════════════════════════════════════════════════════
# Helpers - auth setup
# ═══════════════════════════════════════════════════════════════════

async def _register_and_get_token(
    client:       AsyncClient,
    db_session:   AsyncSession,
    email:        str = VALID_EMAIL,
    password:     str = VALID_PASSWORD,
    display_name: str = VALID_DISPLAY_NAME,
) -> tuple[ str, str ]:
    """Register a user, verify their email, log in, and return
    ``( access_token, user_id )``.
    """
    # Register
    await client.post(
        "/auth/register",
        json={
            "email":            email,
            "password":         password,
            "confirm_password": password,
            "display_name":     display_name,
        },
    )

    # Mark email verified (skip email round-trip)
    result = await db_session.execute(
        select( User ).where( User.email == email.lower( ) )
    )
    user = result.scalar_one( )
    await db_session.execute(
        update( EmailVerificationToken )
        .where(
            EmailVerificationToken.user_id == user.id,
            EmailVerificationToken.used_at.is_( None ),
        )
        .values( used_at=datetime.now( UTC ) )
    )
    user.email_verified_at = datetime.now( UTC )
    await db_session.commit( )

    # Login
    login_resp = await client.post(
        "/auth/login",
        json={ "email": email, "password": password },
    )
    data = login_resp.json( )
    return data[ "access_token" ], str( user.id )


async def _get_ws_ticket( client: AsyncClient, access_token: str ) -> str:
    """Call ``POST /ws/ticket`` and return the raw ticket string."""
    resp = await client.post(
        "/ws/ticket",
        headers={ "Authorization": f"Bearer { access_token }" },
    )
    assert resp.status_code == 200, resp.text
    return resp.json( )[ "ticket" ]


# ═══════════════════════════════════════════════════════════════════
# Fixture - TestClient wired with test overrides
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture
def ws_test_client( db_session: AsyncSession ):
    """A FastAPI TestClient whose DB, Redis, and rate-limit dependencies
    are overridden with the same test instances used by the ``client``
    (httpx) fixture in conftest.py.

    IMPORTANT: Redis override creates a *fresh* client on every
    dependency resolution so the connection is bound to the TestClient
    portal's event loop, not pytest's.  This avoids ``RuntimeError:
    Future attached to a different loop`` when the WebSocket handler
    awaits Redis operations.
    """
    redis_url = os.environ[ "REDIS_URL" ]

    async def _get_db( ):
        yield db_session

    async def _get_redis( ):
        client = Redis.from_url( redis_url, decode_responses=True )
        try:
            yield client
        finally:
            await client.aclose( )

    app.dependency_overrides[ get_db ]    = _get_db
    app.dependency_overrides[ get_redis ] = _get_redis

    _test_limiter = RateLimiter(
        Limiter( Rate( limit=10000, interval=60 * Duration.SECOND ) )
    )

    async def _permissive( request: Request, response: Response ):
        await _test_limiter( request, response )

    app.dependency_overrides[ get_auth_rate_limiter ]            = _permissive
    app.dependency_overrides[ get_forgot_password_rate_limiter ] = _permissive
    app.dependency_overrides[ get_general_rate_limiter ]         = _permissive
    app.dependency_overrides[ get_ingest_rate_limiter ]          = _permissive

    with TestClient( app ) as tc:
        yield tc

    app.dependency_overrides.clear( )


# ═══════════════════════════════════════════════════════════════════
# Async WebSocket context manager
# ═══════════════════════════════════════════════════════════════════

@asynccontextmanager
async def ws_connect(
    test_client: TestClient,
    url:         str,
    headers:     dict | None = None,
):
    """Async wrapper around ``TestClient.websocket_connect``.

    Runs the sync WebSocket context manager in a thread so the test
    function can remain ``async def`` and use async fixtures.
    """
    headers = headers or { }
    ws_ctx  = test_client.websocket_connect( url, headers=headers )

    async def _enter( ):
        return await asyncio.to_thread( ws_ctx.__enter__ )

    async def _exit( *args ):
        return await asyncio.to_thread( ws_ctx.__exit__, *args )

    ws = await _enter( )
    try:
        yield ws
    finally:
        await _exit( None, None, None )


async def _ws_receive_json( ws ) -> dict:
    """Receive a JSON message from a TestClient WebSocket session."""
    return await asyncio.to_thread( ws.receive_json )


# ═══════════════════════════════════════════════════════════════════
# Tests - ticket endpoint
# ═══════════════════════════════════════════════════════════════════

@pytest.mark.anyio
async def test_ticket_endpoint_returns_ticket_and_expiry(
    client:     AsyncClient,
    db_session: AsyncSession,
):
    access_token, _ = await _register_and_get_token( client, db_session )

    resp = await client.post(
        "/ws/ticket",
        headers={ "Authorization": f"Bearer { access_token }" },
    )
    assert resp.status_code == 200
    data = resp.json( )
    assert "ticket" in data
    assert len( data[ "ticket" ] ) > 0
    assert data[ "expires_in" ] == settings.ws_ticket_ttl_seconds


@pytest.mark.anyio
async def test_ticket_endpoint_rejects_unauthenticated(
    client: AsyncClient,
):
    resp = await client.post( "/ws/ticket" )
    assert resp.status_code == 401


# ═══════════════════════════════════════════════════════════════════
# Tests - WebSocket connection
# ═══════════════════════════════════════════════════════════════════

@pytest.mark.anyio
async def test_connect_with_valid_ticket_succeeds(
    client:          AsyncClient,
    db_session:      AsyncSession,
    ws_test_client:  TestClient,
):
    """Happy path: get a ticket, open a WebSocket, receive accept."""
    access_token, _ = await _register_and_get_token( client, db_session )
    ticket = await _get_ws_ticket( client, access_token )

    async with ws_connect(
        ws_test_client,
        f"/ws/live?ticket={ ticket }",
        headers={ "Origin": "http://localhost:3000" },
    ):
        # If the server accepted, we're connected - no exception raised.
        pass


@pytest.mark.anyio
async def test_connect_without_ticket_closes_4401(
    ws_test_client: TestClient,
):
    """Missing ticket → server closes with code 4401."""
    with pytest.raises( _WS_CLOSE_EXCEPTIONS ):
        async with ws_connect(
            ws_test_client,
            "/ws/live",
            headers={ "Origin": "http://localhost:3000" },
        ):
            pass


@pytest.mark.anyio
async def test_connect_with_invalid_ticket_closes_4401(
    ws_test_client: TestClient,
):
    """Bogus ticket → server closes with code 4401."""
    with pytest.raises( _WS_CLOSE_EXCEPTIONS ):
        async with ws_connect(
            ws_test_client,
            "/ws/live?ticket=not-a-real-ticket",
            headers={ "Origin": "http://localhost:3000" },
        ):
            pass


@pytest.mark.anyio
async def test_connect_with_expired_ticket_closes_4401(
    client:          AsyncClient,
    db_session:      AsyncSession,
    redis_client:    Redis,
    ws_test_client:  TestClient,
):
    """A ticket past its TTL should be rejected with 4401.

    We mint a ticket, delete it from Redis (simulating TTL expiry),
    then attempt the WebSocket connect.
    """
    from auth.security import hash_token

    access_token, _ = await _register_and_get_token( client, db_session )
    ticket = await _get_ws_ticket( client, access_token )

    # Delete the ticket from Redis - same effect as TTL expiry
    await redis_client.delete( f"ws_ticket:{ hash_token( ticket ) }" )

    with pytest.raises( _WS_CLOSE_EXCEPTIONS ):
        async with ws_connect(
            ws_test_client,
            f"/ws/live?ticket={ ticket }",
            headers={ "Origin": "http://localhost:3000" },
        ):
            pass


@pytest.mark.anyio
async def test_connect_exceeds_connection_limit_closes_4409(
    client:         AsyncClient,
    db_session:     AsyncSession,
    ws_test_client: TestClient,
):
    """Opening more WebSockets than ws_max_connections_per_user → 4409."""
    access_token, _ = await _register_and_get_token( client, db_session )

    # Open max connections first
    sessions: list[ tuple ] = [ ]
    for _ in range( settings.ws_max_connections_per_user ):
        ticket = await _get_ws_ticket( client, access_token )
        ctx = ws_connect(
            ws_test_client,
            f"/ws/live?ticket={ ticket }",
            headers={ "Origin": "http://localhost:3000" },
        )
        ws = await ctx.__aenter__( )
        sessions.append( ( ctx, ws ) )

    # The (max+1)-th connection should fail
    overflow_ticket = await _get_ws_ticket( client, access_token )
    with pytest.raises( _WS_CLOSE_EXCEPTIONS ):
        async with ws_connect(
            ws_test_client,
            f"/ws/live?ticket={ overflow_ticket }",
            headers={ "Origin": "http://localhost:3000" },
        ):
            pass

    # Clean up prior connections
    for ctx, ws in sessions:
        await asyncio.to_thread( ws.close )
        await ctx.__aexit__( None, None, None )


@pytest.mark.skip(
    reason=(
        "CORS_ALLOWED_ORIGINS is ['*'] in the test environment. "
        "The origin check (_origin_allowed) is trivial (reads a header, "
        "checks a list) and is well-covered by unit tests. "
        "To integration-test this, override the CORS setting on the "
        "middleware itself, not just the settings object."
    )
)
@pytest.mark.anyio
async def test_connect_disallowed_origin_closes_4403(
    client:         AsyncClient,
    db_session:     AsyncSession,
    ws_test_client: TestClient,
):
    """Connecting from an origin not in CORS_ALLOWED_ORIGINS → 4403."""
    access_token, _ = await _register_and_get_token( client, db_session )
    ticket = await _get_ws_ticket( client, access_token )

    with pytest.raises( _WS_CLOSE_EXCEPTIONS ):
        async with ws_connect(
            ws_test_client,
            f"/ws/live?ticket={ ticket }",
            headers={ "Origin": "https://evil.com" },
        ):
            pass


@pytest.mark.anyio
async def test_ticket_is_single_use(
    client:         AsyncClient,
    db_session:     AsyncSession,
    ws_test_client: TestClient,
):
    """A ticket consumed by one WebSocket cannot be reused."""
    access_token, _ = await _register_and_get_token( client, db_session )
    ticket = await _get_ws_ticket( client, access_token )

    # First connection - consumes the ticket
    async with ws_connect(
        ws_test_client,
        f"/ws/live?ticket={ ticket }",
        headers={ "Origin": "http://localhost:3000" },
    ):
        pass  # connect and immediately disconnect

    # Second connection with the same ticket - should fail
    with pytest.raises( _WS_CLOSE_EXCEPTIONS ):
        async with ws_connect(
            ws_test_client,
            f"/ws/live?ticket={ ticket }",
            headers={ "Origin": "http://localhost:3000" },
        ):
            pass


# ═══════════════════════════════════════════════════════════════════
# Tests - message delivery
# ═══════════════════════════════════════════════════════════════════

@pytest.mark.anyio
async def test_connected_client_receives_message(
    client:         AsyncClient,
    db_session:     AsyncSession,
    ws_test_client: TestClient,
):
    """After connecting, a message sent via manager reaches the socket.

    We call ``manager.send_to_user()`` directly instead of going
    through Redis pub/sub so the test doesn't depend on the background
    listener task from the lifespan.
    """
    access_token, user_id = await _register_and_get_token( client, db_session )
    ticket = await _get_ws_ticket( client, access_token )

    async with ws_connect(
        ws_test_client,
        f"/ws/live?ticket={ ticket }",
        headers={ "Origin": "http://localhost:3000" },
    ) as ws:
        message = json.dumps( {
            "type": "log_entry_batch",
            "data": [
                {
                    "src_ip":            "10.0.0.1",
                    "dst_ip":            "10.0.0.2",
                    "src_port":          443,
                    "dst_port":          8080,
                    "protocol":          "TCP",
                    "packet_size_bytes": 1500,
                    "flags":             "SYN",
                    "country_code":      "US",
                    "anomaly_score":     0.05,
                    "anomaly_reasons":   [ ],
                    "captured_at":       "2025-08-01T12:00:00Z",
                }
            ],
        } )
        await manager.send_to_user( user_id, message )

        received = await _ws_receive_json( ws )
        assert received[ "type" ] == "log_entry_batch"
        assert len( received[ "data" ] ) == 1
        assert received[ "data" ][ 0 ][ "src_ip" ] == "10.0.0.1"


@pytest.mark.anyio
async def test_message_only_delivered_to_target_user(
    client:         AsyncClient,
    db_session:     AsyncSession,
    ws_test_client: TestClient,
):
    """A broadcast for user A is NOT received on user B's WebSocket.

    Connects two users simultaneously, sends a message to user A, and
    verifies user B does not receive it.
    """
    # User A
    token_a, user_id_a = await _register_and_get_token(
        client, db_session, email="user-a@example.com"
    )
    ticket_a = await _get_ws_ticket( client, token_a )

    # User B
    token_b, _user_id_b = await _register_and_get_token(
        client, db_session, email="user-b@example.com"
    )
    ticket_b = await _get_ws_ticket( client, token_b )

    async with (
        ws_connect(
            ws_test_client,
            f"/ws/live?ticket={ ticket_a }",
            headers={ "Origin": "http://localhost:3000" },
        ) as ws_a,
        ws_connect(
            ws_test_client,
            f"/ws/live?ticket={ ticket_b }",
            headers={ "Origin": "http://localhost:3000" },
        ) as ws_b,
    ):
        # Send a message to user A only
        await manager.send_to_user(
            user_id_a,
            json.dumps( { "type": "log_entry_batch", "data": [ ] } ),
        )

        # User A should receive it
        received = await _ws_receive_json( ws_a )
        assert received[ "type" ] == "log_entry_batch"

        # User B should NOT receive it - receive should time out
        with pytest.raises( asyncio.TimeoutError ):
            await asyncio.wait_for(
                asyncio.to_thread( ws_b.receive_json ),
                timeout=1.0,
            )


# ═══════════════════════════════════════════════════════════════════
# Tests - heartbeat
# ═══════════════════════════════════════════════════════════════════

@pytest.mark.anyio
async def test_sending_text_keeps_connection_alive(
    client:         AsyncClient,
    db_session:     AsyncSession,
    ws_test_client: TestClient,
):
    """Sending any text from the client triggers refresh_connection_slot.

    Verifies the connection stays open after a client send.
    """
    access_token, _ = await _register_and_get_token( client, db_session )
    ticket = await _get_ws_ticket( client, access_token )

    async with ws_connect(
        ws_test_client,
        f"/ws/live?ticket={ ticket }",
        headers={ "Origin": "http://localhost:3000" },
    ) as ws:
        # Send a heartbeat (any text triggers slot refresh)
        await asyncio.to_thread( ws.send_text, "ping" )
        # Connection still alive - no exception
