from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

from auth.dependencies import (
    get_client_ip,
    get_current_user,
    issue_refresh_token,
    set_refresh_cookie,
)
from auth.schemas import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    LoginResponse,
    LogoutResponse,
    RefreshResponse,
    RegisterRequest,
    RegisterResponse,
    ResendVerificationRequest,
    ResendVerificationResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
    UserPublic,
    VerifyEmailResponse,
)
from auth.security import (
    create_access_token,
    hash_password,
    hash_token,
)
from auth.service import (
    authenticate_user,
    find_valid_token,
    issue_password_reset_token,
    register_user,
    resend_verification_email,
    verify_email_token,
)
from database import get_db
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from models.models import PasswordResetToken, RefreshToken, User
from rate_limiter import get_auth_rate_limiter, get_forgot_password_rate_limiter
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter( dependencies=[ Depends( get_auth_rate_limiter ) ] )


@router.post( "/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED )
async def register(
    payload: RegisterRequest,
    db: Annotated[ AsyncSession, Depends( get_db ) ]
) -> RegisterResponse:
    user = await register_user( db, payload )
    
    await db.commit( )
    await db.refresh( user )

    return RegisterResponse( user=UserPublic.model_validate( user ) )


@router.post( "/login", response_model=LoginResponse )
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: Annotated[ AsyncSession, Depends( get_db ) ]
) -> LoginResponse:
    user = await authenticate_user( db, payload )

    access_token = create_access_token( user_id=str( user.id ) )

    raw_refresh_token = await issue_refresh_token(
        db,
        user_id=user.id,
        ip_address=get_client_ip( request ),
        user_agent=request.headers.get( "user-agent" )
    )
    await db.commit( )

    set_refresh_cookie( response, raw_refresh_token )

    return LoginResponse(
        access_token=access_token,
        user=UserPublic.model_validate( user )
    )

@router.post( "/refresh", response_model=RefreshResponse )
async def refresh(
    request: Request,
    response: Response,
    db: Annotated[ AsyncSession, Depends( get_db ) ]
) -> RefreshResponse:
    refresh_token = request.cookies.get( "refresh_token" )
    if refresh_token is None:
        raise HTTPException( status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing refresh token" )
    
    token_hash = hash_token( refresh_token )
    result = await db.execute(
        select( RefreshToken )
        .where( RefreshToken.token_hash == token_hash )
    )
    token_row = result.scalar_one_or_none( )

    if token_row is None:
        raise HTTPException( status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token" )
    
    if token_row.revoked_at is not None:
        await db.execute(
            update( RefreshToken )
            .where( RefreshToken.family_id == token_row.family_id )
            .values( revoked_at=func.now( ) ) 
        )

        await db.commit( )
        raise HTTPException( status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token was already used" )
    
    if token_row.expires_at < datetime.now( timezone.utc ):
        raise HTTPException( status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token has expired" )
    
    token_row.revoked_at = datetime.now( timezone.utc )

    user = await db.get( User, token_row.user_id )

    new_token = await issue_refresh_token(
        db=db,
        user_id=user.id,
        family_id=token_row.family_id,
        ip_address=get_client_ip( request ),
        user_agent=request.headers.get( "user-agent" )
    )

    await db.commit( )

    set_refresh_cookie( response=response, raw_token=new_token )
    access_token = create_access_token( user_id=str( user.id ) )

    return RefreshResponse( access_token=access_token, user=UserPublic.model_validate( user ) )

@router.post( "/logout", response_model=LogoutResponse )
async def logout(
    request: Request,
    response: Response,
    current_user: Annotated[ User, Depends( get_current_user ) ],
    db: Annotated[ AsyncSession, Depends( get_db ) ]
) -> LogoutResponse:
    raw_token = request.cookies.get( "refresh_token" )
    if raw_token:
        token_row = await find_valid_token(
            db=db,
            model=RefreshToken,
            raw_token=raw_token,
            consumed_at_field=RefreshToken.revoked_at
        )

        token_row.revoked_at = datetime.now( timezone.utc )

        await db.commit( )

    response.delete_cookie( key="refresh_token", path="/auth" )
    return LogoutResponse( )

@router.post( "/forgot-password", response_model=ForgotPasswordResponse, dependencies=[ Depends( get_forgot_password_rate_limiter ) ] )
async def forgot_password(
    payload: ForgotPasswordRequest,
    db: Annotated[ AsyncSession, Depends( get_db ) ]
) -> ForgotPasswordResponse:
    result = await db.execute( select( User ).where( User.email == payload.email.lower( ) ) )
    user = result.scalar_one_or_none( )

    if user is not None:
        await issue_password_reset_token( db=db, user_row=user )

        await db.commit( )       
        
    return ForgotPasswordResponse( )

@router.post( "/reset-password", response_model=ResetPasswordResponse, dependencies=[ Depends( get_forgot_password_rate_limiter ) ] )
async def reset_password(
    payload: ResetPasswordRequest,
    db: Annotated[ AsyncSession, Depends( get_db ) ],
) -> ResetPasswordResponse:
    reset_row = await find_valid_token(
        db=db,
        model=PasswordResetToken,
        raw_token=payload.token,
        consumed_at_field=PasswordResetToken.used_at,
        not_found_detail="Invalid or expired reset token",
        expired_detail="Invalid or expired reset token"
    )

    user = await db.get( User, reset_row.user_id )
    user.password_hash = hash_password( payload.password )
    reset_row.used_at = datetime.now( timezone.utc )

    await db.execute(
        update( RefreshToken )
        .where( RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_( None ) )
        .values( revoked_at=func.now( ) )
    )

    await db.commit( )
    return ResetPasswordResponse( )

@router.get( "/verify-email" )
async def verify_email( token: str, db: Annotated[ AsyncSession, Depends( get_db ) ] ):
    await verify_email_token( db, token )
    await db.commit( )
    return VerifyEmailResponse( )


@router.post(
    "/resend-verification",
    dependencies=[ Depends( get_forgot_password_rate_limiter ) ]
)
async def resend_verification( payload: ResendVerificationRequest, db: Annotated[ AsyncSession, Depends( get_db ) ] ):
    await resend_verification_email( db, payload.email )
    await db.commit()
    return ResendVerificationResponse( )