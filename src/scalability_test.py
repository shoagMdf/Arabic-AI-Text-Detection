"""
============================================================================
Phase 4 - Task 4.4: Scalability Benchmarking
============================================================================
Measures end-to-end pipeline runtime as a function of allocated cores
(Spark `local[N]` parallelism). The same workload — load Parquet, apply
preprocessing, extract stylometric features, build TF-IDF, train Logistic
Regression — is run with N=1, 2, 4 cores. Wall-clock time is recorded.

Outputs: reports/scalability_results.json
         (used by visualizations.py to plot speedup chart)
============================================================================
"""

import os
import json
import time
import argparse
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_pipeline_with_n_cores(n_cores, processed_dir):
    """
    Run a representative subset of the pipeline (preprocess + features +
    fit Logistic Regression) and return the elapsed wall-clock seconds.
    """
    from pyspark.sql import SparkSession
    from pyspark.ml.classification import LogisticRegression

    # Use a fresh SparkSession per measurement so JVM warm-up doesn't bias N>1
    master = f"local[{n_cores}]"
    spark = (
        SparkSession.builder
        .appName(f"scalability_n{n_cores}")
        .master(master)
        .config("spark.sql.shuffle.partitions", str(max(2, n_cores * 2)))
        .config("spark.driver.memory", "3g")
        .config("spark.driver.extraJavaOptions", "-Dfile.encoding=UTF-8")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("ERROR")

    # Import lazily so each Spark session sees the same UDF definitions
    from src.feature_engineering import (
        add_stylometric_features, build_tfidf_pipeline, assemble_feature_vector,
        stratified_split,
    )

    print(f"\n  [N={n_cores}] Starting...")
    t0 = time.time()

    # Step 1: load processed Parquet
    df = spark.read.parquet(processed_dir)

    # Step 2: stylometric features
    df = add_stylometric_features(df)

    # Step 3: split + TF-IDF
    train_df, val_df, test_df = stratified_split(df)

    tfidf_model = build_tfidf_pipeline(num_features=10000).fit(train_df)
    train_df = tfidf_model.transform(train_df)
    test_df  = tfidf_model.transform(test_df)

    stylo_cols = [
        "short_words_ratio", "total_physical_lines", "foreign_letters_count",
        "foreign_letters_ratio", "total_words", "total_sentences",
    ]
    train_df = assemble_feature_vector(train_df, stylo_cols)
    test_df  = assemble_feature_vector(test_df, stylo_cols)

    # Step 4: train Logistic Regression (cheapest of the three models)
    lr = LogisticRegression(
        featuresCol="features", labelCol="category_encode",
        maxIter=20, regParam=0.01,
    )
    model = lr.fit(train_df)

    # Force evaluation by computing accuracy on test set (otherwise lazy)
    n_correct = (
        model.transform(test_df)
             .filter("prediction = category_encode")
             .count()
    )
    elapsed = time.time() - t0

    spark.stop()

    print(f"  [N={n_cores}] Elapsed: {elapsed:.1f}s | correct preds: {n_correct:,}")
    return elapsed, n_correct


def main():
    parser = argparse.ArgumentParser(description="Scalability benchmark")
    parser.add_argument("--processed-dir", default="data/processed")
    parser.add_argument("--cores", default="1,2,4",
                        help="Comma-separated list of core counts to test (e.g. '1,2,4')")
    parser.add_argument("--out-json", default="reports/scalability_results.json")
    args = parser.parse_args()

    cores_to_test = [int(c.strip()) for c in args.cores.split(",")]

    print("=" * 80)
    print("PHASE 4 - TASK 4.4: SCALABILITY BENCHMARK")
    print("=" * 80)
    print(f"  Testing core counts: {cores_to_test}")
    print(f"  Using processed data from: {args.processed_dir}")

    results = {}
    for n in cores_to_test:
        elapsed, n_correct = run_pipeline_with_n_cores(n, args.processed_dir)
        results[str(n)] = {
            "cores": n,
            "elapsed_seconds": elapsed,
            "correct_predictions": n_correct,
        }

    # Compute speedup
    base = results[str(cores_to_test[0])]["elapsed_seconds"]
    for n in cores_to_test:
        results[str(n)]["speedup"] = base / results[str(n)]["elapsed_seconds"]
        results[str(n)]["efficiency"] = results[str(n)]["speedup"] / n * cores_to_test[0]

    os.makedirs(os.path.dirname(args.out_json), exist_ok=True)
    with open(args.out_json, "w") as f:
        json.dump(results, f, indent=2)

    print("\n" + "=" * 80)
    print("SCALABILITY RESULTS")
    print("=" * 80)
    print(f"{'Cores':>6} {'Time (s)':>12} {'Speedup':>10} {'Efficiency':>12}")
    print("-" * 50)
    for n in cores_to_test:
        r = results[str(n)]
        print(f"{n:>6} {r['elapsed_seconds']:>11.2f}s {r['speedup']:>10.2f}x "
              f"{r['efficiency']*100:>11.1f}%")
    print(f"\n✓ Saved: {args.out_json}")


if __name__ == "__main__":
    main()
