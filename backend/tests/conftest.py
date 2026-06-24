import os
from collections.abc import AsyncGenerator

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://NetlogAnalyserUserTest:TestPass@test-db/NetLogAnalyserDBTest",
)

import pytest
from database import Base, get_db
from httpx import ASGITransport, AsyncClient
from main import app
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

    async with AsyncClient(
        transport=ASGITransport( app=app ),
        base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear( )