from __future__ import annotations

import logging
from uuid import UUID

from arq.connections import RedisSettings
from config import settings
from exports.service import run_export_pipeline
from exports.startup_checks import verify_export_storage
from logging_config import configure_logging

logger = logging.getLogger( __name__ )


async def run_export_pipeline_task( ctx: dict, export_id: str, user_id: str ) -> None:
	await run_export_pipeline( UUID( export_id ), UUID( user_id ) )


async def on_startup( ctx: dict ) -> None:
	configure_logging( )
	verify_export_storage( )
	logger.info( "Export worker started." )


async def on_shutdown( ctx: dict ) -> None:
	logger.info( "Export worker shutting down." )


class WorkerSettings:
	functions      = [ run_export_pipeline_task ]
	on_startup     = on_startup
	on_shutdown    = on_shutdown
	redis_settings = RedisSettings.from_dsn( settings.redis_url.get_secret_value( ) )

	max_tries      = 3
	job_timeout    = 600
	max_jobs       = 5