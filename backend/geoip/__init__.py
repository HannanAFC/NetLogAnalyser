from __future__ import annotations

import ipaddress
import logging

import geoip2.database
import geoip2.errors
from config import settings

logger = logging.getLogger( __name__ )

_reader: geoip2.database.Reader | None = None


def init_geoip( ) -> None:
    """Open the GeoLite2-Country database."""
    global _reader
    if _reader is not None:
        return
    try:
        _reader = geoip2.database.Reader( settings.geoip_db_path )
    except FileNotFoundError:
        logger.warning(
            "GeoLite2 database not found at- country lookups will return None."
        )
        _reader = None


def close_geoip( ) -> None:
    """Close the reader."""
    global _reader
    if _reader is not None:
        _reader.close()
        _reader = None


def lookup_country( ip: str ) -> str | None:
    """
    Return the ISO 3166-1 alpha-2 country code for an IP, or None.
    Parameters:
        ip (str): The IP address to lookup.
    Returns:
        country (str | None): Returns None for - an unloaded database, an unparseable IP, private/loopback/link-local/reserved addresses and addresses GeoLite2 has no record for.
    """
    if _reader is None:
        return None

    try:
        address = ipaddress.ip_address( ip )
    except ValueError:
        return None

    if address.is_private or address.is_loopback or address.is_link_local or address.is_reserved:
        return None

    try:
        response = _reader.country( ip )
    except geoip2.errors.AddressNotFoundError:
        return None

    return response.country.iso_code


def resolve_log_country( src_ip: str, dst_ip: str ) -> str | None:
    """
    Pick the most useful country code for a log entry. The destination IP is preferred but the source IP can be used as a fallback.
    Parameters:
        src_ip (str): The source IP.
        dst_ip (str): The destination IP.
    """
    return lookup_country( dst_ip ) or lookup_country( src_ip )