"""
Train throwaway RF and Isolation Forest models on synthetic log_sender data and
export them in the real artifact format, to test the ML plumbing end to end.

    cd backend && uv run python ml/scripts/train_dummy.py --out ../models

Don't read anything into these models' accuracy: the generator labels entries
with the same rules the heuristics check, so they only learn to copy them.
"""
from __future__ import annotations

import argparse
import random
import sys
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
from nla_ml.features import featurize
from nla_ml.inference import calibrate_iforest, export_model, load_model
from sklearn.ensemble import IsolationForest, RandomForestClassifier

REPO_ROOT = Path( __file__ ).resolve( ).parents[ 3 ]
LOG_SENDER = REPO_ROOT / "tools" / "log_sender"


def generate( rows: int, anomaly_rate: float, seed: int ) -> tuple[ list[ dict ], np.ndarray ]:
    # log_sender's modules import each other by bare name (`from config import ...`)
    sys.path.insert( 0, str( LOG_SENDER ) )
    try:
        from generators import generate_entry  # type: ignore[import-not-found]

        from config import SyntheticConfig  # type: ignore[import-not-found]
    finally:
        sys.path.remove( str( LOG_SENDER ) )

    random.seed( seed )
    cfg = SyntheticConfig( anomaly_rate=anomaly_rate )
    entries = [ generate_entry( cfg ) for _ in range( rows ) ]
    labels  = np.array( [ int( e[ "raw_payload" ][ "anomalous" ] ) for e in entries ] )
    return entries, labels


def main( ) -> None:
    parser = argparse.ArgumentParser( description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter )
    parser.add_argument( "--out", type=Path, default=REPO_ROOT / "models", help="artifact root (default: repo models/)" )
    parser.add_argument( "--rows", type=int, default=20_000 )
    parser.add_argument( "--anomaly-rate", type=float, default=0.2 )
    parser.add_argument( "--seed", type=int, default=0 )
    args = parser.parse_args( )

    entries, labels = generate( args.rows, args.anomaly_rate, args.seed )
    features = featurize( entries )
    benign   = features[ labels == 0 ]
    version  = f"dummy-{datetime.now( UTC ):%Y%m%d}"
    extra    = {
        "dummy":      True,
        "trained_on": f"tools/log_sender synthetic data ({ args.rows } rows, seed { args.seed })",
        "note":       "Throwaway model for testing the ML plumbing. Its accuracy means nothing.",
    }

    rf = RandomForestClassifier( n_estimators=50, max_depth=8, class_weight="balanced", random_state=args.seed, n_jobs=-1 )
    rf.fit( features, labels )
    export_model( rf, "rf", args.out / "rf", model_version=f"{ version }-rf", extra=extra )

    iforest = IsolationForest( n_estimators=100, random_state=args.seed, n_jobs=-1 )
    iforest.fit( benign )
    export_model(
        iforest, "iforest", args.out / "iforest",
        model_version=f"{ version }-iforest",
        calibration=calibrate_iforest( iforest, benign ),
        extra=extra,
    )

    # Prove the artifacts load the way the backend will load them
    for name in ( "rf", "iforest" ):
        model  = load_model( args.out / name, name )
        scores = model.score( features )
        print(
            f"{ name:8} { model.version:28} -> { args.out / name }   "
            f"mean score benign={ scores[ labels == 0 ].mean( ):.3f} anomalous={ scores[ labels == 1 ].mean( ):.3f}"
        )


if __name__ == "__main__":
    main( )
