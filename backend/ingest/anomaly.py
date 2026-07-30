from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from config import settings

_XMAS_FLAGS = frozenset( { "FIN", "PSH", "URG" } )
_INVALID_FLAG_PAIRS = (
    frozenset( { "SYN", "FIN" } ),
    frozenset( { "SYN", "RST" } )
)

_PORT_PROTOCOL_EXPECTATIONS: dict[ int, frozenset[ str ] ] = {
    20:    frozenset( { "TCP" } ),          # FTP data
    21:    frozenset( { "TCP" } ),          # FTP control
    22:    frozenset( { "TCP" } ),          # SSH
    23:    frozenset( { "TCP" } ),          # Telnet
    25:    frozenset( { "TCP" } ),          # SMTP
    53:    frozenset( { "TCP", "UDP" } ),   # DNS
    67:    frozenset( { "UDP" } ),          # DHCP server
    68:    frozenset( { "UDP" } ),          # DHCP client
    69:    frozenset( { "UDP" } ),          # TFTP
    80:    frozenset( { "TCP" } ),          # HTTP
    110:   frozenset( { "TCP" } ),          # POP3
    123:   frozenset( { "UDP" } ),          # NTP
    135:   frozenset( { "TCP" } ),          # MS-RPC
    137:   frozenset( { "UDP" } ),          # NetBIOS name
    138:   frozenset( { "UDP" } ),          # NetBIOS datagram
    139:   frozenset( { "TCP" } ),          # NetBIOS session
    143:   frozenset( { "TCP" } ),          # IMAP
    161:   frozenset( { "UDP" } ),          # SNMP
    162:   frozenset( { "UDP" } ),          # SNMP trap
    389:   frozenset( { "TCP" } ),          # LDAP
    443:   frozenset( { "TCP", "UDP" } ),   # HTTPS
    445:   frozenset( { "TCP" } ),          # SMB
    514:   frozenset( { "UDP" } ),          # Syslog
    636:   frozenset( { "TCP" } ),          # LDAPS
    1433:  frozenset( { "TCP" } ),          # MSSQL
    1521:  frozenset( { "TCP" } ),          # Oracle
    3306:  frozenset( { "TCP" } ),          # MySQL
    3389:  frozenset( { "TCP" } ),          # RDP
    5432:  frozenset( { "TCP" } ),          # PostgreSQL
    5900:  frozenset( { "TCP" } ),          # VNC
    6379:  frozenset( { "TCP" } ),          # Redis
    8080:  frozenset( { "TCP" } ),          # HTTP-alt
    8443:  frozenset( { "TCP" } ),          # HTTPS-alt
    27017: frozenset( { "TCP" } ),          # MongoDB
}

@dataclass
class HeuristicResult:
    name:   str
    score:  float
    detail: str | None = None

def _ramp( value: float, low: float, high: float ) -> float:
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

def _score_packet_size( entry: dict[ str, Any ] ) -> HeuristicResult:
    """
    Returns an anomaly score based on the packet size.
    Parameters:
        entry (dict): A dictionary containing the `packet_size_bytes` key.
    Returns:
        result (HeuristicResult): A score in the form of a `HeuristicResult` dataclass.
    """
    size = entry[ "packet_size_bytes" ]

    large_score = _ramp( size, low=settings.anomaly_packet_size_mtu, high=settings.anomaly_packet_size_jumbo_max )
    small_score = _ramp( settings.anomaly_packet_size_tiny_max - size, low=0, high=settings.anomaly_packet_size_tiny_max )

    score = max( large_score, small_score )
    detail = None
    if score > 0:
        detail = f"Packet size { size }B is unusually { 'large' if large_score >= small_score else 'small' }"

    return HeuristicResult( name="packet_size", score=score, detail=detail )

def _parse_flags( flags: str | None ) -> set[ str ] | None:
    """
    Parse the flags string into a set of the present flags.
    Parameters:
        flags (int | None): The flags string to be parsed.
    Returns:
        flags (set[str] | None): The flags parsed into a set, useful for comparisons.
    """
    if flags is None:
        return None
    return { f.strip( ).upper( ) for f in flags.split( "," ) if f.strip( ) }

def _score_tcp_flags( entry: dict[ str, Any ] ) -> HeuristicResult:
    """
    Returns an anomaly score based on the tcp flags contained within the packet.
    Parameters
        entry (dict): A dictionary containing the `protocol` key.
    Returns:
        result (HeuristicResult): A score in the form of a `HeuristicResult` dataclass.
    """
    if entry.get( "protocol" ) != "TCP":
        return HeuristicResult( name="tcp_flags", score=0.0 )

    flags = _parse_flags( entry.get( "flags" ) )

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
    expected = _PORT_PROTOCOL_EXPECTATIONS.get( port )
    return expected is not None and protocol not in expected


def _score_port_protocol_mismatch( entry: dict[ str, Any ] ) -> HeuristicResult:
    """
    Returns an anomaly score based on protocol-port mismatches.
    Parameters
        entry (dict): A dictionary containing the `protocol` key.
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
        detail_string = f"Port { dst_port } is expected to use {', '.join( _PORT_PROTOCOL_EXPECTATIONS[ int( dst_port ) ] ) }, not { protocol }"
        return HeuristicResult( name="port_protocol_mismatch", score=1.0, detail=detail_string )

    if src_port is not None and _check_port( int( src_port ), protocol ):
        detail_string = f"Port { src_port } is expected to use {', '.join( _PORT_PROTOCOL_EXPECTATIONS[ int( src_port ) ] ) }, not { protocol }"
        return HeuristicResult( name="port_protocol_mismatch", score=1.0, detail=detail_string )

    return HeuristicResult( name="port_protocol_mismatch", score=0.0 )

_HEURISTICS: list[ Callable[ [ dict[ str, Any ] ], HeuristicResult ] ] = [
    _score_packet_size,
    _score_tcp_flags,
    _score_port_protocol_mismatch
]

_WEIGHTS = {
    "packet_size":            settings.anomaly_weight_packet_size,
    "tcp_flags":              settings.anomaly_weight_tcp_flags,
    "port_protocol_mismatch": settings.anomaly_weight_mismatch_ports,
    "port_scan_shape":        settings.anomaly_weight_port_scan_shape,
    "host_sweep_shape":       settings.anomaly_weight_host_sweep_shape
}

def _score_batch_heuristics( rows: list[ dict[ str, Any ] ] ) -> list[ list[ HeuristicResult ] ]:
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

        port_scan_score  = _ramp( len( dst_ports ), low=settings.anomaly_port_scan_low,  high=settings.anomaly_port_scan_high )
        host_sweep_score = _ramp( len( dst_ips ),   low=settings.anomaly_host_sweep_low, high=settings.anomaly_host_sweep_high )

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

def compute_anomaly_score(
    entry: dict[ str, Any ],
    extra_results: list[ HeuristicResult ] | None = None
) -> tuple[ float, list[ HeuristicResult ] ]:
    results = [ heuristic( entry ) for heuristic in _HEURISTICS ]

    if extra_results:
        results.extend( extra_results )

    product_term = 1.0
    for result in results:
        weight = _WEIGHTS.get( result.name, 1.0 ) # Default to 1.0 so that missing weights are obvious
        product_term *= ( 1 - min( weight * result.score, 1.0 ) ) # weight musn't exceed 1.0

    score = 1 - product_term
    return score, results