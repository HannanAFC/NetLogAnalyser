from __future__ import annotations

from typing import Annotated

from api_keys.service import verify_api_key
from cache import get_redis
from database import get_db
from fastapi import APIRouter, Depends, Response, Security, status
from fastapi.security import APIKeyHeader
from ingest.schemas import IngestBatchRequest, IngestBatchResponse
from ingest.service import ingest_batch
from rate_limiter import get_ingest_rate_limiter
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter( dependencies=[ Depends( get_ingest_rate_limiter ) ] )
api_key_header = APIKeyHeader( name="X-API-Key" )


@router.post( "", response_model=IngestBatchResponse, status_code=status.HTTP_207_MULTI_STATUS )
async def ingest(
    payload: IngestBatchRequest,
    db:      Annotated[ AsyncSession, Depends( get_db ) ],
    redis:   Annotated[ Redis, Depends( get_redis ) ],
    raw_key: Annotated[ str, Security( api_key_header ) ],
    response: Response
) -> IngestBatchResponse:
    """
    Ingest - send logs to this endpoint with the X-API-KEY header, logs must be submitted as an array with a maximum of 50 logs.
    Logs must be submitted in this format:
    \n\t{
        \n\t\t"src_ip": "192.168.1.1",
        \n\t\t"dst_ip": "10.0.0.1",
        \n\t\t"src_port": 52341,
        \n\t\t"dst_port": 443,
        \n\t\t"protocol": "TCP",
        \n\t\t"packet_size_bytes": 120,
        \n\t\t"flags": "Optional",
        \n\t\t"raw_payload": {
            \n\t\t\t"prop": "value"
        \n\t\t},
        \n\t\t"captured_at": "2026-07-28T00:34:02.735Z"
    \n\t}
    """
    api_key = await verify_api_key( db, redis, raw_key )
    ingest_response = await ingest_batch( db, api_key, payload )
    await db.commit( )

    if ingest_response.accepted == 0:
        response.status_code = status.HTTP_422_UNPROCESSABLE_CONTENT
    return ingest_response