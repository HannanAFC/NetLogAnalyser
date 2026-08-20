"""Send network log entries to a NetLogAnalyser /ingest endpoint.

Two modes:
    synthetic  Generate randomised (optionally anomaly-flavoured) traffic.
    replay     Read entries from a CSV/JSON/JSONL file (e.g. real captures)
               and send them at a controlled rate, optionally looping.

Examples:
    python log_sender.py synthetic --api-key nl-xxx --rate 20 --duration 60
    python log_sender.py synthetic --api-key nl-xxx --rate 5 --anomaly-rate 0.3 --count 200
    python log_sender.py replay --api-key nl-xxx --file captures.csv --rate 10 --loop
    python log_sender.py synthetic --dry-run --count 5 --rate 100   # smoke test, no API key needed
"""
from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Iterator

from config import DEFAULT_API_KEY, DEFAULT_API_URL, SenderConfig, SyntheticConfig
from generators import generate_entry
from replay import read_entries
from sender import send_stream


def _synthetic_stream( cfg: SyntheticConfig ) -> Iterator[ dict ]:
    while True:
        yield generate_entry( cfg )


def _replay_stream( path: str, field_map: dict | None, loop: bool ) -> Iterator[ dict ]:
    if loop:
        while True:
            yield from read_entries( path, field_map )
    else:
        yield from read_entries( path, field_map )


def _add_common_args( p: argparse.ArgumentParser ) -> None:
    p.add_argument( "--api-url", default=DEFAULT_API_URL, help="Backend base URL (default: %(default)s)" )
    p.add_argument( "--api-key", default=DEFAULT_API_KEY, help="Ingest API key (or set LOG_SENDER_API_KEY)" )
    p.add_argument( "--rate", type=float, default=10.0, help="Entries per second (default: %(default)s)" )
    p.add_argument( "--batch-size", type=int, default=50, help="Entries per HTTP request (default: %(default)s)" )
    p.add_argument( "--duration", type=float, default=None, help="Stop after N seconds" )
    p.add_argument( "--count", type=int, default=None, help="Stop after N entries" )
    p.add_argument( "--dry-run", action="store_true", help="Generate/read entries but don't send them" )
    p.add_argument( "--seed", type=int, default=None, help="Random seed, for reproducible synthetic runs" )


def main( argv: list[ str ] | None = None ) -> int:
    parser = argparse.ArgumentParser( description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter )
    sub = parser.add_subparsers( dest="mode", required=True )

    synth = sub.add_parser( "synthetic", help="Generate synthetic log traffic" )
    _add_common_args( synth )
    synth.add_argument( "--src-subnet", default="10.0.0.0/8", help="CIDR for src_ip (default: %(default)s)" )
    synth.add_argument( "--dst-subnet", default="0.0.0.0/0", help="CIDR for dst_ip (default: %(default)s)" )
    synth.add_argument( "--anomaly-rate", type=float, default=0.05, help="Fraction of anomaly-shaped entries (default: %(default)s)" )
    synth.add_argument( "--min-packet-size", type=int, default=40 )
    synth.add_argument( "--max-packet-size", type=int, default=1500 )

    replay = sub.add_parser( "replay", help="Replay log entries from a CSV/JSON/JSONL file" )
    _add_common_args( replay )
    replay.add_argument( "--file", required=True, help="Path to a .csv, .json, or .jsonl file" )
    replay.add_argument( "--loop", action="store_true", help="Loop the file indefinitely" )
    replay.add_argument(
        "--field-map", default=None,
        help='JSON string mapping source columns to schema fields, e.g. \'{"source_ip":"src_ip"}\'',
    )

    args = parser.parse_args( argv )

    try:
        cfg = SenderConfig(
            api_url=args.api_url, api_key=args.api_key, batch_size=args.batch_size,
            rate=args.rate, duration=args.duration, count=args.count,
            dry_run=args.dry_run, seed=args.seed,
        )
    except ValueError as exc:
        print( f"Config error: { exc }", file=sys.stderr )
        return 1

    if args.mode == "synthetic":
        synth_cfg = SyntheticConfig(
            src_subnet=args.src_subnet, dst_subnet=args.dst_subnet,
            anomaly_rate=args.anomaly_rate,
            min_packet_size=args.min_packet_size, max_packet_size=args.max_packet_size,
        )
        stream = _synthetic_stream( synth_cfg )
    else:
        field_map = json.loads( args.field_map ) if args.field_map else None
        stream = _replay_stream( args.file, field_map, args.loop )

    try:
        send_stream( cfg, stream )
    except KeyboardInterrupt:
        print( "\nInterrupted." )
    except RuntimeError as exc:
        print( f"\n{ exc }", file=sys.stderr )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit( main( ) )
