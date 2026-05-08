"""
============================================================================
Phase 3 (continued) & Phase 4: Distributed Modeling with Spark MLlib
============================================================================
Trains and evaluates three classifiers on the feature-engineered data:

  1. Logistic Regression  (baseline, Task 3.4)
  2. Random Forest        (Task 3.5)
  3. Gradient Boosted Trees (substitute for XGBoost — works natively in
                             Spark MLlib without extra JARs)

Each model is trained on:
  - features:       stylometric (3 features) + TF-IDF (10k dims) -- main model
  - features_stylo: stylometric only (3 features) -- for comparison

Evaluation metrics (Task 4.3):
  - Accuracy, Precision, Recall, F1-score
  - ROC-AUC
  - Confusion matrix (saved to PNG)

The best-performing model is saved for Phase 4 (streaming deployment).
============================================================================
"""

import os
import json
import time
import argparse
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.ml.classification import (
    LogisticRegression, RandomForestClassifier, GBTClassifier
)
from pyspark.ml.evaluation import (
    BinaryClassificationEvaluator, MulticlassClassificationEvaluator
)


def create_spark_session(app_name="ArabicAIDetection_Modeling", master="local[*]"):
    spark = (
        SparkSession.builder
        .appName(app_name)
        .master(master)
        .config("spark.sql.shuffle.partitions", "8")
        .config("spark.driver.memory", "4g")
        .config("spark.executor.memory", "4g")
        .config("spark.sql.execution.arrow.pyspark.enabled", "true")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")
    return spark


# ===========================================================================
# 1. EVALUATION HELPER
# ===========================================================================
def evaluate_model(predictions, label_col="category_encode"):
    """
    Compute accuracy, precision, recall, F1, and ROC-AUC for a binary classifier.
    Also returns the confusion-matrix counts as a dict.
    """
    # Binary AUC (probabilistic)
    auc_eval = BinaryClassificationEvaluator(
        labelCol=label_col,
        rawPredictionCol="rawPrediction",
        metricName="areaUnderROC",
    )
    auc = auc_eval.evaluate(predictions)

    # Discrete metrics
    metrics = {}
    for name in ["accuracy", "weightedPrecision", "weightedRecall", "f1"]:
        m = MulticlassClassificationEvaluator(
            labelCol=label_col,
            predictionCol="prediction",
            metricName=name,
        )
        metrics[name] = m.evaluate(predictions)

    # Confusion matrix
    cm = (
        predictions.groupBy(label_col, "prediction")
                   .count()
                   .orderBy(label_col, "prediction")
                   .collect()
    )
    cm_dict = {f"true_{r[label_col]}_pred_{r['prediction']}": r["count"] for r in cm}

    return {
        "accuracy":  metrics["accuracy"],
        "precision": metrics["weightedPrecision"],
        "recall":    metrics["weightedRecall"],
        "f1":        metrics["f1"],
        "roc_auc":   auc,
        "confusion_matrix": cm_dict,
    }


def print_evaluation(model_name, results, split_name="Test"):
    print(f"\n  -- {split_name} set evaluation for {model_name} --")
    print(f"     Accuracy : {results['accuracy']*100:6.2f}%")
    print(f"     Precision: {results['precision']*100:6.2f}%")
    print(f"     Recall   : {results['recall']*100:6.2f}%")
    print(f"     F1-Score : {results['f1']*100:6.2f}%")
    print(f"     ROC-AUC  : {results['roc_auc']*100:6.2f}%")
    print(f"     Confusion: {results['confusion_matrix']}")


# ===========================================================================
# 2. MODEL TRAINING
# ===========================================================================
def train_logistic_regression(train_df, val_df, test_df, features_col="features"):
    print("\n" + "=" * 80)
    print(f"TASK 3.4 / 4.1: LOGISTIC REGRESSION (BASELINE) on '{features_col}'")
    print("=" * 80)

    lr = LogisticRegression(
        featuresCol=features_col,
        labelCol="category_encode",
        maxIter=50,
        regParam=0.01,
        elasticNetParam=0.0,
    )

    t0 = time.time()
    model = lr.fit(train_df)
    train_time = time.time() - t0
    print(f"  Training time: {train_time:.1f} s")

    val_results  = evaluate_model(model.transform(val_df))
    test_results = evaluate_model(model.transform(test_df))
    print_evaluation("Logistic Regression", val_results, "Validation")
    print_evaluation("Logistic Regression", test_results, "Test")

    return model, {"val": val_results, "test": test_results, "train_time_s": train_time}


def train_random_forest(train_df, val_df, test_df, features_col="features"):
    print("\n" + "=" * 80)
    print(f"TASK 3.5: RANDOM FOREST on '{features_col}'")
    print("=" * 80)

    rf = RandomForestClassifier(
        featuresCol=features_col,
        labelCol="category_encode",
        numTrees=100,
        maxDepth=10,
        seed=42,
    )

    t0 = time.time()
    model = rf.fit(train_df)
    train_time = time.time() - t0
    print(f"  Training time: {train_time:.1f} s")

    val_results  = evaluate_model(model.transform(val_df))
    test_results = evaluate_model(model.transform(test_df))
    print_evaluation("Random Forest", val_results, "Validation")
    print_evaluation("Random Forest", test_results, "Test")

    return model, {"val": val_results, "test": test_results, "train_time_s": train_time}


def train_gbt(train_df, val_df, test_df, features_col="features"):
    print("\n" + "=" * 80)
    print(f"TASK 3.5: GRADIENT BOOSTED TREES (XGBoost-equivalent) on '{features_col}'")
    print("=" * 80)
    print("  Note: Spark's native GBTClassifier is used in place of XGBoost4j")
    print("  to avoid distributing extra JARs across executors.")

    gbt = GBTClassifier(
        featuresCol=features_col,
        labelCol="category_encode",
        maxIter=50,
        maxDepth=6,
        stepSize=0.1,
        seed=42,
    )

    t0 = time.time()
    model = gbt.fit(train_df)
    train_time = time.time() - t0
    print(f"  Training time: {train_time:.1f} s")

    val_results  = evaluate_model(model.transform(val_df))
    test_results = evaluate_model(model.transform(test_df))
    print_evaluation("GBT Classifier", val_results, "Validation")
    print_evaluation("GBT Classifier", test_results, "Test")

    return model, {"val": val_results, "test": test_results, "train_time_s": train_time}


# ===========================================================================
# 3. MAIN
# ===========================================================================
def main():
    parser = argparse.ArgumentParser(description="Phase 3-5: Train & evaluate Spark MLlib models")
    parser.add_argument("--features-dir", default="data/features",
                        help="Directory with train/val/test parquet (output of Phase 3)")
    parser.add_argument("--models-dir",   default="models", help="Directory to save trained models")
    parser.add_argument("--reports-dir",  default="reports", help="Directory to save evaluation JSON")
    parser.add_argument("--master",       default="local[*]")
    parser.add_argument("--features-col", default="features",
                        choices=["features", "features_stylo"],
                        help="Which feature vector to train on")
    args = parser.parse_args()

    spark = create_spark_session(master=args.master)
    try:
        print("\n[LOAD] Reading train/val/test splits...")
        train_df = spark.read.parquet(os.path.join(args.features_dir, "train"))
        val_df   = spark.read.parquet(os.path.join(args.features_dir, "val"))
        test_df  = spark.read.parquet(os.path.join(args.features_dir, "test"))

        # Cache for repeated training passes — this matters when training 3 models
        train_df = train_df.cache()
        val_df   = val_df.cache()
        test_df  = test_df.cache()

        print(f"  Train: {train_df.count():,}")
        print(f"  Val:   {val_df.count():,}")
        print(f"  Test:  {test_df.count():,}")

        print("\n[INFO] Class distribution in training set:")
        train_df.groupBy("category_encode").count().show()

        # Train all three models on the chosen feature set
        all_results = {}
        all_models = {}

        lr_model,  lr_res  = train_logistic_regression(train_df, val_df, test_df, args.features_col)
        all_results["LogisticRegression"] = lr_res
        all_models["LogisticRegression"]  = lr_model

        rf_model,  rf_res  = train_random_forest(train_df, val_df, test_df, args.features_col)
        all_results["RandomForest"] = rf_res
        all_models["RandomForest"]  = rf_model

        gbt_model, gbt_res = train_gbt(train_df, val_df, test_df, args.features_col)
        all_results["GBTClassifier"] = gbt_res
        all_models["GBTClassifier"]  = gbt_model

        # Pick the best model by validation F1 — used for streaming deployment
        best_name = max(all_results.keys(), key=lambda n: all_results[n]["val"]["f1"])
        best_model = all_models[best_name]
        print("\n" + "=" * 80)
        print(f"🏆 BEST MODEL: {best_name}")
        print(f"   Validation F1: {all_results[best_name]['val']['f1']*100:.2f}%")
        print(f"   Test F1:       {all_results[best_name]['test']['f1']*100:.2f}%")
        print("=" * 80)

        # Save models
        os.makedirs(args.models_dir, exist_ok=True)
        for name, model in all_models.items():
            path = os.path.join(args.models_dir, name)
            model.write().overwrite().save(path)
            print(f"  Saved: {path}")

        # Mark the best model with a separate symlink-like directory
        best_path = os.path.join(args.models_dir, "best_model")
        best_model.write().overwrite().save(best_path)
        print(f"  Saved best model copy to: {best_path}")

        # Save evaluation report as JSON
        os.makedirs(args.reports_dir, exist_ok=True)
        report = {
            "best_model_name": best_name,
            "feature_set": args.features_col,
            "results": all_results,
        }
        report_path = os.path.join(args.reports_dir, "modeling_results.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        print(f"  Saved evaluation report: {report_path}")

        # Also append a summary table for easy report-writing
        print("\n" + "=" * 80)
        print("FINAL COMPARISON (Test Set)")
        print("=" * 80)
        print(f"{'Model':<25} {'Accuracy':>9} {'F1':>8} {'ROC-AUC':>9} {'TrainTime':>10}")
        print("-" * 80)
        for name, r in all_results.items():
            t = r["test"]
            print(f"{name:<25} {t['accuracy']*100:8.2f}% {t['f1']*100:7.2f}% "
                  f"{t['roc_auc']*100:8.2f}% {r['train_time_s']:9.1f}s")
        print("=" * 80)

        print("\n✅ MODELING PHASE COMPLETED SUCCESSFULLY")

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
