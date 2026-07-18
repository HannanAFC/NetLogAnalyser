"""
Redis rate limiting utilities.

Usage (in any router):
    from rate_limiter import auth_rate_limiter
    router = APIRouter( dependencies=[ Depends( auth_rate_limiter ) ] )

Or per-route:
    @router.post( "/login", dependencies=[ Depends( auth_rate_limiter ) ] )

For WebSocket endpoints use :func:`create_ws_rate_limiter` to build an
instance scoped to the connection's lifespan.
"""

from __future__ import annotations

from typing import Callable, Optional, Union

import redis.asyncio as redis
from config import settings
from fastapi import Request, Response
from fastapi_limiter.depends import RateLimiter, WebSocketRateLimiter
from fastapi_limiter.identifier import default_identifier
from pyrate_limiter import Duration, Limiter, Rate
from pyrate_limiter.buckets.redis_bucket import RedisBucket
from starlette.websockets import WebSocket

_redis: Optional[ redis.Redis ] = None


async def init_redis( ) -> None:
    """Open a shared async-Redis connection pool."""
    global _redis
    if _redis is not None:
        return  # already initialised
    _redis = redis.from_url(
        settings.redis_url.get_secret_value( ),
        encoding="utf-8",
        decode_responses=True
    )
    await _redis.ping( )


async def close_redis( ) -> None:
    """Gracefully close the Redis connection pool."""
    global _redis
    if _redis is not None:
        await _redis.close( )
        _redis = None


def _get_redis( ) -> redis.Redis:
    """Return the shared Redis connection (callable, non-async for Depends)."""
    if _redis is None:
        raise RuntimeError( "Redis has not been initialised yet." )
    return _redis


# Mirror of get_client_ip in auth/dependencies.py
async def _cloudflare_identifier( request_or_ws: Union[ Request, WebSocket ] ) -> str:
    """
    Returns the real client IP, accounting for the Cloudflare Tunnel.
    Falls back to the built-in ``default_identifier`` when used with a
    plain WebSocket (no headers access).
    Parameters:
        request_or_ws (Request | WebSocket): FastAPI Request or WebSocket object.
    """
    headers = getattr( request_or_ws, "headers", None )
    if headers is None:
        return await default_identifier( request_or_ws )

    cf_ip = headers.get( "cf-connecting-ip" )
    if cf_ip:
        return cf_ip

    forwarded_for = headers.get( "x-forwarded-for" )
    if forwarded_for:
        return forwarded_for.split( "," )[ 0 ].strip( )

    if request_or_ws.client:
        return request_or_ws.client.host

    return "127.0.0.1"


# Rate limit creator helpers
async def _create_limiter(
    times: int,
    seconds: int,
    bucket_key: str
) -> Limiter:
    """
    Build a pyrate_limiter, uses RedisBucket.
    Parameters:
        times (int): The amount of times endpoint can be called per interval.
        seconds (int): The interval period.
        bucket_key (str): A grouping identifier for the rate limit. e.g `auth` for all auth endpoints.
    """
    rate = Rate( limit=times, interval=seconds * Duration.SECOND )
    bucket = await RedisBucket.init(
        rates=[ rate ],
        redis=_get_redis( ),
        bucket_key=f"ratelimit:{ bucket_key }"
    )
    return Limiter( bucket )


async def create_rate_limiter(
    times: int,
    seconds: int,
    bucket_key: str,
    *,
    identifier: Callable = _cloudflare_identifier
) -> RateLimiter:
    """Return a *FastAPI* RateLimiter dependency for HTTP endpoints.

    The default ``identifier`` uses the Cloudflare‑aware IP resolver so
    limits are applied per real client IP rather than per tunnel/proxy IP.
    Parameters:
        times (int): The amount of times endpoint can be called per interval.
        seconds (int): The interval period.
        bucket_key (str): A grouping identifier for the rate limit. e.g `auth` for all auth endpoints.
        identifier (callable): A callable that can be used to provide an identity for rate limiting.
    """
    limiter = await _create_limiter( times, seconds, bucket_key )
    return RateLimiter( limiter, identifier=identifier )


async def create_ws_rate_limiter(
    times: int,
    seconds: int,
    bucket_key: str,
    *,
    identifier: Callable = _cloudflare_identifier
) -> WebSocketRateLimiter:
    """
    Return a *FastAPI* WebSocketRateLimiter dependency for WS endpoints.
    Parameters:
        times (int): The amount of times endpoint can be called per interval.
        seconds (int): The interval period.
        bucket_key (str): A grouping identifier for the rate limit. e.g `auth` for all auth endpoints.
        identifier (callable): A callable that can be used to provide an identity for rate limiting.
    """
    limiter = await _create_limiter( times, seconds, bucket_key )
    return WebSocketRateLimiter( limiter, identifier=identifier )


# Fallback rate limits
auth_rate_limiter: RateLimiter = RateLimiter(
    Limiter( Rate( limit=10, interval=60 * Duration.SECOND ) ),
    identifier=_cloudflare_identifier
)
"""Applied to /auth/* endpoints (login, register, refresh, …)."""

forgot_password_rate_limiter: RateLimiter = RateLimiter(
    Limiter( Rate( limit=3, interval=60 * Duration.SECOND ) ),
    identifier=_cloudflare_identifier
)
"""Stricter limit for password‑reset flows (forgot-password, reset-password)."""

ingest_rate_limiter: RateLimiter = RateLimiter(
    Limiter( Rate( limit=1000, interval=60 * Duration.SECOND ) ),
    identifier=_cloudflare_identifier
)
"""Applied to /ingest/* endpoints."""

general_rate_limiter: RateLimiter = RateLimiter(
    Limiter( Rate( limit=100, interval=60 * Duration.SECOND ) ),
    identifier=_cloudflare_identifier
)
"""Fallback for any endpoint that doesn't have a dedicated tier."""


# Returns the current rate limit
async def get_auth_rate_limiter( request: Request, response: Response ) -> None:
    """Rate-limit dependency - enforces the auth tier limit per client IP."""
    await auth_rate_limiter( request, response )


async def get_forgot_password_rate_limiter( request: Request, response: Response ) -> None:
    """Rate-limit dependency - strict limit for password‑reset endpoints."""
    await forgot_password_rate_limiter( request, response )


async def get_ingest_rate_limiter( request: Request, response: Response ) -> None:
    """Rate-limit dependency - enforces the ingest tier limit."""
    await ingest_rate_limiter( request, response )


async def get_general_rate_limiter( request: Request, response: Response ) -> None:
    """Rate-limit dependency - enforces the general fallback limit."""
    await general_rate_limiter( request, response )
