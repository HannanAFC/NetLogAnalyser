"""
Checks that the shared nla-ml package stays in sync with the backend.
The package's own behaviour is tested in ml/tests.
"""
from __future__ import annotations

import random
from datetime import UTC, datetime
from ipaddress import ip_address

import nla_ml.flags
import nla_ml.heuristics
import nla_ml.ports
from nla_ml.compat import SKLEARN_VERSION, assert_sklearn_version
from nla_ml.features import FEATURE_COLUMNS, INPUT_FIELDS, PROTOCOLS, featurize
from nla_ml.heuristics import DEFAULT_WEIGHTS, HeuristicConfig, score_entries

import ingest.anomaly
from config import Settings, settings
from geoip import GeoStatus
from ingest.schemas import LogEntryCreate, ProtocolEnum


def test_heuristics_use_the_shared_code( ):
    # One source of truth: anomaly.py wraps nla_ml.heuristics and keeps no copies of its own
    assert ingest.anomaly.HeuristicResult is nla_ml.heuristics.HeuristicResult
    for name in ( "PORT_PROTOCOL_EXPECTATIONS", "_PORT_PROTOCOL_EXPECTATIONS", "parse_flags", "_parse_flags", "_XMAS_FLAGS", "_check_port" ):
        assert not hasattr( ingest.anomaly, name ), name
    assert nla_ml.heuristics.PORT_PROTOCOL_EXPECTATIONS is nla_ml.ports.PORT_PROTOCOL_EXPECTATIONS
    assert nla_ml.heuristics.parse_flags is nla_ml.flags.parse_flags

def _setting_default( name: str ):
    return Settings.model_fields[ name ].default

def test_heuristic_config_defaults_match_settings_defaults( ):
    # A notebook using HeuristicConfig() must get the same baseline as a backend on default settings
    config = HeuristicConfig( )
    assert config.packet_size_mtu       == _setting_default( "anomaly_packet_size_mtu" )
    assert config.packet_size_jumbo_max == _setting_default( "anomaly_packet_size_jumbo_max" )
    assert config.packet_size_tiny_max  == _setting_default( "anomaly_packet_size_tiny_max" )
    assert config.port_scan_low         == _setting_default( "anomaly_port_scan_low" )
    assert config.port_scan_high        == _setting_default( "anomaly_port_scan_high" )
    assert config.host_sweep_low        == _setting_default( "anomaly_host_sweep_low" )
    assert config.host_sweep_high       == _setting_default( "anomaly_host_sweep_high" )
    assert dict( DEFAULT_WEIGHTS ) == {
        "packet_size":            _setting_default( "anomaly_weight_packet_size" ),
        "tcp_flags":              _setting_default( "anomaly_weight_tcp_flags" ),
        "port_protocol_mismatch": _setting_default( "anomaly_weight_mismatch_ports" ),
        "port_scan_shape":        _setting_default( "anomaly_weight_port_scan_shape" ),
        "host_sweep_shape":       _setting_default( "anomaly_weight_host_sweep_shape" ),
    }

def test_heuristic_config_follows_live_settings( monkeypatch ):
    monkeypatch.setattr( settings, "anomaly_packet_size_mtu", 1000 )
    monkeypatch.setattr( settings, "anomaly_port_scan_high", 7 )
    config = ingest.anomaly.heuristic_config( )
    assert ( config.packet_size_mtu, config.port_scan_high ) == ( 1000, 7 )
    assert ingest.anomaly._score_packet_size( { "packet_size_bytes": 1200 } ).score > 0

def test_backend_and_notebook_scores_are_identical( ):
    # What a notebook computes with the backend's config must equal what ingest stores
    rng = random.Random( 7 )
    entries = [
        {
            "src_ip": rng.choice( [ "10.0.0.1", "10.0.0.2", "203.0.113.9" ] ),
            "dst_ip": f"8.8.{ rng.randint( 0, 30 ) }.8",
            "src_port": rng.choice( [ 0, 53, 443, 50000 ] ),
            "dst_port": rng.randint( 0, 40 ) if rng.random( ) < 0.5 else rng.choice( [ 22, 53, 123, 443, 3389 ] ),
            "protocol": rng.choice( [ "TCP", "UDP", "ICMP", "OTHER" ] ),
            "packet_size_bytes": rng.choice( [ 0, 20, 40, 60, 1500, 4000, 9000 ] ),
            "flags": rng.choice( [ None, ",", "SYN", "SYN,ACK", "FIN,PSH,URG", "SYN,RST" ] ),
        }
        for _ in range( 600 )
    ]
    backend_scores: list[ float ] = [ ]
    backend_results: list[ list ] = [ ]
    for start in range( 0, len( entries ), 50 ):
        batch = entries[ start:start + 50 ]
        for entry, extras in zip( batch, ingest.anomaly._score_batch_heuristics( batch ) ):
            score, results = ingest.anomaly.compute_anomaly_score( entry, extra_results=extras )
            backend_scores.append( score )
            backend_results.append( results )

    scores, results = score_entries( entries, ingest.anomaly.heuristic_config( ), batch_size=50 )
    assert scores == backend_scores
    assert results == backend_results

def test_every_feature_input_is_an_api_field( ):
    # If the ingest schema renames or drops a field, the features can't be computed in production
    assert set( INPUT_FIELDS ) <= set( LogEntryCreate.model_fields )

def test_protocols_match_the_api_enum( ):
    assert set( PROTOCOLS ) == { p.value for p in ProtocolEnum }

def test_featurize_accepts_real_scoring_inputs( ):
    # Build the dicts exactly as ingest/service.py does
    entries = [
        LogEntryCreate(
            src_ip=ip_address( "192.168.1.10" ), dst_ip=ip_address( "2606:4700::1111" ), src_port=51515, dst_port=443,
            protocol=ProtocolEnum[ protocol ], packet_size_bytes=60, flags=flags,
            raw_payload={ "note": "test" }, captured_at=datetime( 2026, 11, 3, tzinfo=UTC ),
        )
        for protocol, flags in ( ( "TCP", "SYN,ACK" ), ( "UDP", None ), ( "ICMP", None ), ( "OTHER", "," ) )
    ]
    scoring_inputs = [
        {
            **entry.model_dump( mode="json" ),
            "src_country_code": None,
            "dst_country_code": "US",
            "src_geo_status":   GeoStatus.PRIVATE,
            "dst_geo_status":   GeoStatus.RESOLVED,
        }
        for entry in entries
    ]

    features = featurize( scoring_inputs )
    assert list( features.columns ) == list( FEATURE_COLUMNS )
    assert features[ [ "proto_TCP", "proto_UDP", "proto_ICMP", "proto_OTHER" ] ].to_numpy( ).tolist( ) == [
        [ 1, 0, 0, 0 ], [ 0, 1, 0, 0 ], [ 0, 0, 1, 0 ], [ 0, 0, 0, 1 ],
    ]
    assert features[ "src_is_private" ].tolist( ) == [ 1, 1, 1, 1 ]
    assert features[ "dst_is_private" ].tolist( ) == [ 0, 0, 0, 0 ]

def test_backend_installs_the_pinned_sklearn( ):
    # The backend gets scikit-learn through nla-ml[sklearn], so it must be exactly the pin
    import sklearn

    assert sklearn.__version__ == SKLEARN_VERSION
    assert_sklearn_version( )
