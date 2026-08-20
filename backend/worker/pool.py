from __future__ import annotations

from arq import create_pool
from arq.connections import ArqRedis, RedisSettings
from config import settings

_pool: ArqRedis | None = None


async def init_arq_pool( ) -> None:
	global _pool
	if _pool is None:
		_pool = await create_pool( RedisSettings.from_dsn( settings.redis_url.get_secret_value( ) ) )


async def close_arq_pool( ) -> None:
	global _pool
	if _pool is not None:
		await _pool.close( )
		_pool = None


def get_arq_pool( ) -> ArqRedis:
	if _pool is None:
		raise RuntimeError( "arq pool not initialised - call init_arq_pool() in lifespan" )
	return _pool