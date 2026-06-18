from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated

from auth.security import decode_access_token, generate_refresh_token, hash_token
from config import settings
from database import get_db
from fastapi import Depends, HTTPException, status, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from models.models import RefreshToken, User
from sqlalchemy.ext.asyncio import AsyncSession

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    db: Annotated[ AsyncSession, Depends( get_db ) ],
    credentials: HTTPAuthorizationCredentials | None = Depends( bearer_scheme )
) -> User:
    """
    Verifies the JWT access token and loads the corresponding user.
    Used as a dependency on every JWT-protected route.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={ "WWW-Authenticate": "Bearer" }
    )

    if credentials is None:
        raise credentials_exception

    try:
        payload = decode_access_token( credentials.credentials )
        user_id = payload.get( "sub" )
        if user_id is None:
            raise credentials_exception
    except Exception:
        raise credentials_exception

    user = await db.get( User, uuid.UUID( user_id ) )
    if user is None:
        raise credentials_exception

    return user


async def issue_refresh_token(
    db: AsyncSession,
    user_id: uuid.UUID,
    *,
    family_id: uuid.UUID | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None
) -> str:
    """
    Creates a new refresh token for a user and adds it to the database.
    Parameters:
        db (AsyncSession): Asynchronous database session.
        user_id (UUID): UUID of the user the token is for.
        family_id (UUID | None): UUID of the family the token is part of, leave blank to start a new family when a user starts a new session.
        ip_address: (str | None): IP address of the client, useful for auditing.
        user_agent: (str | None): User agent of the client's browser.
    Returns:
        refresh_token (str): The new refresh token to pass back to the client.
    """
    raw_token = generate_refresh_token( )
    now = datetime.now( timezone.utc )

    token_row = RefreshToken(
        id=uuid.uuid4( ),
        user_id=user_id,
        family_id=family_id or uuid.uuid4( ),
        token_hash=hash_token( raw_token ),
        expires_at=now + timedelta( days=settings.jwt_refresh_token_expire_days ),
        ip_address=ip_address,
        user_agent=user_agent
    )
    db.add( token_row )
    await db.flush( )  # populate any server defaults before we commit in the caller

    return raw_token


def set_refresh_cookie( response: Response, raw_token: str ) -> None:
    """
    General refresh token cookie setter for consistency, modifies the response object in place.
    Parameters:
        response (Response): FastAPI response object.
        raw_token (str): The new refresh token to send to the client.
    """
    response.set_cookie(
        key="refresh_token",
        value=raw_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=settings.jwt_refresh_token_expire_days * 24 * 60 * 60,
        path="/auth",  # only sent back on auth routes, not every request
    )

CurrentUser = Annotated[ User, Depends( get_current_user ) ] 