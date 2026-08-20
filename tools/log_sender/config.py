"""Configuration for the log sender script.

Values can come from CLI arguments, environment variables, or a `.env` file
in the current working directory. CLI arguments always overwrite.
"""
from __future__ import annotations

import os
import random
from dataclasses import dataclass, field

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


DEFAULT_API_URL = os.getenv( "LOG_SENDER_API_URL", os.getenv( "VITE_API_BASE_URL", "http://localhost:8000" ) )
DEFAULT_API_KEY = os.getenv( "LOG_SENDER_API_KEY", "" )

PROTOCOLS = ( "TCP", "UDP", "ICMP", "OTHER" )
DEFAULT_PROTOCOL_WEIGHTS = { "TCP": 0.6, "UDP": 0.3, "ICMP": 0.08, "OTHER": 0.02 }

# "Interesting" destination ports used when shaping anomalous entries
# (scans, brute-force attempts, database probing, etc.)
SUSPICIOUS_PORTS = ( 22, 23, 445, 3389, 3306, 5432, 6379, 9200, 27017 )
COMMON_PORTS     = ( 80, 443, 53, 22, 25, 110, 143, 993, 995, 8080, 8443 )


@dataclass
class SenderConfig:
    api_url:     str          = DEFAULT_API_URL
    api_key:     str          = DEFAULT_API_KEY
    batch_size:  int          = 50
    rate:        float        = 10.0  # entries per second, across all batches
    duration:    float | None = None  # seconds; None = until count/EOF/Ctrl+C
    count:       int | None   = None  # total entries to send; None = unbounded
    dry_run:     bool         = False
    timeout:     float        = 10.0
    max_retries: int          = 3
    seed:        int | None   = None

    def __post_init__( self ) -> None:
        if self.seed is not None:
            random.seed( self.seed )
        if not self.api_key and not self.dry_run:
            raise ValueError(
                "An API key is required. Pass --api-key, set LOG_SENDER_API_KEY, "
                "or use --dry-run to skip sending."
            )
        if self.batch_size < 1:
            raise ValueError( "--batch-size must be >= 1" )
        if self.rate <= 0:
            raise ValueError( "--rate must be > 0" )


@dataclass
class SyntheticConfig:
    src_subnet:       str                = "10.0.0.0/8"
    dst_subnet:       str                = "0.0.0.0/0"   # public internet by default
    protocol_weights: dict[ str, float ] = field( default_factory=lambda: dict( DEFAULT_PROTOCOL_WEIGHTS ) )
    anomaly_rate:     float              = 0.05           # fraction of entries shaped like anomalies
    min_packet_size:  int                = 40
    max_packet_size:  int                = 1500
