"""
Tests for the shared feature package. These need nothing but nla-ml itself
(no backend settings, no database), so they also run in a Kaggle notebook
against the pinned commit: `pytest backend/ml/tests`.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from nla_ml.addresses import is_private_ip, is_private_probe
from nla_ml.compat import (
    SKLEARN_VERSION,
    IncompatibleModelError,
    assert_compatible,
    assert_sklearn_version,
    compatibility_problems,
    feature_spec,
    installed_sklearn_version,
)
from nla_ml.features import (
    FEATURE_COLUMNS,
    FEATURE_FINGERPRINT,
    FEATURE_VERSION,
    featurize,
    featurize_entry,
    featurize_frame,
)
from nla_ml.flags import parse_flags
from nla_ml.ports import PortBucket, port_bucket

GOLDEN_PATH = Path( __file__ ).parent / "fixtures" / f"golden_features_v{ FEATURE_VERSION }.json"
GOLDEN      = json.loads( GOLDEN_PATH.read_text( ) )
CASES       = GOLDEN[ "cases" ]

# One fingerprint per FEATURE_VERSION. If this test fails you changed the feature
# definition: bump FEATURE_VERSION, add a new golden fixture, and add the new
# fingerprint here. Never edit an entry once a model has been trained on it.
# The fingerprint also covers how this Python's is_private answers a probe set, so a
# failure here on a new Python means is_private changed: check before retraining.
KNOWN_FINGERPRINTS = {
    1: "c19fbc679f8bcca6",
}

def _base_entry( **overrides ):
    entry = {
        "src_ip": "192.168.1.10", "dst_ip": "8.8.8.8", "src_port": 50000, "dst_port": 443,
        "protocol": "TCP", "packet_size_bytes": 60, "flags": "SYN",
    }
    entry.update( overrides )
    return entry


# ---------------------------------------------------------------- golden fixture

def test_golden_fixture_matches_current_version( ):
    assert GOLDEN[ "feature_version" ] == FEATURE_VERSION

@pytest.mark.parametrize( "case", CASES, ids=[ c[ "name" ] for c in CASES ] )
def test_golden_entry( case ):
    actual = dict( zip( FEATURE_COLUMNS, featurize_entry( case[ "entry" ] ) ) )
    expected = dict( zip( FEATURE_COLUMNS, case[ "expected" ] ) )
    assert actual == expected

def test_golden_batch_matches_rows( ):
    frame = featurize( [ c[ "entry" ] for c in CASES ] )
    assert frame.to_numpy( ).tolist( ) == [ c[ "expected" ] for c in CASES ]


# ---------------------------------------------------------------- output shape

def test_columns_and_dtypes( ):
    frame = featurize( [ _base_entry( ) ] )
    assert list( frame.columns ) == list( FEATURE_COLUMNS )
    assert all( dtype == np.int64 for dtype in frame.dtypes )

def test_no_duplicate_columns( ):
    assert len( set( FEATURE_COLUMNS ) ) == len( FEATURE_COLUMNS )

def test_empty_input_gives_empty_frame_with_columns( ):
    frame = featurize( [ ] )
    assert frame.shape == ( 0, len( FEATURE_COLUMNS ) )
    assert list( frame.columns ) == list( FEATURE_COLUMNS )

def test_ips_never_reach_the_features( ):
    assert not any( "ip" in c.split( "_" ) for c in FEATURE_COLUMNS )


# ---------------------------------------------------------------- stripping extra inputs

def test_extra_fields_do_not_change_output( ):
    plain = featurize_entry( _base_entry( ) )
    noisy = featurize_entry( _base_entry( Label="DDoS", anomaly_score=1.0, raw_payload={ "x": 1 }, src_bytes=99999 ) )
    assert plain == noisy

def test_featurize_frame_drops_extra_columns_and_keeps_index( ):
    entries = [ c[ "entry" ] for c in CASES[ :5 ] ]
    frame = pd.DataFrame( entries, index=[ 10, 11, 12, 13, 14 ] )
    frame[ "Label" ] = "BENIGN"
    frame[ "Flow Bytes/s" ] = 1.5

    features = featurize_frame( frame )
    assert list( features.index ) == [ 10, 11, 12, 13, 14 ]
    assert features.reset_index( drop=True ).equals( featurize( entries ) )

def test_featurize_frame_handles_nan_flags_and_float_ports( ):
    # pandas turns None into NaN in mixed columns and upcasts ints to float when NaNs are present
    frame = pd.DataFrame( {
        "src_ip": [ "10.0.0.1", "10.0.0.2" ], "dst_ip": [ "8.8.8.8", "8.8.8.8" ],
        "src_port": [ 50000.0, 0.0 ], "dst_port": [ 443.0, 0.0 ],
        "protocol": [ "TCP", "ICMP" ], "packet_size_bytes": [ 60, 84 ],
        "flags": [ "SYN", np.nan ],
    } )
    features = featurize_frame( frame )
    assert features.loc[ 1, "flags_present" ] == 0
    assert features.loc[ 0, "flag_SYN" ] == 1

def test_featurize_frame_missing_column( ):
    with pytest.raises( KeyError, match="dst_port" ):
        featurize_frame( pd.DataFrame( [ _base_entry( ) ] ).drop( columns=[ "dst_port" ] ) )

def test_flags_key_may_be_absent( ):
    entry = _base_entry( )
    del entry[ "flags" ]
    assert featurize_entry( entry ) == featurize_entry( _base_entry( flags=None ) )


# ---------------------------------------------------------------- input types

def test_accepts_ipaddress_objects_and_str_enums( ):
    from enum import Enum
    from ipaddress import ip_address

    class Proto( str, Enum ):
        TCP = "TCP"

    as_objects = _base_entry( src_ip=ip_address( "192.168.1.10" ), dst_ip=ip_address( "8.8.8.8" ), protocol=Proto.TCP )
    assert featurize_entry( as_objects ) == featurize_entry( _base_entry( ) )

def test_accepts_numpy_integers( ):
    entry = _base_entry( src_port=np.int64( 50000 ), dst_port=np.int32( 443 ), packet_size_bytes=np.uint16( 60 ) )
    assert featurize_entry( entry ) == featurize_entry( _base_entry( ) )


# ---------------------------------------------------------------- invalid input fails loudly

@pytest.mark.parametrize( "overrides, message", [
    ( { "protocol": "SCTP" },          "protocol" ),
    ( { "dst_port": 65536 },           "dst_port out of range" ),
    ( { "src_port": -1 },              "src_port out of range" ),
    ( { "packet_size_bytes": -5 },     "packet_size_bytes out of range" ),
    ( { "dst_port": "443" },           "dst_port must be an integer" ),
    ( { "dst_port": 443.5 },           "dst_port must be an integer" ),
    ( { "dst_port": True },            "dst_port must be an integer" ),
    ( { "src_ip": "999.1.1.1" },       "999.1.1.1" ),
    ( { "flags": 7 },                  "flags must be a string" ),
] )
def test_invalid_entries_raise( overrides, message ):
    with pytest.raises( ( TypeError, ValueError ), match=message ):
        featurize_entry( _base_entry( **overrides ) )

def test_missing_required_field_raises( ):
    entry = _base_entry( )
    del entry[ "protocol" ]
    with pytest.raises( KeyError, match="protocol" ):
        featurize_entry( entry )

def test_batch_error_names_the_entry_index( ):
    with pytest.raises( ValueError, match="entry 2" ):
        featurize( [ _base_entry( ), _base_entry( ), _base_entry( protocol="nope" ) ] )

def test_batch_wraps_type_errors_as_value_errors( ):
    with pytest.raises( ValueError, match="entry 1: dst_port must be an integer" ):
        featurize( [ _base_entry( ), _base_entry( dst_port="443" ) ] )


# ---------------------------------------------------------------- helpers

def test_parse_flags( ):
    assert parse_flags( None ) is None
    assert parse_flags( "," ) == set( )
    assert parse_flags( "" ) == set( )
    assert parse_flags( " syn ,Ack,," ) == { "SYN", "ACK" }

@pytest.mark.parametrize( "port, bucket", [
    ( 0, PortBucket.ZERO ), ( 1, PortBucket.WELL_KNOWN ), ( 1023, PortBucket.WELL_KNOWN ),
    ( 1024, PortBucket.REGISTERED ), ( 49151, PortBucket.REGISTERED ),
    ( 49152, PortBucket.EPHEMERAL ), ( 65535, PortBucket.EPHEMERAL ),
] )
def test_port_bucket_boundaries( port, bucket ):
    assert port_bucket( port ) == bucket

# Pins the is_private semantics the models are trained on (Python 3.13.15 / 3.14.8)
@pytest.mark.parametrize( "ip, private", [
    # RFC 1918, loopback, link-local
    ( "10.255.255.255", True ), ( "11.0.0.0", False ),
    ( "172.15.255.255", False ), ( "172.16.0.0", True ), ( "172.31.255.255", True ), ( "172.32.0.0", False ),
    ( "192.167.255.255", False ), ( "192.168.0.0", True ), ( "127.0.0.1", True ), ( "169.254.1.1", True ),
    # Carrier-grade NAT is neither private nor global
    ( "100.63.255.255", False ), ( "100.64.0.0", False ), ( "100.127.255.255", False ),
    # Documentation, benchmarking, reserved, "this network" and broadcast count as private
    ( "192.0.2.1", True ), ( "198.51.100.1", True ), ( "203.0.113.1", True ), ( "198.18.0.1", True ),
    ( "240.0.0.1", True ), ( "0.0.0.0", True ), ( "255.255.255.255", True ),
    # Multicast and ordinary public addresses
    ( "224.0.0.5", False ), ( "8.8.8.8", False ), ( "45.33.32.156", False ),
    # IPv6
    ( "fc00::1", True ), ( "fdff::1", True ), ( "fe80::1", True ), ( "febf::1", True ), ( "fec0::1", False ),
    ( "::1", True ), ( "::", True ), ( "2001:db8::1", True ), ( "3fff::1", True ), ( "2002::1", True ),
    ( "2606:4700::1111", False ), ( "ff02::1", False ),
    # IPv4-mapped IPv6 behaves like the IPv4 address
    ( "::ffff:10.0.0.1", True ), ( "::ffff:8.8.8.8", False ),
] )
def test_private_ip_table( ip, private ):
    assert is_private_ip( ip ) is private


# ---------------------------------------------------------------- versioning

def test_fingerprint_is_pinned_for_this_version( ):
    assert FEATURE_VERSION in KNOWN_FINGERPRINTS, (
        f"FEATURE_VERSION { FEATURE_VERSION } has no pinned fingerprint. Add { FEATURE_FINGERPRINT!r} to KNOWN_FINGERPRINTS."
    )
    assert KNOWN_FINGERPRINTS[ FEATURE_VERSION ] == FEATURE_FINGERPRINT, (
        "The feature definition changed without a FEATURE_VERSION bump. "
        "Bump FEATURE_VERSION, write a new golden fixture, and pin the new fingerprint."
    )

def test_spec_round_trips_through_json( ):
    spec = json.loads( json.dumps( feature_spec( ) ) )
    assert compatibility_problems( spec ) == [ ]
    assert_compatible( spec )

@pytest.mark.parametrize( "change, problem", [
    ( { "feature_version": FEATURE_VERSION + 1 }, "feature_version" ),
    ( { "feature_fingerprint": "0" * 16 },        "feature_fingerprint" ),
    ( { "feature_columns": list( reversed( FEATURE_COLUMNS ) ) }, "feature_columns" ),
    ( { "sklearn_version": "1.8.0" },             "sklearn_version" ),
] )
def test_incompatible_metadata_is_refused( change, problem ):
    metadata = { **feature_spec( ), **change }
    with pytest.raises( IncompatibleModelError, match=problem ):
        assert_compatible( metadata )

def test_metadata_without_spec_is_refused( ):
    problems = compatibility_problems( { "model_type": "rf" } )
    assert len( problems ) == 4

def test_python_version_is_informational_only( ):
    assert_compatible( { **feature_spec( ), "python_version": "3.0.0" } )

def test_probe_covers_range_edges( ):
    probe = dict( is_private_probe( ) )
    assert len( probe ) > 200
    assert probe[ "100.64.0.0" ] is False and probe[ "100.63.255.255" ] is False
    assert probe[ "192.0.2.0" ] is True and probe[ "192.0.2.255" ] is True and probe[ "192.0.3.0" ] is False

def test_packet_size_definition_is_part_of_the_fingerprint( monkeypatch ):
    from nla_ml import features

    before = features._fingerprint( )
    monkeypatch.setattr( features, "PACKET_SIZE_DEFINITION", "frame_length" )
    assert features._fingerprint( ) != before


# ---------------------------------------------------------------- scikit-learn pin

def test_sklearn_extra_matches_the_pinned_version( ):
    import tomllib

    pyproject = tomllib.loads( ( Path( __file__ ).parents[ 1 ] / "pyproject.toml" ).read_text( ) )
    assert pyproject[ "project" ][ "optional-dependencies" ][ "sklearn" ] == [ f"scikit-learn=={ SKLEARN_VERSION }" ]

def test_sklearn_version_check( monkeypatch ):
    from nla_ml import compat

    monkeypatch.setattr( compat, "installed_sklearn_version", lambda: "0.0.1" )
    with pytest.raises( IncompatibleModelError, match=f"scikit-learn { SKLEARN_VERSION } is required, found 0.0.1." ):
        compat.assert_sklearn_version( )

    monkeypatch.setattr( compat, "installed_sklearn_version", lambda: SKLEARN_VERSION )
    compat.assert_sklearn_version( )

@pytest.mark.skipif( installed_sklearn_version( ) is None, reason="scikit-learn not installed" )
def test_installed_sklearn_is_the_pinned_version( ):
    assert_sklearn_version( )
