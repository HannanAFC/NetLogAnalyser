"""
Redis rate limiting utilities.

Usage (in any router):
    from rate_limiter import get_auth_rate_limiter
    router = APIRouter( dependencies=[ Depends( get_auth_rate_limiter ) ] )

Or per-route:
    @router.post( "/login", dependencies=[ Depends( get_auth_rate_limiter ) ] )

Each tier owns one explicit ``scope``, so every route using a tier shares a
single per-client counter (e.g. all ``/auth/*`` routes draw from ``auth``).
"""

from __future__ import annotations

from config import settings
from fastapi import WebSocket, WebSocketException
from redis_fastapi import get_rate_limit_backend, rate_limit
from starlette.requests import HTTPConnection


# Mirror of get_client_ip in auth/dependencies.py
async def _cloudflare_identifier( request: HTTPConnection ) -> str:
    """
    Returns the real client IP, accounting for the Cloudflare Tunnel.

    The SDK's default identifier uses the immediate peer address, which behind
    the tunnel would be the same for every client.
    Parameters:
        request (HTTPConnection): FastAPI Request (or WebSocket) object.
    """
    cf_ip = request.headers.get( "cf-connecting-ip" )
    if cf_ip:
        return cf_ip

    forwarded_for = request.headers.get( "x-forwarded-for" )
    if forwarded_for:
        return forwarded_for.split( "," )[ 0 ].strip( )

    if request.client:
        return request.client.host

    return "127.0.0.1"


# Rate limit tiers - limits come from the ``ratelimit_*`` settings.
# Auth tiers fail closed: if Redis is unreachable they reject rather than let
# credential-stuffing through. Ingest/general fail open so a Redis blip does
# not take the whole API down.
get_auth_rate_limiter = rate_limit(
    limit=settings.ratelimit_auth_times,
    window=settings.ratelimit_auth_seconds,
    scope="auth",
    identifier=_cloudflare_identifier,
    fail_closed=True
)
"""Applied to /auth/* endpoints (login, register, refresh, …)."""

get_forgot_password_rate_limiter = rate_limit(
    limit=settings.ratelimit_forgot_password_times,
    window=settings.ratelimit_forgot_password_seconds,
    scope="forgot-password",
    identifier=_cloudflare_identifier,
    fail_closed=True
)
"""Stricter limit for password‑reset flows (forgot-password, reset-password)."""

get_ingest_rate_limiter = rate_limit(
    limit=settings.ratelimit_ingest_times,
    window=settings.ratelimit_ingest_seconds,
    scope="ingest",
    identifier=_cloudflare_identifier
)
"""Applied to /ingest/* endpoints."""

get_general_rate_limiter = rate_limit(
    limit=settings.ratelimit_general_times,
    window=settings.ratelimit_general_seconds,
    scope="general",
    identifier=_cloudflare_identifier
)
"""Fallback for any endpoint that doesn't have a dedicated tier."""

WS_CLOSE_RATE_LIMITED = 4429
"""Close code sent when a client exceeds the handshake limit."""


async def get_ws_rate_limiter( websocket: WebSocket ) -> None:
    """
    Rate-limit WebSocket handshakes per client IP (``ratelimit_ws_*``).

    Runs before the origin / ticket / slot gates so a flood of bad tickets is
    rejected cheaply. Fails closed: the handshake needs Redis for the ticket
    lookup anyway, so there is nothing to protect by failing open.
    """
    # get_rate_limit_backend only reads ``.app`` from its argument, which
    # every HTTPConnection (Request and WebSocket alike) provides.
    backend = await get_rate_limit_backend( websocket )  # type: ignore[arg-type]
    result  = await backend.hit(
        await _cloudflare_identifier( websocket ),
        limit=settings.ratelimit_ws_times,
        window=settings.ratelimit_ws_seconds,
        scope="ws",
        fail_closed=True
    )
    if not result.allowed:
        raise WebSocketException(
            code=WS_CLOSE_RATE_LIMITED,
            reason="Too many connection attempts"
        )
