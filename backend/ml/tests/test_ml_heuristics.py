"""
Tests for nla_ml.heuristics on its own: no backend settings, no .env, no database.
Behaviour parity with the backend is tested in backend/tests (test_anomaly.py, test_ml_integration.py).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

import pytest
from nla_ml.heuristics import (
    DEFAULT_CONFIG,
    DEFAULT_WEIGHTS,
    ENTRY_HEURISTICS,
    HeuristicConfig,
    HeuristicResult,
    combine_scores,
    compute_anomaly_score,
    ramp,
    score_batch_heuristics,
    score_entries,
    score_packet_size,
    score_port_protocol_mismatch,
    score_tcp_flags,
)


def _entry( **overrides ) -> dict:
    entry = {
        "src_ip": "10.0.0.1", "dst_ip": "93.184.216.34", "src_port": 50000, "dst_port": 443,
        "protocol": "TCP", "packet_size_bytes": 500, "flags": "ACK",
    }
    entry.update( overrides )
    return entry


def test_imports_without_backend_env_or_database( ):
    # Fresh interpreter, isolated mode, no backend env vars: importing must not need config.py or a DB
    env = { k: v for k, v in os.environ.items( ) if k not in ( "DATABASE_URL", "REDIS_URL", "SECRET_KEY" ) }
    code = (
        "import sys; from nla_ml.heuristics import compute_anomaly_score, HeuristicConfig; "
        "s, r = compute_anomaly_score( { 'packet_size_bytes': 0, 'protocol': 'TCP', 'flags': ',', 'src_port': 1, 'dst_port': 2 } ); "
        "bad = [ m for m in ( 'config', 'sqlalchemy', 'fastapi', 'ingest' ) if m in sys.modules ]; "
        "assert not bad, bad; print( round( s, 6 ) )"
    )
    result = subprocess.run( [ sys.executable, "-I", "-c", code ], env=env, capture_output=True, text=True, timeout=60, check=False )
    assert result.returncode == 0, result.stderr
    assert float( result.stdout ) == pytest.approx( 1 - ( 1 - 0.5 ) * ( 1 - 0.9 ) )

def test_default_config( ):
    assert DEFAULT_CONFIG == HeuristicConfig( )
    assert dict( DEFAULT_CONFIG.weights ) == dict( DEFAULT_WEIGHTS )
    assert json.loads( json.dumps( DEFAULT_CONFIG.as_dict( ) ) )[ "weights" ][ "tcp_flags" ] == 0.9

def test_configs_do_not_share_weights( ):
    a, b = HeuristicConfig( ), HeuristicConfig( )
    assert a.weights is not b.weights
    assert a.weights is not DEFAULT_WEIGHTS

def test_ramp( ):
    assert [ ramp( v, 0, 100 ) for v in ( -1, 0, 25, 100, 101 ) ] == [ 0.0, 0.0, 0.25, 1.0, 1.0 ]


# ---------------------------------------------------------------- thresholds come from the config

def test_packet_size_uses_config_thresholds( ):
    entry = { "packet_size_bytes": 1200 }
    assert score_packet_size( entry ).score == 0.0
    tighter = HeuristicConfig( packet_size_mtu=1000, packet_size_jumbo_max=1400 )
    assert score_packet_size( entry, tighter ).score == pytest.approx( 0.5 )
    assert score_packet_size( entry, tighter ).detail == "Packet size 1200B is unusually large"

def test_tiny_packet_threshold( ):
    assert score_packet_size( { "packet_size_bytes": 30 } ).score == pytest.approx( 0.25 )
    assert score_packet_size( { "packet_size_bytes": 30 }, HeuristicConfig( packet_size_tiny_max=28 ) ).score == 0.0

def test_batch_thresholds_come_from_config( ):
    rows = [ _entry( dst_port=p ) for p in range( 1, 11 ) ]  # 10 distinct ports from one source
    default = score_batch_heuristics( rows )[ 0 ]
    strict  = score_batch_heuristics( rows, HeuristicConfig( port_scan_low=2, port_scan_high=6 ) )[ 0 ]
    assert default[ 0 ].name == "port_scan_shape" and default[ 0 ].score == pytest.approx( 0.25 )
    assert strict[ 0 ].score == 1.0
    assert strict[ 0 ].detail == "10.0.0.1 touched 10 distinct ports in this batch"

def test_weights_come_from_config( ):
    entry = _entry( flags="FIN,PSH,URG" )
    score_default, _ = compute_anomaly_score( entry )
    score_low, _     = compute_anomaly_score( entry, HeuristicConfig( weights={ **DEFAULT_WEIGHTS, "tcp_flags": 0.1 } ) )
    assert score_default == pytest.approx( 0.9 )
    assert score_low == pytest.approx( 0.1 )


# ---------------------------------------------------------------- the heuristics themselves

@pytest.mark.parametrize( "overrides, score, detail", [
    ( { "flags": "ACK" },              0.0, None ),
    ( { "flags": None },               0.0, None ),
    ( { "flags": "," },                1.0, "Packet has no flags set" ),
    ( { "flags": "fin,psh,urg" },      1.0, "Packet contains XMAS flags" ),
    ( { "flags": "SYN,FIN" },          1.0, "Packet has invalid flag pair ( FIN, SYN )" ),
    ( { "flags": "SYN,RST" },          1.0, "Packet has invalid flag pair ( RST, SYN )" ),
    ( { "flags": ",", "protocol": "UDP" }, 0.0, None ),
] )
def test_tcp_flags( overrides, score, detail ):
    result = score_tcp_flags( _entry( **overrides ) )
    assert ( result.score, result.detail ) == ( score, detail )

@pytest.mark.parametrize( "overrides, score", [
    ( { "dst_port": 443 },                                  0.0 ),
    ( { "protocol": "UDP", "dst_port": 22 },                1.0 ),
    ( { "protocol": "TCP", "dst_port": 50000, "src_port": 123 }, 1.0 ),
    ( { "protocol": "ICMP", "src_port": 0, "dst_port": 0 }, 0.0 ),
    ( { "protocol": "ICMP", "src_port": 8, "dst_port": 0 }, 1.0 ),
    ( { "protocol": "OTHER", "dst_port": 22 },              0.0 ),
] )
def test_port_protocol_mismatch( overrides, score ):
    assert score_port_protocol_mismatch( _entry( **overrides ) ).score == score

def test_entry_heuristics_order( ):
    assert [ h.__name__ for h in ENTRY_HEURISTICS ] == [ "score_packet_size", "score_tcp_flags", "score_port_protocol_mismatch" ]

def test_combine_scores_noisy_or_and_missing_weight( ):
    results = [ HeuristicResult( "a", 0.8 ), HeuristicResult( "b", 0.3 ), HeuristicResult( "unweighted", 0.5 ) ]
    expected = 1 - ( 1 - 0.9 * 0.8 ) * ( 1 - 0.5 * 0.3 ) * ( 1 - 0.5 )
    assert combine_scores( results, { "a": 0.9, "b": 0.5 } ) == pytest.approx( expected )
    assert combine_scores( [ ], { } ) == 0.0

def test_extra_results_are_combined( ):
    score, results = compute_anomaly_score( _entry( ), extra_results=[ HeuristicResult( "ml_rf", 0.5 ) ] )
    assert [ r.name for r in results ][ -1 ] == "ml_rf"
    assert score == pytest.approx( 0.5 )  # ml_rf has no default weight, so it counts at 1.0


# ---------------------------------------------------------------- replaying ingest batches

def test_score_entries_matches_manual_batches( ):
    entries = [ _entry( src_ip="10.0.0.9", dst_port=p ) for p in range( 1, 31 ) ] + [ _entry( ) for _ in range( 10 ) ]
    scores, results = score_entries( entries, batch_size=20 )
    expected_scores = [ ]
    for start in ( 0, 20 ):
        batch = entries[ start:start + 20 ]
        for entry, extras in zip( batch, score_batch_heuristics( batch ) ):
            expected_scores.append( compute_anomaly_score( entry, extra_results=extras )[ 0 ] )
    assert scores == expected_scores
    assert len( results ) == 40 and all( len( r ) == 5 for r in results )

def test_batch_size_changes_scan_detection( ):
    # 30 ports from one source: caught in one batch of 50, invisible in batches of 3
    entries = [ _entry( src_ip="10.0.0.9", dst_port=p ) for p in range( 1, 31 ) ]
    big, _   = score_entries( entries, batch_size=50 )
    small, _ = score_entries( entries, batch_size=3 )
    assert min( big ) > max( small )

def test_score_entries_validates_batch_size( ):
    with pytest.raises( ValueError ):
        score_entries( [ _entry( ) ], batch_size=0 )
    assert score_entries( [ ] ) == ( [ ], [ ] )
