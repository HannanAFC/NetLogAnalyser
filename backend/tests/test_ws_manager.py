from __future__ import annotations

import pytest
from websocket.manager import ConnectionManager


class FakeWebSocket:
    def __init__( self, fail: bool = False ) -> None:
        self.sent: list[ str ] = [ ]
        self.fail = fail

    async def send_text( self, message: str ) -> None:
        if self.fail:
            raise RuntimeError( "connection closed" )
        self.sent.append( message )


class TestConnectionManager:
    @pytest.mark.anyio
    async def test_connect_then_send_delivers_to_that_user( self ):
        manager = ConnectionManager( )
        ws = FakeWebSocket( )
        await manager.connect( "user-1", ws )

        await manager.send_to_user( "user-1", "hello" )

        assert ws.sent == [ "hello" ]

    @pytest.mark.anyio
    async def test_send_to_unconnected_user_does_nothing( self ):
        manager = ConnectionManager( )
        # no connections registered at all - should not raise
        await manager.send_to_user( "nobody", "hello" )

    @pytest.mark.anyio
    async def test_message_only_goes_to_the_targeted_user( self ):
        manager = ConnectionManager( )
        ws_a = FakeWebSocket( )
        ws_b = FakeWebSocket( )
        await manager.connect( "user-a", ws_a )
        await manager.connect( "user-b", ws_b )

        await manager.send_to_user( "user-a", "for-a-only" )

        assert ws_a.sent == [ "for-a-only" ]
        assert ws_b.sent == [ ]

    @pytest.mark.anyio
    async def test_multiple_connections_for_one_user_all_receive_it( self ):
        manager = ConnectionManager( )
        ws_1 = FakeWebSocket( )
        ws_2 = FakeWebSocket( )
        await manager.connect( "user-1", ws_1 )
        await manager.connect( "user-1", ws_2 )

        await manager.send_to_user( "user-1", "broadcast" )

        assert ws_1.sent == [ "broadcast" ]
        assert ws_2.sent == [ "broadcast" ]

    @pytest.mark.anyio
    async def test_disconnect_removes_only_that_connection( self ):
        manager = ConnectionManager( )
        ws_1 = FakeWebSocket( )
        ws_2 = FakeWebSocket( )
        await manager.connect( "user-1", ws_1 )
        await manager.connect( "user-1", ws_2 )

        await manager.disconnect( "user-1", ws_1 )
        await manager.send_to_user( "user-1", "still-here" )

        assert ws_1.sent == []
        assert ws_2.sent == [ "still-here" ]

    @pytest.mark.anyio
    async def test_disconnecting_last_connection_cleans_up_the_user_entry( self ):
        manager = ConnectionManager( )
        ws = FakeWebSocket( )
        await manager.connect( "user-1", ws )
        await manager.disconnect( "user-1", ws )

        assert manager.connection_count( "user-1" ) == 0
        assert "user-1" not in manager._connections

    @pytest.mark.anyio
    async def test_disconnect_of_unknown_connection_does_not_raise( self ):
        manager = ConnectionManager( )
        ws = FakeWebSocket( )
        # never connected - disconnecting should be a harmless no-op
        await manager.disconnect( "user-1", ws )

    @pytest.mark.anyio
    async def test_a_failing_send_does_not_prevent_others_from_receiving( self ):
        manager = ConnectionManager( )
        good = FakeWebSocket( )
        bad = FakeWebSocket( fail=True )
        await manager.connect( "user-1", good )
        await manager.connect( "user-1", bad )

        await manager.send_to_user( "user-1", "message" )  # should not raise

        assert good.sent == [ "message" ]

    @pytest.mark.anyio
    async def test_connection_count_reflects_connect_and_disconnect( self ):
        manager = ConnectionManager( )
        ws_1 = FakeWebSocket( )
        ws_2 = FakeWebSocket( )
        assert manager.connection_count( "user-1" ) == 0

        await manager.connect( "user-1", ws_1 )
        assert manager.connection_count( "user-1" ) == 1

        await manager.connect( "user-1", ws_2 )
        assert manager.connection_count( "user-1" ) == 2

        await manager.disconnect( "user-1", ws_1 )
        assert manager.connection_count( "user-1" ) == 1