# Trained Spark MLlib Models

This directory contains the trained Spark MLlib PipelineModels produced by `src/modeling.py`.

## Contents

| Subdirectory | Description | Test F1 | Test AUC |
|--------------|-------------|---------|----------|
| `LogisticRegression/` | Baseline (Task 3.4) - the best performer overall | **96.36%** | **98.61%** |
| `RandomForest/` | Advanced ensemble: 100 decision trees | 88.03% | 98.16% |
| `GBTClassifier/` | Advanced ensemble: 50 gradient boosting iterations | 96.37% | 98.53% |
| `best_model/` | Copy of the best model (Logistic Regression), used by the streaming pipeline |

## Reproducibility

All hyperparameters and the 70/15/15 train/val/test split use fixed random seeds. To regenerate from scratch (~18 minutes):

```bash
spark-submit src/modeling.py
```

Full evaluation results are saved in `reports/modeling_results.json`.

## File format

Each subdirectory contains a Spark MLlib `PipelineModel` serialized to its native format, which includes:
- `metadata/` - Parameters and stage information
- `stages/` - Each pipeline stage (Tokenizer, HashingTF, IDF, classifier) as a separate subdirectory
