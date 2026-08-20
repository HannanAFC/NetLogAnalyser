from __future__ import annotations

from config import settings
from redis.asyncio import ConnectionPool, Redis

_pool: ConnectionPool | None = None

def init_redis( ) -> None:
    """Open a shared async-Redis connection pool."""
    global _pool
    if _pool is not None:
        return
    _pool = ConnectionPool.from_url(
        settings.redis_url.get_secret_value( ),
        encoding="utf-8",
        decode_responses=True
    )

async def close_redis( ) -> None:
    global _pool
    if _pool != None:
        await _pool.disconnect( )
        _pool = None

def _get_pool( ) -> ConnectionPool:
    if _pool == None:
        raise RuntimeError( "Redis pool has not been initialised, call init_redis to initialise first." )
    return _pool

def get_redis( ) -> Redis:
    """
    FastAPI dependency for redis in request-scoped contexts.
    Returns:
        redis (Redis): Redis client object.
    """
    return Redis( connection_pool=_get_pool( ) )

def new_redis_client( ) -> Redis:
    """
    Separate Redis client for use outside of request-scope, for instance in a websocket.
    Returns:
        redis (Redis): Redis client object.
    """
    return Redis( connection_pool=_get_pool( ) )