import asyncio

from config import settings
from sqlalchemy.exc import DBAPIError, OperationalError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

engine = create_async_engine(
    url=settings.database_url,
    pool_pre_ping=True,
    pool_recycle=300
)

AsyncSessionLocal = async_sessionmaker( 
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


class Base( DeclarativeBase ):
    pass


MAX_RETRIES = 3
BASE_DELAY_SECONDS = 1.0

async def get_db( ):
    last_error: Exception | None = None

    for attempt in range( MAX_RETRIES ):
        try:
            async with AsyncSessionLocal( ) as session:
                yield session
                return
        except ( OperationalError, DBAPIError ) as error:
            last_error = error
            delay      = BASE_DELAY_SECONDS * ( 2 ** attempt )

            print( f"Database connection failed, attempt { attempt } of { MAX_RETRIES }, retrying in { round( delay ) }s." )

            await asyncio.sleep( delay )

    if last_error:
        raise last_error