# nla-ml

Feature extraction shared by the NetLogAnalyser backend and the Kaggle notebooks that train its
anomaly models (Random Forest and Isolation Forest).

The backend (at ingest) and the notebooks (at training) both call `featurize()`, so a model only
ever sees features that production can compute from a real ingest request.

```python
from nla_ml.compat import assert_compatible, assert_sklearn_version, feature_spec
from nla_ml.features import featurize, featurize_frame

X = featurize( scoring_inputs )        # list of entry dicts -> DataFrame[FEATURE_COLUMNS]
X = featurize_frame( adapted_df )      # DataFrame of entries -> same, index preserved for labels

metadata = { **feature_spec( ), ... }  # notebook: write into the model's metadata.json
assert_compatible( metadata )          # backend: refuse a model trained on other features
assert_sklearn_version( )              # both: installed scikit-learn must be the pinned one
```

## What goes in, what comes out

**Inputs** (`INPUT_FIELDS`) are the fields of the ingest API's `LogEntryCreate`: `src_ip`, `dst_ip`,
`src_port`, `dst_port`, `protocol`, `packet_size_bytes`, `flags`. Any other key on an entry or
column on a frame is ignored, so dataset-only columns and labels can't leak into a model. A backend
test checks that every input field still exists on `LogEntryCreate`.

**Outputs** (`FEATURE_COLUMNS`, v1), all `int64`, one row per entry:

| Column | Meaning |
|---|---|
| `dst_port` | Raw destination port |
| `dst_port_well_known` | 1 if `dst_port` is 1–1023 (port 0 is not) |
| `dst_port_in_expectations` | 1 if `dst_port` is in `PORT_PROTOCOL_EXPECTATIONS` |
| `src_port_bucket` | 0 = port 0, 1 = well-known, 2 = registered (1024–49151), 3 = ephemeral (49152+) |
| `proto_TCP` / `_UDP` / `_ICMP` / `_OTHER` | One-hot protocol (case-insensitive) |
| `packet_size_bytes` | **IP total length** in bytes (`PACKET_SIZE_DEFINITION = "ip_total_length"`): the IPv4 Total Length field, or 40 + Payload Length for IPv6. No link-layer headers |
| `flag_SYN` … `flag_URG` | One column each for SYN, ACK, FIN, RST, PSH, URG |
| `flag_count` | Distinct flag tokens, including ones without a column (ECE, CWR) |
| `flags_present` | 1 if a flags string was sent at all. `","` and `""` give `flags_present=1, flag_count=0`, which is the "malformed/empty flags" signal the heuristic uses |
| `src_is_private` / `dst_is_private` | Python's `ipaddress` `is_private`. The IP itself is discarded |

Invalid entries (unknown protocol, out-of-range port, bad IP, missing field) raise `KeyError` / `TypeError` /
`ValueError`; `featurize()` re-raises them as `ValueError` naming the entry index. They never get a default value. In production `LogEntryCreate`
has already validated them. In notebooks, the dataset adapter should drop them first.

`is_private` follows the IANA special-purpose registries. It counts documentation, benchmarking
and reserved ranges (192.0.2.0/24, 198.18.0.0/15, 240.0.0.0/4, 2001:db8::/32, ...) as private,
and carrier-grade NAT (100.64.0.0/10) as **not** private. IPv4-mapped IPv6 (`::ffff:a.b.c.d`) is
unwrapped to IPv4 first.

Python has changed `is_private` in patch releases (3.10 and 3.13 disagree on `3fff::/20`, for
example). To catch that, `is_private_probe()` runs `is_private` on the edges of every IANA
special-purpose range, and the answers are part of `FEATURE_FINGERPRINT`. A Python that answers
differently gets a different fingerprint: the pinned-fingerprint test fails and the backend refuses
the model. Verified identical on 3.13.15 (Kaggle) and 3.14.8 (backend).

## Versioning

- `FEATURE_VERSION` (int) is bumped by hand on **any** change to what `featurize()` outputs.
- `FEATURE_FINGERPRINT` is a hash of the definition: columns, input fields, port table, flag list,
  port bounds, dtype, the packet-size definition, and the `is_private` probe results. `tests/test_ml_features.py` pins one fingerprint per
  version, so editing a table or column without bumping the version fails CI.
- `tests/fixtures/golden_features_v<N>.json` holds hand-written expected rows. It catches behaviour
  changes the hash can't see (e.g. a logic edit in `featurize_entry`).
- `feature_spec()` returns `feature_version`, `feature_fingerprint`, `feature_columns`,
  `nla_ml_version`, `sklearn_version` and `python_version` (informational only). Training
  notebooks store it in `metadata.json`. `assert_compatible()` raises `IncompatibleModelError` on
  any mismatch apart from `python_version`.
- **scikit-learn** is pinned once, as `SKLEARN_VERSION` in `compat.py` and the `sklearn` extra in
  `pyproject.toml`; a test keeps the two equal. The backend depends on `nla-ml[sklearn]`, so it
  can't drift from the notebooks.

**To change features:** edit the code → bump `FEATURE_VERSION` → add
`golden_features_v<N+1>.json` (keep the old one only if you still need it) → pin the new fingerprint
in `KNOWN_FINGERPRINTS` → retrain. Old models will then refuse to load, which is what you want.

`PORT_PROTOCOL_EXPECTATIONS` and `parse_flags` are also used by the production heuristics in
`ingest/anomaly.py`. Changing them changes the fingerprint too.

## Using it

**Backend:** it's a path dependency (`"nla-ml[sklearn]"` + `[tool.uv.sources] nla-ml = { path = "ml", editable = true }`).
To change the scikit-learn version, edit `SKLEARN_VERSION` and the extra here, then `uv lock` in `backend/`.
The Dockerfile copies `ml/` before `uv sync`.

**Kaggle:** install from a pinned commit, never a branch:

```
!pip install "nla-ml[sklearn] @ git+https://github.com/HannanAFC/NetLogAnalyser@<sha>#subdirectory=backend/ml"
```

The `[sklearn]` extra installs exactly the pinned scikit-learn, replacing Kaggle's preinstalled one.
Restart the kernel after installing, then call `assert_sklearn_version()` before training.

**Tests:** `uv run pytest ml/tests` from `backend/` (also included in the backend's normal `pytest`
run). They need no database or `.env`.

## Decisions (Phase 0)

| Decision | Status |
|---|---|
| Python floor | `>=3.13`. Kaggle runs 3.13.15, the backend 3.14. Tests pass on both. |
| `packet_size_bytes` definition | **IP total length** (IPv4 Total Length; IPv6 40 + Payload Length). Matches the heuristic thresholds (MTU 1500, jumbo 9000, tiny < 40 = smaller than a bare TCP/IPv4 packet). The CIC-IDS2017 adapter must produce this. Documented in the API schema and `sending-logs.mdx`. |
| Private-address check | Python's `is_private`, with the probe in the fingerprint (see above). |
| scikit-learn pin | `==1.9.1`: the latest release (2026-09-10), already in the backend lockfile, with wheels for cp313 (Kaggle) and cp314 (backend, Linux and macOS arm64). Needs numpy ≥ 1.24.1 and scipy ≥ 1.10. |
| Model artifact format | `joblib` for v1. ONNX later. |
| Kaggle internet access | **TODO:** enable it (needs a phone-verified account) so notebooks can `pip install` from GitHub. |
