"""
Tests for model export/load/scoring. Need scikit-learn (the `sklearn` extra).
"""
from __future__ import annotations

import json
import random

import numpy as np
import pytest

pytest.importorskip( "sklearn" )

from nla_ml import inference
from nla_ml.compat import SKLEARN_VERSION
from nla_ml.features import FEATURE_COLUMNS, featurize
from nla_ml.inference import (
    METADATA_FILE,
    MODEL_FILE,
    ModelLoadError,
    calibrate_iforest,
    export_model,
    load_model,
)
from sklearn.ensemble import IsolationForest, RandomForestClassifier


def _entries( n: int, seed: int = 0 ) -> tuple[ list[ dict ], list[ int ] ]:
    rng = random.Random( seed )
    entries, labels = [ ], [ ]
    for _ in range( n ):
        bad = rng.random( ) < 0.2
        entries.append( {
            "src_ip": f"10.0.{ rng.randint( 0, 255 ) }.{ rng.randint( 1, 254 ) }",
            "dst_ip": f"{ rng.randint( 1, 223 ) }.{ rng.randint( 0, 255 ) }.0.1",
            "src_port": rng.randint( 1024, 65535 ),
            "dst_port": rng.choice( [ 22, 23, 3389, 445 ] if bad else [ 80, 443, 53 ] ),
            "protocol": rng.choice( [ "TCP", "UDP" ] ),
            "packet_size_bytes": rng.choice( [ 0, 1, 40 ] ) if bad else rng.randint( 60, 1500 ),
            "flags": rng.choice( [ "FIN,PSH,URG", "SYN,RST" ] ) if bad else rng.choice( [ "ACK", "PSH,ACK", None ] ),
        } )
        labels.append( int( bad ) )
    return entries, labels

@pytest.fixture( scope="module" )
def data( ):
    entries, labels = _entries( 400 )
    return featurize( entries ), np.array( labels )

@pytest.fixture( scope="module" )
def rf( data ):
    X, y = data
    return RandomForestClassifier( n_estimators=10, max_depth=5, random_state=0 ).fit( X, y )

@pytest.fixture( scope="module" )
def iforest( data ):
    X, y = data
    return IsolationForest( n_estimators=20, random_state=0 ).fit( X[ y == 0 ] )

@pytest.fixture
def rf_dir( tmp_path, rf ):
    export_model( rf, "rf", tmp_path / "rf", model_version="test-rf-1" )
    return tmp_path / "rf"

@pytest.fixture
def iforest_dir( tmp_path, iforest, data ):
    X, y = data
    export_model( iforest, "iforest", tmp_path / "iforest", model_version="test-if-1", calibration=calibrate_iforest( iforest, X[ y == 0 ] ) )
    return tmp_path / "iforest"

def _edit_metadata( directory, **changes ):
    path = directory / METADATA_FILE
    metadata = json.loads( path.read_text( ) )
    metadata.update( changes )
    path.write_text( json.dumps( metadata ) )


# ---------------------------------------------------------------- round trip

def test_rf_round_trip_scores_in_unit_interval( rf_dir, data ):
    X, y = data
    model = load_model( rf_dir, "rf" )
    scores = model.score( X )
    assert scores.dtype == np.float64 and scores.shape == ( len( X ), )
    assert np.all( ( scores >= 0 ) & ( scores <= 1 ) )
    assert scores[ y == 1 ].mean( ) > scores[ y == 0 ].mean( )
    assert model.version == "test-rf-1"

def test_iforest_round_trip_scores_in_unit_interval( iforest_dir, data ):
    X, y = data
    model = load_model( iforest_dir, "iforest" )
    scores = model.score( X )
    assert np.all( ( scores >= 0 ) & ( scores <= 1 ) )
    assert scores[ y == 1 ].mean( ) > scores[ y == 0 ].mean( )

def test_loaded_scores_match_in_memory_model( rf_dir, rf, data ):
    X, _ = data
    assert np.array_equal( load_model( rf_dir ).score( X ), rf.predict_proba( X )[ :, 1 ] )

def test_metadata_contents( rf_dir ):
    metadata = json.loads( ( rf_dir / METADATA_FILE ).read_text( ) )
    assert metadata[ "model_type" ] == "rf"
    assert metadata[ "sklearn_version" ] == SKLEARN_VERSION
    assert metadata[ "feature_columns" ] == list( FEATURE_COLUMNS )
    assert len( metadata[ "model_sha256" ] ) == 64

def test_empty_frame_scores_empty( rf_dir ):
    assert load_model( rf_dir ).score( featurize( [ ] ) ).shape == ( 0, )

def test_load_forces_single_threaded_predict( tmp_path, data ):
    X, y = data
    model = RandomForestClassifier( n_estimators=5, n_jobs=-1, random_state=0 ).fit( X, y )
    export_model( model, "rf", tmp_path, model_version="v" )
    assert load_model( tmp_path ).model.n_jobs == 1

def test_scoring_requires_featurize_columns( rf_dir, data ):
    X, _ = data
    with pytest.raises( ValueError, match="FEATURE_COLUMNS" ):
        load_model( rf_dir ).score( X[ list( reversed( FEATURE_COLUMNS ) ) ] )


# ---------------------------------------------------------------- refusals

def test_missing_directory( tmp_path ):
    with pytest.raises( ModelLoadError, match="missing model.joblib" ):
        load_model( tmp_path / "nope" )

def test_missing_metadata( rf_dir ):
    ( rf_dir / METADATA_FILE ).unlink( )
    with pytest.raises( ModelLoadError, match="missing metadata.json" ):
        load_model( rf_dir )

def test_unreadable_metadata( rf_dir ):
    ( rf_dir / METADATA_FILE ).write_text( "{not json" )
    with pytest.raises( ModelLoadError, match="can't read" ):
        load_model( rf_dir )

def test_wrong_expected_type( rf_dir ):
    with pytest.raises( ModelLoadError, match="expected a iforest model" ):
        load_model( rf_dir, "iforest" )

@pytest.mark.parametrize( "changes, message", [
    ( { "feature_version": 999 },              "feature_version" ),
    ( { "feature_fingerprint": "0" * 16 },     "feature_fingerprint" ),
    ( { "sklearn_version": "1.8.0" },          "sklearn_version" ),
    ( { "feature_columns": [ "dst_port" ] },   "feature_columns" ),
    ( { "model_type": "xgboost" },             "model_type" ),
    ( { "model_version": "" },                 "model_version" ),
    ( { "model_sha256": "" },                  "model_sha256" ),
] )
def test_incompatible_metadata_refused( rf_dir, changes, message ):
    _edit_metadata( rf_dir, **changes )
    with pytest.raises( ModelLoadError, match=message ):
        load_model( rf_dir )

def test_installed_sklearn_mismatch_refused( rf_dir, monkeypatch ):
    from nla_ml import compat
    monkeypatch.setattr( compat, "installed_sklearn_version", lambda: "1.8.0" )
    with pytest.raises( ModelLoadError, match="scikit-learn 1.9.1 is required" ):
        load_model( rf_dir )

def test_swapped_model_file_refused_before_unpickling( rf_dir, iforest_dir, monkeypatch ):
    ( rf_dir / MODEL_FILE ).write_bytes( ( iforest_dir / MODEL_FILE ).read_bytes( ) )
    monkeypatch.setattr( "joblib.load", lambda *_: pytest.fail( "unpickled a file with a bad checksum" ) )
    with pytest.raises( ModelLoadError, match="checksum" ):
        load_model( rf_dir )

def test_wrong_estimator_type_refused( tmp_path, data, rf ):
    # A valid checksum but metadata claiming iforest for an RF
    export_model( rf, "rf", tmp_path, model_version="v" )
    _edit_metadata( tmp_path, model_type="iforest", calibration={ "low": 0, "high": 1 } )
    with pytest.raises( ModelLoadError, match="must be a IsolationForest" ):
        load_model( tmp_path )

@pytest.mark.parametrize( "calibration", [ None, { "low": 1.0, "high": 1.0 }, { "low": "x", "high": 2 }, { "low": float( "nan" ), "high": 1 } ] )
def test_bad_iforest_calibration_refused( iforest_dir, calibration ):
    _edit_metadata( iforest_dir, calibration=calibration )
    with pytest.raises( ModelLoadError, match="calibration" ):
        load_model( iforest_dir )


# ---------------------------------------------------------------- export validation

def test_export_requires_dataframe_feature_names( tmp_path, data ):
    X, y = data
    model = RandomForestClassifier( n_estimators=3 ).fit( X.to_numpy( ), y )
    with pytest.raises( ValueError, match="FEATURE_COLUMNS" ):
        export_model( model, "rf", tmp_path, model_version="v" )

def test_export_requires_binary_labels( tmp_path, data ):
    X, y = data
    model = RandomForestClassifier( n_estimators=3 ).fit( X, y + 1 )
    with pytest.raises( ValueError, match="labels 0" ):
        export_model( model, "rf", tmp_path, model_version="v" )

def test_export_iforest_requires_calibration( tmp_path, iforest ):
    with pytest.raises( TypeError, match="calibration" ):
        export_model( iforest, "iforest", tmp_path, model_version="v" )

def test_export_rejects_reserved_extra_keys( tmp_path, rf ):
    with pytest.raises( ValueError, match="feature_version" ):
        export_model( rf, "rf", tmp_path, model_version="v", extra={ "feature_version": 2 } )

def test_export_keeps_extra_metadata( tmp_path, rf ):
    metadata = export_model( rf, "rf", tmp_path, model_version="v", extra={ "dataset_version": 3, "pr_auc": 0.9 } )
    assert metadata[ "dataset_version" ] == 3
    assert load_model( tmp_path ).metadata[ "pr_auc" ] == 0.9

def test_calibration_maps_quantiles( iforest, data ):
    X, y = data
    calibration = calibrate_iforest( iforest, X[ y == 0 ], 0.5, 0.999 )
    raw = inference.iforest_raw_scores( iforest, X[ y == 0 ] )
    assert calibration[ "low" ] == pytest.approx( np.quantile( raw, 0.5 ) )
    assert calibration[ "high" ] > calibration[ "low" ]

def test_export_rejects_wrong_estimator( tmp_path, iforest ):
    with pytest.raises( TypeError, match="RandomForestClassifier" ):
        export_model( iforest, "rf", tmp_path, model_version="v" )
