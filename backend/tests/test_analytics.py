from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from analytics.dependencies import get_time_range, get_timeseries_params
from analytics.schemas import TimeBucketEnum, TimeRangeRequestParams
from fastapi import HTTPException
from httpx import AsyncClient
from models.models import APIKey, User
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from tests.factories import make_log_entries, make_log_entry

NOW = datetime( 2026, 8, 5, 12, 0, 0, tzinfo=timezone.utc )

class TestGetTimeRange:
	"""
	Tests for validation logic of TimeRange query params
	"""

	@pytest.mark.anyio
	async def test_defaults_to_last_24_hours( self ):
		result = await get_time_range( start=None, end=None )
		assert result.end - result.start == timedelta( hours=24 )

	@pytest.mark.anyio
	async def test_rejects_start_after_end( self ):
		start = NOW
		end   = NOW - timedelta( hours=1 )
		with pytest.raises( HTTPException ) as exc_info:
			await get_time_range( start=start, end=end )
		assert exc_info.value.status_code == 422

	@pytest.mark.anyio
	async def test_rejects_naive_datetime( self ):
		naive_start = datetime( 2026, 8, 1, 0, 0, 0 )  # noqa: DTZ001
		with pytest.raises( HTTPException ) as exc_info:
			await get_time_range( start=naive_start, end=NOW )
		assert exc_info.value.status_code == 422

	@pytest.mark.anyio
	async def test_rejects_range_exceeding_max( self ):
		start = NOW - timedelta( days=90 )
		with pytest.raises( HTTPException ) as exc_info:
			await get_time_range( start=start, end=NOW )
		assert exc_info.value.status_code == 422

	@pytest.mark.anyio
	async def test_rejects_future_end( self ):
		future_end = datetime.now( timezone.utc ) + timedelta( hours=1 )
		with pytest.raises( HTTPException ) as exc_info:
			await get_time_range( start=None, end=future_end )
		assert exc_info.value.status_code == 422

	@pytest.mark.anyio
	async def test_accepts_range_at_max_boundary( self ):
		start = datetime.now( timezone.utc ) - timedelta( days=30 ) + timedelta( minutes=1 )
		result = await get_time_range( start=start, end=None )
		assert result.start == start


class TestGetTimeseriesParams:
	"""
	Tests for the TimeSeries query params, only tests things specific to this param rather than testing start + end again.
	"""
	@pytest.mark.anyio
	async def test_auto_bucket_short_range_is_minute( self ):
		time_range = TimeRangeRequestParams(
			start = NOW - timedelta( hours=1 ),
			end   = NOW
		)
		result = await get_timeseries_params( time_range=time_range, bucket=None )
		assert result.bucket == TimeBucketEnum.minute

	@pytest.mark.anyio
	async def test_auto_bucket_week_range_is_hour( self ):
		time_range = TimeRangeRequestParams(
			start = NOW - timedelta( days=3 ),
			end   = NOW
		)
		result = await get_timeseries_params( time_range=time_range, bucket=None )
		assert result.bucket == TimeBucketEnum.hour

	@pytest.mark.anyio
	async def test_auto_bucket_long_range_is_day( self ):
		time_range = TimeRangeRequestParams(
			start = NOW - timedelta( days=20 ),
			end   = NOW
		)
		result = await get_timeseries_params( time_range=time_range, bucket=None )
		assert result.bucket == TimeBucketEnum.day

	@pytest.mark.anyio
	async def test_rejects_minute_bucket_over_long_range( self ):
		time_range = TimeRangeRequestParams(
			start = NOW - timedelta( days=20 ),
			end   = NOW
		)
		with pytest.raises( HTTPException ) as exc_info:
			await get_timeseries_params( time_range=time_range, bucket=TimeBucketEnum.minute )
		assert exc_info.value.status_code == 422


class TestSummary:
	"""
	Summary endpoint tests.
	"""

	@pytest.mark.anyio
	async def test_empty_range_returns_zeroed_response(
		self,
		client:       AsyncClient,
		auth_headers: dict[ str, str ]
	):
		response = await client.get(
			"/analytics/summary",
			params  = { "start": ( NOW - timedelta( hours=1 ) ).isoformat( ), "end": NOW.isoformat( ) },
			headers = auth_headers
		)
		assert response.status_code         == 200
		body = response.json( )
		assert body[ "total_packets" ]      == 0
		assert body[ "avg_anomaly_score" ]  == 0.0
		assert body[ "total_bytes" ]        == 0

	@pytest.mark.anyio
	async def test_counts_match_inserted_entries(
		self,
		client:       AsyncClient,
		db_session:   AsyncSession,
		auth_headers: dict[ str, str ],
		user:         User,
		api_key:      APIKey
	):
		await make_log_entries(
			db_session, count=5, user_id=user.id, api_key_id=api_key.id,
			captured_at=NOW - timedelta( minutes=30 ), packet_size_bytes=100
		)
		await db_session.commit( )

		response = await client.get(
			"/analytics/summary",
			params  = { "start": ( NOW - timedelta( hours=1 ) ).isoformat( ), "end": NOW.isoformat( ) },
			headers = auth_headers
		)
		body = response.json( )
		assert body[ "total_packets" ] == 5
		assert body[ "total_bytes" ]   == 500

	@pytest.mark.anyio
	async def test_unique_ip_counts_deduplicate(
		self,
		client:       AsyncClient,
		db_session:   AsyncSession,
		auth_headers: dict[ str, str ],
		user:         User,
		api_key:      APIKey
	):
		await make_log_entry(
			db_session, user_id=user.id, api_key_id=api_key.id,
			src_ip="10.0.0.1", dst_ip="10.0.0.100", captured_at=NOW - timedelta( minutes=10 )
		)
		await make_log_entry(
			db_session, user_id=user.id, api_key_id=api_key.id,
			src_ip="10.0.0.1", dst_ip="10.0.0.101", captured_at=NOW - timedelta( minutes=5 )
		)
		await db_session.commit( )

		response = await client.get(
			"/analytics/summary",
			params  = { "start": ( NOW - timedelta( hours=1 ) ).isoformat( ), "end": NOW.isoformat( ) },
			headers = auth_headers
		)
		body = response.json( )
		assert body[ "unique_src_ips" ] == 1
		assert body[ "unique_dst_ips" ] == 2

	@pytest.mark.anyio
	async def test_excludes_entries_outside_range(
		self,
		client:       AsyncClient,
		db_session:   AsyncSession,
		auth_headers: dict[ str, str ],
		user:         User,
		api_key:      APIKey
	):
		await make_log_entry(
			db_session, user_id=user.id, api_key_id=api_key.id,
			captured_at=NOW - timedelta( days=2 )   # outside the queried window
		)
		await db_session.commit( )

		response = await client.get(
			"/analytics/summary",
			params  = { "start": ( NOW - timedelta( hours=1 ) ).isoformat( ), "end": NOW.isoformat( ) },
			headers = auth_headers
		)
		assert response.json( )[ "total_packets" ] == 0

	@pytest.mark.anyio
	async def test_excludes_other_users_entries(
		self,
		client:       AsyncClient,
		db_session:   AsyncSession,
		auth_headers: dict[ str, str ],
		other_user:   User,
		api_key:      APIKey
	):
		await make_log_entry(
			db_session, user_id=other_user.id, api_key_id=api_key.id,
			captured_at=NOW - timedelta( minutes=10 )
		)
		await db_session.commit( )

		response = await client.get(
			"/analytics/summary",
			params  = { "start": ( NOW - timedelta( hours=1 ) ).isoformat( ), "end": NOW.isoformat( ) },
			headers = auth_headers
		)
		assert response.json( )[ "total_packets" ] == 0

	@pytest.mark.anyio
	async def test_repeated_call_hits_cache(
		self,
		client:       AsyncClient,
		db_session:   AsyncSession,
		redis_client: Redis,
		auth_headers: dict[ str, str ],
		user:         User,
		api_key:      APIKey
	):
		params = { "start": ( NOW - timedelta( hours=1 ) ).isoformat( ), "end": NOW.isoformat( ) }

		first = await client.get( "/analytics/summary", params=params, headers=auth_headers )
		assert first.status_code == 200

		cached_keys = [ key async for key in redis_client.scan_iter( f"analytics:{ user.id }:summary:*" ) ]
		assert len( cached_keys ) == 1

		# Insert a new entry after the first (now cached) call — a cache hit
		# should NOT pick this up.
		await make_log_entry( db_session, user_id=user.id, api_key_id=api_key.id, captured_at=NOW - timedelta( minutes=1 ) )
		await db_session.commit( )

		second = await client.get( "/analytics/summary", params=params, headers=auth_headers )
		assert second.json( )[ "total_packets" ] == first.json( )[ "total_packets" ]

	@pytest.mark.anyio
	async def test_different_params_do_not_share_cache(
		self,
		client:       AsyncClient,
		redis_client: Redis,
		auth_headers: dict[ str, str ],
	):
		params_a = { "start": ( NOW - timedelta( hours=1 ) ).isoformat( ), "end": NOW.isoformat( ) }
		params_b = { "start": ( NOW - timedelta( hours=2 ) ).isoformat( ), "end": NOW.isoformat( ) }

		response_a = await client.get( "/analytics/summary", params=params_a, headers=auth_headers )
		response_b = await client.get( "/analytics/summary", params=params_b, headers=auth_headers )

		assert response_a.json( )[ "start" ] != response_b.json( )[ "start" ]


class TestTimeseries:
	"""
	Timeseries endpoint tests.
	"""

	@pytest.mark.anyio
	async def test_entries_bucket_by_hour(
		self,
		client:       AsyncClient,
		db_session:   AsyncSession,
		auth_headers: dict[ str, str ],
		user:         User,
		api_key:      APIKey
	):
		base = NOW.replace( minute=0, second=0, microsecond=0 )
		await make_log_entry( db_session, user_id=user.id, api_key_id=api_key.id, captured_at=base - timedelta( minutes=10 ) )
		await make_log_entry( db_session, user_id=user.id, api_key_id=api_key.id, captured_at=base - timedelta( minutes=5 ) )
		await make_log_entry( db_session, user_id=user.id, api_key_id=api_key.id, captured_at=base - timedelta( hours=1, minutes=5 ) )
		await db_session.commit( )

		response = await client.get(
			"/analytics/timeseries",
			params  = {
				"start":  ( base - timedelta( hours=2 ) ).isoformat( ),
				"end":    ( base + timedelta( minutes=1 ) ).isoformat( ),
				"bucket": "hour"
			},
			headers = auth_headers
		)
		points = { point[ "ts" ]: point[ "count" ] for point in response.json( )[ "points" ] }
		assert len( points ) == 2
		assert sum( points.values( ) ) == 3

	@pytest.mark.anyio
	async def test_points_ordered_ascending(
		self,
		client:       AsyncClient,
		db_session:   AsyncSession,
		auth_headers: dict[ str, str ],
		user:         User,
		api_key:      APIKey
	):
		base = NOW.replace( minute=0, second=0, microsecond=0 )
		for offset_hours in [ 3, 1, 2 ]:
			await make_log_entry(
				db_session, user_id=user.id, api_key_id=api_key.id,
				captured_at=base - timedelta( hours=offset_hours )
			)
		await db_session.commit( )

		response = await client.get(
			"/analytics/timeseries",
			params  = {
				"start":  ( base - timedelta( hours=4 ) ).isoformat( ),
				"end":    ( base + timedelta( minutes=1 ) ).isoformat( ),
				"bucket": "hour"
			},
			headers = auth_headers
		)
		timestamps = [ point[ "ts" ] for point in response.json( )[ "points" ] ]
		assert timestamps == sorted( timestamps )

	@pytest.mark.anyio
	async def test_empty_buckets_are_absent_not_zero(
		self,
		client:       AsyncClient,
		auth_headers: dict[ str, str ]
	):
		response = await client.get(
			"/analytics/timeseries",
			params  = {
				"start":  ( NOW - timedelta( hours=3 ) ).isoformat( ),
				"end":    NOW.isoformat( ),
				"bucket": "hour"
			},
			headers = auth_headers
		)
		assert response.json( )[ "points" ] == []

class TestTopTalkers:
	"""
	Toptalkers endpoint tests.
	"""

	@pytest.mark.anyio
	async def test_direction_src_groups_by_source_ip(
		self,
		client:       AsyncClient,
		db_session:   AsyncSession,
		auth_headers: dict[ str, str ],
		user:         User,
		api_key:      APIKey
	):
		await make_log_entries(
			db_session, count=3, user_id=user.id, api_key_id=api_key.id,
			src_ip="10.0.0.1", captured_at=NOW - timedelta( minutes=5 )
		)
		await make_log_entry(
			db_session, user_id=user.id, api_key_id=api_key.id,
			src_ip="10.0.0.2", captured_at=NOW - timedelta( minutes=5 )
		)
		await db_session.commit( )

		response = await client.get(
			"/analytics/top-talkers",
			params  = {
				"start": ( NOW - timedelta( hours=1 ) ).isoformat( ), "end": NOW.isoformat( ),
				"direction": "src", "metric": "packets"
			},
			headers = auth_headers
		)
		rows = response.json( )[ "rows" ]
		assert rows[ 0 ][ "ip" ] == "10.0.0.1"
		assert rows[ 0 ][ "count" ] == 3

	@pytest.mark.anyio
	async def test_metric_bytes_reorders_relative_to_packets(
		self,
		client:       AsyncClient,
		db_session:   AsyncSession,
		auth_headers: dict[ str, str ],
		user:         User,
		api_key:      APIKey
	):
		# .1 has more packets, .2 has fewer but much larger packets — ranking
		# should flip depending on `metric`.
		await make_log_entries(
			db_session, count=5, user_id=user.id, api_key_id=api_key.id,
			src_ip="10.0.0.1", packet_size_bytes=10, captured_at=NOW - timedelta( minutes=5 )
		)
		await make_log_entry(
			db_session, user_id=user.id, api_key_id=api_key.id,
			src_ip="10.0.0.2", packet_size_bytes=10_000, captured_at=NOW - timedelta( minutes=5 )
		)
		await db_session.commit( )

		params = { "start": ( NOW - timedelta( hours=1 ) ).isoformat( ), "end": NOW.isoformat( ), "direction": "src" }

		by_packets = await client.get( "/analytics/top-talkers", params={ **params, "metric": "packets" }, headers=auth_headers )
		by_bytes   = await client.get( "/analytics/top-talkers", params={ **params, "metric": "bytes" }, headers=auth_headers )

		assert by_packets.json( )[ "rows" ][ 0 ][ "ip" ] == "10.0.0.1"
		assert by_bytes.json( )[ "rows" ][ 0 ][ "ip" ]   == "10.0.0.2"

	@pytest.mark.anyio
	async def test_limit_truncates_results(
		self,
		client:       AsyncClient,
		db_session:   AsyncSession,
		auth_headers: dict[ str, str ],
		user:         User,
		api_key:      APIKey
	):
		for i in range( 5 ):
			await make_log_entry(
				db_session, user_id=user.id, api_key_id=api_key.id,
				src_ip=f"10.0.0.{ i }", captured_at=NOW - timedelta( minutes=5 )
			)
		await db_session.commit( )

		response = await client.get(
			"/analytics/top-talkers",
			params  = {
				"start": ( NOW - timedelta( hours=1 ) ).isoformat( ), "end": NOW.isoformat( ),
				"direction": "src", "metric": "packets", "limit": 2
			},
			headers = auth_headers
		)
		assert len( response.json( )[ "rows" ] ) == 2


class TestProtocols:
	"""
	Protocol endpoint tests.
	"""

	@pytest.mark.anyio
	async def test_percentages_sum_to_100(
		self,
		client:       AsyncClient,
		db_session:   AsyncSession,
		auth_headers: dict[ str, str ],
		user:         User,
		api_key:      APIKey
	):
		await make_log_entries( db_session, count=3, user_id=user.id, api_key_id=api_key.id, protocol="TCP", captured_at=NOW - timedelta( minutes=5 ) )
		await make_log_entries( db_session, count=1, user_id=user.id, api_key_id=api_key.id, protocol="UDP", captured_at=NOW - timedelta( minutes=5 ) )
		await db_session.commit( )

		response = await client.get(
			"/analytics/protocols",
			params  = { "start": ( NOW - timedelta( hours=1 ) ).isoformat( ), "end": NOW.isoformat( ) },
			headers = auth_headers
		)
		total_pct = sum( row[ "packet_percentage" ] for row in response.json( )[ "by_protocol" ] )
		assert abs( total_pct - 100.0 ) < 0.5   # rounding tolerance

	@pytest.mark.anyio
	async def test_no_entries_returns_empty_not_error(
		self,
		client:       AsyncClient,
		auth_headers: dict[ str, str ]
	):
		response = await client.get(
			"/analytics/protocols",
			params  = { "start": ( NOW - timedelta( hours=1 ) ).isoformat( ), "end": NOW.isoformat( ) },
			headers = auth_headers
		)
		assert response.status_code == 200
		assert response.json( )[ "by_protocol" ] == []

	@pytest.mark.anyio
	async def test_protocol_serializes_as_plain_string(
		self,
		client:       AsyncClient,
		db_session:   AsyncSession,
		auth_headers: dict[ str, str ],
		user:         User,
		api_key:      APIKey
	):
		await make_log_entry( db_session, user_id=user.id, api_key_id=api_key.id, protocol="TCP", captured_at=NOW - timedelta( minutes=5 ) )
		await db_session.commit( )

		response = await client.get(
			"/analytics/protocols",
			params  = { "start": ( NOW - timedelta( hours=1 ) ).isoformat( ), "end": NOW.isoformat( ) },
			headers = auth_headers
		)
		assert response.json( )[ "by_protocol" ][ 0 ][ "protocol" ] == "TCP"

	@pytest.mark.anyio
	async def test_top_dst_ports_ordered_descending(
		self,
		client:       AsyncClient,
		db_session:   AsyncSession,
		auth_headers: dict[ str, str ],
		user:         User,
		api_key:      APIKey
	):
		await make_log_entries( db_session, count=1, user_id=user.id, api_key_id=api_key.id, dst_port=22, captured_at=NOW - timedelta( minutes=5 ) )
		await make_log_entries( db_session, count=4, user_id=user.id, api_key_id=api_key.id, dst_port=443, captured_at=NOW - timedelta( minutes=5 ) )
		await db_session.commit( )

		response = await client.get(
			"/analytics/protocols",
			params  = { "start": ( NOW - timedelta( hours=1 ) ).isoformat( ), "end": NOW.isoformat( ) },
			headers = auth_headers
		)
		top_ports = response.json( )[ "top_dst_ports" ]
		assert top_ports[ 0 ][ "port" ] == 443
		assert top_ports[ 0 ][ "count" ] == 4


class TestGeo:
	"""
	Geo endpoint tests.
	"""

	@pytest.mark.anyio
	async def test_null_country_code_included_in_percentages(
		self,
		client:       AsyncClient,
		db_session:   AsyncSession,
		auth_headers: dict[ str, str ],
		user:         User,
		api_key:      APIKey
	):
		await make_log_entry( db_session, user_id=user.id, api_key_id=api_key.id, dst_country_code="US", captured_at=NOW - timedelta( minutes=5 ) )
		await make_log_entry( db_session, user_id=user.id, api_key_id=api_key.id, dst_country_code=None, captured_at=NOW - timedelta( minutes=5 ) )
		await db_session.commit( )

		response = await client.get(
			"/analytics/geo",
			params  = { "start": ( NOW - timedelta( hours=1 ) ).isoformat( ), "end": NOW.isoformat( ), "direction": "dst" },
			headers = auth_headers
		)
		rows = response.json( )[ "rows" ]
		null_row = next( row for row in rows if row[ "country_code" ] is None )
		assert null_row[ "count" ] == 1
		assert abs( sum( row[ "packet_percentage" ] for row in rows ) - 100.0 ) < 0.5

	@pytest.mark.anyio
	async def test_no_entries_returns_empty_not_error(
		self,
		client:       AsyncClient,
		auth_headers: dict[ str, str ]
	):
		response = await client.get(
			"/analytics/geo",
			params  = { "start": ( NOW - timedelta( hours=1 ) ).isoformat( ), "end": NOW.isoformat( ) },
			headers = auth_headers
		)
		assert response.status_code == 200
		assert response.json( )[ "rows" ] == []


class TestAnomalies:
	"""
	Anomalies endpoint tests.
	"""

	@pytest.mark.anyio
	async def test_filters_by_min_score(
		self,
		client:       AsyncClient,
		db_session:   AsyncSession,
		auth_headers: dict[ str, str ],
		user:         User,
		api_key:      APIKey
	):
		await make_log_entry( db_session, user_id=user.id, api_key_id=api_key.id, anomaly_score=0.2, captured_at=NOW - timedelta( minutes=5 ) )
		await make_log_entry( db_session, user_id=user.id, api_key_id=api_key.id, anomaly_score=0.9, captured_at=NOW - timedelta( minutes=4 ) )
		await db_session.commit( )

		response = await client.get(
			"/analytics/anomalies",
			params  = { "start": ( NOW - timedelta( hours=1 ) ).isoformat( ), "end": NOW.isoformat( ), "min_score": 0.5 },
			headers = auth_headers
		)
		rows = response.json( )[ "rows" ]
		assert len( rows ) == 1
		assert rows[ 0 ][ "anomaly_score" ] == 0.9

	@pytest.mark.anyio
	async def test_pagination_returns_distinct_pages(
		self,
		client:       AsyncClient,
		db_session:   AsyncSession,
		auth_headers: dict[ str, str ],
		user:         User,
		api_key:      APIKey
	):
		for i in range( 5 ):
			await make_log_entry(
				db_session, user_id=user.id, api_key_id=api_key.id,
				anomaly_score=0.9, captured_at=NOW - timedelta( minutes=i )
			)
		await db_session.commit( )

		first_page = await client.get(
			"/analytics/anomalies",
			params  = { "start": ( NOW - timedelta( hours=1 ) ).isoformat( ), "end": NOW.isoformat( ), "limit": 2 },
			headers = auth_headers
		)
		first_body = first_page.json( )
		assert len( first_body[ "rows" ] ) == 2
		assert first_body[ "has_more" ] is True
		assert first_body[ "next_cursor" ] is not None

		second_page = await client.get(
			"/analytics/anomalies",
			params  = {
				"start": ( NOW - timedelta( hours=1 ) ).isoformat( ), "end": NOW.isoformat( ),
				"limit": 2, "cursor": first_body[ "next_cursor" ]
			},
			headers = auth_headers
		)
		second_body = second_page.json( )

		first_ids  = { row[ "id" ] for row in first_body[ "rows" ] }
		second_ids = { row[ "id" ] for row in second_body[ "rows" ] }
		assert first_ids.isdisjoint( second_ids )

	@pytest.mark.anyio
	async def test_last_page_has_no_next_cursor(
		self,
		client:       AsyncClient,
		db_session:   AsyncSession,
		auth_headers: dict[ str, str ],
		user:         User,
		api_key:      APIKey
	):
		await make_log_entry( db_session, user_id=user.id, api_key_id=api_key.id, anomaly_score=0.9, captured_at=NOW - timedelta( minutes=1 ) )
		await db_session.commit( )

		response = await client.get(
			"/analytics/anomalies",
			params  = { "start": ( NOW - timedelta( hours=1 ) ).isoformat( ), "end": NOW.isoformat( ), "limit": 25 },
			headers = auth_headers
		)
		body = response.json( )
		assert body[ "has_more" ] is False
		assert body[ "next_cursor" ] is None

	@pytest.mark.anyio
	async def test_ties_on_captured_at_break_by_id(
		self,
		client:       AsyncClient,
		db_session:   AsyncSession,
		auth_headers: dict[ str, str ],
		user:         User,
		api_key:      APIKey
	):
		shared_ts = NOW - timedelta( minutes=1 )
		first  = await make_log_entry( db_session, user_id=user.id, api_key_id=api_key.id, anomaly_score=0.9, captured_at=shared_ts )
		second = await make_log_entry( db_session, user_id=user.id, api_key_id=api_key.id, anomaly_score=0.9, captured_at=shared_ts )
		await db_session.commit( )

		response = await client.get(
			"/analytics/anomalies",
			params  = { "start": ( NOW - timedelta( hours=1 ) ).isoformat( ), "end": NOW.isoformat( ), "limit": 25 },
			headers = auth_headers
		)
		ids = [ row[ "id" ] for row in response.json( )[ "rows" ] ]
		# Both entries share captured_at — id DESC must still give a stable order
		assert ids.index( max( first.id, second.id ) ) < ids.index( min( first.id, second.id ) )

	@pytest.mark.anyio
	async def test_malformed_cursor_returns_clean_error(
		self,
		client:       AsyncClient,
		auth_headers: dict[ str, str ]
	):
		response = await client.get(
			"/analytics/anomalies",
			params  = {
				"start": ( NOW - timedelta( hours=1 ) ).isoformat( ), "end": NOW.isoformat( ),
				"cursor": "not-a-valid-cursor"
			},
			headers = auth_headers
		)
		assert response.status_code in ( 400, 422 )

	@pytest.mark.anyio
	async def test_response_excludes_internal_fields(
		self,
		client:       AsyncClient,
		db_session:   AsyncSession,
		auth_headers: dict[ str, str ],
		user:         User,
		api_key:      APIKey
	):
		await make_log_entry( db_session, user_id=user.id, api_key_id=api_key.id, anomaly_score=0.9, captured_at=NOW - timedelta( minutes=1 ) )
		await db_session.commit( )

		response = await client.get(
			"/analytics/anomalies",
			params  = { "start": ( NOW - timedelta( hours=1 ) ).isoformat( ), "end": NOW.isoformat( ) },
			headers = auth_headers
		)
		row = response.json( )[ "rows" ][ 0 ]
		assert "raw_payload" not in row
		assert "api_key_id" not in row


# Auth testing across all endpoints.

ANALYTICS_PATHS = [
	"/analytics/summary",
	"/analytics/timeseries",
	"/analytics/top-talkers",
	"/analytics/protocols",
	"/analytics/geo",
	"/analytics/anomalies",
]


@pytest.mark.parametrize( "path", ANALYTICS_PATHS )
@pytest.mark.anyio
async def test_requires_auth(
	client: AsyncClient,
	path:   str
):
	response = await client.get( path )
	assert response.status_code == 401


@pytest.mark.parametrize( "path", ANALYTICS_PATHS )
@pytest.mark.anyio
async def test_rejects_naive_datetime(
	client:       AsyncClient,
	auth_headers: dict[ str, str ],
	path:         str
):
	response = await client.get(
		path, params={ "start": "2026-08-01T00:00:00" }, headers=auth_headers
	)
	assert response.status_code == 422