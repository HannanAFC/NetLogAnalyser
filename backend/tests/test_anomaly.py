from __future__ import annotations

from datetime import UTC, datetime
from ipaddress import IPv4Address
from typing import Any
from uuid import uuid4

import ingest.anomaly
import pytest
from ingest.anomaly import (
    HeuristicResult,
    _ramp,
    _score_batch_heuristics,
    _score_packet_size,
    _score_port_protocol_mismatch,
    _score_tcp_flags,
    compute_anomaly_score,
)
from ingest.schemas import LogEntryRow

RAMP_SIZES = [
    ( 0,    0, 100, 0.0 ),
    ( 100,  0, 100, 1.0 ),
    ( 50,   0, 100, 0.5 ),
    ( -10,  0, 100, 0.0 ),
    ( 200,  0, 100, 1.0 ),
    ( 25,   0, 100, 0.25 )
]

@pytest.mark.parametrize( "size,low,high,expected", RAMP_SIZES )
def test_packet_sizes_ramp_function( size, low, high, expected ) -> None:
    assert _ramp( size, low, high ) == expected

class TestPacketSizeScoring:
    def test_normal_value( self ) -> None:
        entry = { "packet_size_bytes": 500 }
        assert _score_packet_size( entry ).score == 0.0

    def test_mtu_boundary_value( self ) -> None:
        entry  = { "packet_size_bytes": 1500 }
        result = _score_packet_size( entry )
        assert result.score  == 0.0
        assert result.detail == None

    def test_large_packet_computed_value( self ) -> None:
        entry = { "packet_size_bytes": 5000 }
        assert _score_packet_size( entry ).score == pytest.approx( 0.466667 )

    def test_jumbo_boundary_value( self ) -> None:
        entry = { "packet_size_bytes": 9000 }
        assert _score_packet_size( entry ).score == 1.0

    def test_0_value( self ) -> None:
        entry = { "packet_size_bytes": 0 }
        assert _score_packet_size( entry ).score == 1.0

    def test_tiny_max_value( self ) -> None:
        entry = { "packet_size_bytes": 40 }
        result = _score_packet_size( entry )
        assert result.score  == 0.0
        assert result.detail == None

    def test_tiny_packet_computed_value( self ) -> None:
        entry = { "packet_size_bytes": 20 }
        assert _score_packet_size( entry ).score == 0.5

    def test_large_packet_detail_message( self ) -> None:
        entry = { "packet_size_bytes": 5000 }
        result = _score_packet_size(entry)
        assert result.detail is not None
        assert "large" in result.detail

    def test_tiny_packet_detail_message(self) -> None:
        entry = { "packet_size_bytes": 20 }
        result = _score_packet_size( entry )
        assert result.detail is not None
        assert "small" in result.detail

class TestTCPFlagScoring:
    def test_null_flags_scores_0( self ):
        entry = { "protocol": "TCP", "flags": None }
        assert _score_tcp_flags( entry ).score == 0.0

    def test_invalid_protocol_scores_0( self ):
        entry = { "protocol": "UDP", "flags": "FIN,PSH,URG" }
        assert _score_tcp_flags( entry ).score == 0.0

    def test_empty_string_scores_1( self ):
        entry = { "protocol": "TCP", "flags": "" }
        result = _score_tcp_flags( entry )
        assert result.score == 1.0
        assert result.detail is not None
        assert "no flags" in result.detail

    def test_normal_combos_score_0( self ):
        entry_1 = { "protocol": "TCP", "flags": "ACK" }
        assert _score_tcp_flags( entry_1 ).score == 0.0

        entry_2 = { "protocol": "TCP", "flags": "SYN,ACK" }
        assert _score_tcp_flags( entry_2 ).score == 0.0

        entry_3 = { "protocol": "TCP", "flags": "FIN,ACK" }
        assert _score_tcp_flags( entry_3 ).score == 0.0

    def test_invalid_combo_different_order_scores_1( self ):
        entry_1  = { "protocol": "TCP", "flags": "FIN,SYN" }
        result_1 = _score_tcp_flags( entry_1 )
        assert result_1.score == 1.0
        assert result_1.detail is not None
        assert "invalid" in result_1.detail

        entry_2  = { "protocol": "TCP", "flags": "RST,SYN" }
        result_2 = _score_tcp_flags( entry_2 )
        assert result_2.score == 1.0
        assert result_2.detail is not None
        assert "invalid" in result_2.detail

        entry_3  = { "protocol": "TCP", "flags": "URG,FIN,PSH" }
        result_3 = _score_tcp_flags( entry_3 )
        assert result_3.score == 1.0
        assert result_3.detail is not None
        assert "XMAS" in result_3.detail

    def test_whitespace_variants( self ):
        entry_1 = { "protocol": "TCP", "flags": " ACK" }
        assert _score_tcp_flags( entry_1 ).score == 0.0

        entry_2 = { "protocol": "TCP", "flags": " RST , SYN " }
        assert _score_tcp_flags( entry_2 ).score == 1.0

        entry_3 = { "protocol": "TCP", "flags": " URG ,  FIN  , PSH " }
        assert _score_tcp_flags( entry_3 ).score == 1.0

    def test_subset_anomalous_flags_scores_1( self ):
        entry  = { "protocol": "TCP", "flags": "FIN,SYN,ACK,RST" }
        result = _score_tcp_flags( entry )
        assert result.score == 1.0
        assert result.detail is not None
        assert "invalid" in result.detail

class TestPortProtocolScoring:
    def test_normal_port_protocol( self ):
        entry_1  = { "protocol": "TCP", "dst_port": 22 }
        result_1 = _score_port_protocol_mismatch( entry_1 )
        assert result_1.score == 0.0

        entry_2  = { "protocol": "UDP", "dst_port": 67 }
        result_2 = _score_port_protocol_mismatch( entry_2 )
        assert result_2.score == 0.0

    def test_mismatch_port_protocol( self ):
        entry_1  = { "protocol": "UDP", "dst_port": "22" }
        result_1 = _score_port_protocol_mismatch( entry_1 )
        assert result_1.score == 1.0
        assert result_1.detail is not None
        assert "22" in result_1.detail

        entry_2  = { "protocol": "TCP", "src_port": 67 }
        result_2 = _score_port_protocol_mismatch( entry_2 )
        assert result_2.score == 1.0
        assert result_2.detail is not None
        assert "67" in result_2.detail

    def test_port_with_no_entries( self ):
        entry_1  = { "protocol": "TCP", "dst_port": 10 }
        result_1 = _score_port_protocol_mismatch( entry_1 )
        assert result_1.score == 0.0

        entry_2  = { "protocol": "UDP", "dst_port": 10 }
        result_2 = _score_port_protocol_mismatch( entry_2 )
        assert result_2.score == 0.0

    def test_icmp_non_zero( self ):
        entry_1  = { "protocol": "ICMP", "dst_port": 0, "src_port": 0 }
        result_1 = _score_port_protocol_mismatch( entry_1 )
        assert result_1.score == 0.0

        entry_2  = { "protocol": "ICMP", "dst_port": 10 }
        result_2 = _score_port_protocol_mismatch( entry_2 )
        assert result_2.score == 1.0
        assert result_2.detail is not None
        assert "Port 0 expected for ICMP protocol" in result_2.detail

        entry_3  = { "protocol": "ICMP", "dst_port": 0, "src_port": 10 }
        result_3 = _score_port_protocol_mismatch( entry_3 )
        assert result_3.score == 1.0
        assert result_3.detail is not None
        assert "Port 0 expected for ICMP protocol" in result_3.detail

    def test_other_returns_0( self ):
        entry_1  = { "protocol": "OTHER", "dst_port": 22, "src_port": 67 }
        result_1 = _score_port_protocol_mismatch( entry_1 )
        assert result_1.score == 0.0

    def test_443_returns_0_tcp_udp( self ):
        entry_1  = { "protocol": "TCP", "dst_port": 443, "src_port": 10 }
        result_1 = _score_port_protocol_mismatch( entry_1 )
        assert result_1.score == 0.0

        entry_2  = { "protocol": "UDP", "dst_port": 443, "src_port": 10 }
        result_2 = _score_port_protocol_mismatch( entry_2 )
        assert result_2.score == 0.0

    def test_both_ports_no_mismatch( self ):
        entry  = { "protocol": "TCP", "dst_port": 22, "src_port": "9999" }
        result = _score_port_protocol_mismatch( entry )
        assert result.score == 0.0

class TestBatchScoring:
    def test_port_count_below_0( self ):
        rows = [
            { "src_ip": "1.1.1.1", "dst_ip": f"2.2.2.{ i }", "dst_port": i } for i in range( 4 )
        ]

        logs = _score_batch_heuristics( rows )
        assert len( logs ) == 4
        for log in logs:
            for result in log:
                assert result.score == 0.0

    def test_port_count_at_boundary_low_0( self ):
            rows = [
                { "src_ip": "1.1.1.1", "dst_ip": f"2.2.2.{ i }", "dst_port": i } for i in range( 5 )
            ]
    
            logs = _score_batch_heuristics( rows )
            assert len( logs ) == 5
            for log in logs:
                for result in log:
                    assert result.score == 0.0

    def test_port_count_midpoint_score( self ):
        rows = [
            { "src_ip": "1.1.1.1", "dst_ip": f"2.2.2.{ i }", "dst_port": i } for i in range( 6 )
        ]

        logs = _score_batch_heuristics( rows )
        assert len( logs ) == 6
        for log in logs:
            for result in log:
                if result.name == "port_scan_shape":
                    assert result.score == pytest.approx( ( 6 - 5 ) / ( 25 - 5 ) )
                    assert result.detail is not None
                    assert "6 distinct ports" in result.detail
                else:
                    assert result.score == pytest.approx( ( 6 - 5 ) / ( 20 - 5 ) )
                    assert result.detail is not None
                    assert "6 distinct destinations" in result.detail

    def test_port_count_at_boundary_high_1( self ):
        rows = [
            { "src_ip": "1.1.1.1", "dst_ip": f"2.2.2.{ i }", "dst_port": i } for i in range( 25 )
        ]

        logs = _score_batch_heuristics( rows )
        assert len( logs ) == 25
        for log in logs:
            for result in log:
                assert result.score == 1.0
                assert result.detail is not None
                assert "25 distinct" in result.detail

    def test_port_count_above_1( self ):
        rows = [
            { "src_ip": "1.1.1.1", "dst_ip": f"2.2.2.{ i }", "dst_port": i } for i in range( 50 )
        ]

        logs = _score_batch_heuristics( rows )
        assert len( logs ) == 50
        for log in logs:
            for result in log:
                assert result.score == 1.0
                assert result.detail is not None
                assert "50 distinct" in result.detail

    def test_many_port_single_ip_1( self ):
        rows = [
            { "src_ip": "1.1.1.1", "dst_ip": "2.2.2.2", "dst_port": i } for i in range( 25 )
        ]
        logs = _score_batch_heuristics( rows )
        assert len( logs ) == 25
        for log in logs:
            for result in log:
                if result.name == "port_scan_shape":
                    assert result.score == 1.0
                    assert result.detail is not None
                    assert "25 distinct ports" in result.detail
                else:
                    assert result.score == 0.0

    def test_many_ip_single_port_1( self ):
        rows = [
            { "src_ip": "1.1.1.1", "dst_ip": f"2.2.2.{ i }", "dst_port": 1 } for i in range( 20 )
        ]
        logs = _score_batch_heuristics( rows )
        assert len( logs ) == 20
        for log in logs:
            for result in log:
                if result.name == "port_scan_shape":
                    assert result.score == 0.0
                else:
                    assert result.score == 1.0
                    assert result.detail is not None
                    assert "20 distinct destinations" in result.detail

    def test_same_src_same_dst_varying_port( self ):
        rows = [
            { "src_ip": "1.1.1.1", "dst_ip": "2.2.2.2", "dst_port": i } for i in range( 10 )
        ]
        logs = _score_batch_heuristics( rows )
        assert len( logs ) == 10
        for log in logs:
            for result in log:
                if result.name == "port_scan_shape":
                    assert result.score > 0
                    assert result.detail is not None
                    assert "10 distinct ports" in result.detail
                else:
                    assert result.score == 0.0
                    assert result.detail is None

    def test_same_src_same_port_varying_dst( self ):
        rows = [
            { "src_ip": "1.1.1.1", "dst_ip": f"2.2.2.{ i }", "dst_port": 80 } for i in range( 10 )
        ]
        logs = _score_batch_heuristics( rows )
        assert len( logs ) == 10
        for log in logs:
            for result in log:
                if result.name == "host_sweep_shape":
                    assert result.score > 0
                    assert result.detail is not None
                    assert "10 distinct destinations" in result.detail
                else:
                    assert result.score == 0.0
                    assert result.detail is None

    def test_duplicate_rows_dedup( self ):
        rows = [
            { "src_ip": "1.1.1.1", "dst_ip": "2.2.2.2", "dst_port": 80 } for _ in range( 20 )
        ]
        logs = _score_batch_heuristics( rows )
        assert len( logs ) == 20
        for log in logs:
            for result in log:
                assert result.score == 0.0
                assert result.detail is None

    def test_multi_source_isolation( self ):
        scanner = [
            { "src_ip": "10.0.0.1", "dst_ip": "192.168.1.1", "dst_port": i } for i in range( 25 )
        ]
        normal = [
            { "src_ip": "10.0.0.2", "dst_ip": "192.168.1.1", "dst_port": 443 } for _ in range( 3 )
        ]
        rows = scanner + normal
        logs = _score_batch_heuristics( rows )

        for i in range( 25 ):
            for result in logs[ i ]:
                if result.name == "port_scan_shape":
                    assert result.score > 0
                    assert result.detail is not None
                    assert "25 distinct ports" in result.detail

        for i in range( 25, 28 ):
            for result in logs[ i ]:
                assert result.score == 0.0
                assert result.detail is None

    def test_empty_batch_returns_empty_list( self ):
        logs = _score_batch_heuristics( [ ] )
        assert logs == [ ]

    def test_output_length_matches_input( self ):
        rows = [
            { "src_ip": "1.1.1.1", "dst_ip": f"2.2.2.{ i }", "dst_port": i } for i in range( 7 )
        ]
        logs = _score_batch_heuristics( rows )
        assert len( logs ) == 7

    def test_same_src_ip_gets_identical_scores( self ):
        rows = [
            { "src_ip": "1.1.1.1", "dst_ip": f"2.2.2.{ i }", "dst_port": i } for i in range( 10 )
        ]
        logs = _score_batch_heuristics( rows )
        port_scores = [ ]
        host_scores = [ ]
        for log in logs:
            for result in log:
                if result.name == "port_scan_shape":
                    port_scores.append( result.score )
                else:
                    host_scores.append( result.score )
        assert len( set( port_scores ) ) == 1
        assert len( set( host_scores ) ) == 1

    def test_each_row_has_exactly_two_results( self ):
        rows = [
            { "src_ip": "1.1.1.1", "dst_ip": f"2.2.2.{ i }", "dst_port": i } for i in range( 5 )
        ]
        logs = _score_batch_heuristics( rows )
        for log in logs:
            assert len( log ) == 2

    def test_score_zero_detail_is_none( self ):
        rows = [
            { "src_ip": "1.1.1.1", "dst_ip": "2.2.2.2", "dst_port": 80 } for _ in range( 3 )
        ]
        logs = _score_batch_heuristics( rows )
        for log in logs:
            for result in log:
                assert result.score == 0.0
                assert result.detail is None

    def test_score_positive_detail_identifies_src_ip( self ):
        rows = [
            { "src_ip": "10.99.0.7", "dst_ip": f"2.2.2.{ i }", "dst_port": i } for i in range( 25 )
        ]
        logs = _score_batch_heuristics( rows )
        for log in logs:
            for result in log:
                assert result.score > 0
                assert result.detail is not None
                assert "10.99.0.7" in result.detail

    def test_single_row_src_ip_scores_zero( self ):
        rows = [
            { "src_ip": "1.1.1.1", "dst_ip": "2.2.2.2", "dst_port": 80 }
        ]
        logs = _score_batch_heuristics( rows )
        assert len( logs ) == 1
        for result in logs[ 0 ]:
            assert result.score == 0.0
            assert result.detail is None


def _fake_heuristic( name: str, score: float ):
    def _inner( entry: dict[str, Any] ) -> HeuristicResult:
        return HeuristicResult( name=name, score=score )
    return _inner

TEST_LOGS = [
    {
        'src_ip': IPv4Address('10.216.32.207'),
        'dst_ip': IPv4Address('0.243.122.189'),
        'src_port': 64807,
        'dst_port': 53,
        'protocol': 'TCP',
        'packet_size_bytes': 53,
        'flags': 'PSH,ACK',
        'raw_payload':
        {
            'synthetic': True,
            'anomalous': False,
            'generator': 'log_sender'
        },
        'captured_at': datetime(2026, 7, 29, 18, 52, 50, 631, tzinfo=UTC)
    },
    {
        'src_ip': IPv4Address('10.43.165.54'),
        'dst_ip': IPv4Address('0.126.92.177'),
        'src_port': 35258,
        'dst_port': 80,
        'protocol': 'TCP',
        'packet_size_bytes': 306,
        'flags': None,
        'raw_payload':
        {
            'synthetic': True,
            'anomalous': False,
            'generator': 'log_sender'
        },
        'captured_at': datetime(2026, 7, 29, 18, 52, 50, 853074, tzinfo=UTC )
    }
]

class TestComputeAnomalyScore:
    def test_compute_anomaly_score_combines_via_noisy_or( self, monkeypatch ):
        monkeypatch.setattr( ingest.anomaly, "_HEURISTICS",
        [
            _fake_heuristic( "a", 0.8 ),
            _fake_heuristic( "b", 0.3 ),
        ] )
        monkeypatch.setattr( ingest.anomaly, "_WEIGHTS", { "a": 0.9, "b": 0.5 } )

        score, _ = compute_anomaly_score( { } )
        assert score == pytest.approx( 1 - ( 1 - 0.9*0.8 ) * ( 1 - 0.5*0.3 ) )

    def test_compute_anomaly_score_returns_0_when_all_0( self, monkeypatch ):
        monkeypatch.setattr( ingest.anomaly, "_HEURISTICS",
        [
            _fake_heuristic( "a", 0.0 ),
            _fake_heuristic( "b", 0.0 ),
        ] )
        monkeypatch.setattr( ingest.anomaly, "_WEIGHTS", { "a": 0.9, "b": 0.5 } )

        score, _ = compute_anomaly_score( { } )
        assert score == 1 - ( 1 - 0.9*0.0 ) * ( 1 - 0.5*0.0 )

    def test_compute_anomaly_score_1_returns_1( self, monkeypatch ):
        monkeypatch.setattr( ingest.anomaly, "_HEURISTICS",
        [
            _fake_heuristic( "a", 1.0 ),
            _fake_heuristic( "b", 0.0 ),
        ] )
        monkeypatch.setattr( ingest.anomaly, "_WEIGHTS", { "a": 1.0, "b": 0.5 } )

        score, _ = compute_anomaly_score( { } )
        assert score == 1.0

    def test_compute_anomaly_score_no_heuristics_returns_0( self, monkeypatch ):
        monkeypatch.setattr( ingest.anomaly, "_HEURISTICS", [ ] )
        monkeypatch.setattr( ingest.anomaly, "_WEIGHTS", { "a": 1.0, "b": 0.5 } )

        score, _ = compute_anomaly_score( { } )
        assert score == 0.0

    def test_compute_anomaly_score_real_logs( self ):
        score, heuristics = compute_anomaly_score( TEST_LOGS[ 0 ] )
        assert score >= 0.0 and score <= 1.0
        assert len( heuristics ) == 3

    def test_compute_anomaly_score_combines_three_heuristics( self, monkeypatch ):
        monkeypatch.setattr( ingest.anomaly, "_HEURISTICS",
        [
            _fake_heuristic( "a", 0.8 ),
            _fake_heuristic( "b", 0.3 ),
            _fake_heuristic( "c", 0.5 )
        ] )
        monkeypatch.setattr( ingest.anomaly, "_WEIGHTS", { "a": 0.9, "b": 0.5, "c": 0.6 } )

        score, _ = compute_anomaly_score( { } )
        expected = 1 - ( 1 - 0.9*0.8 ) * ( 1 - 0.5*0.3 ) * ( 1 - 0.6*0.5 )
        assert score == pytest.approx( expected )

    def test_extra_results_none_unchanged( self, monkeypatch ):
        monkeypatch.setattr( ingest.anomaly, "_HEURISTICS",
            [ _fake_heuristic( "a", 0.8 ) ] )
        monkeypatch.setattr( ingest.anomaly, "_WEIGHTS", { "a": 1.0 } )

        score1, _ = compute_anomaly_score( { } )
        score2, _ = compute_anomaly_score( { }, extra_results=None )
        assert score1 == score2

    def test_extra_results_empty_list_same_as_none( self, monkeypatch ):
        monkeypatch.setattr( ingest.anomaly, "_HEURISTICS",
            [ _fake_heuristic( "a", 0.8 ) ] )
        monkeypatch.setattr( ingest.anomaly, "_WEIGHTS", { "a": 1.0 } )

        score_none, _   = compute_anomaly_score( { }, extra_results=None )
        score_empty, _  = compute_anomaly_score( { }, extra_results=[ ] )
        assert score_none == score_empty

    def test_extra_results_folded_into_noisy_or( self, monkeypatch ):
        monkeypatch.setattr( ingest.anomaly, "_HEURISTICS", [
            _fake_heuristic( "a", 0.5 ),
            _fake_heuristic( "b", 0.3 ),
        ] )
        monkeypatch.setattr( ingest.anomaly, "_WEIGHTS", {
            "a": 0.8, "b": 0.4,
            "port_scan_shape": 0.6, "host_sweep_shape": 0.7,
        } )

        extras = [
            HeuristicResult( name="port_scan_shape",  score=0.9 ),
            HeuristicResult( name="host_sweep_shape", score=0.2 ),
        ]

        score, results = compute_anomaly_score( { }, extra_results=extras )
        expected = 1 - ( 1 - 0.8*0.5 ) * ( 1 - 0.4*0.3 ) * ( 1 - 0.6*0.9 ) * ( 1 - 0.7*0.2 )
        assert score == pytest.approx( expected )
        assert len( results ) == 4

    def test_missing_weight_falls_back_to_1( self, monkeypatch ):
        monkeypatch.setattr( ingest.anomaly, "_HEURISTICS", [ ] )
        monkeypatch.setattr( ingest.anomaly, "_WEIGHTS", { } )

        extras = [
            HeuristicResult( name="port_scan_shape", score=0.5 ),
        ]
        score, _ = compute_anomaly_score( { }, extra_results=extras )
        assert score == 0.5

    def test_registered_weights_used_for_scan_sweep( self, monkeypatch ):
        """Confirm port_scan_shape / host_sweep_shape weights are actually
        registered and not silently falling back to 1.0."""
        monkeypatch.setattr( ingest.anomaly, "_HEURISTICS", [ ] )
        monkeypatch.setattr( ingest.anomaly, "_WEIGHTS", {
            "port_scan_shape":  0.2,
            "host_sweep_shape": 0.8,
        } )

        extras = [
            HeuristicResult( name="port_scan_shape",  score=1.0 ),
            HeuristicResult( name="host_sweep_shape", score=1.0 ),
        ]
        score, _ = compute_anomaly_score( { }, extra_results=extras )
        assert score == pytest.approx( 0.84 )


class TestEndToEndPipeline:
    def test_scanner_rows_score_higher_than_normal( self ):
        from datetime import datetime

        scanner = [
            {
                "src_ip":            "10.0.0.99",
                "dst_ip":            "192.168.1.1",
                "src_port":          50000,
                "dst_port":          i,
                "protocol":          "TCP",
                "packet_size_bytes": 100,
                "flags":             "SYN",
                "raw_payload":       { },
                "captured_at":       datetime.now( UTC ).isoformat( ),
            }
            for i in range( 25 )
        ]
        normal = [
            {
                "src_ip":            "10.0.0.1",
                "dst_ip":            "192.168.1.1",
                "src_port":          50000,
                "dst_port":          443,
                "protocol":          "TCP",
                "packet_size_bytes": 500,
                "flags":             "ACK",
                "raw_payload":       { },
                "captured_at":       datetime.now( UTC ).isoformat( ),
            }
            for _ in range( 3 )
        ]
        rows = scanner + normal

        batch_extras = _score_batch_heuristics( rows )
        assert len( batch_extras ) == len( rows )

        scanner_scores: list[ float ] = [ ]
        normal_scores:  list[ float ] = [ ]

        for i, row in enumerate( rows ):
            score, heuristics = compute_anomaly_score( row, extra_results=batch_extras[ i ] )
            assert len( heuristics ) == 5, f"row { i }: expected 5 heuristics, got { len( heuristics ) }"
            if row[ "src_ip" ] == "10.0.0.99":
                scanner_scores.append( score )
            else:
                normal_scores.append( score )

        assert min( scanner_scores ) > max( normal_scores ), (
            f"scanner min={ min( scanner_scores ) }, normal max={ max( normal_scores ) }"
        )

    def test_normal_rows_heuristic_count_is_5( self ):
        from datetime import datetime

        rows = [
            {
                "src_ip":            "10.0.0.1",
                "dst_ip":            "192.168.1.1",
                "src_port":          50000,
                "dst_port":          443,
                "protocol":          "TCP",
                "packet_size_bytes": 500,
                "flags":             "ACK",
                "raw_payload":       { },
                "captured_at":       datetime.now( UTC ).isoformat( ),
            }
            for _ in range( 3 )
        ]
        batch_extras = _score_batch_heuristics( rows )
        for i, row in enumerate( rows ):
            _, heuristics = compute_anomaly_score( row, extra_results=batch_extras[ i ] )
            assert len( heuristics ) == 5
            names = { r.name for r in heuristics }
            assert names == {
                "packet_size",
                "tcp_flags",
                "port_protocol_mismatch",
                "port_scan_shape",
                "host_sweep_shape",
            }, f"row { i }: unexpected heuristic names: { names }"

    def test_log_entry_row_requires_anomaly_reasons( self ):
        with pytest.raises( TypeError ):
            LogEntryRow(
                api_key_id=uuid4( ),
                user_id=uuid4( ),
                src_ip="1.1.1.1",
                dst_ip="1.1.1.1",
                src_port=10,
                dst_port=10,
                protocol="TCP",
                packet_size_bytes=10,
                flags=None,
                raw_payload={},
                captured_at=datetime.now( tz=UTC ),
                country_code="US",
                anomaly_score=1.0
            ) # type: ignore