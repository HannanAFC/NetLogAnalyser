"""
ML scoring at ingest: startup loading (fail-fast), thread-pool scoring, and
ML reasons reaching stored rows. Models are tiny ones trained per test session.
"""
from __future__ import annotations

import json
import random
import threading
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pytest
from httpx import AsyncClient
from nla_ml.features import featurize
from nla_ml.inference import ModelLoadError, calibrate_iforest, export_model
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import ingest.ml
from config import settings
from ingest.anomaly import _WEIGHTS, compute_anomaly_score
from ingest.ml import close_ml, init_ml, loaded_models, score_batch_ml
from models.models import LogEntry


def _entry( rng: random.Random, bad: bool ) -> dict:
    return {
        "src_ip": f"10.0.0.{ rng.randint( 1, 254 ) }", "dst_ip": f"93.184.{ rng.randint( 0, 255 ) }.1",
        "src_port": rng.randint( 1024, 65535 ),
        "dst_port": rng.choice( [ 23, 3389 ] if bad else [ 80, 443 ] ),
        "protocol": "TCP",
        "packet_size_bytes": rng.choice( [ 0, 1 ] ) if bad else rng.randint( 60, 1500 ),
        "flags": "FIN,PSH,URG" if bad else "ACK",
    }

@pytest.fixture( scope="session" )
def model_dir( tmp_path_factory ) -> Path:
    rng = random.Random( 0 )
    labels  = np.array( [ int( rng.random( ) < 0.3 ) for _ in range( 300 ) ] )
    X       = featurize( [ _entry( rng, bool( b ) ) for b in labels ] )
    root    = tmp_path_factory.mktemp( "models" )

    rf = RandomForestClassifier( n_estimators=10, max_depth=4, random_state=0 ).fit( X, labels )
    export_model( rf, "rf", root / "rf", model_version="test-rf" )

    iforest = IsolationForest( n_estimators=20, random_state=0 ).fit( X[ labels == 0 ] )
    export_model( iforest, "iforest", root / "iforest", model_version="test-if", calibration=calibrate_iforest( iforest, X[ labels == 0 ] ) )
    return root

@pytest.fixture
def ml_on( monkeypatch, model_dir ):
    monkeypatch.setattr( settings, "ml_enabled", True )
    monkeypatch.setattr( settings, "ml_model_dir", str( model_dir ) )
    monkeypatch.setattr( settings, "ml_models", [ "rf", "iforest" ] )
    close_ml( )
    init_ml( )
    yield
    close_ml( )

@pytest.fixture( autouse=True )
def _reset_ml( ):
    yield
    close_ml( )

def _scoring_input( **overrides ) -> dict:
    entry = {
        "src_ip": "10.0.0.5", "dst_ip": "93.184.216.34", "src_port": 51515, "dst_port": 443,
        "protocol": "TCP", "packet_size_bytes": 60, "flags": "ACK",
        "raw_payload": { }, "captured_at": datetime.now( UTC ).isoformat( ),
        "src_country_code": None, "dst_country_code": "US", "src_geo_status": "private", "dst_geo_status": "resolved",
    }
    entry.update( overrides )
    return entry


# ---------------------------------------------------------------- startup

def test_disabled_loads_nothing( monkeypatch ):
    monkeypatch.setattr( settings, "ml_enabled", False )
    init_ml( )
    assert loaded_models( ) == { }

def test_enabled_loads_every_configured_model( ml_on ):
    assert loaded_models( ) == { "rf": "test-rf", "iforest": "test-if" }

def test_enabled_can_load_a_subset( monkeypatch, model_dir ):
    monkeypatch.setattr( settings, "ml_enabled", True )
    monkeypatch.setattr( settings, "ml_model_dir", str( model_dir ) )
    monkeypatch.setattr( settings, "ml_models", [ "rf" ] )
    init_ml( )
    assert loaded_models( ) == { "rf": "test-rf" }

def test_missing_model_refuses_to_start( monkeypatch, tmp_path ):
    monkeypatch.setattr( settings, "ml_enabled", True )
    monkeypatch.setattr( settings, "ml_model_dir", str( tmp_path ) )
    monkeypatch.setattr( settings, "ml_models", [ "rf" ] )
    with pytest.raises( ModelLoadError, match="missing model.joblib" ):
        init_ml( )
    assert loaded_models( ) == { }

def test_incompatible_model_refuses_to_start( monkeypatch, model_dir, tmp_path ):
    # Copy the rf artifact and claim it was built for different features
    bad = tmp_path / "rf"
    bad.mkdir( )
    ( bad / "model.joblib" ).write_bytes( ( model_dir / "rf" / "model.joblib" ).read_bytes( ) )
    metadata = json.loads( ( model_dir / "rf" / "metadata.json" ).read_text( ) )
    ( bad / "metadata.json" ).write_text( json.dumps( { **metadata, "feature_version": 999 } ) )

    monkeypatch.setattr( settings, "ml_enabled", True )
    monkeypatch.setattr( settings, "ml_model_dir", str( tmp_path ) )
    monkeypatch.setattr( settings, "ml_models", [ "rf" ] )
    with pytest.raises( ModelLoadError, match="feature_version" ):
        init_ml( )

def test_app_startup_fails_with_bad_model( monkeypatch, tmp_path ):
    from fastapi.testclient import TestClient

    from main import app

    monkeypatch.setattr( settings, "ml_enabled", True )
    monkeypatch.setattr( settings, "ml_model_dir", str( tmp_path ) )
    monkeypatch.setattr( settings, "ml_models", [ "rf" ] )
    with pytest.raises( ModelLoadError ), TestClient( app ):
        pass


# ---------------------------------------------------------------- scoring

@pytest.mark.anyio
async def test_scores_off_the_event_loop( ml_on, monkeypatch ):
    threads: list[ str ] = [ ]
    real = ingest.ml._score_sync

    def spy( entries ):
        threads.append( threading.current_thread( ).name )
        return real( entries )

    monkeypatch.setattr( ingest.ml, "_score_sync", spy )
    await score_batch_ml( [ _scoring_input( ) ] )
    assert threads and threads[ 0 ].startswith( "ml-inference" )
    assert threads[ 0 ] != threading.current_thread( ).name

@pytest.mark.anyio
async def test_scores_every_row_with_every_model( ml_on ):
    entries = [ _scoring_input( ), _scoring_input( dst_port=23, packet_size_bytes=0, flags="FIN,PSH,URG" ) ]
    results = await score_batch_ml( entries )
    assert len( results ) == 2
    for row in results:
        assert [ r.name for r in row ] == [ "ml_rf", "ml_iforest" ]
        assert all( 0.0 <= r.score <= 1.0 for r in row )
    assert results[ 1 ][ 0 ].score > results[ 0 ][ 0 ].score  # the XMAS-flag row looks worse to the RF

@pytest.mark.anyio
async def test_disabled_scores_nothing( ):
    assert await score_batch_ml( [ _scoring_input( ) ] ) == [ [ ] ]

@pytest.mark.anyio
async def test_scoring_failure_falls_back_to_heuristics( ml_on, monkeypatch, caplog ):
    def boom( entries ):
        raise RuntimeError( "kaboom" )
    monkeypatch.setattr( ingest.ml, "_score_sync", boom )
    assert await score_batch_ml( [ _scoring_input( ), _scoring_input( ) ] ) == [ [ ], [ ] ]
    assert "ML scoring failed" in caplog.text

@pytest.mark.anyio
async def test_ml_results_feed_the_noisy_or( ml_on ):
    entry = _scoring_input( dst_port=23, packet_size_bytes=0, flags="FIN,PSH,URG" )
    ml_results = ( await score_batch_ml( [ entry ] ) )[ 0 ]
    without, _ = compute_anomaly_score( entry )
    with_ml, results = compute_anomaly_score( entry, extra_results=ml_results )
    assert with_ml >= without
    assert { "ml_rf", "ml_iforest" } <= { r.name for r in results }
    assert _WEIGHTS[ "ml_rf" ] == settings.ml_weight_rf
    assert _WEIGHTS[ "ml_iforest" ] == settings.ml_weight_iforest


# ---------------------------------------------------------------- through the API

async def _stored_reasons( db_session: AsyncSession, user_id ) -> list[ list[ dict ] ]:
    rows = await db_session.execute( select( LogEntry.anomaly_reasons ).where( LogEntry.user_id == user_id ) )
    return [ r for ( r, ) in rows ]

def _api_entry( **overrides ) -> dict:
    entry = {
        "src_ip": "10.0.0.5", "dst_ip": "93.184.216.34", "src_port": 51515, "dst_port": 23,
        "protocol": "TCP", "packet_size_bytes": 0, "flags": "FIN,PSH,URG",
        "raw_payload": { }, "captured_at": datetime.now( UTC ).isoformat( ),
    }
    entry.update( overrides )
    return entry

@pytest.mark.anyio
async def test_ingest_stores_ml_reasons( ml_on, client: AsyncClient, db_session: AsyncSession, api_key ):
    response = await client.post( "/ingest", json={ "entries": [ _api_entry( ) ] }, headers={ "X-API-Key": api_key.raw_key } )
    assert response.status_code == 207 and response.json( )[ "accepted" ] == 1

    ( reasons, ) = await _stored_reasons( db_session, api_key.user_id )
    names = { r[ "name" ] for r in reasons }
    assert "ml_rf" in names
    rf_reason = next( r for r in reasons if r[ "name" ] == "ml_rf" )
    assert rf_reason[ "detail" ].startswith( "rf model test-rf:" )

@pytest.mark.anyio
async def test_ingest_without_ml_is_unchanged( client: AsyncClient, db_session: AsyncSession, api_key ):
    response = await client.post( "/ingest", json={ "entries": [ _api_entry( ) ] }, headers={ "X-API-Key": api_key.raw_key } )
    assert response.status_code == 207

    ( reasons, ) = await _stored_reasons( db_session, api_key.user_id )
    assert not any( r[ "name" ].startswith( "ml_" ) for r in reasons )
    assert any( r[ "name" ] == "tcp_flags" for r in reasons )
