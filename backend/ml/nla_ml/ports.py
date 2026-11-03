"""
Port tables and port bucketing shared by the heuristics and the ML features.
"""
from __future__ import annotations

from enum import IntEnum

PORT_PROTOCOL_EXPECTATIONS: dict[ int, frozenset[ str ] ] = {
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

# IANA ranges. Port 0 is reserved, so it gets its own bucket (ICMP and
# OTHER-protocol entries carry port 0).
WELL_KNOWN_PORT_MAX = 1023
REGISTERED_PORT_MAX = 49151
PORT_MAX            = 65535

class PortBucket( IntEnum ):
    ZERO       = 0  # port 0 (no port, e.g. ICMP)
    WELL_KNOWN = 1  # 1 - 1023
    REGISTERED = 2  # 1024 - 49151
    EPHEMERAL  = 3  # 49152 - 65535

def port_bucket( port: int ) -> PortBucket:
    """
    Bucket a port into its IANA range.
    Parameters:
        port (int): A port number in [0, 65535].
    Returns:
        bucket (PortBucket): The range the port falls into.
    """
    if port == 0:
        return PortBucket.ZERO
    if port <= WELL_KNOWN_PORT_MAX:
        return PortBucket.WELL_KNOWN
    if port <= REGISTERED_PORT_MAX:
        return PortBucket.REGISTERED
    return PortBucket.EPHEMERAL

def is_well_known_port( port: int ) -> bool:
    """
    Whether a port is in the well-known range (1 - 1023). Port 0 is not.
    """
    return 1 <= port <= WELL_KNOWN_PORT_MAX
