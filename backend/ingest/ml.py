"""
ML anomaly scoring at ingest.
"""
from __future__ import annotations

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from nla_ml.features import featurize
from nla_ml.inference import LoadedModel, load_model

from config import settings
from ingest.anomaly import HeuristicResult

logger = logging.getLogger( __name__ )

_models:   dict[ str, LoadedModel ] = { }
_executor: ThreadPoolExecutor | None = None


def init_ml( ) -> None:
    """
    Load the configured models. Raises (and so stops startup) if any configured model can't be loaded.
    """
    global _executor
    if _executor is not None:
        return
    if not settings.ml_enabled:
        logger.info( "ML scoring disabled (ML_ENABLED=false)" )
        return

    model_dir = Path( settings.ml_model_dir )
    loaded: dict[ str, LoadedModel ] = { }
    for name in settings.ml_models:
        loaded[ name ] = load_model( model_dir / name, expected_type=name )
        logger.info( "Loaded ML model %s version %s from %s", name, loaded[ name ].version, model_dir / name )

    _models.update( loaded )
    _executor = ThreadPoolExecutor( max_workers=settings.ml_inference_threads, thread_name_prefix="ml-inference" )


def close_ml( ) -> None:
    global _executor
    if _executor is not None:
        _executor.shutdown( wait=True, cancel_futures=True )
        _executor = None
    _models.clear( )


def loaded_models( ) -> dict[ str, str ]:
    """Loaded model names mapped to their versions."""
    return { name: model.version for name, model in _models.items( ) }


def _score_sync( entries: list[ dict[ str, Any ] ] ) -> list[ list[ HeuristicResult ] ]:
    features = featurize( entries )
    per_row: list[ list[ HeuristicResult ] ] = [ [ ] for _ in entries ]
    for name, model in _models.items( ):
        scores = model.score( features )
        for row, score in zip( per_row, scores ):
            value = float( score )
            row.append( HeuristicResult(
                name=f"ml_{ name }",
                score=value,
                detail=f"{ name } model { model.version }: { value:.2f}" if value > 0 else None,
            ) )
    return per_row


async def score_batch_ml( entries: list[ dict[ str, Any ] ] ) -> list[ list[ HeuristicResult ] ]:
    """
    Score a batch of `scoring_inputs` with every loaded model, off the event loop.
    Returns one list of `HeuristicResult`s (`ml_rf`, `ml_iforest`) per entry, or empty lists if ML is off.
    """
    if not _models or _executor is None or not entries:
        return [ [ ] for _ in entries ]
    try:
        return await asyncio.get_running_loop( ).run_in_executor( _executor, _score_sync, entries )
    except Exception:
        logger.exception( "ML scoring failed for a batch of %d entries; storing heuristic scores only", len( entries ) )
        return [ [ ] for _ in entries ]
