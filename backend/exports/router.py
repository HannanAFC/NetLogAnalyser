from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Union
from uuid import UUID

from auth.dependencies import get_current_user
from cache import get_redis
from config import settings
from database import get_db
from exports.schemas import (
	CreateExportResponse,
	DownloadLinkResponse,
	ExportRecordPublic,
	GetExportsResponse,
)
from exports.service import (
	count_exports_today,
	create_download_link,
	create_pending_export,
	resolve_download_token,
)
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse, RedirectResponse
from models.models import DataExport, User
from rate_limiter import get_general_rate_limiter
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from worker.pool import get_arq_pool

router = APIRouter( dependencies=[ Depends( get_general_rate_limiter ) ] )


@router.post( "", status_code=status.HTTP_202_ACCEPTED )
async def create_export(
	user: Annotated[ User, Depends( get_current_user ) ],
	db:   Annotated[ AsyncSession, Depends( get_db ) ]
) -> CreateExportResponse:
	today_count = await count_exports_today( db, user.id )
	if today_count >= settings.export_max_per_user_per_day:
		raise HTTPException(
			status_code=429,
			detail=f"Export limit reached ({ settings.export_max_per_user_per_day } per day). Try again tomorrow.",
		)

	export_row = await create_pending_export( db, user, triggered_by="MANUAL" )

	# Add to queue
	await get_arq_pool( ).enqueue_job( "run_export_pipeline_task", str( export_row.id ), str( user.id ) )

	return CreateExportResponse(
		id=export_row.id,
		status=export_row.status,
		created_at=export_row.created_at
	)


@router.get( "" )
async def list_exports(
	user: Annotated[ User, Depends( get_current_user ) ],
	db:   Annotated[ AsyncSession, Depends( get_db ) ]
) -> GetExportsResponse:
	result = await db.execute(
		select( DataExport )
		.where( DataExport.user_id == user.id )
		.order_by( DataExport.created_at.desc( ) )
		.limit( 20 )
	)
	await asyncio.sleep( 5 )
	return GetExportsResponse( rows=[ ExportRecordPublic.model_validate( row ) for row in result.scalars( ).all( ) ] )


@router.post( "/{export_id}/download-link" )
async def get_download_link(
	export_id: UUID,
	user:      Annotated[ User, Depends( get_current_user ) ],
	db:        Annotated[ AsyncSession, Depends( get_db ) ],
	redis:     Annotated[ Redis, Depends( get_redis ) ]
) -> DownloadLinkResponse:
	response = await create_download_link( db, redis, export_id, user.id )
	return response

@router.get( "/download" )
async def download_export(
	token: str,
	db:    Annotated[ AsyncSession, Depends( get_db ) ],
	redis: Annotated[ Redis, Depends( get_redis ) ]
):
	value = await resolve_download_token( db, redis, token )

	if value is None:
		raise HTTPException( status_code=status.HTTP_404_NOT_FOUND, detail="Download link not found or expired" )
	elif "https" in str( value ):
		return RedirectResponse( str( value ) )

	export_row = await db.get( DataExport, value )
	if export_row is None or export_row.status != "READY":
		raise HTTPException( status_code=status.HTTP_404_NOT_FOUND, detail="Export not found or not ready" )

	path = Path( settings.export_local_path ) / export_row.storage_key
	if not path.exists( ):
		raise HTTPException( status_code=status.HTTP_404_NOT_FOUND, detail="Export file missing" )

	export_row.last_downloaded_at = datetime.now( timezone.utc )

	await db.commit( )
	
	return FileResponse( path, filename="netloganalyser-export.zip", media_type="application/zip" )