"""
Sync test: every entry the CIC-IDS2017 adapter produces must be accepted by the
real ingest schema. If LogEntryCreate changes, this fails before training data drifts.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest
from nla_ml.adapters.cicids2017_packets import (
    ENTRY_COLUMNS,
    MAX_FLAGS_LENGTH,
    adapt_packet_fields,
    to_log_entries,
)

from ingest.schemas import LogEntryCreate, ProtocolEnum

FIXTURE = Path( __file__ ).parents[ 1 ] / "ml" / "tests" / "fixtures" / "cicids2017_packet_fields_sample.json"


@pytest.fixture( scope="module" )
def adapted( ):
    frame = pd.DataFrame( json.loads( FIXTURE.read_text( ) )[ "rows" ] )
    frame[ "IP len" ] = frame[ "IP len" ].astype( "Int64" )
    return adapt_packet_fields( frame )

def test_every_adapted_entry_validates( adapted ):
    entries = list( to_log_entries( adapted.entries ) )
    assert entries
    for entry in entries:
        LogEntryCreate.model_validate( entry )  # raises on any mismatch (extra="forbid" included)

def test_entry_columns_are_api_fields( ):
    assert set( ENTRY_COLUMNS ) <= set( LogEntryCreate.model_fields )

def test_flags_limit_matches_the_schema( ):
    limits = [ m.max_length for m in LogEntryCreate.model_fields[ "flags" ].metadata if hasattr( m, "max_length" ) ]
    assert limits == [ MAX_FLAGS_LENGTH ]

def test_adapter_protocols_are_api_protocols( adapted ):
    assert set( adapted.entries[ "protocol" ] ) <= { p.value for p in ProtocolEnum }
