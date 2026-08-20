from __future__ import annotations

import base64
import json
from binascii import Error as BinasciiError
from datetime import datetime
from uuid import UUID

from fastapi import HTTPException, status
from logs.schemas import CursorData, GetLogsResponse, LogEntryPublic
from models.models import LogEntry
from sqlalchemy import select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession


def encode_cursor( id: int, captured_at: datetime ) -> str:
    """
    Encodes the `id` and `captured_at` of a log entry into a cursor that can be used for paginating log entries.
    Parameters:
        id (int): Integer based ID of the log entry.
        captured_at (datetime): The `captured_at` property of the log entry.
    Returns:
        cursor (str): Base64 encoded cursor data.
    """
    cursor_data = {
        "id": id,
        "captured_at": captured_at.isoformat( )
    }
    json_str = json.dumps( cursor_data )
    return base64.urlsafe_b64encode( json_str.encode( ) ).decode( )

def decode_cursor( cursor: str ) -> CursorData:
    """
    Decodes a Base64 encoded cursor back into the `CursorData` dataclass.
    Parameters:
        cursor (str): Base64 encode string cursor.
    Returns:
        cursor_data (CursorData): Dataclass representing the cursor.
    """
    try:
        json_str              = base64.urlsafe_b64decode( cursor.encode( ) ).decode( )
        data                  = json.loads( json_str )
        data[ "captured_at" ] = datetime.fromisoformat( data[ "captured_at" ] )

        return CursorData( id=data[ "id" ], captured_at=data[ "captured_at" ] )
    except ( BinasciiError, UnicodeDecodeError, json.JSONDecodeError, KeyError, ValueError ):
        raise HTTPException( status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid cursor" )

async def fetch_logs( db: AsyncSession, user_id: UUID, limit: int, cursor: str | None = None ) -> GetLogsResponse:
    """
    Fetch the logs of a user along with a cursor to the next set of logs.
    Parameters:
        db (AsyncSession): Asynchronous database session.
        user_id (UUID): ID of the user to fetch the logs of.
        limit (int): Maximum amount of logs to fetch.
        cursor (str): Base64 encoded cursor.
    Returns:
        response (GetLogsResponse): Response containing the log entries, next cursor and if there are more entries.
    """
    query =  (
        select( LogEntry )
        .where(
            LogEntry.user_id == user_id
        )
        .order_by(
            LogEntry.captured_at.desc( ),
            LogEntry.id.desc( )
        )
    )

    if cursor:
        cursor_data = decode_cursor( cursor )
        query = query.filter(
            tuple_( LogEntry.captured_at, LogEntry.id ) < tuple_( cursor_data.captured_at, cursor_data.id ) # pyright: ignore[reportArgumentType]
        )

    query = query.limit( limit + 1 )
    result = await db.execute( query )
    entries = result.scalars( ).all( )

    has_more = len( entries ) > limit

    if has_more:
        entries = entries[ :limit ]

    next_cursor = None

    if has_more and entries:
        last_item = entries[ -1 ]
        next_cursor = encode_cursor( last_item.id, last_item.captured_at )

    

    return GetLogsResponse(
        entries=[ LogEntryPublic.model_validate( row ) for row in entries ],
        next_cursor=next_cursor,
        has_more=has_more
    )