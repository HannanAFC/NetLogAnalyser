from __future__ import annotations

import time

import fakeredis.aioredis
import pytest
from websocket.service import (
    _conn_key,
    authenticate_ws_ticket,
    create_connection_slot,
    mint_ws_ticket,
    refresh_connection_slot,
    release_connection_slot,
)


@pytest.fixture( scope="function" )
async def redis( ):
    client = fakeredis.aioredis.FakeRedis( )
    yield client
    await client.aclose( )

class TestTicket:
    @pytest.mark.anyio
    async def test_mint_then_consume_resolves_user_id( self, redis ):
        ticket = await mint_ws_ticket( redis, "user-123" )
        resolved = await authenticate_ws_ticket( redis, ticket )
        assert resolved == "user-123"

    @pytest.mark.anyio
    async def test_ticket_is_single_use( self, redis ):
        ticket = await mint_ws_ticket( redis, "user-123" )
        await authenticate_ws_ticket( redis, ticket )
        second_attempt = await authenticate_ws_ticket( redis, ticket )
        assert second_attempt is None

    @pytest.mark.anyio
    async def test_unknown_ticket_returns_none( self, redis ):
        assert await authenticate_ws_ticket( redis, "not-a-real-ticket" ) is None

    @pytest.mark.anyio
    async def test_none_or_empty_ticket_returns_none( self, redis ):
        assert await authenticate_ws_ticket( redis, None ) is None
        assert await authenticate_ws_ticket( redis, "" ) is None

    @pytest.mark.anyio
    async def test_expired_ticket_returns_none( self, redis ):
        # fakeredis honours TTLs; set one at 1s and wait it out rather than
        # relying on internal clock mocking, to keep this test simple.
        from auth.security import generate_ws_ticket, hash_token
        raw = generate_ws_ticket( )
        await redis.set( f"ws_ticket:{ hash_token( raw ) }", "user-123", ex=1 )
        time.sleep( 1.2 )
        assert await authenticate_ws_ticket( redis, raw ) is None

    @pytest.mark.anyio
    async def test_different_users_get_different_tickets( self, redis ):
        ticket_a = await mint_ws_ticket( redis, "user-a" )
        ticket_b = await mint_ws_ticket( redis, "user-b" )
        assert ticket_a != ticket_b
        assert await authenticate_ws_ticket( redis, ticket_a ) == "user-a"
        assert await authenticate_ws_ticket( redis, ticket_b ) == "user-b"


class TestConnectionLimit:
    @pytest.mark.anyio
    async def test_first_connection_succeeds( self, redis ):
        conn_id = await create_connection_slot( redis, "user-1" )
        assert conn_id is not None

    @pytest.mark.anyio
    async def test_allows_up_to_the_configured_max( self, redis ):
        # settings.ws_max_connections_per_user = 5
        ids = [ await create_connection_slot( redis, "user-1" ) for _ in range( 5 ) ]
        assert all( i is not None for i in ids )
        assert len( set( ids ) ) == 5  # all distinct connection ids

    @pytest.mark.anyio
    async def test_rejects_the_one_over_the_limit( self, redis ):
        for _ in range( 5 ):
            assert await create_connection_slot( redis, "user-1" ) is not None
        sixth = await create_connection_slot( redis, "user-1" )
        assert sixth is None

    @pytest.mark.anyio
    async def test_release_frees_a_slot( self, redis ):
        ids = [ await create_connection_slot( redis, "user-1" ) for _ in range( 5 ) ]
        await release_connection_slot( redis, "user-1", ids[ 0 ] )
        new_id = await create_connection_slot( redis, "user-1" )
        assert new_id is not None

    @pytest.mark.anyio
    async def test_limit_is_per_user( self, redis ):
        for _ in range( 5 ):
            assert await create_connection_slot( redis, "user-1" ) is not None
        # a different user is unaffected by user-1 being at their limit
        assert await create_connection_slot( redis, "user-2" ) is not None

    @pytest.mark.anyio
    async def test_rejected_attempt_does_not_leave_a_dangling_member( self, redis ):
        for _ in range( 5 ):
            await create_connection_slot( redis, "user-1" )
        rejected = await create_connection_slot( redis, "user-1" )
        assert rejected is None
        # the rejected attempt's connection_id must not still occupy a slot -
        # count should remain exactly 5, not 6
        count = await redis.zcard( "ws_conns:user-1" )
        assert count == 5

    @pytest.mark.anyio
    async def test_crashed_connection_is_pruned_by_a_later_acquire( self, redis ):
        """The core crash-safety property: a connection that never calls
        release_connection_slot() (simulating a worker crash) should still
        free its slot eventually, once it's stale, the next time anyone
        tries to acquire a slot for that user."""
        conn_id = await create_connection_slot( redis, "user-1" )
        assert conn_id is not None

        # Manually age this entry into the past, simulating time passing
        # without a heartbeat refresh (as if the worker holding it died).
        stale_timestamp = time.time() - 999999
        await redis.zadd( _conn_key( "user-1" ), { conn_id: stale_timestamp } )

        # Fill up the remaining 4 slots
        for _ in range( 4 ):
            assert await create_connection_slot( redis, "user-1" ) is not None

        # A 6th acquire should succeed: the stale entry should have been
        # pruned by one of the acquires above, freeing real room.
        sixth = await create_connection_slot( redis, "user-1" )
        assert sixth is not None

    @pytest.mark.anyio
    async def test_refreshed_connection_is_not_pruned_as_stale( self, redis ):
        conn_id = await create_connection_slot( redis, "user-1" )
        # Age it, but then refresh it before anyone else tries to acquire
        await redis.zadd( _conn_key( "user-1" ), { conn_id: time.time() - 999999 } )
        await refresh_connection_slot( redis, "user-1", conn_id )

        for _ in range( 4 ):
            await create_connection_slot( redis, "user-1" )

        # Now at 5 real, live connections - a 6th should be rejected,
        # proving the refreshed one was NOT pruned as stale.
        sixth = await create_connection_slot( redis, "user-1" )
        assert sixth is None