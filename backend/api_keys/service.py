import uuid
from datetime import datetime, timezone

from api_keys.schemas import ApiKeyCreateRequest
from auth.security import generate_api_key, hash_token
from config import settings
from fastapi import HTTPException, status
from models.models import APIKey, User
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


async def create_api_key( db: AsyncSession, payload: ApiKeyCreateRequest, user: User ) -> tuple[ APIKey, str ]:
    """
    Creates a new API key for a given user.
    Parameters:
        db (AsyncSession): Asynchronous database session.
        payload (APIKeyCreateRequest): Pydantic APIKeyCreateRequest schema.
        user: (User): The user the key is for.
    Returns:
        api_key (APIKey): The newly created API key row.
        token (str): The actual API key which is never stored so can only be shown once.
    """

    current_keys_count_result = await db.execute(
        select( func.count( ) )
        .select_from( APIKey )
        .where( APIKey.user_id == user.id, APIKey.revoked_at.is_( None ))
    )

    current_keys_count = current_keys_count_result.scalar_one( )

    if current_keys_count >= settings.api_key_max_per_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Maximum number of active API keys (${ settings.api_key_max_per_user }) has been reached."
        )

    raw_key = generate_api_key( )
    key_prefix = raw_key[ : settings.api_key_prefix_length ]

    api_key_row = APIKey(
        id=uuid.uuid4( ),
        user_id=user.id,
        key_hash=hash_token( raw_key ),
        key_prefix=key_prefix,
        label=payload.label
    )

    db.add( api_key_row )
    await db.flush( )

    return api_key_row, raw_key

async def list_api_keys( db: AsyncSession, user: User ) -> list[ APIKey ]:
    """
    Fetch all of a users API keys.
    Parameters:
        db (AsyncSession): Asynchronous database session.
        user (User): The user whos keys are to be fetched.
    Returns:
        api_keys list[APIKey]: List of APIKey objects.
    """

    api_keys_result = await db.execute(
        select( APIKey )
        .where( APIKey.user_id == user.id )
        .order_by( APIKey.created_at.desc( ) )
    )

    return list( api_keys_result.scalars( ).all( ) )

async def revoke_api_key( db: AsyncSession, user: User, key_id: uuid.UUID ) -> None:
    """
    Revokes and API key. Returns 404 if key is not found or 409 if key is already revoked.
    Parameters:
        db (AsyncSession): Asynchronous database session.
        user: (User): The user the key is for.
        key_id (UUID): The ID of the key to be revoked.
    """

    key_result = await db.execute(
        select( APIKey )
        .where( APIKey.user_id == user.id, APIKey.id == key_id )
    )

    api_key_row = key_result.scalar_one_or_none( )

    if api_key_row == None:
        raise HTTPException(
            detail="API key was not found.",
            status_code=status.HTTP_404_NOT_FOUND
        )

    if api_key_row.revoked_at != None:
        raise HTTPException(
            detail="API key has already been revoked.",
            status_code=status.HTTP_409_CONFLICT
        )

    api_key_row.revoked_at = datetime.now( timezone.utc )
    await db.flush( )