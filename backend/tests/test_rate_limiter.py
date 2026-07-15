"""
Tests for the rate-limiting module.

Covers:
- Cloudflare-aware IP identifier resolution
- Rate-limit enforcement (HTTP 429 after exceeding quota)
- Stricter per-route limits (forgot-password vs auth router default)
- Bucket isolation (different endpoints don't interfere)
"""

from __future__ import annotations

import pytest
from fastapi import Request, Response
from fastapi_limiter.depends import RateLimiter
from httpx import AsyncClient
from main import app
from pyrate_limiter import Duration, Limiter, Rate
from rate_limiter import (
    _cloudflare_identifier,
    get_auth_rate_limiter,
    get_forgot_password_rate_limiter,
)
from starlette.requests import Request

pytestmark = pytest.mark.anyio


# ═══════════════════════════════════════════════════════════════════
# Helpers - build a strict in-memory limiter for enforcement tests
# ═══════════════════════════════════════════════════════════════════

def _build_strict_limiter( times: int, seconds: int ) -> RateLimiter:
    """Return an in-memory RateLimiter that allows only *times* requests."""
    return RateLimiter( Limiter( Rate( limit=times, interval=seconds * Duration.SECOND ) ) )


# ═══════════════════════════════════════════════════════════════════
# _cloudflare_identifier
# ═══════════════════════════════════════════════════════════════════

class TestCloudflareIdentifier:
    async def test_cf_connecting_ip_takes_precedence( self ):
        """cf-connecting-ip should win over every other header."""
        scope = {
            "type": "http",
            "client": ( "10.0.0.1", 12345 ),
            "headers": [
                ( b"cf-connecting-ip", b"1.2.3.4" ),
                ( b"x-forwarded-for", b"5.6.7.8" )
            ]
        }
        request = Request( scope )
        result = await _cloudflare_identifier( request )
        assert result == "1.2.3.4"

    async def test_x_forwarded_for_fallback( self ):
        """x-forwarded-for should be used when cf-connecting-ip is absent."""
        scope = {
            "type": "http",
            "client": ( "10.0.0.1", 12345 ),
            "headers": [
                ( b"x-forwarded-for", b"5.6.7.8, 9.10.11.12" )
            ]
        }
        request = Request( scope )
        result = await _cloudflare_identifier( request )
        assert result == "5.6.7.8"

    async def test_client_host_fallback( self ):
        """request.client.host when no proxy headers are present."""
        scope = {
            "type": "http",
            "client": ( "10.0.0.1", 12345 ),
            "headers": [ ]
        }
        request = Request( scope )
        result = await _cloudflare_identifier( request )
        assert result == "10.0.0.1"

    async def test_loopback_when_no_client( self ):
        """127.0.0.1 when there's nothing else to fall back to."""
        scope = { "type": "http", "client": None, "headers": [ ] }
        request = Request( scope )
        result = await _cloudflare_identifier( request )
        assert result == "127.0.0.1"


# ═══════════════════════════════════════════════════════════════════
# Rate-limit enforcement
# ═══════════════════════════════════════════════════════════════════

class TestRateLimitEnforcement:
    """Verify that exceeding the configured limit returns HTTP 429."""

    async def test_login_blocked_after_limit( self, client: AsyncClient ):
        """After 3 requests (register + 2 logins) the 4th should be 429."""
        strict = _build_strict_limiter( 3, 60 )  # accounts for register call above

        async def _strict_auth( request: Request, response: Response ) -> None:
            await strict( request, response )

        app.dependency_overrides[ get_auth_rate_limiter ] = _strict_auth

        # Register a user first so login can succeed
        await client.post(
            "/auth/register",
            json={
                "email": "ratelimit@example.com",
                "password": "Str0ng!Pass",
                "confirm_password": "Str0ng!Pass",
                "display_name": "RL"
            }
        )

        login_payload = {
            "email": "ratelimit@example.com",
            "password": "Str0ng!Pass"
        }

        # Register + 2 logins = 3 requests (at the limit), 4th should be blocked
        r1 = await client.post( "/auth/login", json=login_payload )
        r2 = await client.post( "/auth/login", json=login_payload )
        assert r1.status_code == 200
        assert r2.status_code == 200

        # Fourth overall request — must be rate-limited
        r3 = await client.post( "/auth/login", json=login_payload )
        assert r3.status_code == 429
        assert "Too Many Requests" in r3.text

    async def test_register_blocked_after_limit( self, client: AsyncClient ):
        """Registration should also be rate-limited under the auth tier."""
        strict = _build_strict_limiter( 2, 60 )

        async def _strict_auth( request: Request, response: Response ) -> None:
            await strict( request, response )

        app.dependency_overrides[ get_auth_rate_limiter ] = _strict_auth

        base = {
            "password": "Str0ng!Pass",
            "confirm_password": "Str0ng!Pass",
            "display_name": "Reg",
        }

        # Two different emails so registration itself doesn't collide
        r1 = await client.post(
            "/auth/register",
            json={ **base, "email": "reg1@example.com" }
        )
        r2 = await client.post(
            "/auth/register",
            json={ **base, "email": "reg2@example.com" }
        )
        assert r1.status_code == 201
        assert r2.status_code == 201

        r3 = await client.post(
            "/auth/register",
            json={ **base, "email": "reg3@example.com" }
        )

        assert r3.status_code == 429


# ═══════════════════════════════════════════════════════════════════
# Stricter per-route limits
# ═══════════════════════════════════════════════════════════════════

class TestStricterForgotPasswordLimit:
    """Forgot-password should have a lower limit than the auth router default."""

    async def test_forgot_password_has_lower_limit_than_auth( self, client: AsyncClient ):
        """forgot-password is limited to 2, auth default is 10 - forgot-pw hits 429 first."""
        strict_forgot = _build_strict_limiter( 2, 60 )
        lenient_auth = _build_strict_limiter( 10, 60 )

        async def _strict_forgot( request: Request, response: Response ) -> None:
            await strict_forgot( request, response )

        async def _lenient_auth( request: Request, response: Response ) -> None:
            await lenient_auth( request, response )

        app.dependency_overrides[ get_forgot_password_rate_limiter ] = _strict_forgot
        app.dependency_overrides[ get_auth_rate_limiter ] = _lenient_auth

        fp_payload = { "email": "exists@example.com" }  # TestStricterForgotPasswordLimit

        r1 = await client.post( "/auth/forgot-password", json=fp_payload )
        r2 = await client.post( "/auth/forgot-password", json=fp_payload )
        assert r1.status_code == 200
        assert r2.status_code == 200

        r3 = await client.post( "/auth/forgot-password", json=fp_payload )
        assert r3.status_code == 429


# ═══════════════════════════════════════════════════════════════════
# Bucket isolation
# ═══════════════════════════════════════════════════════════════════

class TestBucketIsolation:
    """Hitting the forgot-password limit should NOT block other auth routes."""

    async def test_forgot_password_limit_does_not_block_login( self, client: AsyncClient ):
        """Exhaust forgot-password quota; login should still work."""
        strict_forgot = _build_strict_limiter( 1, 60 )
        lenient_auth = _build_strict_limiter( 10, 60 )

        async def _strict_forgot( request: Request, response: Response ) -> None:
            await strict_forgot( request, response )

        async def _lenient_auth( request: Request, response: Response ) -> None:
            await lenient_auth( request, response )

        app.dependency_overrides[ get_forgot_password_rate_limiter ] = _strict_forgot
        app.dependency_overrides[ get_auth_rate_limiter ] = _lenient_auth

        # Register user for login test  # TestBucketIsolation
        await client.post(
            "/auth/register",
            json={
                "email": "bucketiso@example.com",
                "password": "Str0ng!Pass",
                "confirm_password": "Str0ng!Pass",
                "display_name": "Bucket"
            }
        )

        # Exhaust forgot-password quota
        r1 = await client.post(
            "/auth/forgot-password",
            json={ "email": "bucketiso@example.com" }
        )
        assert r1.status_code == 200

        r2 = await client.post(
            "/auth/forgot-password",
            json={ "email": "bucketiso@example.com" }
        )
        assert r2.status_code == 429  # forgot-pw blocked

        # Login should be unaffected (different bucket)
        r3 = await client.post(
            "/auth/login",
            json={
                "email": "bucketiso@example.com",
                "password": "Str0ng!Pass"
            }
        )
        assert r3.status_code == 200
