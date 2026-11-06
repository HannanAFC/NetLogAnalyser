"""
Adapter for the CIC-IDS2017 "Packet-Fields" subset of `nids-datasets`
(Hugging Face: rdpahalavan/CIC-IDS2017, Packet-Fields/Packet_Fields_File_N.parquet).

Each source row is one captured packet, dissected by scapy into ~260 columns.
Only the columns in `SOURCE_COLUMNS` are used:

    source column         -> entry field / label
    source_ip             -> src_ip
    destination_ip        -> dst_ip
    source_port           -> src_port
    destination_port      -> dst_port
    protocol (+ IP proto) -> protocol         "tcp"/"udp" -> TCP/UDP, ICMP via either column, else OTHER
    IP len                -> packet_size_bytes IPv4 Total Length = IP total length, our definition as is
    TCP flags             -> flags            scapy letters ("PA") -> "PSH,ACK"
    attack_label          -> labels.attack / labels.is_attack   (never in the entry)
    packet_id             -> index (capture order; joins labels back to entries)
    flow_id               -> labels.flow_id

Rows are dropped, with a counted reason, when they can't be a valid API entry:
no IP layer (ARP), unknown TCP flag letters, a flags string longer than the
API's 20-character limit, ports out of range, negative size, or a bad IP.

The subset has no timestamps. `to_log_entries` fills `captured_at` with a
synthetic time that only preserves capture order (epoch + packet_id µs). v1
features don't use time; window features (Phase 7) will need real timestamps.

Reading: the Parquet files are a single huge row group, so always read only
`SOURCE_COLUMNS` (`read_packet_fields` does). Reading every column runs out of memory.
"""
from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from ipaddress import ip_address
from typing import Any

import numpy as np
import pandas as pd

DATASET = "CIC-IDS2017"

SOURCE_COLUMNS: tuple[ str, ... ] = (
    "packet_id", "flow_id",
    "source_ip", "destination_ip", "source_port", "destination_port",
    "protocol", "IP proto", "IP len", "TCP flags",
    "attack_label"
)
OPTIONAL_COLUMNS = frozenset( { "IP proto" } )

BENIGN_LABEL = "BENIGN"

# TCP flags are shortened in the dataset so have map to turn them into standard flags
TCP_FLAG_LETTERS: dict[ str, str ] = {
    "F": "FIN", "S": "SYN", "R": "RST", "P": "PSH", "A": "ACK",
    "U": "URG", "E": "ECE", "C": "CWR", "N": "NS",
}
_FLAG_ORDER = tuple( TCP_FLAG_LETTERS )

# Matches log entry max lenght of model
MAX_FLAGS_LENGTH = 64

# captured_at placeholder: only the order is meaningful (CIC-IDS2017 capture week started Mon 3 July 2017)
CAPTURED_AT = datetime( 2017, 7, 3, tzinfo=UTC )

DROP_NO_IP_LAYER  = "no_ip_layer"
DROP_UNKNOWN_FLAG = "unknown_tcp_flag"
DROP_FLAGS_LENGTH = "flags_too_long"
DROP_BAD_PORT     = "bad_port"
DROP_BAD_SIZE     = "bad_size"
DROP_BAD_IP       = "bad_ip"

ENTRY_COLUMNS: tuple[ str, ... ] = ( "src_ip", "dst_ip", "src_port", "dst_port", "protocol", "packet_size_bytes", "flags" )


@dataclass
class AdaptedPackets:
    entries: pd.DataFrame      # ENTRY_COLUMNS (the API's fields), index = packet_id
    labels:  pd.DataFrame      # flow_id, attack, is_attack; same index as entries
    dropped: dict[ str, int ]  # drop reason -> row count
    total:   int               # rows in

    @property
    def kept( self ) -> int:
        return len( self.entries )


class _InvalidFlags( ValueError ):
    pass


def convert_tcp_flags( letters: str ) -> str:
    """
    Convert shortened TCP flags into useable flags.
    """
    unknown = set( letters ) - set( TCP_FLAG_LETTERS )
    if unknown:
        raise _InvalidFlags( f"unknown TCP flag letter(s): { ''.join( sorted( unknown ) ) }" )
    present = set( letters )
    return ",".join( TCP_FLAG_LETTERS[ letter ] for letter in _FLAG_ORDER if letter in present )


def _map_protocol( frame: pd.DataFrame ) -> pd.Series:
    """
    Map protocols to what is valid for log entry model.
    """
    protocol = frame[ "protocol" ].astype( "string" ).str.strip( ).str.lower( )
    if "IP proto" in frame.columns:
        ip_proto = frame[ "IP proto" ].astype( "string" ).str.strip( ).str.lower( )
    else:
        ip_proto = pd.Series( pd.NA, index=frame.index, dtype="string" )
    is_icmp = ( protocol == "icmp" ).fillna( False ) | ip_proto.isin( [ "icmp", "1" ] ).fillna( False )
    return pd.Series(
        np.select(
            [ ( protocol == "tcp" ).fillna( False ), ( protocol == "udp" ).fillna( False ), is_icmp ],
            [ "TCP", "UDP", "ICMP" ],
            default="OTHER",
        ),
        index=frame.index,
    )


def _valid_ip_mask( values: pd.Series ) -> pd.Series:
    """
    Convert IPs into IP objects if valid.
    """
    cache: dict[ Any, bool ] = { }
    def ok( value: Any ) -> bool:
        if value not in cache:
            try:
                ip_address( str( value ) )
                cache[ value ] = not pd.isna( value )
            except ValueError:
                cache[ value ] = False
        return cache[ value ]
    return values.map( ok ).astype( bool )


def adapt_packet_fields( frame: pd.DataFrame ) -> AdaptedPackets:
    """
    Turn Packet-Fields rows into API entries plus labels.
    Parameters:
        frame (pd.DataFrame): Source rows with at least the required `SOURCE_COLUMNS` (extra columns are ignored).
    Returns:
        adapted (AdaptedPackets): `entries` ready for `featurize_frame` / `score_entries`, `labels` on the
            same index, and counts of dropped rows by reason.
    """
    missing = [ c for c in SOURCE_COLUMNS if c not in OPTIONAL_COLUMNS and c not in frame.columns ]
    if missing:
        raise KeyError( f"frame is missing column(s): { ', '.join( missing ) }" )

    total  = len( frame )
    reason = pd.Series( pd.NA, index=frame.index, dtype="string" )

    def mark( mask: pd.Series, why: str ) -> None:
        reason[ mask & reason.isna( ) ] = why

    size = pd.to_numeric( frame[ "IP len" ], errors="coerce" )
    mark( size.isna( ), DROP_NO_IP_LAYER )

    # Convert each distinct flags value once (there are only a handful)
    raw_flags  = frame[ "TCP flags" ]
    flag_map: dict[ Any, Any ] = { }
    bad_flags: set[ Any ] = set( )
    for value in raw_flags.dropna( ).unique( ):
        try:
            flag_map[ value ] = convert_tcp_flags( str( value ).strip( ) )
        except _InvalidFlags:
            bad_flags.add( value )
    mark( raw_flags.isin( bad_flags ), DROP_UNKNOWN_FLAG )
    # Plain object array with real None for "no flags" (pandas would use NaN, which the API rejects)
    flags = raw_flags.map( flag_map ).to_numpy( dtype=object )
    flags[ pd.isna( flags ) ] = None
    too_long = np.fromiter( ( isinstance( f, str ) and len( f ) > MAX_FLAGS_LENGTH for f in flags ), dtype=bool, count=len( flags ) )
    mark( pd.Series( too_long, index=frame.index ), DROP_FLAGS_LENGTH )

    ports = { name: pd.to_numeric( frame[ name ], errors="coerce" ) for name in ( "source_port", "destination_port" ) }
    for port in ports.values( ):
        mark( port.isna( ) | ( port < 0 ) | ( port > 65535 ) | ( port % 1 != 0 ), DROP_BAD_PORT )

    mark( ( size < 0 ) | ( size % 1 != 0 ), DROP_BAD_SIZE )
    mark( ~_valid_ip_mask( frame[ "source_ip" ] ) | ~_valid_ip_mask( frame[ "destination_ip" ] ), DROP_BAD_IP )

    keep = reason.isna( ).to_numpy( )
    index = pd.Index( pd.to_numeric( frame[ "packet_id" ] ).astype( "int64" ), name="packet_id" )[ keep ]

    entries = pd.DataFrame( {
        "src_ip":            frame[ "source_ip" ].astype( str ).to_numpy( )[ keep ],
        "dst_ip":            frame[ "destination_ip" ].astype( str ).to_numpy( )[ keep ],
        "src_port":          ports[ "source_port" ].to_numpy( )[ keep ].astype( "int64" ),
        "dst_port":          ports[ "destination_port" ].to_numpy( )[ keep ].astype( "int64" ),
        "protocol":          _map_protocol( frame ).to_numpy( )[ keep ],
        "packet_size_bytes": size.to_numpy( )[ keep ].astype( "int64" ),
        # explicit object dtype: pandas 3 would infer its string dtype and turn None into NaN
        "flags":             pd.Series( flags[ keep ], index=index, dtype=object ),
    }, index=index )

    attack = frame[ "attack_label" ].astype( str ).str.strip( ).to_numpy( )[ keep ]
    labels = pd.DataFrame( {
        "flow_id":   pd.to_numeric( frame[ "flow_id" ] ).to_numpy( )[ keep ].astype( "int64" ),
        "attack":    attack,
        "is_attack": ( attack != BENIGN_LABEL ).astype( "int8" ),
    }, index=index )

    dropped = { str( k ): int( v ) for k, v in reason.value_counts( ).items( ) }
    return AdaptedPackets( entries=entries, labels=labels, dropped=dropped, total=total )


def to_log_entries( entries: pd.DataFrame ) -> Iterator[ dict[ str, Any ] ]:
    """
    Create `LogEntryCreate` dicts for the entries.
    """
    for packet_id, row in zip( entries.index, entries.itertuples( index=False ) ):
        yield {
            "src_ip":            row.src_ip,
            "dst_ip":            row.dst_ip,
            "src_port":          int( row.src_port ),
            "dst_port":          int( row.dst_port ),
            "protocol":          row.protocol,
            "packet_size_bytes": int( row.packet_size_bytes ),
            "flags":             row.flags,
            "raw_payload":       { "dataset": DATASET, "packet_id": int( packet_id ) },
            "captured_at":       ( CAPTURED_AT + timedelta( microseconds=int( packet_id ) ) ).isoformat( )
        }


def read_packet_fields( source: Any, columns: tuple[ str, ... ] = SOURCE_COLUMNS ) -> pd.DataFrame:
    """
    Read only the adapter's columns from a Packet-Fields Parquet file.
    """
    try:
        import pyarrow.parquet as pq
    except ImportError as exc:
        raise ImportError( "read_packet_fields needs pyarrow: pip install pyarrow" ) from exc
    parquet = pq.ParquetFile( source )
    present = set( parquet.schema_arrow.names )
    missing = [ c for c in columns if c not in present and c not in OPTIONAL_COLUMNS ]
    if missing:
        raise KeyError( f"file is missing column(s): { ', '.join( missing ) }" )
    return parquet.read( columns=[ c for c in columns if c in present ] ).to_pandas( )
