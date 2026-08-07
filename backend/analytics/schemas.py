from __future__ import annotations

from datetime import datetime
from enum import Enum
from ipaddress import IPv4Address, IPv6Address

from geoip import GeoStatus
from ingest.schemas import ProtocolEnum
from logs.schemas import LogEntryPublic
from pydantic import BaseModel, ConfigDict, Field


class TimeBucketEnum( str, Enum ):
    minute  = "minute"
    hour    = "hour"
    day     = "day"

class DirectionEnum( str, Enum ):
    src     = "src"
    dst     = "dst"

class TopTalkersMetricEnum( str, Enum ):
    packets = "packets"
    bytes   = "bytes"

class TimeRangeRequestParams( BaseModel ):
    model_config       = ConfigDict( frozen=True )

    start:             datetime
    end:               datetime

class SummaryResponse( BaseModel ):
    model_config        = ConfigDict( from_attributes=True )

    start:              datetime
    end:                datetime
    total_packets:      int   = Field( ge=0 )
    unique_src_ips:     int   = Field( ge=0 )
    unique_dst_ips:     int   = Field( ge=0 )
    avg_anomaly_score:  float = Field( ge=0.0, le=1.0 )
    high_anomaly_count: int   = Field( ge=0 )
    total_bytes:        int   = Field( ge=0 )

class TimeSeriesRequestParams( TimeRangeRequestParams ):
    model_config       = ConfigDict( frozen=True )

    bucket:             TimeBucketEnum

class TimeSeriesPoint( BaseModel ):
    model_config        = ConfigDict( from_attributes=True )

    ts:                 datetime
    count:              int   = Field( ge=0 )
    avg_anomaly_score:  float = Field( ge=0.0, le=1.0 )
    total_bytes:        int   = Field( ge=0 )

class TimeSeriesResponse( BaseModel ):
    model_config        = ConfigDict( from_attributes=True )

    bucket:             TimeBucketEnum
    points:             list[ TimeSeriesPoint ]

class TopTalkersRow( BaseModel ):
    model_config        = ConfigDict( from_attributes=True )

    ip:                 IPv4Address | IPv6Address
    count:              int   = Field( ge=0 )
    avg_anomaly_score:  float = Field( ge=0.0, le=1.0 )
    total_bytes:        int   = Field( ge=0 )

class TopTalkersRequestParams( TimeRangeRequestParams ):
    model_config       = ConfigDict( frozen=True )

    direction:          DirectionEnum
    metric:             TopTalkersMetricEnum
    limit:              int = Field( ge=1, le=100, default=10 )

class TopTalkersResponse( BaseModel ):
    model_config        = ConfigDict( from_attributes=True )

    direction:          DirectionEnum
    metric:             TopTalkersMetricEnum
    rows:               list[ TopTalkersRow ]

class ProtocolsProtocolRow( BaseModel ):
    model_config        = ConfigDict( from_attributes=True )

    protocol:           ProtocolEnum
    count:              int   = Field( ge=0 )
    packet_percentage:  float = Field( ge=0.0, le=100.0 )

class ProtocolsPortRow( BaseModel ):
    model_config        = ConfigDict( from_attributes=True )

    port:               int = Field( ge=0 )
    count:              int = Field( ge=0 )

class ProtocolsResponse( BaseModel ):
    model_config        = ConfigDict( from_attributes=True )

    by_protocol:        list[ ProtocolsProtocolRow ]
    top_dst_ports:      list[ ProtocolsPortRow ]

class GeoRequestParams( TimeRangeRequestParams ):
    model_config       = ConfigDict( frozen=True )
    
    limit:              int = Field( ge=1, le=50, default=25 )
    direction:          DirectionEnum

class GeoRow( BaseModel ):
    model_config        = ConfigDict( from_attributes=True )
    
    country_code:       str | None
    geo_status:         GeoStatus
    count:              int   = Field( ge=0 )
    packet_percentage:  float = Field( ge=0.0, le=100.0 )

class GeoResponse( BaseModel ):
    model_config        = ConfigDict( from_attributes=True )
    rows:               list[ GeoRow ]
    direction:          DirectionEnum

class AnomaliesRequestParams( TimeRangeRequestParams ):
    model_config       = ConfigDict( frozen=True )
    
    min_score:          float      = Field( ge=0.0, le=1.0, default=0.5 )
    limit:              int        = Field( ge=1, le=100, default=25 )
    cursor:             str | None = None

class AnomaliesResponse( BaseModel ):
    model_config        = ConfigDict( from_attributes=True )
    
    rows:               list[ LogEntryPublic ]
    next_cursor:        str | None
    has_more:           bool