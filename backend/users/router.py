from __future__ import annotations

from typing import Annotated

from auth.dependencies import get_current_user
from auth.schemas import UserPublic
from fastapi import APIRouter, Depends
from models.models import User

router = APIRouter( )


@router.get( "/me", response_model=UserPublic )
async def me(
    current_user: Annotated[ User, Depends( get_current_user ) ],
) -> UserPublic:
    return UserPublic( id=current_user.id, email=current_user.email, display_name=current_user.display_name, created_at=current_user.created_at )