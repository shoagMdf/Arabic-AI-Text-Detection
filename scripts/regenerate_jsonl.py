#!/usr/bin/env python3
"""
============================================================================
Regenerate MapReduce Input JSONL with Class Labels
============================================================================
Reads the processed Parquet data and writes a JSONL file where each line
contains both `processed_text` and `category_encode` so that MapReduce can
emit per-class statistics (Human vs AI).

Input:   data/processed/*.parquet
Output:  data/mapreduce_input_by_class.jsonl
============================================================================
"""

import os
import json
from pyspark.sql import SparkSession
from pyspark.sql import functions as F


def main():
    project_root = os.path.expanduser("~/arabic_nlp_project")
    in_path  = os.path.join(project_root, "data/processed")
    out_path = os.path.join(project_root, "data/mapreduce_input_by_class.jsonl")

    print(f"=== Regenerating MapReduce input with class labels ===")
    print(f"Input  : {in_path}")
    print(f"Output : {out_path}")
    print()

    spark = (
        SparkSession.builder
        .appName("regenerate-jsonl-by-class")
        .master("local[*]")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")

    # Read processed data
    df = spark.read.parquet(in_path)
    print(f"Schema:")
    df.printSchema()
    print(f"Total rows: {df.count():,}")
    print()

    # Verify required columns
    required = ["processed_text", "category_encode"]
    for col in required:
        if col not in df.columns:
            print(f"ERROR: column '{col}' not found!")
            print(f"Available columns: {df.columns}")
            spark.stop()
            return

    # Keep only the two columns we need (compact JSONL)
    df_out = df.select(
        F.col("processed_text"),
        F.col("category_encode").cast("integer")
    ).filter(F.col("processed_text").isNotNull())

    # Show distribution
    print("Class distribution:")
    df_out.groupBy("category_encode").count().orderBy("category_encode").show()

    # Collect to driver (small enough), write JSONL manually for clean output
    rows = df_out.toLocalIterator()
    n_written = 0
    n_human = 0
    n_ai = 0
    with open(out_path, "w", encoding="utf-8") as f:
        for row in rows:
            obj = {
                "processed_text": row["processed_text"],
                "category_encode": int(row["category_encode"])
            }
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")
            n_written += 1
            if obj["category_encode"] == 1:
                n_human += 1
            else:
                n_ai += 1

    size_mb = os.path.getsize(out_path) / (1024 * 1024)

    print()
    print(f"=== Done ===")
    print(f"Rows written : {n_written:,}")
    print(f"  - Human    : {n_human:,}")
    print(f"  - AI       : {n_ai:,}")
    print(f"File size    : {size_mb:.1f} MB")
    print(f"Path         : {out_path}")

    spark.stop()


if __name__ == "__main__":
    main()
