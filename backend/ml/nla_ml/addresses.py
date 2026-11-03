"""
IP address helpers for the ML features.

The IP addresses should be stripped before the model sees them, the only info
that is retained is whether the IP address is private.

Behaviour of ip_address module has changed between python versions so tests to
make sure it is working as expected is included.
"""
from __future__ import annotations

from ipaddress import IPv4Address, IPv6Address, ip_address, ip_network

# Special ranges to make sure it is working as expected.
_PROBE_NETWORKS: tuple[ str, ... ] = (
    # IPv4
    "0.0.0.0/8", "10.0.0.0/8", "100.64.0.0/10", "127.0.0.0/8", "169.254.0.0/16", "172.16.0.0/12",
    "192.0.0.0/24", "192.0.0.0/29", "192.0.0.8/32", "192.0.0.9/32", "192.0.0.10/32", "192.0.0.170/31",
    "192.0.2.0/24", "192.31.196.0/24", "192.52.193.0/24", "192.88.99.0/24", "192.168.0.0/16",
    "192.175.48.0/24", "198.18.0.0/15", "198.51.100.0/24", "203.0.113.0/24", "224.0.0.0/4",
    "240.0.0.0/4", "255.255.255.255/32",
    # IPv6
    "::/128", "::1/128", "::ffff:0:0/96", "64:ff9b::/96", "64:ff9b:1::/48", "100::/64",
    "2001::/23", "2001::/32", "2001:1::1/128", "2001:1::2/128", "2001:1::3/128", "2001:2::/48",
    "2001:3::/32", "2001:4:112::/48", "2001:10::/28", "2001:20::/28", "2001:30::/28",
    "2001:db8::/32", "2002::/16", "3fff::/20", "5f00::/16", "fc00::/7", "fe80::/10",
    "fec0::/10", "ff00::/8",
)

def parse_ip( value: object ) -> IPv4Address | IPv6Address:
    """
    Parse an IP address, unwrapping IPv4-mapped IPv6 addresses (::ffff:a.b.c.d)
    to plain IPv4 so both produce the same features.
    Parameters:
        value (object): A string or `ipaddress` object.
    Returns:
        address (IPv4Address | IPv6Address): The parsed address.
    Raises:
        ValueError: If the value is not a valid IP address.
    """
    address = ip_address( str( value ) )
    if isinstance( address, IPv6Address ) and address.ipv4_mapped is not None:
        return address.ipv4_mapped
    return address

def is_private_ip( value: object ) -> bool:
    """
    Whether an address is private, per `ipaddress` `is_private`.
    """
    return parse_ip( value ).is_private

def is_private_probe( ) -> list[ tuple[ str, bool ] ]:
    """
    `is_private_ip` evaluated on the first, last and adjacent addresses of every
    `_PROBE_NETWORKS` range. Hashed into the feature fingerprint.
    Returns:
        probe (list[tuple[str, bool]]): (address, is_private) pairs, sorted.
    """
    addresses: set[ IPv4Address | IPv6Address ] = set( )
    for network in map( ip_network, _PROBE_NETWORKS ):
        top = 2 ** network.max_prefixlen - 1
        for edge in ( network.network_address, network.broadcast_address ):
            addresses.add( edge )
            if int( edge ) > 0:
                addresses.add( type( edge )( int( edge ) - 1 ) )
            if int( edge ) < top:
                addresses.add( type( edge )( int( edge ) + 1 ) )
    ordered = sorted( addresses, key=lambda a: ( a.version, int( a ) ) )
    return [ ( str( a ), is_private_ip( a ) ) for a in ordered ]
