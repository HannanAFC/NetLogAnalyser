from __future__ import annotations

import argparse
import asyncio
import logging
import sys
import traceback

from cache import init_redis, new_redis_client
from config import settings
from database import AsyncSessionLocal
from exports.service import mark_stale_pending_exports_failed, purge_expired_exports
from exports.startup_checks import verify_export_storage
from logging_config import configure_logging
from redis.asyncio import Redis
from retention.service import delete_expired_logs_for_all_users, send_retention_warnings

logger = logging.getLogger( __name__ )

LOCK_KEY_TEMPLATE = "retention_lock:{mode}"


async def _acquire_lock( redis: Redis, mode: str ) -> bool:
    """
    Set redis lock to prevent cron job running twice at once.
    Parameters:
        redis (Redis): Redis client.
        mode (str): Key for the type of job running (warn or delete)
    """
    return bool(
		await redis.set(
			LOCK_KEY_TEMPLATE.format( mode=mode ),
			"1",
			nx=True,
			ex=settings.retention_job_lock_ttl_seconds
		)
	)


async def run( mode: str ) -> None:
	configure_logging( )
	logger.info(
		"Retention job starting: mode=%s retention_enabled=%s retention_days=%s grace_days=%s",
		mode, settings.retention_enabled, settings.retention_days, settings.retention_grace_period_days
	)

	if mode in ( "warn", "delete" ) and not settings.retention_enabled:
		logger.info( "RETENTION_ENABLED=false, skipping mode=%s.", mode )
		return
	
	if mode in ( "warn", "purge-exports"):
		# Both modes write to or read from export storage — fail fast if
		# it's misconfigured, same check the app and worker run at startup.
		verify_export_storage( )

	init_redis( )
	redis = new_redis_client( )
	if not await _acquire_lock( redis, mode ):
		logger.info( "Another process already holds the retention lock for mode=%s, exiting", mode )
		return

	async with AsyncSessionLocal( ) as db:
		if mode == "warn":
			count = await send_retention_warnings( db, redis )
			logger.info( "Retention warn complete: %s users warned", count )
		elif mode == "delete":
			deleted, skipped = await delete_expired_logs_for_all_users( db )
			stale = await mark_stale_pending_exports_failed(db)
			logger.info(
				"Retention delete complete: %s log rows deleted, %s users skipped "
				"(no confirmed warning), %s stale pending exports marked failed.",
				deleted, skipped, stale
			)
		elif mode == "purge-exports":
			purged = await purge_expired_exports( db )
			logger.info( "Retention purge-exports complete: %s expired export files purged.", purged )

		else:
			raise ValueError( f"Unknown mode: {mode!r}" )


def main( ) -> None:
	parser = argparse.ArgumentParser( description="NetLogAnalyser retention job" )
	parser.add_argument( "--mode", choices=[ "warn", "delete", "purge-exports" ], required=True )
	args = parser.parse_args( )

	try:
		asyncio.run( run( args.mode ) )
	except Exception:
		# Fail loudly as this is an actual issue.
		logger.exception( "Retention job failed." )
		print( "[Retention job failed]", file=sys.stderr )
		traceback.print_exc( )
		sys.exit( 1 )


if __name__ == "__main__":
	main( )