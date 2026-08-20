"""Synthetic network log entry generation.

Every entry produced here matches the ingest API's `LogEntryCreate` schema
exactly (`extra="forbid"` on the backend means it must not include computed
fields like `anomaly_score`, `country_code`, or `user_id`).
"""
from __future__ import annotations

import ipaddress
import random
from datetime import datetime, timedelta, timezone
from typing import Any

from config import COMMON_PORTS, SUSPICIOUS_PORTS, SyntheticConfig


def _random_ip( cidr: str ) -> str:
    network = ipaddress.ip_network( cidr, strict=False )
    # Clamp the search space for huge ranges (e.g. 0.0.0.0/0) so this stays fast.
    span = min( network.num_addresses - 2, 2 ** 24 ) if network.num_addresses > 2 else 0
    if span <= 0:
        return str( network.network_address )
    offset = random.randint( 1, span )
    return str( network.network_address + offset )


def _weighted_protocol( weights: dict[str, float] ) -> str:
    protocols = list( weights.keys( ) )
    probs     = list( weights.values( ) )
    return random.choices( protocols, weights=probs, k=1 )[ 0 ]


def _tcp_flags( anomalous: bool ) -> str | None:
    if anomalous:
        return random.choice( [ "SYN", "FIN,PSH,URG", "RST", "SYN,RST" ] )
    return random.choice( [ None, "SYN,ACK", "ACK", "PSH,ACK", "FIN,ACK" ] )


def generate_entry( cfg: SyntheticConfig, *, now: datetime | None = None ) -> dict[ str, Any ]:
    """Build a single log entry dict matching the ingest API's LogEntryCreate schema."""
    now       = now or datetime.now( timezone.utc )
    anomalous = random.random( ) < cfg.anomaly_rate
    protocol  = _weighted_protocol( cfg.protocol_weights )

    if anomalous:
        dst_port    = random.choice( SUSPICIOUS_PORTS )
        packet_size = random.choice( [ 0, 1, 40, 60 ] )  # tiny scan-style packets
    else:
        dst_port    = random.choice( COMMON_PORTS )
        packet_size = random.randint( cfg.min_packet_size, cfg.max_packet_size )

    entry: dict[ str, Any ] = {
        "src_ip":            _random_ip( cfg.src_subnet ),
        "dst_ip":            _random_ip( cfg.dst_subnet ),
        "src_port":          random.randint( 1024, 65535 ),
        "dst_port":          dst_port,
        "protocol":          protocol,
        "packet_size_bytes": packet_size,
        "captured_at":       ( now - timedelta( milliseconds=random.randint( 0, 500 ) ) ).isoformat( ),
        "raw_payload":
        {
            "synthetic":  True,
            "anomalous":  anomalous,
            "generator":  "log_sender"
        }
    }

    if protocol == "TCP":
        flags = _tcp_flags( anomalous )
        if flags:
            entry[ "flags" ] = flags[ :20 ]

    return entry


def generate_batch( cfg: SyntheticConfig, size: int ) -> list[dict[str, Any]]:
    now = datetime.now( timezone.utc )
    return [ generate_entry( cfg, now=now ) for _ in range( size ) ]
