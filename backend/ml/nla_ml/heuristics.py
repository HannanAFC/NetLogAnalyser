"""
The production anomaly heuristics, as pure functions.

Needs no settings, `.env` or database. Entries are `LogEntryCreate`-shaped
dicts (protocol as an upper-case string), e.g. the output of a dataset adapter.

Two kinds of heuristic:
- per entry: packet size, TCP flags, port/protocol mismatch
- per batch: port-scan and host-sweep shape, from how many distinct ports and
  destinations each src_ip touched *in the same ingest batch*. Results depend on
  how entries are batched, so `score_entries` replays them in ingest-sized batches.

Scores combine with a weighted noisy-OR: 1 - prod( 1 - min( weight * score, 1 ) ).
A result with no weight counts at full strength (1.0), so a missing weight is obvious.
"""
from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, field
from typing import Any

from nla_ml.flags import parse_flags
from nla_ml.ports import PORT_PROTOCOL_EXPECTATIONS

_XMAS_FLAGS = frozenset( { "FIN", "PSH", "URG" } )
_INVALID_FLAG_PAIRS = (
    frozenset( { "SYN", "FIN" } ),
    frozenset( { "SYN", "RST" } )
)

# Same values as the backend's ANOMALY_WEIGHT_* defaults (a backend test keeps them equal)
DEFAULT_WEIGHTS: Mapping[ str, float ] = {
    "packet_size":            0.5,
    "tcp_flags":              0.9,
    "port_protocol_mismatch": 0.6,
    "port_scan_shape":        0.7,
    "host_sweep_shape":       0.6,
}

@dataclass
class HeuristicResult:
    name:   str
    score:  float
    detail: str | None = None

@dataclass( frozen=True )
class HeuristicConfig:
    """
    Thresholds and weights for the heuristics. Defaults match the backend's
    ANOMALY_* setting defaults (a backend test keeps them equal).
    """
    packet_size_mtu:       int = 1500
    packet_size_jumbo_max: int = 9000
    packet_size_tiny_max:  int = 40
    port_scan_low:         int = 5
    port_scan_high:        int = 25
    host_sweep_low:        int = 5
    host_sweep_high:       int = 20
    weights:               Mapping[ str, float ] = field( default_factory=lambda: dict( DEFAULT_WEIGHTS ) )

    def as_dict( self ) -> dict[ str, Any ]:
        """JSON-friendly copy, for recording the baseline's config next to results."""
        data = asdict( self )
        data[ "weights" ] = dict( self.weights )
        return data

DEFAULT_CONFIG = HeuristicConfig( )

def ramp( value: float, low: float, high: float ) -> float:
    """
    Compute a score for a value in between a low risk and a high risk value, returns 0.0 when below the low value, 1.0 when above the high value and a linear value in between.
    Parameters:
        value (float): The value to compute a score for.
        low (float): The low end value for the computation.
        high (float): A high risk value which equates to an anomalous result.
    Returns:
        score (float): The computed score.
    """
    if value <= low:
        return 0.0
    if value >= high:
        return 1.0
    return ( value - low ) / ( high - low )

def score_packet_size( entry: Mapping[ str, Any ], config: HeuristicConfig = DEFAULT_CONFIG ) -> HeuristicResult:
    """
    Returns an anomaly score based on the packet size.
    Parameters:
        entry (Mapping): A dictionary containing the `packet_size_bytes` key.
        config (HeuristicConfig): Thresholds to use.
    Returns:
        result (HeuristicResult): A score in the form of a `HeuristicResult` dataclass.
    """
    size = entry[ "packet_size_bytes" ]

    large_score = ramp( size, low=config.packet_size_mtu, high=config.packet_size_jumbo_max )
    small_score = ramp( config.packet_size_tiny_max - size, low=0, high=config.packet_size_tiny_max )

    score = max( large_score, small_score )
    detail = None
    if score > 0:
        detail = f"Packet size { size }B is unusually { 'large' if large_score >= small_score else 'small' }"

    return HeuristicResult( name="packet_size", score=score, detail=detail )

def score_tcp_flags( entry: Mapping[ str, Any ], config: HeuristicConfig = DEFAULT_CONFIG ) -> HeuristicResult:
    """
    Returns an anomaly score based on the tcp flags contained within the packet.
    Parameters:
        entry (Mapping): A dictionary containing the `protocol` key.
        config (HeuristicConfig): Unused; accepted so every per-entry heuristic has the same signature.
    Returns:
        result (HeuristicResult): A score in the form of a `HeuristicResult` dataclass.
    """
    if entry.get( "protocol" ) != "TCP":
        return HeuristicResult( name="tcp_flags", score=0.0 )

    flags = parse_flags( entry.get( "flags" ) )

    if flags is None:
        return HeuristicResult( name="tcp_flags", score=0.0 )

    # Malformed strings e.g. "," also count as empty
    if len( flags ) == 0:
        return HeuristicResult( name="tcp_flags", score=1.0, detail="Packet has no flags set" )

    if _XMAS_FLAGS <= flags:
        return HeuristicResult( name="tcp_flags", score=1.0, detail="Packet contains XMAS flags" )

    for invalid_flag_pair in _INVALID_FLAG_PAIRS:
        if invalid_flag_pair <= flags:
            return HeuristicResult( name="tcp_flags", score=1.0, detail=f"Packet has invalid flag pair ( {', '.join( sorted( invalid_flag_pair ) ) } )" )

    return HeuristicResult( name="tcp_flags", score=0.0 )

def _check_port( port: int, protocol: str ) -> bool:
    """
    Checks if `port` is in the expectations table and `protocol` isn't one of its allowed values.
    Parameters:
        port (int): The port number.
        protocol (str): The protocol the packet used.
    Returns:
        is_expected_port (bool): Whether the protocol doesn't match what is expected for the port
    """
    expected = PORT_PROTOCOL_EXPECTATIONS.get( port )
    return expected is not None and protocol not in expected

def score_port_protocol_mismatch( entry: Mapping[ str, Any ], config: HeuristicConfig = DEFAULT_CONFIG ) -> HeuristicResult:
    """
    Returns an anomaly score based on protocol-port mismatches.
    Parameters:
        entry (Mapping): A dictionary containing the `protocol` key.
        config (HeuristicConfig): Unused; accepted so every per-entry heuristic has the same signature.
    Returns:
        result (HeuristicResult): A score in the form of a `HeuristicResult` dataclass.
    """
    protocol = entry.get( "protocol" )
    src_port = entry.get( "src_port" )
    dst_port = entry.get( "dst_port" )

    if protocol == "ICMP" and ( src_port != 0 or dst_port != 0 ):
        return HeuristicResult( name="port_protocol_mismatch", score=1.0, detail=f"Port 0 expected for ICMP protocol, received destination port { dst_port } and source port: { src_port }" )

    if protocol not in ( "TCP", "UDP" ):
        return HeuristicResult( name="port_protocol_mismatch", score=0.0 )

    if dst_port is not None and _check_port( int( dst_port ), protocol ):
        detail_string = f"Port { dst_port } is expected to use {', '.join( PORT_PROTOCOL_EXPECTATIONS[ int( dst_port ) ] ) }, not { protocol }"
        return HeuristicResult( name="port_protocol_mismatch", score=1.0, detail=detail_string )

    if src_port is not None and _check_port( int( src_port ), protocol ):
        detail_string = f"Port { src_port } is expected to use {', '.join( PORT_PROTOCOL_EXPECTATIONS[ int( src_port ) ] ) }, not { protocol }"
        return HeuristicResult( name="port_protocol_mismatch", score=1.0, detail=detail_string )

    return HeuristicResult( name="port_protocol_mismatch", score=0.0 )

EntryHeuristic = Callable[ [ Mapping[ str, Any ], HeuristicConfig ], HeuristicResult ]

ENTRY_HEURISTICS: tuple[ EntryHeuristic, ... ] = (
    score_packet_size,
    score_tcp_flags,
    score_port_protocol_mismatch,
)

def score_batch_heuristics( rows: Sequence[ Mapping[ str, Any ] ], config: HeuristicConfig = DEFAULT_CONFIG ) -> list[ list[ HeuristicResult ] ]:
    """
    For each row, returns extra HeuristicResults reflecting scan/sweep-shaped
    behaviour from that row's src_ip elsewhere in this same batch.
    """
    by_src_ip: dict[ str, list[ int ] ] = defaultdict( list )
    for i, row in enumerate( rows ):
        by_src_ip[ row[ "src_ip" ] ].append( i )

    extra_per_row: list[ list[ HeuristicResult ] ] = [ [ ] for _ in rows ]

    for src_ip, indices in by_src_ip.items( ):
        dst_ports = { rows[ i ][ "dst_port" ] for i in indices }
        dst_ips   = { rows[ i ][ "dst_ip" ]   for i in indices }

        port_scan_score  = ramp( len( dst_ports ), low=config.port_scan_low,  high=config.port_scan_high )
        host_sweep_score = ramp( len( dst_ips ),   low=config.host_sweep_low, high=config.host_sweep_high )

        port_scan_result = HeuristicResult(
            name="port_scan_shape",
            score=port_scan_score,
            detail=f"{ src_ip } touched { len( dst_ports ) } distinct ports in this batch" if port_scan_score > 0 else None,
        )
        host_sweep_result = HeuristicResult(
            name="host_sweep_shape",
            score=host_sweep_score,
            detail=f"{ src_ip } touched { len( dst_ips ) } distinct destinations in this batch" if host_sweep_score > 0 else None,
        )

        for i in indices:
            extra_per_row[ i ].append( port_scan_result )
            extra_per_row[ i ].append( host_sweep_result )

    return extra_per_row

def combine_scores( results: Iterable[ HeuristicResult ], weights: Mapping[ str, float ] ) -> float:
    """
    Weighted noisy-OR of heuristic results. Results without a weight count at 1.0.
    """
    product_term = 1.0
    for result in results:
        weight = weights.get( result.name, 1.0 ) # Default to 1.0 so that missing weights are obvious
        product_term *= ( 1 - min( weight * result.score, 1.0 ) ) # weight musn't exceed 1.0
    return 1 - product_term

def compute_anomaly_score(
    entry:         Mapping[ str, Any ],
    config:        HeuristicConfig = DEFAULT_CONFIG,
    extra_results: Sequence[ HeuristicResult ] | None = None,
) -> tuple[ float, list[ HeuristicResult ] ]:
    """
    Score one entry with the per-entry heuristics plus any `extra_results`
    (batch heuristics, ML results). Returns the combined score and every result.
    """
    results = [ heuristic( entry, config ) for heuristic in ENTRY_HEURISTICS ]
    if extra_results:
        results.extend( extra_results )
    return combine_scores( results, config.weights ), results

def score_entries(
    entries:    Sequence[ Mapping[ str, Any ] ],
    config:     HeuristicConfig = DEFAULT_CONFIG,
    batch_size: int = 50,
) -> tuple[ list[ float ], list[ list[ HeuristicResult ] ] ]:
    """
    Score entries the way ingest would if they arrived in order, `batch_size` at a time
    (log_sender's default is 50; the API allows up to 500). The batch heuristics only see
    entries in the same batch, so the result depends on `batch_size`: keep it fixed when
    comparing against models.
    Returns:
        scores (list[float]): One heuristic score per entry.
        results (list[list[HeuristicResult]]): Every result per entry, per-entry heuristics first.
    """
    if batch_size < 1:
        raise ValueError( "batch_size must be >= 1" )
    scores:  list[ float ] = [ ]
    results: list[ list[ HeuristicResult ] ] = [ ]
    for start in range( 0, len( entries ), batch_size ):
        batch = entries[ start:start + batch_size ]
        for entry, extras in zip( batch, score_batch_heuristics( batch, config ) ):
            score, row = compute_anomaly_score( entry, config, extras )
            scores.append( score )
            results.append( row )
    return scores, results
