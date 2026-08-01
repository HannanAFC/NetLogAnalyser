from __future__ import annotations

import time
import uuid
from typing import Any

from auth.security import generate_ws_ticket, hash_token
from config import settings
from fastapi import WebSocket
from redis.asyncio import Redis

_TICKET_PREFIX = "ws_ticket:"
_CONN_ZSET_PREFIX = "ws_conns:"

def _ticket_key( ticket_hash: str ) -> str:
    """
    Creates a ticket key using a hash with the correct prefix.
    Parameters:
        ticket_hash (str): An already hashed ticket.
    Returns:
        ticket_key (str): A ticket key that uses the hash.
    """
    return f"{ _TICKET_PREFIX }{ ticket_hash }"

def _conn_key( user_id: str ) -> str:
    """
    Creates a user key using the user ID.
    Parameters:
        user_id (str): The users ID.
    Returns:
        conn_key (str): A connection key.
    """
    return f"{ _CONN_ZSET_PREFIX }{ user_id }"

async def mint_ws_ticket( redis: Redis, user_id: str ) -> str:
    """
    Create a very short lived ticket to establish a websocket. The hash of the ticket is stored in redis only.
    Parameters:
        redis (Redis): The redis client to use.
        user_id (str): The user ID of the user to establish a connection for.
    Returns:
        ws_ticket (str): The ticket that will be needed to establish a connection.
    """

    raw_ticket  = generate_ws_ticket( )
    ticket_hash = hash_token( raw_ticket )
    await redis.set( _ticket_key( ticket_hash ), user_id, ex=settings.ws_ticket_ttl_seconds )
    return raw_ticket

async def authenticate_ws_ticket( redis: Redis, raw_ticket: str | None ) -> str | None:
    """
    Authenticates a ticket and returns a user_id if it is a valid ticket.
    Parameters:
        redis (Redis): The redis client to use.
        raw_ticket (str): Ticket from the client that needs to be authenticated.
    Returns:
        user_id (str | None): If the ticket is valid the user ID will be returned, if not None is returned.
    """
    if not raw_ticket:
        return None

    ticket_hash = hash_token( raw_ticket )
    key         = _ticket_key( ticket_hash )


    user_id     = await redis.get( key )
    if user_id is None:
        return None

    await redis.delete( key )
    return user_id.decode( ) if isinstance( user_id, bytes ) else user_id

async def create_connection_slot( redis: Redis, user_id: str ) -> str | None:
    """
    Create a new connection for a user_id *if* they are under their limit. This also prunes stale connections, active connection should be refreshed to prevent them from also gettings pruned.
    Parameters:
        redis (Redis): The redis client to use.
        user_id (str): User to create a connection for.
    Returns:
        connection_id (str): Connection ID that is to be passed to refresh or release connection functions, or None if the user is at the limit of WS connections.
    """
    key = _conn_key( user_id )
    now = time.time( )
    stale_before = now - settings.ws_stale_connection_seconds

    await redis.zremrangebyscore( key, "-inf", stale_before )

    connection_id = str( uuid.uuid4( ) )
    await redis.zadd( key, { connection_id: now } )

    count = await redis.zcard( key )
    if count > settings.ws_max_connections_per_user:
        await redis.zrem( key, connection_id )
        return None

    # If the key is somehow forgotten, this safety precaution will expire it
    await redis.expire( key, settings.ws_stale_connection_seconds * 2 )
    return connection_id

async def refresh_connection_slot( redis: Redis, user_id: str, connection_id: str ) -> None:
    """
    Call this function periodically (e.g. on each heartbeat) to refresh a connection and prove it's still alive, refreshing resets the redis key's score so that it isn't pruned.
    Parameters:
        redis (Redis): The redis client to use.
        user_id (str): User to refresh a connection for.
        connection_id (str): The user connection that is to be refreshed.
    """
    key = _conn_key( user_id )
    await redis.zadd( key, { connection_id: time.time( ) } )

async def release_connection_slot( redis: Any, user_id: str, connection_id: str ) -> None:
    """
    Release a web socket connection.
    Parameters:
        redis (Redis): The redis client to use.
        user_id (str): User of the connection to release.
        connection_id (str): The user connection that is to be released.
    """
    key = _conn_key( user_id )
    await redis.zrem( key, connection_id )

def _origin_allowed( websocket: WebSocket ) -> bool:
    """
    Manual check for websockets to see if the origin is allowed before establishing a connection:
    Parameters:
        websocket (WebSocket): The websocket to check the origin of.
    Returns:
        allowed (bool): Whether the origin is allowed.
    """
    origin = websocket.headers.get( "origin" )
    return origin in settings.cors_allowed_origins