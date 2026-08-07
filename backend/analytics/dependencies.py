# analytics/dependencies.py
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from analytics.schemas import (
    AnomaliesRequestParams,
    GeoRequestParams,
    TimeBucketEnum,
    TimeRangeRequestParams,
    TimeSeriesRequestParams,
    TopTalkersDirectionEnum,
    TopTalkersMetricEnum,
    TopTalkersRequestParams,
)
from config import settings
from fastapi import Depends, HTTPException, Query

MAX_RANGE     = timedelta( days=settings.analytics_max_range_days )
DEFAULT_RANGE = timedelta( hours=24 )
MAX_POINTS    = 1000
_BUCKET_SECONDS = {
    TimeBucketEnum.minute: 60,
    TimeBucketEnum.hour:   3600,
    TimeBucketEnum.day:    86400
}


async def get_time_range(
    start: datetime | None = Query( default=None ),
    end:   datetime | None = Query( default=None )
) -> TimeRangeRequestParams:
    now = datetime.now( timezone.utc )

    resolved_end   = end or now
    resolved_start = start or ( resolved_end - DEFAULT_RANGE )

    if resolved_start.tzinfo is None or resolved_end.tzinfo is None:
        raise HTTPException(
            status_code = 422,
            detail      = "Start and end must include a timezone offset"
        )

    if resolved_start >= resolved_end:
        raise HTTPException(
            status_code = 422,
            detail      = "Start must be before end"
        )

    if resolved_end - resolved_start > MAX_RANGE:
        raise HTTPException(
            status_code = 422,
            detail      = f"Range cannot exceed { MAX_RANGE.days } days"
        )

    if resolved_end > now + timedelta( minutes=5 ):
        raise HTTPException(
            status_code = 422,
            detail      = "End cannot be in the future"
        )

    return TimeRangeRequestParams( start=resolved_start, end=resolved_end )

def _auto_bucket( span: timedelta ) -> TimeBucketEnum:
    if span <= timedelta( hours=2 ):
        return TimeBucketEnum.minute
    if span <= timedelta( days=7 ):
        return TimeBucketEnum.hour
    return TimeBucketEnum.day

async def get_timeseries_params(
    time_range: TimeRangeRequestParams = Depends( get_time_range ),
    bucket:     TimeBucketEnum | None  = Query( default=None )
) -> TimeSeriesRequestParams:
    span = time_range.end - time_range.start
    resolved_bucket = bucket or _auto_bucket( span )

    point_count = span.total_seconds( ) / _BUCKET_SECONDS[ resolved_bucket ]
    if point_count > MAX_POINTS:
        raise HTTPException(
            status_code = 422,
            detail      = (
                f"The bucket '{ resolved_bucket.value }' over this time range would return "
                f"{ int( point_count ) } points (max { MAX_POINTS }), "
                f"choose a larger bucket or a shorter range"
            ),
        )

    return TimeSeriesRequestParams(
        start=time_range.start,
        end=time_range.end,
        bucket=resolved_bucket
    )

async def get_toptalkers_params(
    time_range: TimeRangeRequestParams  = Depends( get_time_range ),
    direction:  TopTalkersDirectionEnum = Query( default=TopTalkersDirectionEnum.src ),
    metric:     TopTalkersMetricEnum    = Query( default=TopTalkersMetricEnum.bytes ),
    limit:      int                     = Query( default=10 )
) -> TopTalkersRequestParams:
    return TopTalkersRequestParams(
        start=time_range.start,
        end=time_range.end,
        direction=direction,
        metric=metric,
        limit=limit
    )

async def get_geo_params(
    time_range: TimeRangeRequestParams  = Depends( get_time_range ),
    limit:      int                     = Query( default=25 )
) -> GeoRequestParams:
    return GeoRequestParams(
        start=time_range.start,
        end=time_range.end,
        limit=limit
    )

async def get_anomalies_params(
    time_range: TimeRangeRequestParams = Depends( get_time_range ),
    min_score:  float                  = Query( default=0.5 ),
    limit:      int                    = Query( default=25 ),
    cursor:     str | None             = Query( min_length=1, description="Pointer to the next page of logs, obtained by making a request without a cursor first.", default=None )
) -> AnomaliesRequestParams:
    return AnomaliesRequestParams(
        start=time_range.start,
        end=time_range.end,
        min_score=min_score,
        limit=limit,
        cursor=cursor
    )