from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import UUID

from auth.schemas import UserPublic
from auth.security import hash_password, verify_password
from auth.service import issue_verification_token
from config import settings
from database import AsyncSessionLocal
from exports.storage import get_export_storage
from fastapi import HTTPException, status
from models.models import DataExport, RefreshToken, User
from redis.asyncio import Redis
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from users.schemas import (
    UpdatePasswordResponse,
    UpdateUserPasswordRequest,
    UpdateUserRequest,
)

logger = logging.getLogger( __name__ )

async def update_user_details(
    payload:      UpdateUserRequest,
    user:         User,
    db:           AsyncSession,
    redis:        Redis,
    frontend_url: str
) -> UserPublic:
    if payload.email == user.email:
        raise HTTPException( detail="New email must be different to the old one.", status_code=status.HTTP_422_UNPROCESSABLE_CONTENT )
    
    if payload.email is not None:
        result = await db.execute(
            select( User )
            .where( User.email == payload.email.lower( ) )
        )

        user_row = result.scalar_one_or_none( )

        if user_row:
            raise HTTPException( detail="Email is already taken.", status_code=status.HTTP_400_BAD_REQUEST )
        elif settings.email_verification_enabled == True:
            await issue_verification_token( db, user, frontend_url, "change" )
            await redis.set(
                f"useremail:{ user.id }",
                payload.email,
                ex=300
            )
        else:
            user.email = payload.email

    if payload.display_name is not None:
        user.display_name = payload.display_name

    await db.commit( )
    await db.refresh( user )
    return UserPublic.model_validate( user )

async def update_user_password(
    payload: UpdateUserPasswordRequest,
    user:    User,
    db:      AsyncSession,
)  -> UpdatePasswordResponse:
    if verify_password( payload.current_password, user.password_hash ) == False:
        raise HTTPException( detail="Password is incorrect.", status_code=status.HTTP_400_BAD_REQUEST )

    user.password_hash = hash_password( payload.password )

    await db.execute(
        update( RefreshToken )
        .where( RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_( None ) )
        .values( revoked_at=func.now( ) )
    )

    await db.commit( )
    return UpdatePasswordResponse( )

async def delete_user_data(
    user_id:   UUID
) -> None:
    async with AsyncSessionLocal( ) as db:
        result = await db.execute(
            select( DataExport )
            .where(
                DataExport.status == "READY",
                DataExport.purged_at.is_( None ),
                DataExport.user_id == user_id
            )
        )
        expired = result.scalars( ).all( )

        purged = 0
        for export_row in expired:

            export_id = export_row.id
            storage_key = export_row.storage_key
            storage_backend = export_row.storage_backend

            try:
                storage = get_export_storage( storage_backend )
                await storage.delete( storage_key )
            except Exception:
                logger.exception(
                    "Failed to purge expired export: storage delete failed.",
                    extra={ "export_id": str( export_id ) }
                )
                continue
        
            try:
                async with db.begin_nested( ):
                    export_row.purged_at = datetime.now( timezone.utc )
                    await db.flush( )
                await db.commit( )
                purged += 1
                logger.info(
                    "Purged expired export file.", extra={ "export_id": str( export_id ), "key": storage_key }
                )
            except Exception:
                logger.exception(
                    "Failed to purge expired export: db write failed.", extra={ "export_id": str( export_id ) }
                )
                continue

        logger.info(
            "Deleted user exports.",
            extra={ "user_id": str( user_id ) }
        )

        user = await db.get( User, user_id )
        if user is None:
            logger.exception(
                "Failed to find user in database to delete.",
                extra={ "user_id": str( user_id ) }
            )
            return

        await db.delete( user )
        await db.commit( )