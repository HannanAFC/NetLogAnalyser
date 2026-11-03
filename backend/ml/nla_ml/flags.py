"""
TCP flag parsing shared by the heuristics and the ML features.

Flags arrive as a comma-separated string, e.g. "SYN,ACK". `parse_flags` used to
live in `ingest/anomaly.py`.
"""
from __future__ import annotations

# The flags that get their own feature column, in column order.
TCP_FLAGS: tuple[ str, ... ] = ( "SYN", "ACK", "FIN", "RST", "PSH", "URG" )

def parse_flags( flags: str | None ) -> set[ str ] | None:
    """
    Parse the flags string into a set of the present flags.
    Tokens are stripped and upper-cased; empty tokens are dropped, so a
    malformed string such as "," parses to an empty set.
    Parameters:
        flags (str | None): The flags string to be parsed.
    Returns:
        flags (set[str] | None): The flags parsed into a set, or None if no flags string was sent.
    """
    if flags is None:
        return None
    return { f.strip( ).upper( ) for f in flags.split( "," ) if f.strip( ) }
