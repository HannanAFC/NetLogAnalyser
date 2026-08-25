from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Literal, TypeVar

from auth.dependencies import hash_token
from auth.schemas import LoginRequest, RegisterRequest
from auth.security import generate_url_safe_token, hash_password, verify_password
from config import settings
from email_service.service import (
    send_change_email_verification_email,
    send_email_changed_email,
    send_password_reset_email,
    send_verification_email,
    send_welcome_email,
)
from fastapi import HTTPException, status
from models.models import EmailVerificationToken, PasswordResetToken, User
from redis.asyncio import Redis
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute
from testing.token_capture import record_token

TokenModel = TypeVar( "TokenModel" )


async def register_user( db: AsyncSession, payload: RegisterRequest, frontend_url: str ) -> User:
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

    result = await db.execute( select( User ).where( User.email == payload.email.lower( ) ) )
    existing_user = result.scalar_one_or_none( )

    if ( existing_user ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists."
        )

    db.add( user )
    await db.flush( )

    if settings.email_verification_enabled == True:
        await issue_verification_token( db=db, user_row=user, frontend_url=frontend_url )
    else:
        user.email_verified_at = datetime.now( timezone.utc )
        await db.flush( )
        await db.refresh( user )

    return user


async def authenticate_user( db: AsyncSession, payload: LoginRequest ) -> User:
    """
    Verifies email and password. Raises 401 for invalid credentials or 403 if not verified.
    Parameters:
        db (AsyncSession): Asynchronous database session.
        payload (LoginRequest): Pydantic LoginRequest schema.
    Returns:
        user (User): The corresponding user if the login details are correct.
    """
    invalid_credentials = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect email or password."
    )

    result = await db.execute( select( User ).where( User.email == payload.email.lower( ) ) )
    user = result.scalar_one_or_none( )

    if user is None:
        raise invalid_credentials

    if not verify_password( payload.password, user.password_hash ):
        raise invalid_credentials
    
    if user.email_verified_at is None:
        raise HTTPException( status_code=status.HTTP_403_FORBIDDEN, detail="Email has not been verified." )

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

async def issue_password_reset_token( db: AsyncSession, user_row: User, frontend_url: str ) -> None:
    raw_token = generate_url_safe_token( 32 )
    token_row = PasswordResetToken(
        user_id=user_row.id,
        token_hash=hash_token( raw_token ),
        expires_at=datetime.now( timezone.utc ) + timedelta(
            minutes=settings.password_reset_token_expire_minutes
        )
    )
    db.add( token_row )
    await db.flush( )

    if settings.enable_test_endpoints:
        record_token( email=user_row.email, token_type="reset", raw_token=raw_token )

    await send_password_reset_email(
        to=user_row.email,
        display_name=user_row.display_name,
        raw_token=raw_token,
        frontend_url=frontend_url
    )

async def issue_verification_token( db: AsyncSession, user_row: User, frontend_url: str, type: Literal[ "register", "change" ] = "register" ) -> None:
    """
    Send an email verification email to a user.
    Parameters:
        db (AsyncSession): Asynchronous database session.
        user_row (User): The user to issue the verification token to.
    """
    raw_token  = generate_url_safe_token( 32 )
    token_row  = EmailVerificationToken(
        user_id=user_row.id,
        token_hash=hash_token( raw_token ),
        expires_at=datetime.now( timezone.utc ) + timedelta(
            minutes=settings.email_verification_token_expire_minutes
        )
    )
    db.add( token_row )
    await db.flush( )

    if settings.enable_test_endpoints:
        record_token( email=user_row.email, token_type="verification", raw_token=raw_token )

    if type == "register":
        await send_verification_email(
            to=user_row.email,
            display_name=user_row.display_name,
            raw_token=raw_token,
            frontend_url=frontend_url
        )
    elif type == "change":
        await send_change_email_verification_email(
            to=user_row.email,
            display_name=user_row.display_name,
            raw_token=raw_token,
            frontend_url=frontend_url
        )

async def verify_email_token( db: AsyncSession, redis: Redis, raw_token: str, frontend_url: str, type: Literal[ "register", "change" ] = "register") -> User:
    """
    Verify an email verification token received from a user, raises HTTP error 400 if invalid token.
    Parameters:
        db (AsyncSession): Asynchronous database session.
        raw_token (str): raw verification token.
    Returns:
        user (User): The user for which the token is for.
    """
    invalid = HTTPException( status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired verification link" )

    token_hash = hash_token( raw_token )
    result = await db.execute(
        select( EmailVerificationToken ).where( EmailVerificationToken.token_hash == token_hash )
    )
    token_row = result.scalar_one_or_none( )

    if token_row is None:
        raise invalid
    if token_row.used_at is not None:
        raise invalid
    if token_row.expires_at < datetime.now( timezone.utc ):
        raise invalid

    user_row = await db.get( User, token_row.user_id )
    if user_row is None:
        raise invalid

    token_row.used_at = datetime.now( timezone.utc )
    user_row.email_verified_at = datetime.now( timezone.utc )
    await db.flush( )

    cached = await redis.get( f"useremail:{ user_row.id }" )

    if cached is None:
        await send_welcome_email( to=user_row.email, display_name=user_row.display_name, frontend_url=frontend_url )
    elif cached:
        cached_email = str( cached )
        result = await db.execute(
            select( User )
            .where( User.email == cached_email.lower( ) )
        )
        existing = result.scalar_one_or_none( )
        if existing:
            raise HTTPException( detail="Email is already taken.", status_code=status.HTTP_400_BAD_REQUEST )
        old_email      = user_row.email
        user_row.email = cached_email

        await send_email_changed_email( to=old_email, display_name=user_row.display_name, email=user_row.email )

        await db.flush( )

    return user_row

async def resend_verification_email( db: AsyncSession, email: str, frontend_url: str ) -> None:
    """
    Resend an email verification token to a user.
    Parameters:
        db (AsyncSession): Asynchronous database session.
        email (str): The email of the user.
    """
    result = await db.execute( select( User ).where( User.email == email ) )
    user_row = result.scalar_one_or_none( )

    if user_row is None or user_row.email_verified_at is not None:
        return

    # invalidate old email tokens
    await db.execute(
        update( EmailVerificationToken )
        .where(
            EmailVerificationToken.user_id == user_row.id,
            EmailVerificationToken.used_at.is_( None )
        )
        .values( used_at=datetime.now( timezone.utc ) )
    )

    await issue_verification_token( db, user_row, frontend_url=frontend_url )