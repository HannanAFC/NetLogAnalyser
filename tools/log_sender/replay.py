"""Read log entries from a file for replay against the ingest endpoint.

Supports CSV (header row required), JSON (a list of objects), and JSONL
(one JSON object per line). A `field_map` lets you point this at exports
from real capture tools that use different column names, e.g.:

    {"source_ip": "src_ip", "sport": "src_port", "dport": "dst_port"}
"""
from __future__ import annotations

import csv
import json
from collections.abc import Iterator
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config import PROTOCOLS

REQUIRED_FIELDS = (
    "src_ip", "dst_ip", "src_port", "dst_port",
    "protocol", "packet_size_bytes", "captured_at",
)

# The backend's `protocol` column is a 4-value enum (TCP/UDP/ICMP/OTHER), but
# real-world exports (e.g. CICIDS2017, CICFlowMeter output generally) often
# report the raw IANA protocol number instead of a name. Only the numbers
# that map onto our enum are translated; anything else falls through to
# OTHER. Full registry: https://www.iana.org/assignments/protocol-numbers/
_IANA_NUMBER_TO_ENUM = {
    "1":  "ICMP",
    "6":  "TCP",
    "17": "UDP",
}


def _normalise_protocol( value: Any ) -> str:
    text = str( value ).strip()
    if text.upper( ) in PROTOCOLS:
        return text.upper( )
    return _IANA_NUMBER_TO_ENUM.get( text, "OTHER" )

 
def _to_int( value: Any ) -> int:
    """Coerce a value to int, tolerating float-formatted strings.
 
    CICFlowMeter-derived CSVs (CICIDS2017 and similar) export every numeric
    column as float64, so a destination port shows up as "80.0" rather than
    "80". `int("80.0")` raises ValueError, so go through float() first.
    """
    return int( float( value ) )

def _coerce_row( raw: dict[ str, Any ], field_map: dict[ str, str ] | None ) -> dict[ str, Any ]:
    if field_map:
        raw = { field_map.get( k, k ): v for k, v in raw.items( ) }

    try:
        original_protocol = raw[ "protocol" ]
        entry: dict[ str, Any ] = {
            "src_ip":            raw[ "src_ip" ],
            "dst_ip":            raw[ "dst_ip" ],
            "src_port":          _to_int( raw[ "src_port" ] ),
            "dst_port":          _to_int( raw[ "dst_port" ] ),
            "protocol":          _normalise_protocol( original_protocol ),
            "packet_size_bytes": _to_int( raw[ "packet_size_bytes" ] )
        }
    except KeyError as exc:
        raise ValueError( f"Row missing required field: { exc }" ) from exc

    captured_at = raw.get( "captured_at" )
    entry[ "captured_at" ] = captured_at if captured_at not in ( None, "" ) else datetime.now( timezone.utc ).isoformat()

    flags = raw.get( "flags" )
    if flags not in ( None, "" ):
        entry[ "flags" ] = str( flags )[ :20 ]

    raw_payload = raw.get( "raw_payload" )
    if isinstance( raw_payload, str ):
        try:
            raw_payload = json.loads( raw_payload )
        except json.JSONDecodeError:
            raw_payload = { "raw": raw_payload }
    entry[ "raw_payload" ] = raw_payload if isinstance( raw_payload, dict ) else { "source": "replay" }

    # Preserve the original, untranslated protocol value so nothing is lost
    # when it gets bucketed into the coarse TCP/UDP/ICMP/OTHER enum.
    entry[ "raw_payload" ].setdefault( "source_protocol", original_protocol )

    return entry


def read_entries( path: str | Path, field_map: dict[ str, str ] | None = None ) -> Iterator[ dict[ str, Any ] ]:
    path = Path( path )
    suffix = path.suffix.lower( )

    if suffix == ".csv":
        with path.open( newline="", encoding="utf-8" ) as f:
            for row in csv.DictReader( f ):
                yield _coerce_row( row, field_map )

    elif suffix in ( ".json", ".jsonl" ):
        text = path.read_text( encoding="utf-8" ).strip( )
        if text.startswith( "[" ):
            for row in json.loads( text ):
                yield _coerce_row( row, field_map )
        else:
            for line in text.splitlines():
                line = line.strip()
                if line:
                    yield _coerce_row( json.loads( line ), field_map )

    else:
        raise ValueError( f"Unsupported replay file type: { path.suffix } (use .csv, .json, or .jsonl)" )
