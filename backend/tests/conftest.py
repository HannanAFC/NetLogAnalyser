import os
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from unittest.mock import AsyncMock

from auth.security import (
    create_access_token,
    generate_api_key,
    hash_password,
    hash_token,
)
from models.models import APIKey, User

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://NetlogAnalyserUserTest:TestPass@test-db/NetLogAnalyserDBTest"
)

os.environ.setdefault(
    "REDIS_URL",
    "redis://localhost/15"
)

import pytest
from cache import get_redis
from database import Base, get_db
from fastapi import Request, Response
from fastapi_limiter.depends import RateLimiter
from httpx import ASGITransport, AsyncClient
from main import app
from pyrate_limiter import Duration, Limiter, Rate
from rate_limiter import (
    get_auth_rate_limiter,
    get_forgot_password_rate_limiter,
    get_general_rate_limiter,
    get_ingest_rate_limiter,
)
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

pytest_plugins = [ "anyio" ]

VALID_EMAIL        = "test@example.com"
VALID_PASSWORD     = "Str0ng!Pass"
VALID_DISPLAY_NAME = "Test"
VALID_KEY_LABEL    = "Testing Key"

VALID_EMAIL_2        = "test-2@example.com"
VALID_PASSWORD_2     = "Str0ng!Pass"
VALID_DISPLAY_NAME_2 = "Test 2"
VALID_KEY_LABEL_2    = "Testing Key 2"

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
async def redis_client( ) -> AsyncGenerator[ Redis ]:
    client = Redis.from_url( os.environ[ "REDIS_URL" ], decode_responses=True )
    await client.flushdb( )
    try:
        yield client
    finally:
        await client.flushdb( )
        await client.aclose( )

@pytest.fixture
async def client(
    db_session: AsyncSession,
    redis_client: Redis
) -> AsyncGenerator[ AsyncClient ]:

    async def override_get_db( ):
        yield db_session

    async def override_get_redis( ):
        yield redis_client

    app.dependency_overrides[ get_db ]    = override_get_db
    app.dependency_overrides[ get_redis ] = override_get_redis

    # Override rate limiter with a permissive in-memory instance so tests
    # never hit real rate limits and don't require a running Redis.
    _test_rate_limiter = RateLimiter(
        Limiter(Rate(limit=10000, interval=60 * Duration.SECOND))
    )

    async def _permissive_rate_limit( request: Request, response: Response ) -> None:
        await _test_rate_limiter( request, response )

    app.dependency_overrides[ get_auth_rate_limiter ]            = _permissive_rate_limit
    app.dependency_overrides[ get_forgot_password_rate_limiter ] = _permissive_rate_limit
    app.dependency_overrides[ get_general_rate_limiter ]         = _permissive_rate_limit
    app.dependency_overrides[ get_ingest_rate_limiter ]          = _permissive_rate_limit

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
@pytest.fixture
async def user( db_session: AsyncSession ):
	user_row = User(
		email             = f"test-{ uuid.uuid4().hex[ :8 ] }@example.com",
		password_hash     = hash_password( "TestingPassword" ),
		display_name      = "Test User",
        email_verified_at = datetime.now( timezone.utc )
	)
	db_session.add( user_row )
	await db_session.commit()
	await db_session.refresh( user_row )
	return user_row
 
 
@pytest.fixture
async def other_user( db_session: AsyncSession ):
	user_row = User(
		email             = f"other-{ uuid.uuid4().hex[ :8 ] }@example.com",
		password_hash     = hash_password( "TestingPassword" ),
		display_name      = "Other User",
        email_verified_at = datetime.now( timezone.utc )
	)
	db_session.add( user_row )
	await db_session.commit()
	await db_session.refresh( user_row )
	return user_row
 
 
@pytest.fixture
async def api_key( db_session: AsyncSession, user: User ):
	raw_key = generate_api_key()
	key_row = APIKey(
		user_id    = user.id,
		key_hash   = hash_token( raw_key ),
		key_prefix = raw_key[ :8 ],
		label      = "test-key"
	)
	db_session.add( key_row )
	await db_session.commit()
	await db_session.refresh( key_row )
 
	key_row.raw_key = raw_key
 
	return key_row
 
 
@pytest.fixture
def auth_headers( user: User ):
	access_token = create_access_token( str( user.id ) )
	return { "Authorization": f"Bearer { access_token }" }
