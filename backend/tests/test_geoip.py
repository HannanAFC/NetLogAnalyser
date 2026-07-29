from __future__ import annotations

from types import SimpleNamespace

import geoip as geoip_module
import geoip2.errors
import pytest
from geoip import close_geoip, lookup_country, resolve_log_country


class FakeReader:
    """
    Stands in for geoip2.database.Reader. Maps specific IPs to country
    codes and raises AddressNotFoundError for anything else, mirroring the
    real reader's behaviour for addresses it has no record of.
    """

    def __init__( self, known: dict[ str, str ] ) -> None:
        self._known = known

    def country( self, ip: str ):
        if ip not in self._known:
            raise geoip2.errors.AddressNotFoundError( "not found" )
        return SimpleNamespace( country=SimpleNamespace( iso_code=self._known[ ip ] ) )

    def close( self ) -> None:
        pass


@pytest.fixture( autouse=True )
def _reset_reader( ):
    """
    Ensure each test starts with a clean module-level reader and the
    real one (if any) is restored afterwards.
    """
    original = geoip_module._reader
    yield
    geoip_module._reader = original


def _install_fake_reader( known: dict[ str, str ] ) -> None:
    geoip_module._reader = FakeReader( known )


def test_lookup_country_returns_code_for_known_public_ip( ) -> None:
    _install_fake_reader( { "8.8.8.8": "US" } )
    assert lookup_country( "8.8.8.8" ) == "US"


def test_lookup_country_returns_none_when_reader_not_loaded( ) -> None:
    geoip_module._reader = None
    assert lookup_country( "8.8.8.8" ) is None


def test_lookup_country_returns_none_for_private_ip( ) -> None:
    _install_fake_reader( { } )
    assert lookup_country( "10.0.0.5" ) is None
    assert lookup_country( "192.168.1.1" ) is None
    assert lookup_country( "127.0.0.1" ) is None


def test_lookup_country_returns_none_for_unparseable_ip( ) -> None:
    _install_fake_reader( { } )
    assert lookup_country( "not-an-ip" ) is None


def test_lookup_country_returns_none_when_address_not_found( ) -> None:
    _install_fake_reader( { "8.8.8.8": "US" } )
    assert lookup_country( "203.0.113.1" ) is None  # TEST-NET-3, deliberately absent


def test_resolve_log_country_prefers_destination( ) -> None:
    _install_fake_reader( { "1.2.3.4": "GB", "5.6.7.8": "DE" } )
    assert resolve_log_country( src_ip="1.2.3.4", dst_ip="5.6.7.8" ) == "DE"


def test_resolve_log_country_falls_back_to_source_when_destination_is_private( ) -> None:
    _install_fake_reader( { "1.2.3.4": "GB" } )
    assert resolve_log_country( src_ip="1.2.3.4", dst_ip="10.0.0.1" ) == "GB"


def test_resolve_log_country_falls_back_to_source_when_destination_unresolvable( ) -> None:
    _install_fake_reader( { "1.2.3.4": "GB" } )
    assert resolve_log_country( src_ip="1.2.3.4", dst_ip="203.0.113.1" ) == "GB"


def test_resolve_log_country_returns_none_when_neither_resolves( ) -> None:
    _install_fake_reader( { } )
    assert resolve_log_country( src_ip="10.0.0.1", dst_ip="10.0.0.2" ) is None


def test_close_geoip_clears_the_reader( ) -> None:
    _install_fake_reader( { "8.8.8.8": "US" } )
    close_geoip( )
    assert geoip_module._reader is None