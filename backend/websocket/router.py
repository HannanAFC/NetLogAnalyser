from __future__ import annotations

from typing import Annotated

from auth.dependencies import get_current_user
from cache import get_redis
from config import settings
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from models.models import User
from redis.asyncio import Redis
from websocket.manager import manager
from websocket.schemas import CreateTicketResponse
from websocket.service import (
    _origin_allowed,
    authenticate_ws_ticket,
    create_connection_slot,
    mint_ws_ticket,
    refresh_connection_slot,
    release_connection_slot,
)

router = APIRouter( )

@router.post( "/ticket" )
async def create_ws_ticket(
    current_user: Annotated[ User, Depends( get_current_user ) ],
    redis: Annotated[ Redis, Depends( get_redis ) ]
) -> CreateTicketResponse:
    ticket = await mint_ws_ticket( redis, str( current_user.id ) )
    return CreateTicketResponse( ticket=ticket, expires_in=settings.ws_ticket_ttl_seconds )

@router.websocket( "/live" )
async def live_feed(
    websocket: WebSocket,
    redis: Annotated[ Redis, Depends( get_redis ) ]
) -> None:
    if not _origin_allowed( websocket ):
        await websocket.close( code=4403 )
        return

    ticket  = websocket.query_params.get( "ticket" )
    user_id = await authenticate_ws_ticket( redis, ticket )
    if user_id is None:
        await websocket.close( code=4401 )
        return

    connection_id = await create_connection_slot( redis, user_id )
    if connection_id is None:
        await websocket.close( code=4409 )
        return

    await websocket.accept( )
    await manager.connect( user_id, websocket )

    try:
        while True:
            # Client to server payloads aren't expected so treat as a signal to refresh.
            await websocket.receive_text( )
            await refresh_connection_slot( redis, user_id, connection_id )
    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect( user_id, websocket )
        await release_connection_slot( redis, user_id, connection_id )