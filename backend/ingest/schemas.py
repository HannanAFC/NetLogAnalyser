from __future__ import annotations

from datetime import datetime
from ipaddress import IPv4Address, IPv6Address
from typing import Any, Literal

from config import settings
from pydantic import BaseModel, ConfigDict, Field

Protocol = Literal[ "TCP", "UDP", "ICMP", "OTHER" ]

# forbid extra entries so that users can't spoof by adding in anomaly_score etc
class LogEntryCreate( BaseModel ):
    model_config = ConfigDict( extra="forbid" )

    src_ip:            IPv4Address | IPv6Address
    dst_ip:            IPv4Address | IPv6Address
    src_port:          int = Field( ge=0, le=65535 )
    dst_port:          int = Field( ge=0, le=65535 )
    protocol: Protocol
    packet_size_bytes: int = Field( ge=0 )
    flags:             str | None = Field( default=None, max_length=20 )
    raw_payload:       dict
    captured_at:       datetime

class IngestBatchRequest( BaseModel ):
    entries: list[ dict[ str, Any ] ] = Field(
        min_length=1,
        max_length=settings.ingest_max_batch_size
    )

class IngestEntryError( BaseModel ):
    index:  int
    detail: str


class IngestBatchResponse( BaseModel ):
    accepted: int
    rejected: int
    errors:   list[ IngestEntryError ] = Field( default_factory=list )
