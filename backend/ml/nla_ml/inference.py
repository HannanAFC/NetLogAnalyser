"""
Model artifacts: saving, loading and scoring.

An artifact must have metadata.json and model.joblib
"""
from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

import numpy as np
import pandas as pd

from nla_ml.compat import (
    IncompatibleModelError,
    assert_compatible,
    assert_sklearn_version,
    feature_spec,
)
from nla_ml.features import FEATURE_COLUMNS, featurize

ModelType = Literal[ "rf", "iforest" ]
MODEL_TYPES: tuple[ str, ... ] = ( "rf", "iforest" )

MODEL_FILE    = "model.joblib"
METADATA_FILE = "metadata.json"

# Prevent extra keys from overriding these reserved ones
_RESERVED_KEYS = frozenset( { *feature_spec( ), "model_type", "model_version", "model_sha256", "created_at", "calibration" } )

# A good entry to check against
_SMOKE_ENTRY = {
    "src_ip": "192.168.1.10", "dst_ip": "93.184.216.34", "src_port": 51515, "dst_port": 443,
    "protocol": "TCP", "packet_size_bytes": 60, "flags": "SYN",
}

class ModelLoadError( RuntimeError ):
    """Raised when a model artifact can't be loaded safely. The message names the artifact and the reason."""

@dataclass( frozen=True )
class LoadedModel:
    model_type: str
    model:      Any
    metadata:   dict[ str, Any ]
    path:       Path | None = field( default=None )

    @property
    def version( self ) -> str:
        return str( self.metadata[ "model_version" ] )

    def score( self, features: pd.DataFrame ) -> np.ndarray:
        """Score a `featurize()` frame. Returns float64 scores in [0, 1], one per row."""
        return score_model( self.model_type, self.model, self.metadata, features )


def _estimator_class( model_type: str ) -> type:
    from sklearn.ensemble import IsolationForest, RandomForestClassifier
    return { "rf": RandomForestClassifier, "iforest": IsolationForest }[ model_type ]

def _sha256( path: Path ) -> str:
    digest = hashlib.sha256( )
    with path.open( "rb" ) as file:
        for chunk in iter( lambda: file.read( 1 << 20 ), b"" ):
            digest.update( chunk )
    return digest.hexdigest( )

def _check_features( features: pd.DataFrame ) -> None:
    if list( features.columns ) != list( FEATURE_COLUMNS ):
        raise ValueError( "features must have exactly FEATURE_COLUMNS, in order; build them with featurize()" )

def _check_estimator( model_type: str, model: Any ) -> None:
    """Raise TypeError/ValueError if `model` isn't a fitted estimator of the right kind, trained on FEATURE_COLUMNS."""
    if model_type not in MODEL_TYPES:
        raise ValueError( f"model_type must be one of { ', '.join( MODEL_TYPES ) }, got { model_type!r}" )

    expected = _estimator_class( model_type )
    if not isinstance( model, expected ):
        raise TypeError( f"{ model_type } model must be a { expected.__name__ }, got { type( model ).__name__ }" )

    names = getattr( model, "feature_names_in_", None )
    if names is None or list( names ) != list( FEATURE_COLUMNS ):
        raise ValueError( "model was not fitted on a DataFrame with exactly FEATURE_COLUMNS, in order" )

    if model_type == "rf":
        classes = [ int( c ) for c in getattr( model, "classes_", [ ] ) ]
        if classes != [ 0, 1 ]:
            raise ValueError( f"rf model must be trained on labels 0 (benign) and 1 (anomalous), got classes { classes }" )

def _check_calibration( calibration: Any ) -> tuple[ float, float ]:
    if not isinstance( calibration, Mapping ):
        raise TypeError( "iforest model needs calibration {'low': ..., 'high': ...}" )
    try:
        low, high = float( calibration[ "low" ] ), float( calibration[ "high" ] )
    except ( KeyError, TypeError, ValueError ) as exc:
        raise ValueError( "iforest calibration needs numeric 'low' and 'high'" ) from exc
    if not ( math.isfinite( low ) and math.isfinite( high ) and high > low ):
        raise ValueError( f"iforest calibration must have finite low < high, got low={ low }, high={ high }" )
    return low, high

def iforest_raw_scores( model: Any, features: pd.DataFrame ) -> np.ndarray:
    """IsolationForest anomaly scores before calibration: -decision_function, higher = more anomalous."""
    return -np.asarray( model.decision_function( features ), dtype=np.float64 )

def calibrate_iforest(
    model:         Any,
    features:      pd.DataFrame,
    low_quantile:  float = 0.5,
    high_quantile: float = 0.999,
) -> dict[ str, float ]:
    """
    Compute calibration bounds for an IsolationForest from (usually benign) data.
    By default a median benign row scores 0 and only the top 0.1% of benign rows reach 1.
    Parameters:
        model: A fitted IsolationForest.
        features (pd.DataFrame): `featurize()` output to calibrate on, e.g. the benign validation split.
        low_quantile (float): Raw-score quantile that maps to 0.
        high_quantile (float): Raw-score quantile that maps to 1.
    Returns:
        calibration (dict): Pass to `export_model( ..., calibration=... )`.
    """
    if not 0.0 <= low_quantile < high_quantile <= 1.0:
        raise ValueError( "need 0 <= low_quantile < high_quantile <= 1" )
    _check_features( features )
    raw  = iforest_raw_scores( model, features )
    low  = float( np.quantile( raw, low_quantile ) )
    high = float( np.quantile( raw, high_quantile ) )
    if not high > low:
        raise ValueError( "calibration data gives high <= low; use more varied data or wider quantiles" )
    return { "low": low, "high": high, "low_quantile": low_quantile, "high_quantile": high_quantile }

def score_model( model_type: str, model: Any, metadata: Mapping[ str, Any ], features: pd.DataFrame ) -> np.ndarray:
    """
    Score a `featurize()` frame with a fitted model. Returns float64 scores in [0, 1].
    """
    _check_features( features )
    if len( features ) == 0:
        return np.zeros( 0, dtype=np.float64 )

    if model_type == "rf":
        positive = list( model.classes_ ).index( 1 )
        scores = np.asarray( model.predict_proba( features )[ :, positive ], dtype=np.float64 )
    elif model_type == "iforest":
        low, high = _check_calibration( metadata.get( "calibration" ) )
        scores = ( iforest_raw_scores( model, features ) - low ) / ( high - low )
    else:
        raise ValueError( f"unknown model_type { model_type!r}" )

    return np.clip( scores, 0.0, 1.0 )

def export_model(
    model:         Any,
    model_type:    ModelType,
    directory:     str | Path,
    *,
    model_version: str,
    calibration:   Mapping[ str, float ] | None = None,
    extra:         Mapping[ str, Any ] | None = None,
) -> dict[ str, Any ]:
    """
    Write a model artifact (model.joblib + metadata.json) that `load_model` accepts.
    Parameters:
        model: The fitted estimator (fit it on a `featurize()` DataFrame so it records the feature names).
        model_type (str): "rf" or "iforest".
        directory (str | Path): Output directory; created if missing. Existing artifact files are overwritten.
        model_version (str): A human-readable version shown in anomaly reasons, e.g. "2026-11-03-rf-1".
        calibration (Mapping | None): Required for "iforest"; see `calibrate_iforest`.
        extra (Mapping | None): More metadata (dataset version, git SHA, metrics...). Can't override reserved keys.
    Returns:
        metadata (dict): What was written to metadata.json.
    """
    import joblib

    assert_sklearn_version( )
    _check_estimator( model_type, model )
    if model_type == "iforest":
        _check_calibration( calibration )
    elif calibration is not None:
        raise ValueError( "calibration only applies to iforest models" )
    if not model_version or not str( model_version ).strip( ):
        raise ValueError( "model_version is required" )
    clashes = _RESERVED_KEYS & set( extra or { } )
    if clashes:
        raise ValueError( f"extra metadata can't override: { ', '.join( sorted( clashes ) ) }" )

    out = Path( directory )
    out.mkdir( parents=True, exist_ok=True )
    model_path = out / MODEL_FILE
    joblib.dump( model, model_path )

    metadata: dict[ str, Any ] = {
        **( extra or { } ),
        **feature_spec( ),
        "model_type":    model_type,
        "model_version": str( model_version ),
        "model_sha256":  _sha256( model_path ),
        "created_at":    datetime.now( UTC ).isoformat( timespec="seconds" ),
    }
    if calibration is not None:
        metadata[ "calibration" ] = dict( calibration )

    ( out / METADATA_FILE ).write_text( json.dumps( metadata, indent=2, sort_keys=True ) + "\n" )
    return metadata

def load_model( directory: str | Path, expected_type: ModelType | None = None, *, n_jobs: int | None = 1 ) -> LoadedModel:
    """
    Load and validate a model artifact. Raises `ModelLoadError` on any problem.
    Parameters:
        directory (str | Path): The artifact directory.
        expected_type (str | None): Refuse the artifact unless its model_type matches.
        n_jobs (int | None): Override the estimator's n_jobs (default 1).
        Leave low so utilisation doesn't become too high.
    Returns:
        model (LoadedModel): The validated model.
    """
    import joblib

    path = Path( directory )

    def fail( reason: str ) -> ModelLoadError:
        return ModelLoadError( f"model artifact { path }: { reason }" )

    model_path, metadata_path = path / MODEL_FILE, path / METADATA_FILE
    for required in ( model_path, metadata_path ):
        if not required.is_file( ):
            raise fail( f"missing { required.name }" )

    try:
        metadata = json.loads( metadata_path.read_text( ) )
    except ( OSError, ValueError ) as exc:
        raise fail( f"can't read { METADATA_FILE }: { exc }" ) from exc
    if not isinstance( metadata, dict ):
        raise fail( f"{ METADATA_FILE } must be a JSON object" )

    model_type = metadata.get( "model_type" )
    if model_type not in MODEL_TYPES:
        raise fail( f"model_type must be one of { ', '.join( MODEL_TYPES ) }, got { model_type!r}" )
    if expected_type is not None and model_type != expected_type:
        raise fail( f"expected a { expected_type } model, found { model_type }" )
    if not metadata.get( "model_version" ):
        raise fail( "metadata has no model_version" )

    try:
        assert_sklearn_version( )
        assert_compatible( metadata )
    except IncompatibleModelError as exc:
        raise fail( str( exc ) ) from exc

    # Checked before unpickling, so a swapped or corrupted file never gets loaded
    expected_sha = metadata.get( "model_sha256" )
    if not expected_sha:
        raise fail( "metadata has no model_sha256" )
    actual_sha = _sha256( model_path )
    if actual_sha != expected_sha:
        raise fail( f"{ MODEL_FILE } checksum { actual_sha[ :12 ] }... doesn't match metadata { str( expected_sha )[ :12 ] }..." )

    try:
        model = joblib.load( model_path )
    except Exception as exc:  # any unpickling failure means the artifact is unusable
        raise fail( f"can't unpickle { MODEL_FILE }: { exc }" ) from exc

    try:
        _check_estimator( model_type, model )
        if model_type == "iforest":
            _check_calibration( metadata.get( "calibration" ) )
    except ( TypeError, ValueError ) as exc:
        raise fail( str( exc ) ) from exc

    if n_jobs is not None and hasattr( model, "n_jobs" ):
        model.n_jobs = n_jobs

    loaded = LoadedModel( model_type=model_type, model=model, metadata=metadata, path=path )

    try:
        smoke = loaded.score( featurize( [ _SMOKE_ENTRY ] ) )
    except Exception as exc:
        raise fail( f"smoke-test prediction failed: { exc }" ) from exc
    if smoke.shape != ( 1, ) or not np.all( np.isfinite( smoke ) ) or not 0.0 <= smoke[ 0 ] <= 1.0:
        raise fail( f"smoke-test prediction gave { smoke!r}, expected one score in [0, 1]" )

    return loaded
