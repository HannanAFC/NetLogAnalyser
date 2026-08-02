from __future__ import annotations

from typing import Annotated

from auth.dependencies import get_current_user
from database import get_db
from fastapi import APIRouter, Depends, Query
from logs.schemas import GetLogsResponse
from logs.service import fetch_logs
from models.models import User
from rate_limiter import get_general_rate_limiter
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter( dependencies=[ Depends( get_general_rate_limiter ) ] )

@router.get( "" )
async def get_logs(
    user:   Annotated[ User, Depends( get_current_user ) ],
    db:     Annotated[ AsyncSession, Depends( get_db ) ],
    limit:  Annotated[ int, Query( ge=1, le=50, description="Maximum number of logs to fetch." ) ] = 20,
    cursor: Annotated[ str | None, Query( min_length=1, description="Pointer to the next page of logs, obtained by making a request without a cursor first." ) ] = None
) -> GetLogsResponse:
    response = await fetch_logs( db, user.id, limit, cursor )
    return response