from __future__ import annotations

import asyncio
import logging
import os
import shutil
import tempfile
from functools import lru_cache
from pathlib import Path
from typing import Protocol

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from config import settings

logger = logging.getLogger( __name__ )


class ExportStorage( Protocol ):
	async def save( self, key: str, source_path: Path ) -> None:
		"""
		Stores a file under a temp path to persistent storage.
		Parameters:
			key (str): Storage type key.
			source_path (Path): Path of temp storage.
		"""
		...

	async def delete( self, key: str ) -> None:
		"""
		Deletes an export.
		Parameters:
			key (str): Export key.
		"""
		...

	async def get_size( self, key: str ) -> int | None:
		"""
		Returns the saved file size for validation.
		Parameters:
			key (str): Export key.
		Returns:
			size (int | None): Export file size.
		"""
		...

class LocalExportStorage:
	def __init__( self, base_path: str):
		self._base = Path.cwd( ) / Path( base_path )
		try:
			self._base.mkdir( parents=True, exist_ok=True )
		except Exception:
			raise RuntimeError( "Cannot create export storage directory." )

	def _resolve( self, key: str ) -> Path:
		"""
		Safety check to make sure file path resolves inside the storage root.
		Parameters:
			key (str): Export key.
		Returns:
			path (Path): Export path.
		"""
		path = ( self._base / key ).resolve( )
		if self._base.resolve( ) not in path.parents:
			raise ValueError( f"Export key resolves outside storage root: { key }" )
		return path

	async def save( self, key: str, source_path: Path ) -> None:
		def _write():
			dest = self._resolve( key )
			dest.parent.mkdir( parents=True, exist_ok=True )

			fd, tmp_path = tempfile.mkstemp( dir=dest.parent, suffix=".tmp" )
			try:
				with os.fdopen( fd, "wb" ) as tmp_f:
					with open( source_path, "rb" ) as src_f:
						shutil.copyfileobj( src_f, tmp_f )
					tmp_f.flush( )
					os.fsync( tmp_f.fileno( ) )
				os.replace( tmp_path, dest )
			except Exception:
				Path( tmp_path ).unlink( missing_ok=True )
				raise

		await asyncio.to_thread( _write )

	async def delete( self, key: str ) -> None:
		await asyncio.to_thread( lambda: self._resolve( key ).unlink( missing_ok=True ) )

	async def get_size( self, key: str ) -> int | None:
		def _stat( ) -> int | None:
			path = self._resolve( key )
			return path.stat( ).st_size if path.exists( ) else None
		return await asyncio.to_thread( _stat )

@lru_cache( maxsize=1 )
def _s3_client( ):
	return boto3.client(
		"s3",
		endpoint_url=settings.export_s3_endpoint_url or None,
		region_name=settings.export_s3_region,
		aws_access_key_id=settings.export_s3_access_key_id.get_secret_value( ) if settings.export_s3_access_key_id is not None else None,
		aws_secret_access_key=settings.export_s3_secret_access_key.get_secret_value( ) if settings.export_s3_secret_access_key is not None else None,
		config=Config(
			signature_version="s3v4",
			retries={ "max_attempts": 3, "mode": "standard" },
			connect_timeout=5,
			read_timeout=30
		)
	)

class S3ExportStorage:
	def __init__( self, bucket: str ):
		self._bucket = bucket

	async def save( self, key: str, source_path: Path ) -> None:
		def _upload( ):
			_s3_client( ).upload_file(
				str( source_path ),
				self._bucket,
				key,
				ExtraArgs={ "ContentType": "application/zip" }
			)

		try:
			await asyncio.to_thread( _upload )
		except ClientError as exc:
			logger.error( "S3 export upload failed", extra={ "key": key, "error": str( exc ) } )
			raise

	async def get_download_ref( self, key: str, ttl_seconds: int ) -> str:
		"""
		Returns S3 download link.
		Parameters:
			key (str): Export key.
			ttl_seconds (int): TTL time in seconds.
		Returns:
			url (str): S3 download link.
		"""
		def _presign( ):
			return _s3_client( ).generate_presigned_url(
				"get_object",
				Params={ "Bucket": self._bucket, "Key": key },
				ExpiresIn=ttl_seconds
			)

		return await asyncio.to_thread( _presign )

	async def delete( self, key: str ) -> None:
		def _delete( ):
			_s3_client( ).delete_object( Bucket=self._bucket, Key=key )

		await asyncio.to_thread( _delete )

	async def get_size( self, key: str ) -> int | None:
		def _head( ) -> int | None:
			try:
				resp = _s3_client( ).head_object( Bucket=self._bucket, Key=key )
				return resp[ "ContentLength" ]
			except ClientError as exc:
				if exc.response.get( "Error", { } ).get( "Code" ) in ( "404", "NoSuchKey" ):
					return None
				raise
		return await asyncio.to_thread( _head )

def get_export_storage( backend: str | None = None ) -> ExportStorage:
	"""
	Get the current configured backend storage interface OR the configured one for the export row.
	Parameters:
		backend (str | None): Backend config string.
	Returns:
		export_storage (ExportStorage): Export storage interface.
	"""
	resolved = ( backend or settings.export_storage_backend ).lower( )
	if settings.export_s3_bucket is not None and resolved == "s3":
		return S3ExportStorage( bucket=settings.export_s3_bucket )
	return LocalExportStorage( settings.export_local_path )