from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from config import settings
from email_service.service import send_retention_warning_email
from exports.service import (
	create_pending_export,
	run_export_pipeline,
	setup_ttl_download_link,
)
from models.models import DataExport, LogEntry, User
from redis.asyncio import Redis
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger( __name__ )


def _now( ) -> datetime:
	return datetime.now( timezone.utc )

async def distinct_user_ids_with_logs_older_than(
	db:     AsyncSession,
	cutoff: datetime
) -> list[ UUID ]:
    """
    Returns users with logs older than the cutoff.
    Paramters:
        db (AsyncSession): Asynchronous database session.
        cutoff (datetime): A datetime that logs with a captured at before should be deleted.
    Returns:
        uuids (list[UUID]): List of user IDs that qualify.
    """
    result = await db.execute(
		select( LogEntry.user_id )
		.where( LogEntry.captured_at < cutoff )
		.distinct( )
	)
    return [ row[ 0 ] for row in result.all( ) ]

async def has_recent_retention_export(
	db:      AsyncSession,
	user_id: UUID,
	since:   datetime
) -> bool:
    """
    Checks if user has a recent retention job export ready, assumes email is only sent after successful export.
    Parameters:
        db (AsyncSession): Asynchronous database session.
        user_id (UUID): ID of the user to run the check for.
        since (datetime): Date to check for an export since.
    Returns:
        has_recent_retention_export (bool): Whether the user has a recent retention job export.
    """
    result = await db.execute(
		select( DataExport.id )
		.where(
			DataExport.user_id == user_id,
			DataExport.triggered_by == "RETENTION_JOB",
			DataExport.status == "READY",
			DataExport.created_at >= since
		)
		.limit( 1 )
	)
    return result.scalar_one_or_none( ) is not None

async def send_retention_warnings(
	db:    AsyncSession,
	redis: Redis
) -> int:
    """
    Sends retention warning emails to users with logs that qualify for deletion and also generates exports for them.
    Over includes in terms of what's included in the export.
    Parameters:
        db (AsyncSession): Asynchronous database session.
        redis (Redis): Redis client.
    Returns:
        warned (int): Amount of users warned.
    """
    warn_cutoff         = _now( ) - timedelta( days=settings.retention_days - settings.retention_grace_period_days )
    dedupe_window_start = _now( ) - timedelta( days=settings.retention_grace_period_days )

    user_ids = await distinct_user_ids_with_logs_older_than( db, warn_cutoff )
    logger.info( "Retention warn: %s users have logs older than %s.", len( user_ids ), warn_cutoff )

    warned = 0
    for user_id in user_ids:
        if await has_recent_retention_export( db, user_id, dedupe_window_start ):
            logger.info( "Retention warn: skipping user %s, already warned this cycle.", user_id )
            continue

        user = await db.get( User, user_id )
        if user is None:
            continue

        try:
            export_row = await create_pending_export( db, user, triggered_by="RETENTION_JOB" )
            await run_export_pipeline( export_row.id, user.id )
            await db.refresh( export_row )

            if export_row.status != "READY":
                logger.error(
                    "Retention warn: export for user %s did not reach READY "
                    "(status=%s) - not sending email, see export pipeline "
                    "logs for export_id=%s.",
                    user_id, export_row.status, export_row.id,
                )
                continue

            download_url = await setup_ttl_download_link(
                redis, export_row, ttl_seconds=settings.export_link_ttl_hours * 3600
            )
            deletion_date = ( _now( ) + timedelta(days=settings.retention_grace_period_days ) ).date( )

            if settings.retention_export_email_enabled:
                await send_retention_warning_email(
                    to=user.email,
                    display_name=user.display_name,
                    download_url=download_url,
                    deletion_date=str( deletion_date )
                )
                logger.info(
                    "Retention warn: emailed user %s, deletion_date=%s.",
                    user_id,
                    deletion_date
                )
            else:
                logger.info(
                    "Retention warn: export ready for user %s but "
                    "RETENTION_EXPORT_EMAIL_ENABLED=false, not emailing.",
                    user_id,
                )

            warned += 1

        except Exception:
            logger.exception( "Retention warn: failed for user %s.", user_id)
            continue

    return warned

async def _delete_chunk(
    db:         AsyncSession,
    user_id:    UUID,
    cutoff:     datetime,
    chunk_size: int
) -> int:
    """
    Deletes an individual chunk of logs for a user.
    Parameters:
        db (AsyncSession): Asynchronous database session.
        user_id (UUID): The ID of the user to delete logs for.
        cutoff (datetime): Cutoff date to delete logs before.
        chunk_size (int): Maximum amount of logs to delete.
    Returns:
        count (int): Number of logs deleted.
    """
    result = await db.execute(
        select( LogEntry.id )
        .where( LogEntry.user_id == user_id, LogEntry.captured_at < cutoff )
        .limit( chunk_size )
    )
    ids = [ row[ 0 ] for row in result.all( ) ]
    if not ids:
        return 0

    await db.execute(
        delete( LogEntry )
        .where( LogEntry.id.in_( ids ) )
    )
    await db.commit( )
    return len( ids )


async def delete_expired_logs_for_user(
    db:      AsyncSession,
    user_id: UUID,
    cutoff:  datetime
) -> int:
    """
    Deletes the logs of a user before the cutoff date chunk by chunk.
    Parameters:
        db (AsyncSession): Asynchronous database session.
        user_id (UUID): The ID of the user to delete logs for.
        cutoff (datetime): Cutoff date to delete logs before.
    Returns:
        deleted (int): Number of logs deleted.
    """
    chunk_size = settings.retention_delete_chunk_size
    total = 0
    while True:
        deleted = await _delete_chunk( db, user_id, cutoff, chunk_size )
        total += deleted
        if deleted < chunk_size:
            break
    return total


async def delete_expired_logs_for_all_users( db: AsyncSession ) -> tuple[ int, int ]:
    """
    Deletes the old logs of a user captured before the retention period.
    Parameters:
        db (AsyncSession): Asynchronous database session.
    Returns:
        deleted_total (int): Total number of logs deleted across all users.
        skipped (int): Number of skipped users.
    NOTE: Behaviour - Skips deletion if the automatic export generated by the retention email isn't found.
    """
    cutoff = _now( ) - timedelta( days=settings.retention_days )
    # Looks back a full retention_days window, comfortably covering the
    # warn run that happened retention_grace_days before this one.
    warn_confirmation_window = _now( ) - timedelta( days=settings.retention_days )

    user_ids = await distinct_user_ids_with_logs_older_than( db, cutoff )
    logger.info(" Retention delete: %s users have logs older than %s.", len( user_ids ), cutoff )

    deleted_total = 0
    skipped = 0
    for user_id in user_ids:
        if not await has_recent_retention_export( db, user_id, warn_confirmation_window ):
            logger.warning(
                "Retention delete: SKIPPING user %s - no confirmed warning "
                "export found in the last %s days. Their expired logs will "
                "NOT be deleted this cycle. Investigate why warning kept "
                "failing for this user.",
                user_id, settings.retention_days,
            )
            skipped += 1
            continue

        count = await delete_expired_logs_for_user( db, user_id, cutoff )
        deleted_total += count
        logger.info( "Retention delete: removed %s rows for user %s.", count, user_id)

    return deleted_total, skipped