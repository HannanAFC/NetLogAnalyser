"""
Version metadata for trained models, and the check that a model matches this code.

Training notebooks write `feature_spec()` into each model's `metadata.json`.
The backend calls `assert_compatible(metadata)` before using a model and
refuses to load it on any mismatch.

`SKLEARN_VERSION` is the configured version, it must match what is in the
`pyproject.toml` file.
"""
from __future__ import annotations

import platform
from collections.abc import Mapping
from typing import Any

from nla_ml import __version__
from nla_ml.features import FEATURE_COLUMNS, FEATURE_FINGERPRINT, FEATURE_VERSION

SKLEARN_VERSION = "1.9.1"


class IncompatibleModelError( RuntimeError ):
    """Raised when a model was trained with a different feature definition."""

def feature_spec( ) -> dict[ str, Any ]:
    """
    The feature definition this code produces, for storing in model metadata.
    """
    return {
        "feature_version":     FEATURE_VERSION,
        "feature_fingerprint": FEATURE_FINGERPRINT,
        "feature_columns":     list( FEATURE_COLUMNS ),
        "nla_ml_version":      __version__,
        "sklearn_version":     SKLEARN_VERSION,
        "python_version":      platform.python_version( ),  # informational, not checked
    }

def installed_sklearn_version( ) -> str | None:
    """
    The installed scikit-learn version, or None if it isn't installed.
    """
    try:
        import sklearn
    except ImportError:
        return None
    return sklearn.__version__

def assert_sklearn_version( ) -> None:
    """
    Raise `IncompatibleModelError` unless the installed scikit-learn is `SKLEARN_VERSION`.
    """
    installed = installed_sklearn_version( )
    if installed != SKLEARN_VERSION:
        raise IncompatibleModelError(
            f"scikit-learn { SKLEARN_VERSION } is required, found { installed or 'none' }. "
        )

def compatibility_problems( metadata: Mapping[ str, Any ] ) -> list[ str ]:
    """
    Compare a model's metadata with this code's feature definition.
    Parameters:
        metadata (Mapping): The model's metadata (must contain the `feature_spec()` keys).
    Returns:
        problems (list[str]): Human-readable mismatches; empty if compatible.
    """
    problems: list[ str ] = [ ]

    if metadata.get( "feature_version" ) != FEATURE_VERSION:
        problems.append( f"feature_version: model has { metadata.get( 'feature_version' )!r}, code has { FEATURE_VERSION }" )

    if metadata.get( "feature_fingerprint" ) != FEATURE_FINGERPRINT:
        problems.append( f"feature_fingerprint: model has { metadata.get( 'feature_fingerprint' )!r}, code has { FEATURE_FINGERPRINT }" )

    if metadata.get( "sklearn_version" ) != SKLEARN_VERSION:
        problems.append( f"sklearn_version: model has { metadata.get( 'sklearn_version' )!r}, code pins { SKLEARN_VERSION }" )

    columns = metadata.get( "feature_columns" )
    if columns is None or list( columns ) != list( FEATURE_COLUMNS ):
        problems.append( "feature_columns: model's columns differ from FEATURE_COLUMNS (names or order)" )

    return problems

def assert_compatible( metadata: Mapping[ str, Any ] ) -> None:
    """
    Raise `IncompatibleModelError` if a model's metadata doesn't match this code.
    """
    problems = compatibility_problems( metadata )
    if problems:
        raise IncompatibleModelError( "model is incompatible with nla-ml features: " + "; ".join( problems ) )
