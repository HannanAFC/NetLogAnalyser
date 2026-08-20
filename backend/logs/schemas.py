from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from ipaddress import IPv4Address, IPv6Address

from geoip import GeoStatus
from pydantic import BaseModel, ConfigDict


class LogEntryPublic( BaseModel ):
    model_config = ConfigDict( from_attributes=True )

    id:                int
    src_ip:            IPv4Address | IPv6Address
    dst_ip:            IPv4Address | IPv6Address
    src_port:          int
    dst_port:          int
    protocol:          str
    packet_size_bytes: int
    flags:             str | None
    src_country_code:  str | None
    dst_country_code:  str | None
    src_geo_status:    GeoStatus
    dst_geo_status:    GeoStatus
    anomaly_score:     float
    anomaly_reasons:   list[ dict ]
    captured_at:       datetime

class GetLogsResponse( BaseModel ):
    entries:           list[ LogEntryPublic ]
    next_cursor:       str | None
    has_more:          bool

@dataclass
class CursorData:
    id:                int
    captured_at:       datetime
