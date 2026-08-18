from __future__ import annotations

# Same fixture notes as test_exports.py. Uses `user` / `other_user` /
# `api_key` from conftest.py directly where they fit (most tests here need
# at most two distinct users), and local helpers only for LogEntry /
# DataExport, which have no conftest fixtures of their own.
from datetime import datetime, timedelta, timezone
from ipaddress import IPv4Address
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
import retention.job as retention_job
import retention.service as retention_service
from models.models import APIKey, DataExport, LogEntry, User
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.anyio


# ---------------------------------------------------------------------------
# Local helpers
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
	db_session: AsyncSession, user: User, api_key: APIKey, captured_at: datetime
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
		raw_payload       = { },
		anomaly_reasons   = [ ],
		captured_at       = captured_at
	)
	db_session.add( entry_row )
	await db_session.commit( )
	await db_session.refresh( entry_row )
	return entry_row


def _build_data_export_row( user: User, **overrides ) -> DataExport:
	export_id = uuid4( )
	defaults = {
		"id": export_id,
		"user_id": user.id,
		"storage_backend": "LOCAL",
		"storage_key": f"{ user.id }/{ export_id }.zip",
		"status": "READY",
		"triggered_by": "RETENTION_JOB",
		"created_at": datetime.now( timezone.utc ),
		"expires_at": datetime.now( timezone.utc ) + timedelta( hours=72 )
	}
	defaults.update( overrides )
	return DataExport( **defaults )


def _days_ago( n: int ) -> datetime:
	return datetime.now( timezone.utc ) - timedelta( days=n )


class _AsyncSessionCtx:
	"""Minimal stand-in for `async with AsyncSessionLocal() as db:` so job-level
	tests can run without touching a real database — they only care which
	service functions get CALLED, not what a real session does."""
	def __init__( self, session ):
		self._session = session

	async def __aenter__( self ):
		return self._session

	async def __aexit__( self, *args ):
		return False


# ---------------------------------------------------------------------------
# distinct_user_ids_with_logs_older_than
# ---------------------------------------------------------------------------

class TestDistinctUserIds:
	async def test_returns_only_users_with_logs_older_than_cutoff(
		self, db_session, user, other_user, api_key
	):
		other_key = await _make_api_key_row( db_session, other_user )
		await _make_log_entry_row( db_session, user, api_key, captured_at=_days_ago( 40 ) )
		await _make_log_entry_row( db_session, other_user, other_key, captured_at=_days_ago( 1 ) )

		user_ids = await retention_service.distinct_user_ids_with_logs_older_than( db_session, _days_ago( 30 ) )

		assert user_ids == [ user.id ]

	async def test_deduplicates_multiple_logs_from_same_user( self, db_session, user, api_key ):
		await _make_log_entry_row( db_session, user, api_key, captured_at=_days_ago( 40 ) )
		await _make_log_entry_row( db_session, user, api_key, captured_at=_days_ago( 35 ) )

		user_ids = await retention_service.distinct_user_ids_with_logs_older_than( db_session, _days_ago( 30 ) )

		assert user_ids == [ user.id ]


# ---------------------------------------------------------------------------
# has_recent_retention_export
# ---------------------------------------------------------------------------

class TestHasRecentRetentionExport:
	async def test_true_when_ready_export_exists_in_window( self, db_session, user ):
		db_session.add( _build_data_export_row( user, status="READY", created_at=_days_ago( 2 ) ) )
		await db_session.commit( )

		assert await retention_service.has_recent_retention_export( db_session, user.id, _days_ago( 7 ) ) is True

	async def test_false_when_export_is_outside_window( self, db_session, user ):
		db_session.add( _build_data_export_row( user, status="READY", created_at=_days_ago( 10 ) ) )
		await db_session.commit( )

		assert await retention_service.has_recent_retention_export( db_session, user.id, _days_ago( 7 ) ) is False

	async def test_false_when_export_exists_but_not_ready( self, db_session, user ):
		db_session.add( _build_data_export_row( user, status="FAILED", created_at=_days_ago( 1 ) ) )
		await db_session.commit( )

		assert await retention_service.has_recent_retention_export( db_session, user.id, _days_ago( 7 ) ) is False

	async def test_ignores_manual_exports_only_counts_retention_job( self, db_session, user ):
		db_session.add(
			_build_data_export_row( user, status="READY", created_at=_days_ago( 1 ), triggered_by="MANUAL" )
		)
		await db_session.commit( )

		assert await retention_service.has_recent_retention_export( db_session, user.id, _days_ago( 7 ) ) is False


# ---------------------------------------------------------------------------
# send_retention_warnings — orchestration, mocking its collaborators
# ---------------------------------------------------------------------------

class TestSendRetentionWarnings:
	@pytest.fixture( autouse=True )
	def _patch_settings( self, monkeypatch ):
		monkeypatch.setattr( retention_service.settings, "retention_days", 30 )
		monkeypatch.setattr( retention_service.settings, "retention_grace_period_days", 7 )
		monkeypatch.setattr( retention_service.settings, "retention_export_email_enabled", True )
		monkeypatch.setattr( retention_service.settings, "export_link_ttl_hours", 72 )

	async def test_warns_eligible_user_and_sends_email( self, db_session, user, api_key, monkeypatch ):
		await _make_log_entry_row( db_session, user, api_key, captured_at=_days_ago( 25 ) )

		export_row = _build_data_export_row( user, status="READY" )

		monkeypatch.setattr( retention_service, "create_pending_export", AsyncMock( return_value=export_row ) )
		monkeypatch.setattr( retention_service, "run_export_pipeline", AsyncMock( ) )
		monkeypatch.setattr( db_session, "refresh", AsyncMock( ) )
		monkeypatch.setattr(
			retention_service, "setup_ttl_download_link", AsyncMock( return_value="/exports/download?token=abc" )
		)
		mock_email = AsyncMock( )
		# Patched at the point retention/service.py CALLS it — same lesson
		# as conftest.py's mock_email_send: `from mailer.service import
		# send_retention_warning_email` creates a local binding in
		# retention.service's namespace, so patching mailer.service itself
		# would not touch this copy.
		monkeypatch.setattr( retention_service, "send_retention_warning_email", mock_email )

		count = await retention_service.send_retention_warnings( db_session, redis=AsyncMock( ) )

		assert count == 1
		mock_email.assert_called_once( )

	async def test_skips_user_already_warned_this_cycle( self, db_session, user, api_key, monkeypatch ):
		await _make_log_entry_row( db_session, user, api_key, captured_at=_days_ago( 25 ) )
		db_session.add( _build_data_export_row( user, status="READY", created_at=_days_ago( 2 ) ) )
		await db_session.commit( )

		create_mock = AsyncMock( )
		monkeypatch.setattr( retention_service, "create_pending_export", create_mock )

		count = await retention_service.send_retention_warnings( db_session, redis=AsyncMock( ) )

		assert count == 0
		create_mock.assert_not_called( )

	async def test_does_not_email_if_export_fails_to_reach_ready(
		self, db_session, user, api_key, monkeypatch
	):
		await _make_log_entry_row( db_session, user, api_key, captured_at=_days_ago( 25 ) )

		failed_export = _build_data_export_row( user, status="FAILED" )
		monkeypatch.setattr( retention_service, "create_pending_export", AsyncMock( return_value=failed_export ) )
		monkeypatch.setattr( retention_service, "run_export_pipeline", AsyncMock( ) )
		monkeypatch.setattr( db_session, "refresh", AsyncMock( ) )
		mock_email = AsyncMock( )
		monkeypatch.setattr( retention_service, "send_retention_warning_email", mock_email )

		count = await retention_service.send_retention_warnings( db_session, redis=AsyncMock( ) )

		assert count == 0
		mock_email.assert_not_called( )

	async def test_does_not_email_when_email_flag_disabled( self, db_session, user, api_key, monkeypatch ):
		monkeypatch.setattr( retention_service.settings, "retention_export_email_enabled", False )
		await _make_log_entry_row( db_session, user, api_key, captured_at=_days_ago( 25 ) )

		export_row = _build_data_export_row( user, status="READY" )
		monkeypatch.setattr( retention_service, "create_pending_export", AsyncMock( return_value=export_row ) )
		monkeypatch.setattr( retention_service, "run_export_pipeline", AsyncMock( ) )
		monkeypatch.setattr( db_session, "refresh", AsyncMock( ) )
		monkeypatch.setattr( retention_service, "setup_ttl_download_link", AsyncMock( return_value="url" ) )
		mock_email = AsyncMock( )
		monkeypatch.setattr( retention_service, "send_retention_warning_email", mock_email )

		# Still counted as "warned" (export exists, dedupe works next cycle)
		# even though no email went out — the flag controls notification,
		# not whether the export itself happens.
		count = await retention_service.send_retention_warnings( db_session, redis=AsyncMock( ) )

		assert count == 1
		mock_email.assert_not_called( )

	async def test_one_users_failure_does_not_block_the_rest(
		self, db_session, user, other_user, api_key, monkeypatch
	):
		other_key = await _make_api_key_row( db_session, other_user )
		await _make_log_entry_row( db_session, user, api_key, captured_at=_days_ago( 25 ) )
		await _make_log_entry_row( db_session, other_user, other_key, captured_at=_days_ago( 25 ) )

		export_other = _build_data_export_row( other_user, status="READY" )
		call_count = { "n": 0 }

		async def _create_pending_export( db_arg, target_user, triggered_by ):
			call_count[ "n" ] += 1
			if target_user.id == user.id:
				raise RuntimeError( "simulated failure for first user" )
			return export_other

		monkeypatch.setattr( retention_service, "create_pending_export", _create_pending_export )
		monkeypatch.setattr( retention_service, "run_export_pipeline", AsyncMock( ) )
		monkeypatch.setattr( db_session, "refresh", AsyncMock( ) )
		monkeypatch.setattr( retention_service, "setup_ttl_download_link", AsyncMock( return_value="url" ) )
		monkeypatch.setattr( retention_service, "send_retention_warning_email", AsyncMock( ) )

		count = await retention_service.send_retention_warnings( db_session, redis=AsyncMock( ) )

		# both users attempted despite the first one failing
		assert call_count[ "n" ] == 2
		assert count == 1


# ---------------------------------------------------------------------------
# delete_expired_logs_for_user — chunked deletion
# ---------------------------------------------------------------------------

class TestDeleteExpiredLogsForUser:
	async def test_deletes_all_matching_rows_across_multiple_chunks(
		self, db_session, user, api_key, monkeypatch
	):
		monkeypatch.setattr( retention_service.settings, "retention_delete_chunk_size", 3 )

		for i in range( 7 ):
			await _make_log_entry_row(
				db_session, user, api_key, captured_at=_days_ago( 40 ) + timedelta( seconds=i )
			)

		deleted = await retention_service.delete_expired_logs_for_user( db_session, user.id, _days_ago( 30 ) )

		assert deleted == 7
		remaining = (
			await db_session.execute( select( LogEntry ).where( LogEntry.user_id == user.id ) )
		).scalars( ).all( )
		assert remaining == [ ]

	async def test_does_not_delete_rows_newer_than_cutoff( self, db_session, user, api_key, monkeypatch ):
		monkeypatch.setattr( retention_service.settings, "retention_delete_chunk_size", 100 )

		old_entry = await _make_log_entry_row( db_session, user, api_key, captured_at=_days_ago( 40 ) )
		new_entry = await _make_log_entry_row( db_session, user, api_key, captured_at=_days_ago( 1 ) )

		deleted = await retention_service.delete_expired_logs_for_user( db_session, user.id, _days_ago( 30 ) )

		assert deleted == 1
		assert await db_session.get( LogEntry, old_entry.id ) is None
		assert await db_session.get( LogEntry, new_entry.id ) is not None

	async def test_does_not_delete_other_users_rows(
		self, db_session, user, other_user, api_key, monkeypatch
	):
		monkeypatch.setattr( retention_service.settings, "retention_delete_chunk_size", 100 )

		other_key = await _make_api_key_row( db_session, other_user )
		await _make_log_entry_row( db_session, user, api_key, captured_at=_days_ago( 40 ) )
		other_entry = await _make_log_entry_row( db_session, other_user, other_key, captured_at=_days_ago( 40 ) )

		await retention_service.delete_expired_logs_for_user( db_session, user.id, _days_ago( 30 ) )

		assert await db_session.get( LogEntry, other_entry.id ) is not None


# ---------------------------------------------------------------------------
# delete_expired_logs_for_all_users — the skip-without-confirmed-warning safety logic
# ---------------------------------------------------------------------------

class TestDeleteExpiredLogsForAllUsers:
	@pytest.fixture( autouse=True )
	def _patch_settings( self, monkeypatch ):
		monkeypatch.setattr( retention_service.settings, "retention_days", 30 )
		monkeypatch.setattr( retention_service.settings, "retention_delete_chunk_size", 100 )

	async def test_deletes_for_user_with_confirmed_warning( self, db_session, user, api_key ):
		await _make_log_entry_row( db_session, user, api_key, captured_at=_days_ago( 40 ) )
		db_session.add( _build_data_export_row( user, status="READY", created_at=_days_ago( 5 ) ) )
		await db_session.commit( )

		deleted, skipped = await retention_service.delete_expired_logs_for_all_users( db_session )

		assert deleted == 1
		assert skipped == 0

	async def test_skips_user_with_no_confirmed_warning_and_leaves_logs_intact(
		self, db_session, user, api_key
	):
		"""The core safety property: never delete without a real, confirmed
		chance to export first. This is what makes warn/delete two separate
		steps meaningful rather than decorative."""
		entry_row = await _make_log_entry_row( db_session, user, api_key, captured_at=_days_ago( 40 ) )
		# no DataExport row at all for this user

		deleted, skipped = await retention_service.delete_expired_logs_for_all_users( db_session )

		assert deleted == 0
		assert skipped == 1
		assert await db_session.get( LogEntry, entry_row.id ) is not None

	async def test_skips_user_whose_warning_failed( self, db_session, user, api_key ):
		entry_row = await _make_log_entry_row( db_session, user, api_key, captured_at=_days_ago( 40 ) )
		db_session.add( _build_data_export_row( user, status="FAILED", created_at=_days_ago( 5 ) ) )
		await db_session.commit( )

		deleted, skipped = await retention_service.delete_expired_logs_for_all_users( db_session )

		assert deleted == 0
		assert skipped == 1
		assert await db_session.get( LogEntry, entry_row.id ) is not None


# ---------------------------------------------------------------------------
# retention/job.py — locking and RETENTION_ENABLED gating
# ---------------------------------------------------------------------------

class TestRetentionJobRun:
	@pytest.fixture( autouse=True )
	def _patch_common( self, monkeypatch, db_session ):
		monkeypatch.setattr( retention_job, "configure_logging", lambda: None )
		monkeypatch.setattr( retention_job, "verify_export_storage", lambda: None )
		monkeypatch.setattr( retention_job, "AsyncSessionLocal", lambda: _AsyncSessionCtx( db_session ) )

	async def test_warn_mode_skipped_when_retention_disabled( self, monkeypatch ):
		monkeypatch.setattr( retention_job.settings, "retention_enabled", False )
		warn_mock = AsyncMock( )
		monkeypatch.setattr( retention_job, "send_retention_warnings", warn_mock )

		await retention_job.run( "warn" )

		warn_mock.assert_not_called( )

	async def test_delete_mode_skipped_when_retention_disabled( self, monkeypatch ):
		monkeypatch.setattr( retention_job.settings, "retention_enabled", False )
		delete_mock = AsyncMock( )
		monkeypatch.setattr( retention_job, "delete_expired_logs_for_all_users", delete_mock )

		await retention_job.run( "delete" )

		delete_mock.assert_not_called( )

	async def test_purge_exports_runs_even_when_retention_disabled(
		self, monkeypatch, redis_client: Redis
	):
		"""The specific behavior this test exists for: export file cleanup
		must NOT be tied to the log-retention feature flag, since on-demand
		exports exist independently of automatic log deletion."""
		monkeypatch.setattr( retention_job.settings, "retention_enabled", False )
		monkeypatch.setattr( retention_job, "new_redis_client", lambda: redis_client )
		purge_mock = AsyncMock( return_value=3 )
		monkeypatch.setattr( retention_job, "purge_expired_exports", purge_mock )

		await retention_job.run( "purge-exports" )

		purge_mock.assert_called_once( )

	async def test_lock_not_acquired_skips_all_work( self, monkeypatch, redis_client: Redis ):
		monkeypatch.setattr( retention_job.settings, "retention_enabled", True )
		monkeypatch.setattr( retention_job, "new_redis_client", lambda: redis_client )
		warn_mock = AsyncMock( )
		monkeypatch.setattr( retention_job, "send_retention_warnings", warn_mock )

		# Pre-acquire the lock ourselves, using the SAME real Redis the job
		# will check against — a genuine test of the SETNX-with-TTL
		# behavior rather than mocking the lock away entirely.
		await redis_client.set( "retention_lock:warn", "1", nx=True, ex=3600 )

		await retention_job.run( "warn" )

		warn_mock.assert_not_called( )

	async def test_lock_acquired_runs_warn_and_sets_ttl( self, monkeypatch, redis_client: Redis ):
		monkeypatch.setattr( retention_job.settings, "retention_enabled", True )
		monkeypatch.setattr( retention_job.settings, "retention_job_lock_ttl_seconds", 3600 )
		monkeypatch.setattr( retention_job, "new_redis_client", lambda: redis_client )
		warn_mock = AsyncMock( return_value=2 )
		monkeypatch.setattr( retention_job, "send_retention_warnings", warn_mock )

		await retention_job.run( "warn" )

		warn_mock.assert_called_once( )
		ttl = await redis_client.ttl( "retention_lock:warn" )
		assert 0 < ttl <= 3600