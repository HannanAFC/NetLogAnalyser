from __future__ import annotations

from typing import Annotated
from uuid import UUID

from api_keys.schemas import APIKeyCreateRequest, APIKeyCreateResponse, APIKeyPublic
from api_keys.service import create_api_key, list_api_keys, revoke_api_key
from auth.dependencies import get_current_user
from database import get_db
from fastapi import APIRouter, Depends, status
from models.models import User
from rate_limiter import get_general_rate_limiter
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter( dependencies=[ Depends( get_general_rate_limiter ) ] )


@router.post( "", response_model=APIKeyCreateResponse, status_code=status.HTTP_201_CREATED )
async def create_key(
    payload: APIKeyCreateRequest,
    user: Annotated[ User, Depends( get_current_user ) ],
    db: Annotated[ AsyncSession, Depends( get_db ) ]
):
    api_key_row, raw_key = await create_api_key( db, payload, user )
    await db.commit( )

    return APIKeyCreateResponse(
        id=api_key_row.id,
        label=api_key_row.label,
        key_prefix=api_key_row.key_prefix,
        api_key=raw_key,
        created_at=api_key_row.created_at
    )


@router.get( "", response_model=list[ APIKeyPublic ] )
async def list_keys(
    user: Annotated[ User, Depends( get_current_user ) ],
    db: Annotated[ AsyncSession, Depends( get_db ) ]
):
    api_key_rows = await list_api_keys( db, user )
    return [ APIKeyPublic.model_validate( row ) for row in api_key_rows ]


@router.delete( "/{key_id}", status_code=status.HTTP_204_NO_CONTENT )
async def delete_key(
    key_id: UUID,
    user: Annotated[ User, Depends( get_current_user ) ],
    db: Annotated[ AsyncSession, Depends( get_db ) ]
):
    await revoke_api_key( db, user, key_id )
    await db.commit( )