"""
Checks that the shared nla-ml package stays in sync with the backend.
The package's own behaviour is tested in ml/tests.
"""
from __future__ import annotations

from datetime import UTC, datetime

import nla_ml.flags
import nla_ml.ports
from nla_ml.compat import SKLEARN_VERSION, assert_sklearn_version
from nla_ml.features import FEATURE_COLUMNS, INPUT_FIELDS, PROTOCOLS, featurize

import ingest.anomaly
from geoip import GeoStatus
from ingest.schemas import LogEntryCreate, ProtocolEnum
from ipaddress import ip_address


def test_heuristics_use_the_shared_tables( ):
    # One source of truth: anomaly.py must not keep its own copies
    assert ingest.anomaly.PORT_PROTOCOL_EXPECTATIONS is nla_ml.ports.PORT_PROTOCOL_EXPECTATIONS
    assert ingest.anomaly.parse_flags is nla_ml.flags.parse_flags
    assert not hasattr( ingest.anomaly, "_PORT_PROTOCOL_EXPECTATIONS" )
    assert not hasattr( ingest.anomaly, "_parse_flags" )

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
