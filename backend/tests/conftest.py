import os
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://NetlogAnalyserUserTest:TestPass@test-db/NetLogAnalyserDBTest",
)

import pytest
from database import Base, get_db
from fastapi import Request, Response
from fastapi_limiter.depends import RateLimiter
from httpx import ASGITransport, AsyncClient
from main import app
from pyrate_limiter import Duration, Limiter, Rate
from rate_limiter import get_auth_rate_limiter, get_forgot_password_rate_limiter
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

pytest_plugins = [ "anyio" ]

@pytest.fixture( scope="session" )
def anyio_backend( ):
    return "asyncio"

@pytest.fixture( scope="session" )
def test_engine( ):
    engine = create_async_engine(
        os.environ[ "DATABASE_URL" ],
        poolclass=NullPool
    )
    return engine

@pytest.fixture( scope="session" )
async def setup_database( test_engine ):
    async with test_engine.begin( ) as conn:
        await conn.run_sync( Base.metadata.create_all )

    yield

    async with test_engine.begin( ) as conn:
        await conn.run_sync( Base.metadata.drop_all )

    await test_engine.dispose( )

@pytest.fixture
async def db_session(
    test_engine,
    setup_database
) -> AsyncGenerator[ AsyncSession ]:
    conn = await test_engine.connect( )
    trans = await conn.begin( )

    test_async_session = async_sessionmaker(
        bind=conn,
        class_=AsyncSession,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint"
    )

    async with test_async_session( ) as session:
        try:
            yield session
        finally:
            await session.close( )
            await trans.rollback( )
            await conn.close( )

@pytest.fixture
async def client(
    db_session: AsyncSession
) -> AsyncGenerator[ AsyncClient ]:

    async def override_get_db( ):
        yield db_session

    app.dependency_overrides[ get_db ] = override_get_db

    # Override rate limiter with a permissive in-memory instance so tests
    # never hit real rate limits and don't require a running Redis.
    _test_rate_limiter = RateLimiter(
        Limiter(Rate(limit=10_000, interval=60 * Duration.SECOND))
    )

    async def _permissive_rate_limit( request: Request, response: Response ) -> None:
        await _test_rate_limiter( request, response )

    app.dependency_overrides[ get_auth_rate_limiter ] = _permissive_rate_limit
    app.dependency_overrides[ get_forgot_password_rate_limiter ] = _permissive_rate_limit

    async with AsyncClient(
        transport=ASGITransport( app=app ),
        base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear( )

@pytest.fixture( autouse=True )
def mock_email_send( monkeypatch ):
    """
    Prevent tests from hitting the real Resend API.

    IMPORTANT: patched at `auth.service.*`, not `mailer.service.*` or
    `mailer.client.*`. auth/service.py does
    `from mailer.service import send_verification_email`, which creates a
    *separate* local binding in auth.service's namespace — patching the
    original mailer.service (or mailer.client) attribute doesn't touch that
    copy, so the real function would still run. Always patch the name at
    the point it's called from, not where it's defined.
    """
    verification_mock = AsyncMock( )
    reset_mock        = AsyncMock( )
    welcome_mock      = AsyncMock( )

    monkeypatch.setattr( "auth.service.send_verification_email", verification_mock )
    monkeypatch.setattr( "auth.service.send_password_reset_email", reset_mock )
    monkeypatch.setattr( "auth.service.send_welcome_email", welcome_mock )

    return { "verification": verification_mock, "reset": reset_mock, "welcome": welcome_mock }
