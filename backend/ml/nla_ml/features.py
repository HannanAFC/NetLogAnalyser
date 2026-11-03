"""
Extract features from both log entries and datasets, remove all other
features that aren't present in ingest entries.

Versioning
----------
`FEATURE_VERSION` is bumped by hand on any change to what `featurize` outputs.
`FEATURE_FINGERPRINT` is a hash of the feature definition (columns, inputs, the
lookup tables the features depend on, and how this Python's `is_private`
answers a fixed probe set). A test pins the fingerprint for each version, so
changing a table or column without bumping the version fails CI, and a Python
whose `is_private` behaves differently gets a different fingerprint.
Behaviour changes that the hash can't see are caught by the golden fixture test.
"""
from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Iterable, Mapping
from typing import Any

import numpy as np
import pandas as pd

from nla_ml.addresses import is_private_ip, is_private_probe
from nla_ml.flags import TCP_FLAGS, parse_flags
from nla_ml.ports import (
    PORT_MAX,
    PORT_PROTOCOL_EXPECTATIONS,
    REGISTERED_PORT_MAX,
    WELL_KNOWN_PORT_MAX,
    is_well_known_port,
    port_bucket
)

FEATURE_VERSION = 1

# The entry fields featurize reads. Each one must exist on the ingest API's
# `LogEntryCreate` schema (checked by a backend test).
INPUT_FIELDS: tuple[ str, ... ] = (
    "src_ip",
    "dst_ip",
    "src_port",
    "dst_port",
    "protocol",
    "packet_size_bytes",
    "flags"
)
_REQUIRED_FIELDS = tuple( f for f in INPUT_FIELDS if f != "flags" )

PROTOCOLS: tuple[ str, ... ] = ( "TCP", "UDP", "ICMP", "OTHER" )

FEATURE_COLUMNS: tuple[ str, ... ] = (
    "dst_port",
    "dst_port_well_known",
    "dst_port_in_expectations",
    "src_port_bucket",
    *( f"proto_{ p }" for p in PROTOCOLS ),
    "packet_size_bytes",
    *( f"flag_{ f }" for f in TCP_FLAGS ),
    "flag_count",
    "flags_present",
    "src_is_private",
    "dst_is_private"
)

FEATURE_DTYPE = np.int64

PACKET_SIZE_DEFINITION = "ip_total_length"

def _definition( ) -> dict[ str, Any ]:
    return {
        "feature_version":  FEATURE_VERSION,
        "feature_columns":  list( FEATURE_COLUMNS ),
        "input_fields":     list( INPUT_FIELDS ),
        "protocols":        list( PROTOCOLS ),
        "tcp_flags":        list( TCP_FLAGS ),
        "port_bounds":      [ WELL_KNOWN_PORT_MAX, REGISTERED_PORT_MAX, PORT_MAX ],
        "port_expectations": { str( p ): sorted( v ) for p, v in sorted( PORT_PROTOCOL_EXPECTATIONS.items( ) ) },
        "packet_size":      PACKET_SIZE_DEFINITION,
        "is_private_probe": is_private_probe( ),  # interpreter-dependent on purpose
        "dtype":            np.dtype( FEATURE_DTYPE ).name,
    }

def _fingerprint( ) -> str:
    return hashlib.sha256(
        json.dumps( _definition( ), sort_keys=True, separators=( ",", ":" ) ).encode( )
    ).hexdigest( )[ :16 ]

FEATURE_FINGERPRINT: str = _fingerprint( )

def _int_field( entry: Mapping[ str, Any ], name: str, low: int, high: int | None ) -> int:
    value = entry[ name ]
    if isinstance( value, bool ) or not isinstance( value, ( int, np.integer ) ):
        # Accept integral floats (pandas upcasts int columns with NaNs to float)
        if isinstance( value, ( float, np.floating ) ) and math.isfinite( value ) and float( value ).is_integer( ):
            value = int( value )
        else:
            raise TypeError( f"{ name } must be an integer, got { value!r}" )
    value = int( value )
    if value < low or ( high is not None and value > high ):
        raise ValueError( f"{ name } out of range: { value }" )
    return value

def _protocol( value: Any ) -> str:
    # Accept plain strings and str-Enums (e.g. ProtocolEnum.TCP)
    protocol = str( getattr( value, "value", value ) ).strip( ).upper( )
    if protocol not in PROTOCOLS:
        raise ValueError( f"protocol must be one of { ', '.join( PROTOCOLS ) }, got { value!r}" )
    return protocol

def _flags( value: Any ) -> str | None:
    if value is None:
        return None
    if isinstance( value, float ) and math.isnan( value ):  # missing value in a DataFrame
        return None
    if not isinstance( value, str ):
        raise TypeError( f"flags must be a string or None, got { value!r}" )
    return value

def featurize_entry( entry: dict[ Any, Any ] ) -> tuple[ int, ... ]:
    """
    Compute the feature row for one entry.
    Parameters:
        entry (Mapping): A log entry with at least the `INPUT_FIELDS` keys (`flags` may be missing).
    Returns:
        row (tuple[int, ...]): Feature values in `FEATURE_COLUMNS` order.
    Raises:
        KeyError: If a required field is missing.
        TypeError: If a field has the wrong type.
        ValueError: If a field has an invalid value.
    """
    missing = [ f for f in _REQUIRED_FIELDS if f not in entry ]
    if missing:
        raise KeyError( f"entry is missing required field(s): { ', '.join( missing ) }" )

    src_port = _int_field( entry, "src_port", 0, PORT_MAX )
    dst_port = _int_field( entry, "dst_port", 0, PORT_MAX )
    size     = _int_field( entry, "packet_size_bytes", 0, None )
    protocol = _protocol( entry[ "protocol" ] )
    flags    = parse_flags( _flags( entry.get( "flags" ) ) )
    present  = flags if flags is not None else set( )

    return (
        dst_port,
        int( is_well_known_port( dst_port ) ),
        int( dst_port in PORT_PROTOCOL_EXPECTATIONS ),
        int( port_bucket( src_port ) ),
        *( int( protocol == p ) for p in PROTOCOLS ),
        size,
        *( int( f in present ) for f in TCP_FLAGS ),
        len( present ),  # distinct tokens, including flags without their own column (e.g. ECE, CWR)
        int( flags is not None ),
        int( is_private_ip( entry[ "src_ip" ] ) ),
        int( is_private_ip( entry[ "dst_ip" ] ) ),
    )

def featurize( entries: list[ dict[ Any, Any ] ] ) -> pd.DataFrame:
    """
    Turn log entries into the model's feature matrix.
    In the backend, pass the `scoring_inputs` dicts built in `ingest/service.py`.
    In a notebook, pass dataset rows that have been through an adapter.
    Parameters:
        entries (Iterable[Mapping]): Log entries.
    Returns:
        features (pd.DataFrame): One row per entry; columns are exactly `FEATURE_COLUMNS`, in order, all int64.
    Raises:
        ValueError: If any entry is invalid. The message includes the entry's index.
    """
    rows: list[ tuple[ int, ... ] ] = [ ]
    for index, entry in enumerate( entries ):
        try:
            rows.append( featurize_entry( entry ) )
        except ( KeyError, TypeError, ValueError ) as exc:
            raise ValueError( f"entry { index }: { exc.args[ 0 ] if exc.args else exc }" ) from exc

    matrix = np.array( rows, dtype=FEATURE_DTYPE ).reshape( len( rows ), len( FEATURE_COLUMNS ) )
    return pd.DataFrame( matrix, columns=list( FEATURE_COLUMNS ) )

def featurize_frame( frame: pd.DataFrame ) -> pd.DataFrame:
    """
    `featurize` for a DataFrame of entries (the notebook path). Columns other than
    `INPUT_FIELDS` are dropped before featurizing. The output index matches the input's,
    so labels can be joined back on.
    """
    missing = [ f for f in _REQUIRED_FIELDS if f not in frame.columns ]
    if missing:
        raise KeyError( f"frame is missing required column(s): { ', '.join( missing ) }" )
    columns  = [ f for f in INPUT_FIELDS if f in frame.columns ]
    features = featurize( frame[ columns ].to_dict( orient="records" ) )
    features.index = frame.index
    return features
