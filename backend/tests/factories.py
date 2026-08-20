from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from geoip import GeoStatus
from models.models import LogEntry
from sqlalchemy.ext.asyncio import AsyncSession

_DEFAULT_CAPTURED_AT = datetime( 2026, 8, 1, 12, 0, 0, tzinfo=timezone.utc )

# Making this file now for reusable helpers and utilities, need to go back to old tests and
# move common helpers into here as they're currently repeated.

async def make_log_entry(
    db: AsyncSession,
    *,
    user_id:           UUID,
    api_key_id:        UUID,
    src_ip:            str        = "10.0.0.1",
    dst_ip:            str        = "10.0.0.2",
    src_port:          int        = 51000,
    dst_port:          int        = 443,
    protocol:          str        = "TCP",
    packet_size_bytes: int        = 512,
    anomaly_score:     float      = 0.1,
    dst_country_code:  str | None = "US",
    src_country_code:  str | None = None,
    src_geo_status:    GeoStatus  = GeoStatus.PRIVATE,
    dst_geo_status:    GeoStatus  = GeoStatus.RESOLVED,
    captured_at:       datetime   = _DEFAULT_CAPTURED_AT,
    flags:             str | None = None,
) -> LogEntry:
    entry = LogEntry(
        user_id           = user_id,
        api_key_id        = api_key_id,
        src_ip            = src_ip,
        dst_ip            = dst_ip,
        src_port          = src_port,
        dst_port          = dst_port,
        protocol          = protocol,
        packet_size_bytes = packet_size_bytes,
        anomaly_score     = anomaly_score,
        src_country_code  = src_country_code,
        dst_country_code  = dst_country_code,
        src_geo_status    = src_geo_status,
        dst_geo_status    = dst_geo_status,
        captured_at       = captured_at,
        raw_payload       = {},
        flags             = flags,
    )
    db.add( entry )
    await db.flush( )
    return entry


async def make_log_entries( db: AsyncSession, *, count: int, **overrides ) -> list[ LogEntry ]:
    """
    Bulk make log entries and add them to the db, not committed.
    """
    entries = [
        LogEntry(
            user_id           = overrides[ "user_id" ],
            api_key_id        = overrides[ "api_key_id" ],
            src_ip            = overrides.get( "src_ip", "10.0.0.1" ),
            dst_ip            = overrides.get( "dst_ip", "10.0.0.2" ),
            src_port          = overrides.get( "src_port", 51000 ),
            dst_port          = overrides.get( "dst_port", 443 ),
            protocol          = overrides.get( "protocol", "TCP" ),
            packet_size_bytes = overrides.get( "packet_size_bytes", 512 ),
            anomaly_score     = overrides.get( "anomaly_score", 0.1 ),
            src_country_code  = overrides.get( "src_country_code", None ),
            dst_country_code  = overrides.get( "dst_country_code", "US" ),
            src_geo_status    = overrides.get( "src_geo_status", "PRIVATE" ),
            dst_geo_status    = overrides.get( "dst_geo_status", "RESOLVED" ),
            captured_at       = overrides.get( "captured_at", _DEFAULT_CAPTURED_AT ),
            raw_payload       = {},
        )
        for _ in range( count )
    ]
    db.add_all( entries )
    await db.flush( )
    return entries