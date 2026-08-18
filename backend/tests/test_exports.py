from __future__ import annotations

# Fixtures used here come straight from conftest.py: db_session (savepoint-
# isolated, rolled back per test), client (httpx AsyncClient with get_db /
# get_redis / rate limiters overridden), redis_client (real Redis, flushed
# per test), user / other_user / api_key / auth_headers.
#
# ASSUMES the DataExport model exists with the schema built up over this
# conversation, INCLUDING a nullable `purged_at` column — these tests
# won't run until that migration lands.
import contextlib
import csv
import json
from datetime import datetime, timedelta, timezone
from ipaddress import IPv4Address
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import exports.service as export_service
import pytest
from auth.security import create_access_token
from botocore.exceptions import ClientError
from exports.format import flatten_for_csv, to_export_dict
from exports.storage import LocalExportStorage, S3ExportStorage, get_export_storage
from httpx import AsyncClient
from models.models import APIKey, DataExport, LogEntry, User
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.anyio


# ---------------------------------------------------------------------------
# Local helpers — LogEntry / DataExport have no fixtures of their own yet
# ---------------------------------------------------------------------------

async def _make_api_key_row( db_session: AsyncSession, user: User ) -> APIKey:
	from auth.security import generate_api_key, hash_token

	raw_key = generate_api_key( )
	key_row = APIKey(
		user_id    = user.id,
		key_hash   = hash_token( raw_key ),
		key_prefix = raw_key[ :8 ],
		label      = "test-key"
	)
	db_session.add( key_row )
	await db_session.commit( )
	await db_session.refresh( key_row )
	return key_row


async def _make_log_entry_row(
	db_session: AsyncSession,
	user: User,
	api_key: APIKey,
	captured_at: datetime | None = None,
	**overrides
) -> LogEntry:
	entry_row = LogEntry(
		api_key_id        = api_key.id,
		user_id           = user.id,
		src_ip            = IPv4Address( "10.0.0.1" ),
		dst_ip            = IPv4Address( "10.0.0.2" ),
		src_port          = 1234,
		dst_port          = 443,
		protocol          = "TCP",
		packet_size_bytes = 512,
		flags             = "SYN",
		src_country_code  = "US",
		dst_country_code  = "GB",
		src_geo_status    = "RESOLVED",
		dst_geo_status    = "RESOLVED",
		anomaly_score     = 0.1,
		raw_payload       = { "raw": "payload" },
		anomaly_reasons   = [ { "name": "test", "score": 0.1, "detail": "test" } ],
		captured_at       = captured_at or datetime.now( timezone.utc )
	)
	for field, value in overrides.items( ):
		setattr( entry_row, field, value )
	db_session.add( entry_row )
	await db_session.commit( )
	await db_session.refresh( entry_row )
	return entry_row


def _build_data_export_row( user: User, **overrides ) -> DataExport:
	"""Deliberately NOT committed — callers add + commit explicitly, so
	tests that only need an in-memory object (e.g. get_download_link unit
	tests) don't pay for a DB round trip they don't need."""
	export_id = uuid4( )
	defaults = {
		"id":              export_id,
		"user_id":         user.id,
		"storage_backend": "LOCAL",
		"storage_key":     f"{ user.id }/{ export_id }.zip",
		"status":          "PENDING",
		"triggered_by":    "MANUAL",
		"expires_at":      datetime.now( timezone.utc ) + timedelta( hours=72 )
	}
	defaults.update( overrides )
	return DataExport( **defaults )


def _auth_headers_for( user: User ) -> dict[ str, str ]:
	access_token = create_access_token( str( user.id ) )
	return { "Authorization": f"Bearer { access_token }" }


@pytest.fixture
def patch_export_session( monkeypatch, db_session: AsyncSession ):
	"""run_export_pipeline deliberately opens its OWN db session via
	async_session() — see its docstring, this matters for background-task
	reliability outside a request's lifecycle. In tests that's the wrong
	thing: db_session is savepoint-isolated and rolled back at teardown, so
	a genuinely separate connection opened via the real async_session()
	factory would never see this test's uncommitted fixture data. This
	patches exports.service.async_session so run_export_pipeline
	transparently reuses db_session instead of opening a real second
	connection."""
	@contextlib.asynccontextmanager
	async def _fake_session( ):
		yield db_session

	monkeypatch.setattr( export_service, "AsyncSessionLocal", _fake_session )


# ---------------------------------------------------------------------------
# format.py
# ---------------------------------------------------------------------------

class TestFormat:
	async def test_to_export_dict_includes_raw_payload( self, db_session, user, api_key ):
		entry_row = await _make_log_entry_row(
			db_session, user, api_key, raw_payload={ "secret": "value" }
		)

		row = to_export_dict( entry_row )

		# The one deliberate deviation from GET /logs / GET /analytics/* —
		# raw_payload is normally excluded everywhere else, but export is
		# the user's one channel to get back exactly what they submitted.
		assert row[ "raw_payload" ] == { "secret": "value" }
		assert row[ "src_ip" ] == "10.0.0.1"
		assert "api_key_id" not in row     # internal FK never exported
		assert "inserted_at" not in row    # server bookkeeping never exported

	def test_flatten_for_csv_stringifies_nested_fields( self ):
		row = {
			"captured_at":     datetime( 2026, 1, 1, tzinfo=timezone.utc ),
			"anomaly_reasons": [ { "name": "x", "score": 0.5 } ],
			"raw_payload":     { "a": 1 },
			"id":              1
		}
		flat = flatten_for_csv( row )

		assert isinstance( flat[ "anomaly_reasons" ], str )
		assert json.loads( flat[ "anomaly_reasons" ] ) == [ { "name": "x", "score": 0.5 } ]
		assert isinstance( flat[ "raw_payload" ], str )
		assert flat[ "captured_at" ] == "2026-01-01T00:00:00+00:00"


# ---------------------------------------------------------------------------
# LocalExportStorage
# ---------------------------------------------------------------------------

class TestLocalExportStorage:
	async def test_save_then_get_size_round_trip( self, tmp_path ):
		storage = LocalExportStorage( str( tmp_path ) )
		source = tmp_path / "source.zip"
		source.write_bytes( b"hello world" )

		await storage.save( "user123/export1.zip", source )

		size = await storage.get_size( "user123/export1.zip" )
		assert size == len( b"hello world" )
		assert ( tmp_path / "user123" / "export1.zip" ).read_bytes( ) == b"hello world"

	async def test_get_size_returns_none_for_missing_key( self, tmp_path ):
		storage = LocalExportStorage( str( tmp_path ) )
		assert await storage.get_size( "does/not/exist.zip" ) is None

	async def test_delete_removes_file( self, tmp_path ):
		storage = LocalExportStorage( str( tmp_path ) )
		source = tmp_path / "source.zip"
		source.write_bytes( b"data" )
		await storage.save( "u/e.zip", source )

		await storage.delete( "u/e.zip" )

		assert await storage.get_size( "u/e.zip" ) is None

	async def test_delete_missing_key_does_not_raise( self, tmp_path ):
		storage = LocalExportStorage( str( tmp_path ) )
		await storage.delete( "never/existed.zip" )

	async def test_path_traversal_key_is_rejected( self, tmp_path ):
		storage = LocalExportStorage( str( tmp_path ) )
		with pytest.raises( ValueError ):
			storage._resolve( "../../etc/passwd" )

	async def test_failed_write_leaves_no_partial_file_at_destination( self, tmp_path, monkeypatch ):
		storage = LocalExportStorage( str( tmp_path ) )
		source = tmp_path / "source.zip"
		source.write_bytes( b"partial write test" )

		import shutil as shutil_module

		def _boom( *args, **kwargs ):
			raise OSError( "simulated disk failure mid-copy" )

		monkeypatch.setattr( shutil_module, "copyfileobj", _boom )

		with pytest.raises( OSError ):
			await storage.save( "u/e.zip", source )

		# The atomic-write guarantee: a failed write must never leave a
		# partial file visible at the final destination.
		assert not ( tmp_path / "u" / "e.zip" ).exists( )

	def test_constructor_raises_clear_error_on_unwritable_path( self, monkeypatch ):
		from pathlib import Path

		def _boom( self, parents=True, exist_ok=True ):
			raise OSError( "Read-only file system" )

		monkeypatch.setattr( Path, "mkdir", _boom )

		with pytest.raises( RuntimeError, match="Cannot create export storage directory" ):
			LocalExportStorage( "/some/unwritable/path" )


# ---------------------------------------------------------------------------
# S3ExportStorage — boto3 client mocked, no real network/AWS calls
# ---------------------------------------------------------------------------

class TestS3ExportStorage:
	@pytest.fixture
	def mock_s3_client( self, monkeypatch ):
		client = MagicMock( )
		monkeypatch.setattr( "exports.storage._s3_client", lambda: client )
		return client

	async def test_save_calls_upload_file_with_correct_args( self, mock_s3_client, tmp_path ):
		storage = S3ExportStorage( bucket="my-bucket" )
		source = tmp_path / "export.zip"
		source.write_bytes( b"zip content" )

		await storage.save( "user1/export1.zip", source )

		mock_s3_client.upload_file.assert_called_once( )
		args, kwargs = mock_s3_client.upload_file.call_args
		assert args[ 0 ] == str( source )
		assert args[ 1 ] == "my-bucket"
		assert args[ 2 ] == "user1/export1.zip"
		assert kwargs[ "ExtraArgs" ][ "ContentType" ] == "application/zip"

	async def test_get_size_returns_content_length( self, mock_s3_client ):
		mock_s3_client.head_object.return_value = { "ContentLength": 4096 }
		storage = S3ExportStorage( bucket="my-bucket" )

		size = await storage.get_size( "user1/export1.zip" )

		assert size == 4096

	async def test_get_size_returns_none_on_404( self, mock_s3_client ):
		mock_s3_client.head_object.side_effect = ClientError(
			{ "Error": { "Code": "404", "Message": "Not Found" } }, "HeadObject"
		)
		storage = S3ExportStorage( bucket="my-bucket" )

		assert await storage.get_size( "missing.zip" ) is None

	async def test_get_size_reraises_non_404_errors( self, mock_s3_client ):
		mock_s3_client.head_object.side_effect = ClientError(
			{ "Error": { "Code": "403", "Message": "Forbidden" } }, "HeadObject"
		)
		storage = S3ExportStorage( bucket="my-bucket" )

		with pytest.raises( ClientError ):
			await storage.get_size( "forbidden.zip" )

	async def test_get_download_ref_presigns_with_given_ttl( self, mock_s3_client ):
		mock_s3_client.generate_presigned_url.return_value = "https://signed.example/url"
		storage = S3ExportStorage( bucket="my-bucket" )

		url = await storage.get_download_ref( "key.zip", ttl_seconds=300 )

		assert url == "https://signed.example/url"
		_, kwargs = mock_s3_client.generate_presigned_url.call_args
		assert kwargs[ "ExpiresIn" ] == 300
		assert kwargs[ "Params" ][ "Bucket" ] == "my-bucket"
		assert kwargs[ "Params" ][ "Key" ] == "key.zip"


class TestGetExportStorageFactory:
	def test_defaults_to_current_settings_backend( self, monkeypatch, tmp_path ):
		monkeypatch.setattr( "exports.storage.settings.export_storage_backend", "local" )
		monkeypatch.setattr( "exports.storage.settings.export_local_path", str( tmp_path ) )
		storage = get_export_storage( )
		assert isinstance( storage, LocalExportStorage )

	def test_explicit_backend_overrides_current_settings( self, monkeypatch, tmp_path ):
		# Guards against the resolved bug: an export ROW created under an
		# old backend config must still resolve to that backend, even if
		# the deployment's current default has since changed.
		monkeypatch.setattr( "exports.storage.settings.export_storage_backend", "s3" )
		monkeypatch.setattr( "exports.storage.settings.export_local_path", str( tmp_path ) )
		storage = get_export_storage( backend="LOCAL" )
		assert isinstance( storage, LocalExportStorage )


# ---------------------------------------------------------------------------
# stream_logs_for_export — keyset pagination correctness
# ---------------------------------------------------------------------------

class TestStreamLogsForExport:
	async def test_chunks_respect_chunk_size_and_cover_all_rows(
		self, db_session, user, api_key, monkeypatch
	):
		monkeypatch.setattr( export_service, "EXPORT_CHUNK_SIZE", 3 )

		base = datetime( 2026, 1, 1, tzinfo=timezone.utc )
		for i in range( 7 ):
			await _make_log_entry_row( db_session, user, api_key, captured_at=base + timedelta( minutes=i ) )

		chunks = [ ]
		async for chunk in export_service.stream_logs_for_export( db_session, user.id ):
			chunks.append( chunk )

		sizes = [ len( c ) for c in chunks ]
		assert sizes == [ 3, 3, 1 ]   # 7 rows, chunk size 3: full, full, partial
		assert sum( sizes ) == 7

		all_ids = [ row.id for chunk in chunks for row in chunk ]
		assert len( all_ids ) == len( set( all_ids ) )   # no duplicates across the chunk boundary

	async def test_does_not_include_other_users_logs(
		self, db_session, user, other_user, api_key
	):
		other_key = await _make_api_key_row( db_session, other_user )
		await _make_log_entry_row( db_session, user, api_key )
		await _make_log_entry_row( db_session, other_user, other_key )

		chunks = [ chunk async for chunk in export_service.stream_logs_for_export( db_session, user.id ) ]
		all_rows = [ row for chunk in chunks for row in chunk ]

		assert len( all_rows ) == 1
		assert all_rows[ 0 ].user_id == user.id

	async def test_empty_result_for_user_with_no_logs( self, db_session, user ):
		chunks = [ chunk async for chunk in export_service.stream_logs_for_export( db_session, user.id ) ]
		assert chunks == [ ]


# ---------------------------------------------------------------------------
# write_export_files
# ---------------------------------------------------------------------------

class TestWriteExportFiles:
	async def test_writes_correct_row_count_to_both_formats(
		self, db_session, user, api_key, tmp_path
	):
		for _ in range( 5 ):
			await _make_log_entry_row( db_session, user, api_key )

		csv_path, jsonl_path, row_count = await export_service.write_export_files(
			db_session, user.id, tmp_path
		)

		assert row_count == 5

		with open( csv_path ) as f:
			csv_rows = list( csv.DictReader( f ) )
		assert len( csv_rows ) == 5

		with open( jsonl_path ) as f:
			jsonl_lines = f.readlines( )
		assert len( jsonl_lines ) == 5
		assert json.loads( jsonl_lines[ 0 ] )[ "raw_payload" ] == { "raw": "payload" }

	async def test_zero_rows_still_produces_valid_header_only_csv(
		self, db_session, user, tmp_path
	):
		csv_path, jsonl_path, row_count = await export_service.write_export_files(
			db_session, user.id, tmp_path
		)

		assert row_count == 0
		with open( csv_path ) as f:
			assert list( csv.DictReader( f ) ) == [ ]
		assert jsonl_path.read_text( ) == ""


# ---------------------------------------------------------------------------
# create_pending_export
# ---------------------------------------------------------------------------

class TestCreatePendingExport:
	async def test_creates_pending_row_with_correct_storage_key( self, db_session, user, monkeypatch ):
		monkeypatch.setattr( export_service.settings, "export_storage_backend", "local" )
		monkeypatch.setattr( export_service.settings, "export_link_ttl_hours", 72 )

		export_row = await export_service.create_pending_export( db_session, user, triggered_by="MANUAL" )

		assert export_row.status == "PENDING"
		assert export_row.storage_backend == "LOCAL"
		assert export_row.storage_key == f"{ user.id }/{ export_row.id }.zip"
		assert export_row.triggered_by == "MANUAL"
		assert export_row.expires_at > datetime.now( timezone.utc )

		# Committed, not just flushed — the router needs this row visible
		# immediately so it can return the id in the 202 response.
		fetched = await db_session.get( DataExport, export_row.id )
		assert fetched is not None


# ---------------------------------------------------------------------------
# run_export_pipeline — success, verification failure, exception paths
# ---------------------------------------------------------------------------

class TestRunExportPipeline:
	async def test_success_path_marks_ready_with_verified_size(
		self, db_session, user, api_key, tmp_path, monkeypatch, patch_export_session
	):
		monkeypatch.setattr( export_service.settings, "export_storage_backend", "local" )
		monkeypatch.setattr( export_service.settings, "export_local_path", str( tmp_path ) )

		await _make_log_entry_row( db_session, user, api_key )
		export_row = _build_data_export_row( user )
		db_session.add( export_row )
		await db_session.commit( )

		await export_service.run_export_pipeline( export_row.id, user.id )

		refreshed = await db_session.get( DataExport, export_row.id )
		assert refreshed.status == "READY"
		assert refreshed.file_size_bytes is not None
		assert refreshed.file_size_bytes > 0

		# Would have caught the earlier volume-mount incident: the bytes
		# must actually be retrievable through the same storage abstraction.
		storage = get_export_storage( refreshed.storage_backend )
		assert await storage.get_size( refreshed.storage_key ) == refreshed.file_size_bytes

	async def test_save_verification_failure_marks_failed_not_ready(
		self, db_session, user, monkeypatch, patch_export_session
	):
		"""Regression test for the actual incident: a save() that raises
		no exception but doesn't land where expected must NOT reach READY."""
		export_row = _build_data_export_row( user )
		db_session.add( export_row )
		await db_session.commit( )

		fake_storage = AsyncMock( )
		fake_storage.save     = AsyncMock( return_value=None )    # "succeeds" but writes nothing
		fake_storage.get_size = AsyncMock( return_value=None )    # verification finds nothing
		monkeypatch.setattr( export_service, "get_export_storage", lambda backend=None: fake_storage )

		await export_service.run_export_pipeline( export_row.id, user.id )

		refreshed = await db_session.get( DataExport, export_row.id )
		assert refreshed.status == "FAILED"

	async def test_exception_during_pipeline_marks_failed_and_does_not_propagate(
		self, db_session, user, monkeypatch, patch_export_session
	):
		"""run_export_pipeline is called from arq/BackgroundTasks context
		with no caller watching for a raised exception — it MUST swallow
		and record failure rather than propagate, or the failure is lost."""
		export_row = _build_data_export_row( user )
		db_session.add( export_row )
		await db_session.commit( )

		async def _boom( *args, **kwargs ):
			raise RuntimeError( "simulated failure writing export files" )

		monkeypatch.setattr( export_service, "write_export_files", _boom )

		await export_service.run_export_pipeline( export_row.id, user.id )   # must not raise

		refreshed = await db_session.get( DataExport, export_row.id )
		assert refreshed.status == "FAILED"

	async def test_missing_export_row_logs_and_returns_without_error(
		self, patch_export_session
	):
		await export_service.run_export_pipeline( uuid4( ), uuid4( ) )


# ---------------------------------------------------------------------------
# get_download_link / resolve_download_token
# ---------------------------------------------------------------------------

class TestGetDownloadLink:
	async def test_s3_backend_mints_real_redis_token_with_given_ttl( self, user, monkeypatch ):
		export_row = _build_data_export_row( user, storage_backend="S3", status="READY" )

		mock_storage = AsyncMock( S3ExportStorage )
		mock_storage.get_download_ref = AsyncMock( return_value="https://presigned.example/x" )
		monkeypatch.setattr( export_service, "get_export_storage", lambda backend=None: mock_storage )

		redis = AsyncMock( )
		url = await export_service.setup_ttl_download_link( redis, export_row, ttl_seconds=300 )

		assert "/exports/download?token=" in url
		redis.set.assert_called( )

	async def test_local_backend_mints_real_redis_token_with_given_ttl(
		self, user, db_session, redis_client: Redis
	):
		export_row = _build_data_export_row( user, storage_backend="LOCAL", status="READY" )
		db_session.add( export_row )
		await db_session.commit( )
		await db_session.refresh( export_row )

		url = await export_service.setup_ttl_download_link( redis_client, export_row, ttl_seconds=300 )

		assert "/exports/download?token=" in url
		raw_token = url.split( "token=" )[ 1 ]

		resolved = await export_service.resolve_download_token( db_session, redis_client, raw_token )
		assert resolved == export_row.id


class TestResolveDownloadToken:
	async def test_returns_none_for_unknown_or_expired_token( self, db_session, redis_client: Redis ):
		resolved = await export_service.resolve_download_token( db_session, redis_client, "garbage-token" )
		assert resolved is None


# ---------------------------------------------------------------------------
# Quota + staleness + purge
# ---------------------------------------------------------------------------

class TestCountExportsToday:
	async def test_counts_only_last_24_hours( self, db_session, user ):
		recent = _build_data_export_row( user, created_at=datetime.now( timezone.utc ) )
		old    = _build_data_export_row( user, created_at=datetime.now( timezone.utc ) - timedelta( days=2 ) )
		db_session.add_all( [ recent, old ] )
		await db_session.commit( )

		count = await export_service.count_exports_today( db_session, user.id )

		assert count == 1


class TestMarkStalePendingExportsFailed:
	async def test_old_pending_marked_failed( self, db_session, user, monkeypatch ):
		monkeypatch.setattr( export_service, "STALE_PENDING_THRESHOLD_MINUTES", 30 )

		stale = _build_data_export_row(
			user, status="PENDING", created_at=datetime.now( timezone.utc ) - timedelta( minutes=60 )
		)
		fresh = _build_data_export_row(
			user, status="PENDING", created_at=datetime.now( timezone.utc ) - timedelta( minutes=1 )
		)
		db_session.add_all( [ stale, fresh ] )
		await db_session.commit( )

		count = await export_service.mark_stale_pending_exports_failed( db_session )

		assert count == 1
		assert ( await db_session.get( DataExport, stale.id ) ).status == "FAILED"
		assert ( await db_session.get( DataExport, fresh.id ) ).status == "PENDING"


class TestPurgeExpiredExports:
	async def test_deletes_file_and_sets_purged_at( self, db_session, user, monkeypatch ):
		expired = _build_data_export_row(
			user, status="READY", expires_at=datetime.now( timezone.utc ) - timedelta( hours=1 )
		)
		db_session.add( expired )
		await db_session.commit( )

		mock_storage = AsyncMock( )
		monkeypatch.setattr( export_service, "get_export_storage", lambda backend=None: mock_storage )

		purged = await export_service.purge_expired_exports( db_session )

		assert purged == 1
		mock_storage.delete.assert_called_once_with( expired.storage_key )
		refreshed = await db_session.get( DataExport, expired.id )
		assert refreshed.purged_at is not None
		assert refreshed.status == "READY"   # status unchanged — audit trail preserved

	async def test_skips_already_purged_and_not_yet_expired( self, db_session, user, monkeypatch ):
		already_purged = _build_data_export_row(
			user,
			status     = "READY",
			expires_at = datetime.now( timezone.utc ) - timedelta( hours=1 ),
			purged_at  = datetime.now( timezone.utc )
		)
		not_expired = _build_data_export_row(
			user, status="READY", expires_at=datetime.now( timezone.utc ) + timedelta( hours=1 )
		)
		db_session.add_all( [ already_purged, not_expired ] )
		await db_session.commit( )

		mock_storage = AsyncMock( )
		monkeypatch.setattr( export_service, "get_export_storage", lambda backend=None: mock_storage )

		purged = await export_service.purge_expired_exports( db_session )

		assert purged == 0
		mock_storage.delete.assert_not_called( )

	async def test_uses_the_rows_own_backend_not_current_default( self, db_session, user, monkeypatch ):
		"""Regression test for the backend-resolution bug fixed alongside
		purge: a row's OWN storage_backend must be used, not whatever the
		live settings currently say."""
		s3_export = _build_data_export_row(
			user,
			status          = "READY",
			storage_backend = "S3",
			expires_at      = datetime.now( timezone.utc ) - timedelta( hours=1 )
		)
		db_session.add( s3_export )
		await db_session.commit( )

		seen_backends = [ ]

		def _fake_get_storage( backend=None ):
			seen_backends.append( backend )
			return AsyncMock( )

		monkeypatch.setattr( export_service, "get_export_storage", _fake_get_storage )
		monkeypatch.setattr( export_service.settings, "export_storage_backend", "local" )   # current default differs

		await export_service.purge_expired_exports( db_session )

		assert seen_backends == [ "S3" ]

	async def test_one_failure_does_not_block_the_rest( self, db_session, user, monkeypatch ):
		e1 = _build_data_export_row(
			user, status="READY", expires_at=datetime.now( timezone.utc ) - timedelta( hours=1 )
		)
		e2 = _build_data_export_row(
			user, status="READY", expires_at=datetime.now( timezone.utc ) - timedelta( hours=1 )
		)
		db_session.add_all( [ e1, e2 ] )
		await db_session.commit( )

		call_count = { "n": 0 }

		async def _delete( key ):
			call_count[ "n" ] += 1
			if call_count[ "n" ] == 1:
				raise RuntimeError( "simulated transient storage error" )

		mock_storage = AsyncMock( )
		mock_storage.delete = _delete
		monkeypatch.setattr( export_service, "get_export_storage", lambda backend=None: mock_storage )

		purged = await export_service.purge_expired_exports( db_session )

		assert purged == 1   # the second one still succeeds


# ---------------------------------------------------------------------------
# Router — real HTTP calls through `client`, real redis via `redis_client`
# ---------------------------------------------------------------------------

class TestExportsRouter:
	async def test_create_export_returns_202_and_enqueues_pipeline(
		self, client: AsyncClient, auth_headers, monkeypatch
	):
		mock_pool = AsyncMock( )
		monkeypatch.setattr( "exports.router.get_arq_pool", lambda: mock_pool )

		response = await client.post( "/exports", headers=auth_headers )

		assert response.status_code == 202
		body = response.json( )
		assert body[ "status" ] == "PENDING"
		mock_pool.enqueue_job.assert_called_once( )
		assert mock_pool.enqueue_job.call_args[ 0 ][ 0 ] == "run_export_pipeline_task"

	async def test_create_export_returns_429_over_daily_limit(
		self, client: AsyncClient, auth_headers, monkeypatch
	):
		monkeypatch.setattr( "exports.router.settings.export_max_per_user_per_day", 1 )
		monkeypatch.setattr( "exports.router.get_arq_pool", lambda: AsyncMock( ) )

		first = await client.post( "/exports", headers=auth_headers )
		assert first.status_code == 202

		second = await client.post( "/exports", headers=auth_headers )
		assert second.status_code == 429

	async def test_list_exports_only_returns_own_users_exports(
		self, client: AsyncClient, auth_headers, db_session, user, other_user
	):
		mine   = _build_data_export_row( user, status="READY" )
		theirs = _build_data_export_row( other_user, status="READY" )
		db_session.add_all( [ mine, theirs ] )
		await db_session.commit( )

		response = await client.get( "/exports", headers=auth_headers )

		assert response.status_code == 200
		ids = [ row[ "id" ] for row in response.json( )[ "rows" ] ]
		assert str( mine.id ) in ids
		assert str( theirs.id ) not in ids

	async def test_download_link_rejects_non_owner(
		self, client: AsyncClient, db_session, user, other_user
	):
		export_row = _build_data_export_row( user, status="READY" )
		db_session.add( export_row )
		await db_session.commit( )

		response = await client.post(
			f"/exports/{ export_row.id }/download-link",
			headers = _auth_headers_for( other_user )
		)

		assert response.status_code == 404

	async def test_download_link_rejects_not_ready(
		self, client: AsyncClient, auth_headers, db_session, user
	):
		export_row = _build_data_export_row( user, status="PENDING" )
		db_session.add( export_row )
		await db_session.commit( )

		response = await client.post( f"/exports/{ export_row.id }/download-link", headers=auth_headers )

		assert response.status_code == 409

	async def test_full_authenticated_local_download_round_trip(
		self, client: AsyncClient, auth_headers, db_session, user, tmp_path, monkeypatch
	):
		"""End-to-end: authenticated link mint -> real Redis token ->
		public download route -> actual file bytes served."""
		monkeypatch.setattr( "exports.router.settings.export_local_path", str( tmp_path ) )

		storage = LocalExportStorage( str( tmp_path ) )
		source = tmp_path / "source.zip"
		source.write_bytes( b"export contents" )

		export_row = _build_data_export_row( user, status="READY" )
		await storage.save( export_row.storage_key, source )
		db_session.add( export_row )
		await db_session.commit( )

		link_response = await client.post( f"/exports/{ export_row.id }/download-link", headers=auth_headers )
		assert link_response.status_code == 200
		download_url = link_response.json( )[ "download_url" ]

		download_response = await client.get( download_url )
		assert download_response.status_code == 200
		assert download_response.content == b"export contents"