from __future__ import annotations

import asyncio
import csv
import json
import logging
import sys
import tempfile
import traceback
import zipfile
from collections.abc import AsyncIterator
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID, uuid4

from auth.security import generate_url_safe_token, hash_token
from config import settings
from database import AsyncSessionLocal
from exports.format import EXPORT_FIELDNAMES, flatten_for_csv, to_export_dict
from exports.schemas import DownloadLinkResponse, ExportStatusEnum
from exports.storage import S3ExportStorage, get_export_storage
from fastapi import HTTPException, status
from models.models import DataExport, LogEntry, User
from redis.asyncio import Redis
from sqlalchemy import func, select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger( __name__ )

EXPORT_CHUNK_SIZE = 1000
DOWNLOAD_TOKEN_PREFIX = "export_dl"
STALE_PENDING_THRESHOLD_MINUTES = 30

async def stream_logs_for_export(
	db:      AsyncSession,
	user_id: UUID
) -> AsyncIterator[ list[ LogEntry ] ]:
	"""
	Yields chunks of LogEntry rows, oldest first.
	Parameters:
		db (AsyncSession): Asynchronous database session.
		user_id (UUID): The user whos logs to fetch.
	"""
	last_captured_at: datetime | None = None
	last_id:          int | None = None

	while True:
		query = (
			select( LogEntry )
			.where( LogEntry.user_id == user_id )
			.order_by( LogEntry.captured_at.asc( ), LogEntry.id.asc( ) )
			.limit( EXPORT_CHUNK_SIZE )
		)
		if last_captured_at is not None:
			query = query.where(
				tuple_( LogEntry.captured_at, LogEntry.id )
				> tuple_( last_captured_at, last_id ) # pyright: ignore[reportArgumentType]
			)

		result = await db.execute( query )
		rows   = result.scalars( ).all( )

		if not rows:
			break

		yield rows # pyright: ignore[reportReturnType]

		last_captured_at = rows[ -1 ].captured_at
		last_id          = rows[ -1 ].id

		if len( rows ) < EXPORT_CHUNK_SIZE:
			break

async def write_export_files(
	db:       AsyncSession,
	user_id:  UUID,
	dest_dir: Path
) -> tuple[ Path, Path, int ]:
	"""
	Streams chunks and writes them to a CSV and JSON.
	Parameters:
		db (AsyncSession): Asynchronous database session.
		user_id (UUID): The user whos logs to fetch.
	Returns:
		csv_path (Path): Path of where the CSV is saved.
		jsonl_file (Path): Path of where the JSONL file is saved.
	"""
	csv_path   = dest_dir / "logs.csv"
	jsonl_path = dest_dir / "logs.jsonl"
	row_count  = 0

	csv_file   = open( csv_path, "w", newline="" )  # noqa: ASYNC230, SIM115
	jsonl_file = open( jsonl_path, "w" )  # noqa: ASYNC230, SIM115
	try:
		writer = csv.DictWriter( csv_file, fieldnames=EXPORT_FIELDNAMES )
		writer.writeheader( )

		async for chunk in stream_logs_for_export( db, user_id ):

			def _write_chunk( chunk=chunk ):
				for entry in chunk:
					row = to_export_dict( entry )
					writer.writerow( flatten_for_csv( row ) )
					jsonl_file.write( json.dumps( row, default=str ) + "\n" )

			await asyncio.to_thread( _write_chunk )
			row_count += len( chunk )
	finally:
		csv_file.close( )
		jsonl_file.close( )

	return csv_path, jsonl_path, row_count

def _zip_files(
	paths:    list[ Path ],
	zip_path: Path
) -> None:
	with zipfile.ZipFile( zip_path, "w", zipfile.ZIP_DEFLATED ) as zf:
		for p in paths:
			zf.write( p, arcname=p.name )

async def count_exports_today(
	db:      AsyncSession,
	user_id: UUID
) -> int:
	"""
	Helper to count the number of exports a user has requested in the current day.
	Parameters:
		db (AsyncSession): Asynchronous database session.
		user_id (UUID): The user to fetch the export count for.
	Returns:
		count (int): The number of export requested by the user in the current day.
	"""
	since = datetime.now( timezone.utc ) - timedelta( hours=24 )
	result = await db.execute(
		select( func.count( ) ).select_from( DataExport ).where(
			DataExport.user_id == user_id,
			DataExport.created_at >= since
		)
	)
	return result.scalar_one( )

async def create_pending_export(
	db:           AsyncSession,
	user:         User,
	triggered_by: str
) -> DataExport:
	"""
	Creates a pending export row.
	Parameters:
		db (AsyncSession): Asynchronous database session.
		user (User): The user the export is for.
	Returns:
		export (DataExport): Export object.
	"""
	export_id = uuid4( )

	export_row = DataExport(
		id=export_id,
		user_id=user.id,
		storage_backend=settings.export_storage_backend.upper( ),
		storage_key=f"{ user.id }/{ export_id }.zip",
		status="PENDING",
		triggered_by=triggered_by,
		expires_at=datetime.now( timezone.utc ) + timedelta( hours=settings.export_link_ttl_hours )
	)
	db.add( export_row )
	await db.commit( )
	await db.refresh( export_row )

	return export_row

async def create_download_link(
	db: AsyncSession,
	redis: Redis,
	export_id: UUID,
	user_id: UUID
) -> DownloadLinkResponse:
	"""
	Creates a shortlived download link and returns it, raises exception if the export ID is invalid.
	Parameters:
		db (AsyncSession): Asynchronous database session.
		redis (Redis): Redis client.
		export_id (UUID): ID of the export to create a download link for.
		user_id (UUID): The user ID of the user requesting the download link.
	Returns:
		response (DownloadLinkResponse): A response containing the download link.
	"""
	export_row = await db.get( DataExport, export_id )
	if export_row is None or export_row.user_id != user_id:
		raise HTTPException( status_code=status.HTTP_404_NOT_FOUND, detail="Export not found" )
	if export_row.status != "READY":
		raise HTTPException( status_code=status.HTTP_409_CONFLICT, detail="Export is not ready yet" )
	if export_row.expires_at < datetime.now( timezone.utc ):
		raise HTTPException( status_code=status.HTTP_404_NOT_FOUND, detail="Export has expired" )

	url = await setup_ttl_download_link(
		redis, export_row, ttl_seconds=settings.export_authenticated_link_ttl_seconds
	)
	return DownloadLinkResponse( download_url=url )

async def setup_ttl_download_link(
	redis:       Redis,
	export_row:  DataExport,
	ttl_seconds: int
) -> str:
	"""
	Returns a temporary download link for an export. When using S3, this is a link to download via S3.
	When using local, this points to the download endpoint with a signed token for the download.
	Parameters:
		redis (Redis): Redis client.
		export_row (DataExport): The data export row to download.
		ttl_seconds (int): How long the download link should be valid for.
	Returns:
		download_link (str): The generated download link.
	"""
	raw_token         = generate_url_safe_token( 32 )
	token_hash        = hash_token( raw_token )
	value: str | None = None

	if export_row.storage_backend == "S3":
		storage = get_export_storage( )
		assert isinstance( storage, S3ExportStorage )
		value   = await storage.get_download_ref( export_row.storage_key, ttl_seconds )
	else:
		value = str( export_row.id )

	await redis.set(
		f"{ DOWNLOAD_TOKEN_PREFIX }:{ token_hash }",
		value,
		ex=ttl_seconds
	)
	return f"{ settings.backend_url }/exports/download?token={ raw_token }"

async def resolve_download_token(
	db:        AsyncSession,
	redis:     Redis,
	raw_token: str
) -> UUID | str | None:
	"""
	Resolves a download token to the corresponding file response, if there is an issue with the link a HTTPException is raised.
	Parameters:
		db (AsyncSession): Asynchronous database session.
		redis (Redis): Redis client.
		raw_token (str): Token from the download link.
	Returns:
		response (FileResponse): A response to download the file.
	"""
	token_hash = hash_token( raw_token )
	value      = await redis.get( f"{ DOWNLOAD_TOKEN_PREFIX }:{ token_hash }" )
	if "https" in str( value ):
		return str( value )
	elif value is not None:
		return UUID( str( value ) )
	else:
		return None

async def run_export_pipeline(
	export_id: UUID,
	user_id:   UUID
) -> None:
	"""
	Runs the entire data export pipeline, should only ever be ran by the ARQ worker as it can be a slow process and can fail which would require a retry.
	Parameters:
		export_id (UUID): The ID of the export to run.
		user_id (UUID): The ID of the user the export belongs to.
	NOTE: Make sure to setup logging correctly for debugging.
	"""
	async with AsyncSessionLocal( ) as db:
		export_row = await db.get( DataExport, export_id )
		if export_row is None:
			logger.warning( "run_export_pipeline: Export row not found", extra={ "export_id": str( export_id ) } )
			return

		logger.info( "Export pipeline starting", extra={ "export_id": str( export_id ), "user_id": str( user_id ) } )

		try:
			with tempfile.TemporaryDirectory( ) as tmp_dir:
				tmp_path = Path( tmp_dir )

				csv_path, jsonl_path, row_count = await write_export_files( db, user_id, tmp_path )
				logger.info(
					"Export rows written", extra={ "export_id": str( export_id ), "row_count": row_count }
				)
				if row_count == 0:
					logger.warning(
						"Export produced zero rows", extra={ "export_id": str( export_id ), "user_id": str( user_id ) }
					)

				zip_path = tmp_path / "export.zip"
				await asyncio.to_thread( _zip_files, [ csv_path, jsonl_path ], zip_path )

				if not await asyncio.to_thread( zipfile.is_zipfile, zip_path ):
					raise RuntimeError( f"Produced zip failed validation: { zip_path }" )

				file_size = await asyncio.to_thread( lambda: zip_path.stat( ).st_size )
				logger.info( "Export zipped", extra={ "export_id": str(export_id), "zip_bytes": file_size } )

				storage = get_export_storage( )
				await storage.save( export_row.storage_key, zip_path )
				logger.info(
					"Export saved to storage",
					extra={
						"export_id": str( export_id ),
						"backend": export_row.storage_backend,
						"key": export_row.storage_key
					}
				)

				saved_size = await storage.get_size( export_row.storage_key )
				if saved_size is None:
					raise RuntimeError(
						f"Export save verification failed: nothing found at key={ export_row.storage_key }"
					)
				if saved_size != file_size:
					logger.warning(
						"Export saved size mismatch",
						extra={ "export_id": str( export_id ), "expected": file_size, "actual": saved_size }
					)

			export_row.status = ExportStatusEnum.ready
			export_row.file_size_bytes = saved_size
			await db.commit( )
			logger.info(
				"Export marked READY", extra={ "export_id": str( export_id ), "file_size_bytes": saved_size }
			)

		except Exception:
			logger.exception( "Export pipeline failed", extra={" export_id": str( export_id ) } )
			print( f"[Export pipeline failed] export_id={ export_id }", file=sys.stderr )
			traceback.print_exc( ) 
			export_row.status = ExportStatusEnum.failed
			await db.commit( )

async def mark_stale_pending_exports_failed( db: AsyncSession ) -> int:
	"""
	CRON job function to mark export that crashed as failed.
	Parameters:
		db (AsyncSession): Asynchronous database session.
	Returns:
		stale (int): Number of stale exports.
	"""
	cutoff = datetime.now (timezone.utc ) - timedelta( minutes=STALE_PENDING_THRESHOLD_MINUTES )
	result = await db.execute(
		select( DataExport )
		.where(
			DataExport.status == "PENDING",
			DataExport.created_at < cutoff
		)
	)
	stale = result.scalars( ).all( )
	for export_row in stale:
		export_row.status = ExportStatusEnum.failed
	await db.commit( )
	return len( stale )

async def purge_expired_exports( db: AsyncSession ) -> int:
	"""
	Deletes the physical files for an export if they are expired.
	Parameters:
		db (AsyncSession): Asynchronous database session.
	Returns:
		purged (int): Number of purged exports.
	"""
	cutoff = datetime.now( timezone.utc )
	result = await db.execute(
		select( DataExport )
		.where(
			DataExport.status == "READY",
			DataExport.purged_at.is_( None ),
			DataExport.expires_at < cutoff
		)
	)
	expired = result.scalars( ).all( )

	purged = 0
	for export_row in expired:

		export_id = export_row.id
		storage_key = export_row.storage_key
		storage_backend = export_row.storage_backend

		try:
			storage = get_export_storage( storage_backend )
			await storage.delete( storage_key )
		except Exception:
			logger.exception(
				"Failed to purge expired export: storage delete failed.",
				extra={ "export_id": str( export_id ) }
			)
			continue
 
		try:
			async with db.begin_nested( ):
				export_row.purged_at = cutoff
				await db.flush( )
			await db.commit( )
			purged += 1
			logger.info(
				"Purged expired export file.", extra={ "export_id": str( export_id ), "key": storage_key }
			)
		except Exception:
			logger.exception(
				"Failed to purge expired export: db write failed.", extra={ "export_id": str( export_id ) }
			)
			continue


	return purged