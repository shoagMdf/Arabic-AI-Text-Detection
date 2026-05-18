# Trained Models

This directory stores trained Spark MLlib pipeline models from `src/modeling.py`.

## Why this directory is empty on GitHub

Trained Spark MLlib models are large binary artifacts (10–100 MB each) and are
intentionally excluded from version control via `.gitignore`. The models can be
regenerated from scratch by running the modeling pipeline:

```bash
spark-submit src/modeling.py
```

This will produce:
- `models/LogisticRegression/` — Baseline model (best by validation F1)
- `models/RandomForest/`       — Advanced ensemble (100 trees)
- `models/GBTClassifier/`      — Advanced gradient boosting (50 iterations)
- `models/best_model/`         — Copy of the best model, used by the streaming pipeline

## Reproducibility

All hyperparameters and the train/val/test split are deterministic (fixed
random seeds), so the same models can be reproduced exactly. The full
evaluation results are saved in `reports/modeling_results.json`.
