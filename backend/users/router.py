from __future__ import annotations

from typing import Annotated

from auth.dependencies import get_current_user
from auth.schemas import UserPublic
from auth.security import verify_password
from cache import get_redis
from database import get_db
from fastapi import APIRouter, Depends, HTTPException, status
from models.models import User
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from users.schemas import (
    DeleteUserRequest,
    UpdatePasswordResponse,
    UpdateUserPasswordRequest,
    UpdateUserRequest,
)
from users.service import update_user_details, update_user_password
from worker.pool import get_arq_pool

router = APIRouter( )


@router.get( "/me" )
async def me(
    user: Annotated[ User, Depends( get_current_user ) ],
) -> UserPublic:
    return UserPublic.model_validate( user )

@router.patch( "/me", )
async def update_user(
    payload: UpdateUserRequest,
    user:    Annotated[ User, Depends( get_current_user ) ],
    db:      Annotated[ AsyncSession, Depends( get_db ) ],
    redis:   Annotated[ Redis, Depends( get_redis ) ]
) -> UserPublic:
    response = await update_user_details( payload, user, db, redis )
    return response

@router.patch( "/me/change-password" )
async def update_password(
    payload: UpdateUserPasswordRequest,
    user:    Annotated[ User, Depends( get_current_user ) ],
    db:      Annotated[ AsyncSession, Depends( get_db ) ]
) -> UpdatePasswordResponse:
    response = await update_user_password( payload, user, db )
    return response

@router.post( "/me" )
async def delete_user(
    payload: DeleteUserRequest,
    user:    Annotated[ User, Depends( get_current_user ) ],
    db:      Annotated[ AsyncSession, Depends( get_db ) ]
) -> None:
    if payload.password != payload.confirm_password:
        raise HTTPException( detail="Passwords do not match.", status_code=status.HTTP_400_BAD_REQUEST )

    if verify_password( payload.password, user.password_hash ) == False:
        raise HTTPException( detail="Password is incorrect.", status_code=status.HTTP_401_UNAUTHORIZED )

    await get_arq_pool( ).enqueue_job( "delete_user_data_task", str( user.id ) )

