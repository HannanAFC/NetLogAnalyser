from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class StorageBackendEnum( str, Enum ):
	local = "LOCAL"
	s3    = "S3"

class ExportStatusEnum( str, Enum ):
	pending = "PENDING"
	ready   = "READY"
	failed  = "FAILED"

class ExportTriggeredByEnum( str, Enum ):
	manual        = "MANUAL"
	retention_job = "RETENTION_JOB"

class CreateExportResponse( BaseModel ):
	model_config = ConfigDict( from_attributes=True )
	
	id:         UUID
	status:     ExportStatusEnum
	created_at: datetime

class ExportRecordPublic( BaseModel ):
	model_config = ConfigDict( from_attributes=True )

	id:                  UUID
	status:              ExportStatusEnum
	triggered_by:        ExportTriggeredByEnum
	file_size_bytes:     int | None
	created_at:          datetime
	expires_at:          datetime
	purged_at:           datetime | None
	last_downloaded_at:  datetime | None

class GetExportsResponse( BaseModel ):
	rows: list[ ExportRecordPublic ]

class DownloadLinkResponse( BaseModel ):
	download_url: str