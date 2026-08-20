from __future__ import annotations

from types import SimpleNamespace

import geoip as geoip_module
import geoip2.errors
import pytest
from geoip import close_geoip, lookup_country


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
    country, status = lookup_country( "8.8.8.8" )
    assert country == "US"
    assert status.value == "resolved"


def test_lookup_country_returns_none_when_reader_not_loaded( ) -> None:
    geoip_module._reader = None
    country, status = lookup_country( "8.8.8.8" )
    assert country is None
    assert status.value == "unavailable"


def test_lookup_country_returns_none_for_private_ip( ) -> None:
    _install_fake_reader( { } )
    country, status = lookup_country( "10.0.0.5" )
    assert country is None
    assert status.value == "private"
    country, status = lookup_country( "192.168.1.1" )
    assert country is None
    assert status.value == "private"
    country, status = lookup_country( "127.0.0.1" )
    assert country is None
    assert status.value == "private"


def test_lookup_country_returns_none_for_unparseable_ip( ) -> None:
    _install_fake_reader( { } )
    country, status = lookup_country( "not-an-ip" )
    assert country is None
    assert status.value == "unavailable"


def test_lookup_country_returns_none_when_address_not_found( ) -> None:
    _install_fake_reader( { "8.8.8.8": "US" } )
    country, status = lookup_country( "203.0.113.1" )
    assert country is None
    assert status.value == "private"


def test_close_geoip_clears_the_reader( ) -> None:
    _install_fake_reader( { "8.8.8.8": "US" } )
    close_geoip( )
    assert geoip_module._reader is None