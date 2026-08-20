from __future__ import annotations

from typing import Annotated

from analytics.dependencies import (
    get_anomalies_params,
    get_geo_params,
    get_time_range,
    get_timeseries_params,
    get_toptalkers_params,
)
from analytics.schemas import (
    AnomaliesRequestParams,
    AnomaliesResponse,
    GeoRequestParams,
    GeoResponse,
    ProtocolsResponse,
    SummaryResponse,
    TimeRangeRequestParams,
    TimeSeriesRequestParams,
    TimeSeriesResponse,
    TopTalkersRequestParams,
    TopTalkersResponse,
)
from analytics.service import (
    get_anomalies,
    get_geo,
    get_protocols,
    get_summary,
    get_timeseries,
    get_top_talkers,
)
from auth.dependencies import get_current_user
from cache import get_redis
from database import get_db
from fastapi import APIRouter, Depends, status
from models.models import User
from rate_limiter import get_general_rate_limiter
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter( dependencies=[ Depends( get_general_rate_limiter ) ] )



@router.get( "/summary", status_code=status.HTTP_200_OK )
async def summary(
    user:       Annotated[ User, Depends( get_current_user ) ],
    db:         Annotated[ AsyncSession, Depends( get_db ) ],
    redis:      Annotated[ Redis, Depends( get_redis ) ],
    time_range: Annotated[ TimeRangeRequestParams, Depends( get_time_range ) ]
) -> SummaryResponse:
    response = await get_summary( db, redis, user.id, time_range )
    return response

@router.get( "/timeseries", status_code=status.HTTP_200_OK )
async def timeseries(
    user:       Annotated[ User, Depends( get_current_user ) ],
    db:         Annotated[ AsyncSession, Depends( get_db ) ],
    redis:      Annotated[ Redis, Depends( get_redis ) ],
    timeseries: Annotated[ TimeSeriesRequestParams, Depends( get_timeseries_params ) ]
) -> TimeSeriesResponse:
    response = await get_timeseries( db, redis, user.id, timeseries )
    return response

@router.get( "/top-talkers", status_code=status.HTTP_200_OK )
async def top_talkers(
    user:   Annotated[ User, Depends( get_current_user ) ],
    db:     Annotated[ AsyncSession, Depends( get_db ) ],
    params: Annotated[ TopTalkersRequestParams, Depends( get_toptalkers_params ) ]
) -> TopTalkersResponse:
    response = await get_top_talkers( db, user.id, params )
    return response

@router.get( "/protocols", status_code=status.HTTP_200_OK )
async def protocols(
    user:       Annotated[ User, Depends( get_current_user ) ],
    db:         Annotated[ AsyncSession, Depends( get_db ) ],
    time_range: Annotated[ TimeRangeRequestParams, Depends( get_time_range ) ]
) -> ProtocolsResponse:
    response = await get_protocols( db, user.id, time_range )
    return response

@router.get( "/geo", status_code=status.HTTP_200_OK )
async def geo(
    user:   Annotated[ User, Depends( get_current_user ) ],
    db:     Annotated[ AsyncSession, Depends( get_db ) ],
    params: Annotated[ GeoRequestParams, Depends( get_geo_params ) ]
) -> GeoResponse:
    response = await get_geo( db, user.id, params )
    return response

@router.get( "/anomalies", status_code=status.HTTP_200_OK )
async def anomalies(
    user:   Annotated[ User, Depends( get_current_user ) ],
    db:     Annotated[ AsyncSession, Depends( get_db ) ],
    params: Annotated[ AnomaliesRequestParams, Depends( get_anomalies_params ) ]
) -> AnomaliesResponse:
    response = await get_anomalies( db, user.id, params )
    return response