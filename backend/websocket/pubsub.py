from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Callable
from datetime import datetime
from typing import Any
from uuid import UUID

from redis.asyncio import Redis
from websocket.manager import manager

logger = logging.getLogger( __name__ )

_CHANNEL_PATTERN = "ws:user:*:live"
_RECONNECT_DELAY_SECONDS = 2

_task: asyncio.Task | None = None


def _channel_for_user( user_id: str ) -> str:
    """
    Helper to return a channel string for a user.
    Parameters:
        user_id (str): User ID of the user to create the channel string for.
    Returns:
        channel (str): The channel string.
    """
    return f"ws:user:{ user_id }:live"


def _extract_user_id( channel: str ) -> str | None:
    """
    Extract the user ID from a channel string.
    Parameters:
        channel (str): The channel string>
    Returns:
        user_id (str | None): The extracted user ID.
    """
    prefix, suffix = "ws:user:", ":live"
    if channel.startswith( prefix ) and channel.endswith( suffix ):
        return channel[ len( prefix ) : -len( suffix ) ]
    return None


def _json_default( obj: Any ) -> Any:
    """
    Handles the dict log entry's non-JSON types and convert them to strings. Throws an error for unsupported objects as this is used as protection against new types leaking into responses.
    Parameters:
        obj (Any): Any object type.
    Returns:
        converted_value (Any): A JSON serialisable type. 
    """
    if isinstance( obj, UUID ):
        return str( obj )
    if isinstance( obj, datetime ):
        return obj.isoformat()
    raise TypeError( f"Object of type { type( obj ).__name__ } is not JSON serialisable" )


_BROADCAST_FIELDS = (
    "src_ip",
    "dst_ip",
    "src_port",
    "dst_port",
    "protocol",
    "packet_size_bytes",
    "flags",
    "src_country_code",
    "dst_country_code",
    "src_geo_status",
    "dst_geo_status",
    "anomaly_score",
    "anomaly_reasons",
    "captured_at",
)


def _to_broadcast_row( row: dict ) -> dict:
    """
    Strips fields from a dict log entry that aren't in the allowlist.
    Parameters:
        row (dict): A log entry row in a dict form.
    Returns:
        row (dict): The same dict but only with fields that are allowed to be broadcasted.
    """
    return { field: row[ field ] for field in _BROADCAST_FIELDS }


async def publish_log_entries( redis: Redis, user_id: str, rows: list[ dict ] ) -> None:
    """
    Publish a batch of log entries to the live feed websockets. Only use after the log entries have been committed to the DB.
    Parameters:
        redis (Redis): The redis instance.
        user_id (str): The user ID of the user who the entries belong to.
        rows (list[dict]): The log entries to publish.
    """
    broadcast_rows = [ _to_broadcast_row( row ) for row in rows ]
    message = json.dumps(
        { "type": "log_entry_batch", "data": broadcast_rows },
        default=_json_default,
    )
    await redis.publish( _channel_for_user( user_id ), message )


async def _listen_once( redis_factory: Callable[ ..., Redis ] ) -> None:
    """
    Lifetime for a subscriber. Listens to all ingest events for all users.
    Parameters:
        redis_factory (Callable): A callable that returns the redis client of the worker.
    """
    redis = redis_factory( )
    pubsub = redis.pubsub( )
    await pubsub.psubscribe( _CHANNEL_PATTERN )
    logger.info( "WS pubsub subscriber connected, listening on %s", _CHANNEL_PATTERN )

    try:
        async for message in pubsub.listen( ):
            if message[ "type" ] != "pmessage":
                continue

            channel = message[ "channel" ]
            if isinstance( channel, bytes ):
                channel = channel.decode()

            user_id = _extract_user_id( channel )
            if user_id is None:
                logger.warning( f"WS pubsub message on unexpected channel: { channel }" )
                continue

            data = message[ "data" ]
            if isinstance( data, bytes ):
                data = data.decode( )

            await manager.send_to_user( user_id, data )
    finally:
        await pubsub.punsubscribe( _CHANNEL_PATTERN )
        await pubsub.aclose( )
        await redis.aclose( )


async def _listen_forever( redis_factory: Callable[ ..., Redis ] ) -> None:
    """
    Wrapper for _listen_one that acts as a reconnect loop for the connection.
    Parameters:
        redis_factory (Callable): A callable that returns the redis client of the worker.
    """
    while True:
        try:
            await _listen_once( redis_factory )
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception(
                "WS pubsub subscriber crashed, reconnecting in %ss",
                _RECONNECT_DELAY_SECONDS,
            )
            await asyncio.sleep( _RECONNECT_DELAY_SECONDS )


def start_pubsub_listener( redis_factory: Callable[ ..., Redis ] ) -> None:
    """
    Starts the subscriber, include in the FastAPI lifespan.
    Parameters:
        redis_factory (Callable): A callable that returns the redis client of the worker. Create a new client for the subscriber.
    """
    global _task
    if _task is not None:
        return
    _task = asyncio.create_task( _listen_forever( redis_factory ) )


async def stop_pubsub_listener( ) -> None:
    """
    Closes the subscriber during the lifespan shutdown.
    """
    global _task
    if _task is None:
        return
    _task.cancel( )
    try:
        await _task
    except asyncio.CancelledError:
        pass
    _task = None