from ipaddress import IPv4Address, IPv6Address

from api_keys.schemas import APIKeyCacheEntry
from geoip import resolve_log_country
from ingest.schemas import (
    IngestBatchRequest,
    IngestBatchResponse,
    IngestEntryError,
    LogEntryCreate,
)
from models.models import LogEntry
from pydantic import ValidationError
from sqlalchemy import insert
from sqlalchemy.exc import DataError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession


def lookup_country( src_ip: IPv4Address | IPv6Address, dst_ip: IPv4Address | IPv6Address ) -> str | None:
    return resolve_log_country( str( src_ip ), str( dst_ip ) )

def compute_anomaly_score( log_entry: LogEntryCreate ) -> float:
    return 0

async def insert_log_entries(
    db: AsyncSession,
    rows: list[ dict ],
    validated: list[ tuple[ int, LogEntryCreate ] ],
    errors: list[ IngestEntryError ]
) -> int:

    # attempt to add all the rows at once
    try:
        await db.execute( insert( LogEntry ), rows )
        await db.flush( )
        return len( rows )
    except ( IntegrityError, DataError ):
        await db.rollback( )

    # fallback to row by row inserts
    accepted = 0
    for ( original_index, log_entry ), row in zip( validated, rows ):
        try:
            async with db.begin_nested( ): # SAVEPOINT
                await db.execute( insert( LogEntry ), [ row ] )
            accepted += 1
        except ( IntegrityError, DataError ) as exc:
            errors.append( IngestEntryError( index=original_index, detail=str( exc.orig ) ) )

    await db.flush()
    return accepted

async def ingest_batch( db: AsyncSession, api_key: APIKeyCacheEntry, payload: IngestBatchRequest ) -> IngestBatchResponse:
    validated:  list[ tuple[ int, LogEntryCreate ] ] = [ ]
    errors:     list[ IngestEntryError ] = [ ]

    for index, raw in enumerate( payload.entries ):
        try:
            entry = LogEntryCreate.model_validate( raw )
        except ValidationError as error:
            errors.append( IngestEntryError( index=index, detail=error.errors( )[ 0 ][ "msg" ] ) )
            continue
        except DataError as error:
            errors.append( IngestEntryError( index=index, detail=error._message( ) ) )
            continue
        validated.append( ( index, entry ) )

    if len( validated ) == 0:
        return IngestBatchResponse( accepted=0, rejected=len( errors ), errors=errors )

    rows = [ ]

    for index, entry in validated:
        rows.append(
        {
            **entry.model_dump( mode="json" ),
            "api_key_id":    api_key.id,
            "user_id":       api_key.user_id,
            "country_code":  lookup_country( entry.src_ip, entry.dst_ip ),
            "anomaly_score": compute_anomaly_score( entry )
        })

    accepted = await insert_log_entries( db, rows, validated, errors )
    return IngestBatchResponse( accepted=accepted, rejected=len( errors ), errors=errors )