# log_sender

A standalone CLI for sending network log entries to a NetLogAnalyser
`POST /ingest` endpoint. Useful for testing the live feed, WebSocket
broadcast, analytics, and anything else downstream of ingestion, without
needing real captured traffic.

Not part of the FastAPI app - this is a client, so it has no dependency on
the backend package and can be run from anywhere with network access to it.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # then fill in LOG_SENDER_API_KEY
```
Or use UV like the FastAPI app:
```bash
uv sync
cp .env.example .env   # then fill in LOG_SENDER_API_KEY
```

You'll need an active API key from `/api-keys` (create one via the API or
dashboard first). `.env` is loaded automatically if `python-dotenv` is
installed; CLI flags always override it.

## Modes

### `synthetic` - generate randomised traffic

```bash
# 20 entries/sec for 60 seconds
python log_sender.py synthetic --rate 20 --duration 60

# Heavier anomaly mix, useful for testing anomaly-score UI / alerting
python log_sender.py synthetic --rate 5 --anomaly-rate 0.3 --count 200

# Confine src IPs to a specific internal subnet
python log_sender.py synthetic --src-subnet 192.168.0.0/16 --rate 15

# Smoke-test without hitting the network at all
python log_sender.py synthetic --dry-run --count 5 --rate 100
```
**Note - replace `python` with `uv` if you are using that instead of pip.**

Traffic is shaped by `--anomaly-rate` (0.0–1.0): anomalous entries use
suspicious destination ports (22, 3389, 3306, 6379, etc.), unusually small
packet sizes, and scan-like TCP flag combinations, so downstream anomaly
detection / dashboards have something meaningful to react to.

### `replay` - send entries from a file

Accepts `.csv`, `.json` (a list of objects), or `.jsonl` (one object per
line). Required fields: `src_ip`, `dst_ip`, `src_port`, `dst_port`,
`protocol`, `packet_size_bytes`, `captured_at`. Optional: `flags`,
`raw_payload`.

```bash
python log_sender.py replay --file captures.csv --rate 10 --loop
```

If your source file uses different column names (e.g. exported from Zeek,
tshark, or another tool), map them with `--field-map`:

```bash
python log_sender.py replay --file zeek_export.csv --rate 10 \
  --field-map '{"id.orig_h":"src_ip","id.resp_h":"dst_ip","id.orig_p":"src_port","id.resp_p":"dst_port","proto":"protocol"}'
```

**Protocol values:** the backend's `protocol` column only accepts
`TCP`/`UDP`/`ICMP`/`OTHER`. Some tools (notably CICFlowMeter, used by
CICIDS2017 and similar datasets) report the raw IANA protocol number instead
- `replay.py` automatically translates `1`→`ICMP`, `6`→`TCP`, `17`→`UDP`,
and anything else (including CICIDS2017's `0` values) to `OTHER`. The
original value is preserved as `raw_payload.source_protocol` either way, so
nothing is lost even when it's bucketed into `OTHER`.

**CICIDS2017 note:** it's a flow-level dataset (each row summarizes a whole
bidirectional flow, not a single packet), so it doesn't translate perfectly to the type of log data that is expected. However, it is good enough and is what was used when developing this CLI.
Example mapping:

```bash
python log_sender.py replay --file Monday-WorkingHours.pcap_ISCX.csv --rate 20 \
  --field-map '{" Source IP":"src_ip"," Destination IP":"dst_ip"," Source Port":"src_port"," Destination Port":"dst_port"," Protocol":"protocol"," Average Packet Size":"packet_size_bytes"," Timestamp":"captured_at"}'
```
**Note that there are spaces before the column names, this is a quirk with the CICIDS2017 dataset.**

## Shared options

| Flag | Meaning |
|---|---|
| `--api-url` | Backend base URL (default `http://localhost:8000`, or `LOG_SENDER_API_URL`) |
| `--api-key` | Ingest API key (or `LOG_SENDER_API_KEY`) |
| `--rate` | Target entries/sec across all batches, batch size is divided by this number which then corresponds to how often a batch is sent. E.g. a batch size of 50 and a rate of 10 means a batch is sent every 5 seconds. |
| `--batch-size` | Entries per HTTP request (server caps at `INGEST_MAX_BATCH_SIZE`, default 500) |
| `--duration` | Stop after N seconds |
| `--count` | Stop after N entries |
| `--dry-run` | Generate/read entries but don't POST them (no API key required) |
| `--seed` | Random seed, for reproducible synthetic runs |

Ctrl+C stops cleanly at any point and prints a final tally.

## Output

Each batch's response is folded into a running tally:

```
sent=450 accepted=448 rejected=2 elapsed=45.2s
```

Rejected rows are printed to stderr with their index and reason, taken
directly from the endpoint's `207 Multi-Status` `errors` array, so you can
tell a malformed-input rejection from a real server-side issue.

## Files

| File | Purpose |
|---|---|
| `log_sender.py` | CLI entrypoint (argparse, `synthetic` / `replay` subcommands) |
| `config.py` | `SenderConfig` / `SyntheticConfig` dataclasses, env loading |
| `generators.py` | Synthetic entry generation, including anomaly shaping |
| `replay.py` | CSV/JSON/JSONL parsing with optional field mapping |
| `sender.py` | Batching, rate pacing, retries, response tallying |