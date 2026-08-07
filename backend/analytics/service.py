from __future__ import annotations

import hashlib
from uuid import UUID

from analytics.schemas import (
    AnomaliesRequestParams,
    AnomaliesResponse,
    DirectionEnum,
    GeoRequestParams,
    GeoResponse,
    GeoRow,
    ProtocolsPortRow,
    ProtocolsProtocolRow,
    ProtocolsResponse,
    SummaryResponse,
    TimeRangeRequestParams,
    TimeSeriesPoint,
    TimeSeriesRequestParams,
    TimeSeriesResponse,
    TopTalkersMetricEnum,
    TopTalkersRequestParams,
    TopTalkersResponse,
    TopTalkersRow,
)
from config import settings
from logs.schemas import LogEntryPublic
from logs.service import decode_cursor, encode_cursor
from models.models import LogEntry
from redis.asyncio import Redis
from sqlalchemy import case, func, select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession

HIGH_ANOMALY_THRESHOLD = 0.8
TOP_PORTS_LIMIT        = 10

def _cache_key( user_id: UUID, name: str, *parts: str ) -> str:
    """
    Creates cache key for analytics endpoints scoped to a user, provided name and unique indentifiers. Can be used for recreating a key to check for a cached result.
    Parameters:
        user_id (UUID): The ID of the user the key is for.
        name: (str): The name for the usecase.
        parts: (str): Any amount of unique identifiers to make the key more unique, can be used for caching results under specific parameters.
    Returns:
        cache_key (str): The cache key.
    """
    raw = ":".join( str( p ) for p in parts )
    digest = hashlib.sha256( raw.encode( ) ).hexdigest( )[ :16 ]
    return f"analytics:{ user_id }:{ name }:{ digest }"

async def get_summary(
    db:         AsyncSession,
    redis:      Redis,
    user_id:    UUID,
    time_range: TimeRangeRequestParams
) -> SummaryResponse:
    """
    Get the user summary over a given period.
    Parameters:
        db (AsyncSession): Asynchronous database session.
        redis (Redis): Redis client.
        user_id (UUID): The ID of the user to fetch the summary of.
        time_range (TimeRangeRequestParams): Summary params.
    Returns:
        response (SummaryResponse): A response containing the summary.
    """
    cache_key = _cache_key( user_id, "summary", time_range.start.isoformat( ), time_range.end.isoformat( ) )
    cached = await redis.get( cache_key )
    if cached:
        summary = SummaryResponse.model_validate_json( cached )
        return summary

    stmt = (
        select(
            func.count( ).label( "total_packets" ),
            func.count( func.distinct( LogEntry.src_ip ) ).label( "unique_src_ips" ),
            func.count( func.distinct( LogEntry.dst_ip ) ).label( "unique_dst_ips" ),
            func.coalesce( func.avg( LogEntry.anomaly_score ), 0.0 ).label( "avg_anomaly_score" ),
            func.count(
                case( ( LogEntry.anomaly_score >= HIGH_ANOMALY_THRESHOLD, 1 ) )
            ).label( "high_anomaly_count" ),
            func.coalesce( func.sum( LogEntry.packet_size_bytes ), 0 ).label( "total_bytes" ),
        )
        .where(
            LogEntry.user_id == user_id,
            LogEntry.captured_at >= time_range.start,
            LogEntry.captured_at < time_range.end
        )
    )

    result      = await db.execute( stmt )
    summary_row = result.one( )

    summary_response = SummaryResponse(
        start=time_range.start,
        end=time_range.end,
        total_packets=summary_row.total_packets,
        unique_src_ips=summary_row.unique_src_ips,
        unique_dst_ips=summary_row.unique_dst_ips,
        avg_anomaly_score=round( summary_row.avg_anomaly_score, 4 ),
        high_anomaly_count=summary_row.high_anomaly_count,
        total_bytes=summary_row.total_bytes
    )

    await redis.set(
        cache_key,
        summary_response.model_dump_json( ),
        ex=settings.analytics_summary_expire_seconds
    )

    return summary_response

async def get_timeseries(
    db:          AsyncSession,
    redis:       Redis,
    user_id:     UUID,
    timeseries:  TimeSeriesRequestParams
) -> TimeSeriesResponse:
    """
    Get the user timeseries over a given period and bucket.
    Parameters:
        db (AsyncSession): Asynchronous database session.
        redis (Redis): Redis client.
        user_id (UUID): The ID of the user to fetch the timeseries of.
        timeseries (TimeSeriesRequestParams): Timeseries params.
    Returns:
        response (TimeSeriesResponse): A response containing the timeseries.
    """
    cache_key = _cache_key(
        user_id, "timeseries",
        timeseries.start.isoformat( ), timeseries.end.isoformat( ), timeseries.bucket.value
    )

    cached = await redis.get( cache_key )
    if cached:
        timeseries_response = TimeSeriesResponse.model_validate_json( cached )
        return timeseries_response

    bucket_expr = func.date_trunc( timeseries.bucket.value, LogEntry.captured_at ).label( "bucket" )

    stmt = (
        select(
            bucket_expr,
            func.count( ).label( "log_count" ),
            func.coalesce( func.avg( LogEntry.anomaly_score ), 0.0 ).label( "avg_anomaly_score" ),
            func.coalesce( func.sum( LogEntry.packet_size_bytes ), 0 ).label( "total_bytes" ),
        )
        .where(
            LogEntry.user_id == user_id,
            LogEntry.captured_at >= timeseries.start,
            LogEntry.captured_at < timeseries.end
        )
        .group_by( bucket_expr )
        .order_by( bucket_expr )
    )

    result = await db.execute( stmt )
    time_series_rows = result.all( )

    points = [
        TimeSeriesPoint(
            ts                = row.bucket,
            count             = row.log_count,
            avg_anomaly_score = round( row.avg_anomaly_score, 4 ),
            total_bytes       = row.total_bytes,
        )
        for row in time_series_rows
    ]

    response = TimeSeriesResponse(
        bucket = timeseries.bucket,
        points = points
    )

    await redis.set(
        cache_key,
        response.model_dump_json( ),
        ex = settings.analytics_summary_expire_seconds
    )

    return response

async def get_top_talkers(
    db:      AsyncSession,
    user_id: UUID,
    params:  TopTalkersRequestParams
) -> TopTalkersResponse:
    """
    Get the user top-talkers over a given period and filter by direction and sort by metric.
    Parameters:
        db (AsyncSession): Asynchronous database session.
        user_id (UUID): The ID of the user to fetch the top-talkers of.
        params (TopTalkersRequestParams): Top-talkers params.
    Returns:
        response (TopTalkersResponse): A response containing the top-talkers.
    """
    ip_column = LogEntry.src_ip if params.direction == DirectionEnum.src else LogEntry.dst_ip
    count_expr = func.count().label( "log_count" )
    bytes_expr = func.coalesce( func.sum( LogEntry.packet_size_bytes ), 0 ).label( "total_bytes" )
    order_expr = count_expr if params.metric == TopTalkersMetricEnum.packets else bytes_expr
    
    stmt = (
        select(
            ip_column.label( "ip" ),
            count_expr,
            bytes_expr,
            func.coalesce( func.avg( LogEntry.anomaly_score ), 0.0 ).label( "avg_anomaly_score" ),
        )
        .where(
            LogEntry.user_id == user_id,
            LogEntry.captured_at >= params.start,
            LogEntry.captured_at < params.end,
        )
        .group_by( ip_column )
        .order_by( order_expr.desc( ) )
        .limit( params.limit )
    )

    result           = await db.execute( stmt )
    top_talkers_rows = result.all( )

    rows = [
        TopTalkersRow(
            ip=row.ip,
            count=row.log_count,
            total_bytes=row.total_bytes,
            avg_anomaly_score=round( row.avg_anomaly_score, 4 )
        )
        for row in top_talkers_rows
    ]

    return TopTalkersResponse(
        direction=params.direction,
        metric=params.metric,
        rows=rows
    )

async def get_protocols(
    db:         AsyncSession,
    user_id:    UUID,
    time_range: TimeRangeRequestParams
) -> ProtocolsResponse:
    """
    Get the user protocol metrics over a given period.
    Parameters:
        db (AsyncSession): Asynchronous database session.
        user_id (UUID): The ID of the user to fetch the protocol metrics of.
        params (TimeRangeRequestParams): Protocols params.
    Returns:
        response (ProtocolsResponse): A response containing the protocol metrics.
    """
    base_filter = (
        LogEntry.user_id == user_id,
        LogEntry.captured_at >= time_range.start,
        LogEntry.captured_at < time_range.end
    )

    total_expr = func.sum( func.count( ) ).over( ).label( "total" )

    protocol_stmt = (
        select(
            LogEntry.protocol,
            func.count( ).label( "log_count" ),
            total_expr
        )
        .where( *base_filter )
        .group_by( LogEntry.protocol )
        .order_by( func.count( ).desc( ) )
    )

    protocol_result = await db.execute( protocol_stmt )
    protocol_rows   = protocol_result.all( )

    total = protocol_rows[ 0 ].total if protocol_rows else 0

    by_protocol = [
        ProtocolsProtocolRow(
            protocol=row.protocol,
            count=row.log_count,
            packet_percentage=round( ( row.log_count / total ) * 100, 1 ) if total else 0.0
        )
        for row in protocol_rows
    ]

    port_stmt = (
        select(
            LogEntry.dst_port,
            func.count( ).label( "log_count" )
        )
        .where( *base_filter )
        .group_by( LogEntry.dst_port )
        .order_by( func.count( ).desc( ) )
        .limit( TOP_PORTS_LIMIT )
    )

    port_results = await db.execute( port_stmt )
    port_rows    = port_results.all( )

    top_dst_ports = [
        ProtocolsPortRow(
            port=row.dst_port,
            count=row.log_count
        )
        for row in port_rows
    ]

    return ProtocolsResponse(
        by_protocol=by_protocol,
        top_dst_ports=top_dst_ports
    )

async def get_geo(
    db:      AsyncSession,
    user_id: UUID,
    params:  GeoRequestParams
) -> GeoResponse:
    """
    Get the user geo metrics over a given period.
    Parameters:
        db (AsyncSession): Asynchronous database session.
        user_id (UUID): The ID of the user to fetch the geo metrics of.
        params (GeoRequestParams): Geo params.
    Returns:
        response (GeoResponse): A response containing the geo metrics.
    """
    country_column = getattr( LogEntry, f"{ params.direction.value }_country_code" )
    status_column  = getattr( LogEntry, f"{ params.direction.value }_geo_status" )

    total_expr = func.sum( func.count( ) ).over( ).label( "total" )

    stmt = (
        select(
            country_column.label( "country_code" ),
            status_column.label( "geo_status" ),
            func.count( ).label( "log_count" ),
            total_expr
            )
        .where(
            LogEntry.user_id == user_id,
            LogEntry.captured_at >= params.start,
            LogEntry.captured_at < params.end
        )
        .group_by( country_column, status_column )
        .order_by( func.count( ).desc( ) )
        .limit( params.limit )
    )

    results  = await db.execute( stmt )
    geo_rows = results.all( )

    total = geo_rows[ 0 ].total if geo_rows else 0

    rows = [
        GeoRow(
            country_code=row.country_code,
            geo_status=row.geo_status,
            count=row.log_count,
            packet_percentage=round( ( row.log_count / total ) * 100, 1 ) if total else 0.0
        )
        for row in geo_rows
    ]

    return GeoResponse(
        direction=params.direction,
        rows=rows
    )

async def get_anomalies(
    db: AsyncSession,
    user_id: UUID,
    params: AnomaliesRequestParams
) -> AnomaliesResponse:
    """
    Get the user anomaly metrics over a given period.
    Parameters:
        db (AsyncSession): Asynchronous database session.
        user_id (UUID): The ID of the user to fetch the anomaly metrics of.
        params (AnomaliesRequestParams): Anomaly params.
    Returns:
        response (AnomaliesResponse): A response containing the anomaly metrics.
    """
    query =  (
        select( LogEntry )
        .where(
            LogEntry.user_id == user_id,
            LogEntry.captured_at >= params.start,
            LogEntry.captured_at < params.end,
            LogEntry.anomaly_score >= params.min_score
        )
        .order_by(
            LogEntry.captured_at.desc( ),
            LogEntry.id.desc( )
        )
    )

    if params.cursor:
        cursor_data = decode_cursor( params.cursor )
        query = query.filter(
            tuple_( LogEntry.captured_at, LogEntry.id ) < tuple_( cursor_data.captured_at, cursor_data.id ) # pyright: ignore[reportArgumentType]
        )

    query     = query.limit( params.limit + 1 )
    results   = await db.execute( query )
    logs_rows = results.scalars( ).all( )

    has_more = len( logs_rows ) > params.limit
    
    if has_more:
        logs_rows = logs_rows[ :params.limit ]

    next_cursor = None

    if has_more and logs_rows:
        last_log_row = logs_rows[ -1 ]
        next_cursor = encode_cursor( last_log_row.id, last_log_row.captured_at )

    return AnomaliesResponse(
        rows=[ LogEntryPublic.model_validate( row ) for row in logs_rows ],
        next_cursor=next_cursor,
        has_more=has_more
    )