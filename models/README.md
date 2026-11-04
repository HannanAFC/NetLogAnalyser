# Model artifacts

This folder is mounted read-only into the backend at `/app/shared/models` (`ML_MODEL_DIR`).
Its contents are git-ignored; only this README is committed.

```
models/
  rf/        model.joblib + metadata.json   (Random Forest)
  iforest/   model.joblib + metadata.json   (Isolation Forest)
```

Artifacts are written by `nla_ml.inference.export_model`, from the Kaggle notebooks or, for a
throwaway model to test the plumbing, by:

```
cd backend && uv run python ml/scripts/train_dummy.py --out ../models
```

Then set `ML_ENABLED=true` and restart the backend. With ML enabled, every model in `ML_MODELS`
must load and pass validation (feature version and fingerprint, scikit-learn version, checksum,
estimator type), or the backend refuses to start. Only put artifacts you made here: loading one
unpickles it, which runs code.
