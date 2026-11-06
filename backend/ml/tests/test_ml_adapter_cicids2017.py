"""
Tests for the CIC-IDS2017 Packet-Fields adapter against a fixture of real rows
(Packet_Fields_File_3) plus marked synthetic edge cases. The backend validates
the adapter's output with the real LogEntryCreate in tests/test_ml_adapter.py.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from nla_ml.adapters.cicids2017_packets import (
    ENTRY_COLUMNS,
    MAX_FLAGS_LENGTH,
    SOURCE_COLUMNS,
    adapt_packet_fields,
    convert_tcp_flags,
    to_log_entries,
)
from nla_ml.features import FEATURE_COLUMNS, INPUT_FIELDS, featurize_frame
from nla_ml.heuristics import score_entries

FIXTURE = json.loads( ( Path( __file__ ).parent / "fixtures" / "cicids2017_packet_fields_sample.json" ).read_text( ) )


@pytest.fixture
def frame( ) -> pd.DataFrame:
    # Mirror what pyarrow gives for this file: nullable ints for IP len (all-null for ARP rows)
    df = pd.DataFrame( FIXTURE[ "rows" ] )
    df[ "IP len" ] = df[ "IP len" ].astype( "Int64" )
    return df

@pytest.fixture
def adapted( frame ):
    return adapt_packet_fields( frame )


# ---------------------------------------------------------------- against the hand-written expectations

def test_kept_rows_match_expected( adapted ):
    expected = FIXTURE[ "expected" ]
    assert [ str( i ) for i in adapted.entries.index ] == list( expected )
    for packet_id, row in adapted.entries.iterrows( ):
        want = expected[ str( packet_id ) ]
        label = adapted.labels.loc[ packet_id ]
        # row[ "flags" ], not row.flags: Series.flags is a pandas attribute
        got = [ row[ "src_ip" ], row[ "dst_ip" ], int( row[ "src_port" ] ), int( row[ "dst_port" ] ), row[ "protocol" ],
                int( row[ "packet_size_bytes" ] ), row[ "flags" ], label[ "attack" ], int( label[ "is_attack" ] ) ]
        assert got == want, packet_id

def test_drop_reasons_are_counted( adapted, frame ):
    assert adapted.dropped == FIXTURE[ "dropped" ]
    assert adapted.total == len( frame )
    assert adapted.kept + sum( adapted.dropped.values( ) ) == adapted.total

def test_entries_have_only_api_fields_and_no_labels( adapted ):
    assert tuple( adapted.entries.columns ) == ENTRY_COLUMNS
    assert set( ENTRY_COLUMNS ) == set( INPUT_FIELDS )
    assert "attack" not in adapted.entries.columns and "attack_label" not in adapted.entries.columns
    assert adapted.labels.index.equals( adapted.entries.index )
    assert adapted.entries.index.name == "packet_id"

def test_dtypes( adapted ):
    e = adapted.entries
    assert all( e[ c ].dtype == np.int64 for c in ( "src_port", "dst_port", "packet_size_bytes" ) )
    assert adapted.labels[ "is_attack" ].dtype == np.int8
    assert all( f is None or isinstance( f, str ) for f in e[ "flags" ] )


# ---------------------------------------------------------------- pieces

@pytest.mark.parametrize( "letters, flags", [
    ( "A", "ACK" ), ( "PA", "PSH,ACK" ), ( "SA", "SYN,ACK" ), ( "FA", "FIN,ACK" ), ( "RA", "RST,ACK" ),
    ( "FPA", "FIN,PSH,ACK" ), ( "SEC", "SYN,ECE,CWR" ), ( "SAE", "SYN,ACK,ECE" ), ( "PAC", "PSH,ACK,CWR" ),
    ( "FAN", "FIN,ACK,NS" ), ( "FPU", "FIN,PSH,URG" ), ( "", "" ), ( "AS", "SYN,ACK" ),
] )
def test_convert_tcp_flags( letters, flags ):
    assert convert_tcp_flags( letters ) == flags

def test_convert_tcp_flags_rejects_unknown_letters( ):
    with pytest.raises( ValueError, match="X" ):
        convert_tcp_flags( "SX" )

def test_longest_possible_flags_fit_the_api_limit( ):
    # Every scapy TCP flag letter at once is 34 characters
    assert len( convert_tcp_flags( "FSRPAUECN" ) ) == 34 <= MAX_FLAGS_LENGTH

def test_flags_over_the_limit_are_dropped( frame, monkeypatch ):
    from nla_ml.adapters import cicids2017_packets
    monkeypatch.setattr( cicids2017_packets, "MAX_FLAGS_LENGTH", 20 )
    adapted = adapt_packet_fields( frame )
    assert adapted.dropped[ "flags_too_long" ] == 1
    assert 9000009 not in adapted.entries.index

def test_every_flag_seen_in_file_3_fits_the_api_limit( ):
    for letters in ( "A", "PA", "FA", "S", "SA", "R", "RA", "FPA", "SEC", "SAE", "PAC", "FAN" ):
        assert len( convert_tcp_flags( letters ) ) <= MAX_FLAGS_LENGTH

def test_missing_required_column( frame ):
    with pytest.raises( KeyError, match="IP len" ):
        adapt_packet_fields( frame.drop( columns=[ "IP len" ] ) )

def test_ip_proto_column_is_optional( frame ):
    adapted = adapt_packet_fields( frame.drop( columns=[ "IP proto" ] ) )
    # Without IP proto, "other" + icmp can't be recognised: 9000005 becomes OTHER, plain "icmp" still ICMP
    assert adapted.entries.loc[ 9000005, "protocol" ] == "OTHER"
    assert adapted.entries.loc[ 9000004, "protocol" ] == "ICMP"

def test_extra_columns_are_ignored( frame ):
    noisy = frame.assign( packet_hex="deadbeef", **{ "TCP window": 512 } )
    assert adapt_packet_fields( noisy ).entries.equals( adapt_packet_fields( frame ).entries )

def test_float_ports_from_nullable_columns( frame ):
    # pandas may hand ints back as floats when a column has nulls
    as_float = frame.assign( source_port=frame[ "source_port" ].astype( float ) )
    assert adapt_packet_fields( as_float ).entries[ "src_port" ].tolist( ) == adapt_packet_fields( frame ).entries[ "src_port" ].tolist( )

def test_source_columns_cover_what_the_adapter_reads( ):
    assert set( SOURCE_COLUMNS ) >= { "source_ip", "destination_ip", "source_port", "destination_port", "protocol", "IP len", "TCP flags", "attack_label", "packet_id", "flow_id" }


# ---------------------------------------------------------------- downstream: features, heuristics, API entries

def test_entries_featurize( adapted ):
    features = featurize_frame( adapted.entries )
    assert list( features.columns ) == list( FEATURE_COLUMNS )
    assert features.index.equals( adapted.entries.index )
    assert features.loc[ 9000008, "flags_present" ] == 1 and features.loc[ 9000008, "flag_count" ] == 0
    assert features.loc[ 9000007, "flag_count" ] == 3  # FIN, ACK, NS

def test_entries_score_with_the_heuristics( adapted ):
    scores, results = score_entries( adapted.entries.to_dict( orient="records" ), batch_size=50 )
    assert len( scores ) == adapted.kept
    by_id = dict( zip( adapted.entries.index, results ) )
    flags_result = next( r for r in by_id[ 9000008 ] if r.name == "tcp_flags" )
    assert flags_result.detail == "Packet has no flags set"

def test_to_log_entries( adapted ):
    entries = list( to_log_entries( adapted.entries ) )
    assert len( entries ) == adapted.kept
    first = entries[ 0 ]
    assert set( first ) == set( ENTRY_COLUMNS ) | { "raw_payload", "captured_at" }
    assert first[ "raw_payload" ] == { "dataset": "CIC-IDS2017", "packet_id": 8394003 }
    assert first[ "captured_at" ] == "2017-07-03T00:00:08.394003+00:00"
    times = [ e[ "captured_at" ] for e in entries ]
    assert times == sorted( times )  # capture order preserved
    assert not any( "attack" in json.dumps( e ) or "BENIGN" in json.dumps( e ) for e in entries )
