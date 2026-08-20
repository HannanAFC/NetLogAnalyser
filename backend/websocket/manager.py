from __future__ import annotations

import asyncio
import logging
from collections import defaultdict

from fastapi import WebSocket

logger = logging.getLogger( __name__ )

class ConnectionManager:
    """
    A manager for a worker process to track it's websocket connections, which are keyed by user ID. Should be used as a singleton.

    Connection limits are handled by Redis and not this manager.

    The manager uses an async lock in order to prevent coroutines from mixing up and corrupting the dicts.
    """

    def __init__( self ) -> None:
        self._connections: dict[ str, set[ WebSocket ] ] = defaultdict( set )
        self._lock = asyncio.Lock( )

    async def connect( self, user_id: str, websocket: WebSocket ) -> None:
        """
        Add a user and their websocket to the manager.
        Parameters:
            user_id (str): User ID of the user to add to the manager.
            websocket (WebSocket): The websocket that the user is going to connect to.
        """
        async with self._lock:
            self._connections[ user_id ].add( websocket )

    async def disconnect( self, user_id: str, websocket: WebSocket ) -> None:
        """
        Remove a users websocket from the connections list, also removes the user if no more websockets are present for the user.
        Parameters:
            user_id (str): User ID of the user to remove from the manager.
            websocket (WebSocket): The websocket that will be removed from the user.
        """
        async with self._lock:
            conns = self._connections.get( user_id )
            if conns is not None:
                conns.discard( websocket )
                # Discard the set if it is empty
                if not conns:
                    del self._connections[ user_id ]

    def connection_count( self, user_id: str ) -> int:
        """
        Returns tha amount of websockets that a user holds (currently handled by redis so not used).
        Parameters:
            user_id (str): User ID of the user to list the connection count of.
        Returns:
            count (int): The amount of websockets the user holds.
        """
        return len( self._connections.get( user_id, ( ) ) )

    async def send_to_user( self, user_id: str, message: str ) -> None:
        """
        Send a message to a user across all their websockets that are being managed by this manager. One manager is present per worker so a websocket in a worker won't be managed by one in a different worker. Intended for use inside of a route handler.
        Parameters:
            user_id (str): User ID of the user to send the message to.
        """
        async with self._lock:
            targets = list( self._connections.get( user_id, ( ) ) )

            for websocket in targets:
                try:
                    await websocket.send_text( message )
                except Exception:
                    # Route handler will triggers it's own disconnect for broken sockets,
                    # also we do not remove the socker here as other targets may be being
                    # iterated on.
                    logger.warning(
                        f"Failed to send to a websocket connection for user { user_id }, handler will automatically clean up."
                    )

manager = ConnectionManager( )