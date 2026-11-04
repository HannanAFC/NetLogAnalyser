"""
Backend wrapper around the shared heuristics in `nla_ml.heuristics`.
"""
from collections.abc import Callable
from typing import Any

from nla_ml import heuristics
from nla_ml.heuristics import HeuristicConfig, HeuristicResult, combine_scores
from nla_ml.heuristics import ramp as _ramp  # noqa: F401 - re-exported for tests/test_anomaly.py

from config import settings

__all__ = [
    "HeuristicResult",
    "compute_anomaly_score",
    "heuristic_config",
]

_WEIGHTS = {
    "packet_size":            settings.anomaly_weight_packet_size,
    "tcp_flags":              settings.anomaly_weight_tcp_flags,
    "port_protocol_mismatch": settings.anomaly_weight_mismatch_ports,
    "port_scan_shape":        settings.anomaly_weight_port_scan_shape,
    "host_sweep_shape":       settings.anomaly_weight_host_sweep_shape,
    "ml_rf":                  settings.ml_weight_rf,
    "ml_iforest":             settings.ml_weight_iforest
}

def heuristic_config( ) -> HeuristicConfig:
    """
    The `HeuristicConfig` the backend is currently running with.
    """
    return HeuristicConfig(
        packet_size_mtu       = settings.anomaly_packet_size_mtu,
        packet_size_jumbo_max = settings.anomaly_packet_size_jumbo_max,
        packet_size_tiny_max  = settings.anomaly_packet_size_tiny_max,
        port_scan_low         = settings.anomaly_port_scan_low,
        port_scan_high        = settings.anomaly_port_scan_high,
        host_sweep_low        = settings.anomaly_host_sweep_low,
        host_sweep_high       = settings.anomaly_host_sweep_high,
        weights               = _WEIGHTS
    )

def _score_packet_size( entry: dict[ str, Any ] ) -> HeuristicResult:
    return heuristics.score_packet_size( entry, heuristic_config( ) )

def _score_tcp_flags( entry: dict[ str, Any ] ) -> HeuristicResult:
    return heuristics.score_tcp_flags( entry, heuristic_config( ) )

def _score_port_protocol_mismatch( entry: dict[ str, Any ] ) -> HeuristicResult:
    return heuristics.score_port_protocol_mismatch( entry, heuristic_config( ) )

_HEURISTICS: list[ Callable[ [ dict[ str, Any ] ], HeuristicResult ] ] = [
    _score_packet_size,
    _score_tcp_flags,
    _score_port_protocol_mismatch
]

def _score_batch_heuristics( rows: list[ dict[ str, Any ] ] ) -> list[ list[ HeuristicResult ] ]:
    """
    For each row, returns extra HeuristicResults reflecting scan/sweep-shaped
    behaviour from that row's src_ip elsewhere in this same batch.
    """
    return heuristics.score_batch_heuristics( rows, heuristic_config( ) )

def compute_anomaly_score(
    entry: dict[ str, Any ],
    extra_results: list[ HeuristicResult ] | None = None
) -> tuple[ float, list[ HeuristicResult ] ]:
    # Module-level lookups on purpose: _HEURISTICS and _WEIGHTS can be swapped (e.g. in tests)
    results = [ heuristic( entry ) for heuristic in _HEURISTICS ]

    if extra_results:
        results.extend( extra_results )

    return combine_scores( results, _WEIGHTS ), results
