from __future__ import annotations

import asyncio
import json
from uuid import uuid4

import fakeredis.aioredis
import pytest
import websocket.pubsub as pubsub_module
from websocket.manager import ConnectionManager
from websocket.pubsub import (
    _extract_user_id,
    _listen_forever,
    publish_log_entries,
)


class FakeWebSocket:
    def __init__( self ) -> None:
        self.sent: list[ str ] = []

    async def send_text( self, message: str ) -> None:
        self.sent.append( message )


def _full_row( **overrides ) -> dict:
    row = {
        "src_ip":            "1.2.3.4",
        "dst_ip":             "5.6.7.8",
        "src_port":           1234,
        "dst_port":           443,
        "protocol":           "TCP",
        "packet_size_bytes":  512,
        "flags":              None,
        "src_country_code":   "US",
        "dst_country_code":   None,
        "src_geo_status":     "RESOLVED",
        "dst_geo_status":     "PRIVATE",
        "anomaly_score":      0.9,
        "anomaly_reasons":    [],
        "captured_at":        "2026-07-29T18:52:50Z",
    }
    row.update( overrides )
    return row


class TestExtractUserId:
    def test_extracts_from_well_formed_channel( self ):
        assert _extract_user_id( "ws:user:abc-123:live" ) == "abc-123"

    def test_returns_none_for_unrelated_channel( self ):
        assert _extract_user_id( "some:other:channel" ) is None

    def test_returns_none_for_missing_suffix( self ):
        assert _extract_user_id( "ws:user:abc-123" ) is None

    def test_returns_none_for_missing_prefix( self ):
        assert _extract_user_id( "user:abc-123:live" ) is None

    def test_handles_a_user_id_containing_colons( self ):
        assert _extract_user_id( "ws:user:abc:def:live" ) == "abc:def"


class TestPublishLogEntries:
    @pytest.mark.anyio
    async def test_publish_reaches_a_subscriber( self ):
        redis = fakeredis.aioredis.FakeRedis()
        sub = redis.pubsub()
        await sub.psubscribe( "ws:user:*:live" )

        rows = [ _full_row() ]
        await publish_log_entries( redis, "user-1", rows )

        msg = None
        for _ in range( 5 ):
            candidate = await sub.get_message( timeout=1 )
            if candidate and candidate[ "type" ] == "pmessage":
                msg = candidate
                break

        assert msg is not None
        payload = json.loads( msg[ "data" ] )
        assert payload[ "type" ] == "log_entry_batch"
        assert payload[ "data" ] == rows

        await sub.punsubscribe( "ws:user:*:live" )
        await sub.aclose()
        await redis.aclose()

    @pytest.mark.anyio
    async def test_publish_is_scoped_to_the_right_user_channel( self ):
        redis = fakeredis.aioredis.FakeRedis()
        sub = redis.pubsub()
        await sub.subscribe( "ws:user:user-2:live" )

        await publish_log_entries( redis, "user-1", [ _full_row() ] )
        # give fakeredis a moment to deliver, if it were going to
        await asyncio.sleep( 0.1 )
        msg = await sub.get_message( timeout=0.2 )

        assert msg is None or msg[ "type" ] != "message"

        await sub.unsubscribe( "ws:user:user-2:live" )
        await sub.aclose()
        await redis.aclose()

    @pytest.mark.anyio
    async def test_publish_serializes_uuid_fields( self ):
        from datetime import datetime, timezone

        from websocket.pubsub import _json_default

        u = uuid4()
        assert _json_default( u ) == str( u )

        dt = datetime( 2026, 7, 29, 18, 52, 50, tzinfo=timezone.utc )
        assert _json_default( dt ) == dt.isoformat()

        class Unhandled:
            pass

        with pytest.raises( TypeError ):
            _json_default( Unhandled() )

    @pytest.mark.anyio
    async def test_publish_strips_internal_and_redundant_fields( self ):
        redis = fakeredis.aioredis.FakeRedis()
        sub = redis.pubsub()
        await sub.psubscribe( "ws:user:*:live" )

        row = {
            "api_key_id":       uuid4(),
            "user_id":          uuid4(),
            "raw_payload":      { "synthetic": True },
            "src_ip":           "10.0.0.5",
            "dst_ip":           "8.8.8.8",
            "src_port":         1234,
            "dst_port":         443,
            "protocol":         "TCP",
            "packet_size_bytes": 512,
            "flags":            None,
            "src_country_code":   "US",
            "dst_country_code":   None,
            "src_geo_status":     "RESOLVED",
            "dst_geo_status":     "PRIVATE",
            "anomaly_score":    0.1,
            "anomaly_reasons":  [],
            "captured_at":      "2026-07-29T18:52:50Z",
        }
        await publish_log_entries( redis, "user-1", [ row ] )

        msg = None
        for _ in range( 5 ):
            candidate = await sub.get_message( timeout=1 )
            if candidate and candidate[ "type" ] == "pmessage":
                msg = candidate
                break

        published_row = json.loads( msg[ "data" ] )[ "data" ][ 0 ]
        assert "api_key_id" not in published_row
        assert "user_id" not in published_row
        assert "raw_payload" not in published_row
        assert published_row[ "src_ip" ] == "10.0.0.5"
        assert published_row[ "anomaly_score" ] == 0.1

        await sub.punsubscribe( "ws:user:*:live" )
        await sub.aclose()
        await redis.aclose()

    @pytest.mark.anyio
    async def test_publish_fails_loudly_on_a_genuinely_incomplete_row( self ):
        redis = fakeredis.aioredis.FakeRedis()
        incomplete_row = { "src_ip": "10.0.0.5" }

        with pytest.raises( KeyError ):
            await publish_log_entries( redis, "user-1", [ incomplete_row ] )

        await redis.aclose()


class TestListenForever:
    @pytest.mark.anyio
    async def test_delivers_published_messages_to_the_connection_manager( self, monkeypatch ):
        redis = fakeredis.aioredis.FakeRedis()
        test_manager = ConnectionManager()
        monkeypatch.setattr( pubsub_module, "manager", test_manager )

        ws = FakeWebSocket()
        await test_manager.connect( "user-1", ws )

        task = asyncio.create_task( _listen_forever( lambda: redis ) )
        await asyncio.sleep( 0.2 ) 

        rows = [ _full_row() ]
        await publish_log_entries( redis, "user-1", rows )
        await asyncio.sleep( 0.2 )

        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        await redis.aclose()

        assert len( ws.sent ) == 1
        payload = json.loads( ws.sent[ 0 ] )
        assert payload[ "data" ] == rows

    @pytest.mark.anyio
    async def test_message_for_unconnected_user_is_dropped_silently( self, monkeypatch ):
        redis = fakeredis.aioredis.FakeRedis()
        test_manager = ConnectionManager()
        monkeypatch.setattr( pubsub_module, "manager", test_manager )

        task = asyncio.create_task( _listen_forever( lambda: redis ) )
        await asyncio.sleep( 0.2 )

        await publish_log_entries( redis, "user-nobody", [ _full_row() ] )
        await asyncio.sleep( 0.2 )

        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        await redis.aclose()

    @pytest.mark.anyio
    async def test_reconnects_after_the_listener_raises( self ):
        attempts = 0

        class ExplodingPubSub:
            async def psubscribe( self, pattern ):
                pass

            async def punsubscribe( self, pattern ):
                pass

            async def aclose( self ):
                pass

            async def listen( self ):
                nonlocal attempts
                attempts += 1
                if attempts == 1:
                    raise ConnectionError( "simulated dropped connection" )
                while True:
                    await asyncio.sleep( 3600 )
                    yield 

        class ExplodingRedis:
            def pubsub( self ):
                return ExplodingPubSub()

            async def aclose( self ):
                pass

        original_delay = pubsub_module._RECONNECT_DELAY_SECONDS
        pubsub_module._RECONNECT_DELAY_SECONDS = 0.05

        task = asyncio.create_task( _listen_forever( lambda: ExplodingRedis() ) )
        await asyncio.sleep( 0.3 )

        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

        pubsub_module._RECONNECT_DELAY_SECONDS = original_delay

        assert attempts >= 2