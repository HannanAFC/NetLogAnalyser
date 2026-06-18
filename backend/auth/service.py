from __future__ import annotations

import uuid

from auth.schemas import LoginRequest, RegisterRequest
from auth.security import hash_password, verify_password
from typing import TypeVar
from fastapi import HTTPException, status
from models.models import User
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from auth.dependencies import hash_token
from sqlalchemy.orm import InstrumentedAttribute

from datetime import datetime, timezone

TokenModel = TypeVar( "TokenModel" )


async def register_user( db: AsyncSession, payload: RegisterRequest ) -> User:
    """
    Creates a new user. Raises 409 if the email is already registered.
    Parameters:
        db (AsyncSession): Asynchronous database session.
        payload (RegisterRequest): Pydantic RegisterRequest schema.
    Returns:
        user (User): The newly created user.
    """
    user = User(
        id=uuid.uuid4( ),
        email=payload.email.lower( ),
        password_hash=hash_password( payload.password ),
        display_name=payload.display_name
    )

    db.add( user )
    try:
        await db.commit( )
    except IntegrityError:
        await db.rollback( )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists"
        )

    await db.refresh( user )
    return user


async def authenticate_user( db: AsyncSession, payload: LoginRequest ) -> User:
    """
    Verifies email + password. Raises 401 on any failure.
    Parameters:
        db (AsyncSession): Asynchronous database session.
        payload (LoginRequest): Pydantic LoginRequest schema.
    Returns:
        user (User): The corresponding user if the login details are correct.
    """
    invalid_credentials = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect email or password"
    )

    result = await db.execute( select( User ).where( User.email == payload.email.lower( ) ) )
    user = result.scalar_one_or_none( )

    if user is None:
        raise invalid_credentials

    if not verify_password( payload.password, user.password_hash ):
        raise invalid_credentials

    return user

async def find_valid_token(
    db: AsyncSession,
    model: type[ TokenModel ],
    raw_token: str,
    *,
    consumed_at_field: InstrumentedAttribute,
    not_found_detail: str = "Invalid token",
    expired_detail: str = "Token has expired",
    consumed_detail: str = "Token has already been used",
) -> TokenModel:
    """
    General purpose token finding helper function for logout and reset password routes.
    Parameters:
        db (AsyncSession): Asynchronous database session.
        model (sqlalchemy model): Model that contains the token_hash attribute to check.
        raw_token (str): Token to find.
        consumed_at_field (sqlalchemy row): Row that has to be null in addition to the token existing.
        not_found_detail (str): HTTPException message to use when token is not found.
        expired_detail (str): HTTPException message to use when token is expired.
        consumed_detail (str): HTTPException message to use when token is already used.
    Returns:
        token_row (sqlalchemy row): A matching entity.
    """
    token_hash = hash_token( raw_token )
 
    result = await db.execute( select( model ).where(model.token_hash == token_hash ) )
    token_row = result.scalar_one_or_none( )
 
    if token_row is None:
        raise HTTPException( status_code=status.HTTP_401_UNAUTHORIZED, detail=not_found_detail )
 
    if getattr( token_row, consumed_at_field.key ) is not None:
        raise HTTPException( status_code=status.HTTP_401_UNAUTHORIZED, detail=consumed_detail )
 
    if token_row.expires_at < datetime.now( timezone.utc) :
        raise HTTPException( status_code=status.HTTP_401_UNAUTHORIZED, detail=expired_detail )
 
    return token_row
