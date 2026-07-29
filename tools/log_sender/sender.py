"""HTTP transport: batches, paces, and posts log entries to /ingest."""
from __future__ import annotations

import itertools
import sys
import time
from collections.abc import Iterable, Iterator
from typing import Any

import requests
from config import SenderConfig


def _chunk( iterable: Iterable[ dict ], size: int ) -> Iterator[ list[ dict ] ]:
    it = iter( iterable )
    while True:
        batch = list( itertools.islice( it, size ) )
        if not batch:
            return
        yield batch


def _post_batch( cfg: SenderConfig, entries: list[ dict[ str, Any ] ] ) -> dict[ str, Any ] | None:
    if cfg.dry_run:
        print( f"[dry-run] would send { len( entries ) } entries" )
        return None

    url     = f"{ cfg.api_url.rstrip( '/' ) }/ingest"
    headers = { "X-API-Key": cfg.api_key }
    payload = { "entries": entries }

    last_error: Exception | None = None
    for attempt in range( 1, cfg.max_retries + 1 ):
        try:
            resp = requests.post( url, json=payload, headers=headers, timeout=cfg.timeout )
            # 207 = partial acceptance, 422 = all rejected (still a meaningful response)
            if resp.status_code in ( 200, 207, 422 ):
                return resp.json( )
            resp.raise_for_status( )
        except requests.RequestException as exc:
            last_error = exc
            wait = min( 2 ** attempt, 10 )
            print( f"  attempt { attempt }/{ cfg.max_retries } failed ({ exc }); retrying in { wait }s", file=sys.stderr )
            time.sleep( wait )

    raise RuntimeError( f"Failed to POST batch after { cfg.max_retries } attempts: { last_error }" )


def send_stream( cfg: SenderConfig, entries: Iterable[ dict[ str, Any ] ] ) -> None:
    """Send entries from an iterable, batching and pacing to cfg.rate entries/sec."""
    start          = time.monotonic( )
    sent_total     = 0
    accepted_total = 0
    rejected_total = 0
    batch_interval = cfg.batch_size / cfg.rate

    for batch in _chunk( entries, cfg.batch_size ):
        if cfg.count is not None and sent_total >= cfg.count:
            break
        if cfg.count is not None and sent_total + len( batch ) > cfg.count:
            batch = batch[ : cfg.count - sent_total ]

        batch_start = time.monotonic( )
        result = _post_batch( cfg, batch )
        sent_total += len( batch )

        if result:
            accepted_total += result.get( "accepted", 0 )
            rejected_total += result.get( "rejected", 0 )
            for err in result.get( "errors", [ ] ):
                print( f"  rejected[{ err.get( 'index' ) }]: { err.get( 'detail' ) }", file=sys.stderr )

        elapsed_total = time.monotonic( ) - start
        print(
            f"sent={ sent_total } accepted={ accepted_total } rejected={ rejected_total } elapsed={elapsed_total:0.1f}s",
            end="\r",
            flush=True
        )

        if cfg.duration is not None and elapsed_total >= cfg.duration:
            break
        if cfg.count is not None and sent_total >= cfg.count:
            break

        sleep_for = batch_interval - ( time.monotonic( ) - batch_start )
        if sleep_for > 0:
            time.sleep( sleep_for )

    print( )
    print( f"Done. sent={ sent_total } accepted={ accepted_total } rejected={ rejected_total }" )
