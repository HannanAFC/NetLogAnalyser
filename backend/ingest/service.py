from dataclasses import asdict

from api_keys.schemas import APIKeyCacheEntry
from geoip import lookup_country
from ingest.anomaly import _score_batch_heuristics, compute_anomaly_score
from ingest.schemas import (
    IngestBatchRequest,
    IngestBatchResponse,
    IngestEntryError,
    LogEntryCreate,
    LogEntryRow,
)
from models.models import LogEntry
from pydantic import ValidationError
from sqlalchemy import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession


async def insert_log_entries(
    db: AsyncSession,
    rows: list[ dict ],
    validated: list[ tuple[ int, LogEntryCreate ] ],
    errors: list[ IngestEntryError ]
) -> list[ dict ]:

    # attempt to add all the rows at once
    try:
        await db.execute( insert( LogEntry ), rows )
        await db.flush( )
        return rows
    except IntegrityError:
        await db.rollback( )

    # fallback to row by row inserts
    accepted_rows: list[ dict ] = [ ]
    for ( original_index, _ ), row in zip( validated, rows ):
        try:
            async with db.begin_nested( ): # SAVEPOINT
                await db.execute( insert( LogEntry ), [ row ] )
            accepted_rows.append( row )
        except IntegrityError as exc:
            errors.append( IngestEntryError( index=original_index, detail=str( exc.orig ) ) )

    await db.flush()
    return accepted_rows

async def ingest_batch( db: AsyncSession, api_key: APIKeyCacheEntry, payload: IngestBatchRequest ) -> tuple[ IngestBatchResponse, list[ dict ] ]:
    validated:  list[ tuple[ int, LogEntryCreate ] ] = [ ]
    errors:     list[ IngestEntryError ] = [ ]

    for index, raw in enumerate( payload.entries ):
        try:
            entry = LogEntryCreate.model_validate( raw )
        except ValidationError as error:
            errors.append( IngestEntryError( index=index, detail=error.errors( )[ 0 ][ "msg" ] ) )
            continue
        validated.append( ( index, entry ) )

    if len( validated ) == 0:
        return IngestBatchResponse( accepted=0, rejected=len( errors ), errors=errors ), [ ]

    # Building a standard dict here just to fill in the data
    scoring_inputs: list[ dict ] = [ ]
    for index, entry in validated:
        src_country_code, src_geo_status = lookup_country( str( entry.src_ip ) )
        dst_country_code, dst_geo_status = lookup_country( str( entry.dst_ip ) )
        scoring_inputs.append(
        {
            **entry.model_dump( mode="json" ),
            "src_country_code": src_country_code,
            "dst_country_code": dst_country_code,
            "src_geo_status":   src_geo_status,
            "dst_geo_status":   dst_geo_status
        } )

    # Do batch level heuristics first
    batch_extras = _score_batch_heuristics( scoring_inputs )

    # Phase 3: now that score + reasons are knowable, construct the final,
    # immutable row in one shot. Forgetting a required field here is a
    # TypeError raised right now, not a DB-level surprise three lines later.
    rows: list[ dict ] = [ ]
    for ( index, entry ), scoring_input, extras in zip( validated, scoring_inputs, batch_extras ):
        score, results = compute_anomaly_score( scoring_input, extra_results=extras )
        # Only including non zero scores and returning them as dict
        reasons = [
            asdict( r ) for r in sorted(
                ( r for r in results if r.score > 0 ), key=lambda r: r.score, reverse=True
            )
        ]

        row = LogEntryRow(
            api_key_id      = api_key.id,
            user_id         = api_key.user_id,
            anomaly_score   = score,
            anomaly_reasons = reasons,
            **scoring_input,   # entry's own fields + country_code
        )
        rows.append( asdict( row ) )

    accepted_rows = await insert_log_entries( db, rows, validated, errors )
    response = IngestBatchResponse( accepted=len( accepted_rows ), rejected=len( errors ), errors=errors )
    return response, accepted_rows
