# nla-ml - NetLogAnalyser ML Dependency

This is a feature extraction dependency shared by the NetLogAnalyser backend and the Kaggle notebooks that train its
anomaly models (Random Forest and Isolation Forest).

The backend (at ingest) and the notebooks (at training) both call `featurize()`, so a model is only trained on and sees features that the backend can produce from an ingest request.

```python
from nla_ml.compat import assert_compatible, assert_sklearn_version, feature_spec
from nla_ml.features import featurize, featurize_frame

X = featurize( scoring_inputs )        # list of entry dicts to DataFrame[FEATURE_COLUMNS]
X = featurize_frame( adapted_df )      # DataFrame of entries remains as DataFrame, index preserved for labels

metadata = { **feature_spec( ), ... }  # notebook: write into the model's metadata.json
assert_compatible( metadata )          # backend: refuse a model trained on other features
assert_sklearn_version( )              # both: installed scikit-learn must be the pinned one
```

## What goes in and what comes out

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

Invalid entries via datasets are rejected and fail, so adaptors for datasets which are made to train models need to drop invalid entries before hand. For the ingest endpoint, validation is performed already.

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
!pip install "nla-ml[sklearn] @ git+https://github.com/HannanAFC/NetLogAnalyser.git@<sha>#subdirectory=backend/ml"
```

The `[sklearn]` extra installs exactly the pinned scikit-learn, replacing Kaggle's preinstalled one.
Restart the kernel after installing, then call `assert_sklearn_version()` before training.

**Tests:** `uv run pytest ml/tests` from `backend/` (also included in the backend's normal `pytest`
run). They need no database or `.env`.

## Models

`nla_ml.inference` saves, loads and scores model artifacts. An artifact is a directory with
`model.joblib` and `metadata.json` (`feature_spec()` + `model_type`, `model_version`,
`model_sha256`, `created_at`, plus `calibration` for Isolation Forests and any `extra` you pass).

```python
from nla_ml.inference import calibrate_iforest, export_model, load_model

# notebook: fit on featurize() output so the model records FEATURE_COLUMNS
export_model( rf, "rf", "out/rf", model_version="2026-11-rf-1", extra={ "dataset_version": 3 } )
export_model( iforest, "iforest", "out/iforest", model_version="2026-11-if-1",
              calibration=calibrate_iforest( iforest, X_benign_val ) )

model  = load_model( "out/rf", "rf" )   # raises ModelLoadError on any problem
scores = model.score( featurize( entries ) )   # float64 in [0, 1], higher = more anomalous
```

`load_model` refuses an artifact if: a file is missing; the scikit-learn version, feature version,
fingerprint or columns don't match; `model.joblib` doesn't match `model_sha256` (checked **before**
unpickling); the estimator isn't a `RandomForestClassifier` / `IsolationForest` fitted on
`FEATURE_COLUMNS`; the RF wasn't trained on labels 0/1; the IF calibration is missing or invalid; or a
smoke-test prediction isn't a finite score in [0, 1]. It also sets `n_jobs=1`, because the backend
already runs predictions on its own thread pool. Only load artifacts you made: unpickling runs code.

**Scores:** RF = `predict_proba` for class 1. IF = `-decision_function`, mapped linearly so that
`calibration.low` → 0 and `calibration.high` → 1, then clipped. `calibrate_iforest` sets low/high to
the 50th / 99.9th percentile of the raw scores on the data you give it (use benign validation data).

**In the backend** (`ingest/ml.py`):
- Models load at startup from `ML_MODEL_DIR/<name>/` for each name in `ML_MODELS`. With
  `ML_ENABLED=true`, any load failure **stops startup**. It runs before Redis and the other services
  connect.
- Each ingest batch is featurized once and scored by every model on a dedicated thread pool
  (`ML_INFERENCE_THREADS`, default 2), off the event loop. A full 500-row batch takes about 10 ms
  with the dummy models (featurize 3 ms, RF 2 ms, IF 5 ms on 4 cores).
- Each row gets `ml_rf` / `ml_iforest` results in the noisy-OR, weighted by `ML_WEIGHT_RF` /
  `ML_WEIGHT_IFOREST`, shown in `anomaly_reasons` as e.g. `rf model 2026-11-rf-1: 0.93`.
- If scoring fails at runtime, the error is logged and the batch is stored with heuristic scores
  only, so ingest never drops logs because of ML.
- The repo's `models/` folder is mounted read-only at `/app/shared/models` (dev and self-host compose).

**Dummy models**, for testing the plumbing (their accuracy is meaningless: the generator labels
packets with the heuristics' own rules):

```
cd backend && uv run python ml/scripts/train_dummy.py --out ../models
# then set ML_ENABLED=true and restart the backend
```
