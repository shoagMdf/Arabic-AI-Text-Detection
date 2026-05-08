#!/usr/bin/env python3
"""
============================================================================
Local MapReduce Simulation
============================================================================
Simulates a Hadoop Streaming job locally using Unix pipes:

    cat input | mapper.py | sort | reducer.py > output

This is exactly the workflow Hadoop Streaming follows internally — only
the input/output filesystem (HDFS vs local) and the parallelism differ.

Use this for development before deploying to a real Hadoop cluster.
============================================================================
"""

import os
import sys
import argparse
import subprocess
from collections import Counter
import json


def export_text_to_jsonl(parquet_dir, output_jsonl, text_col="processed_text"):
    """Convert the Phase-1&2 Parquet output into newline-delimited JSON for the
    MapReduce mapper to consume. Keeps only the text column to minimize I/O."""
    from pyspark.sql import SparkSession

    spark = (
        SparkSession.builder
        .master("local[*]")
        .appName("export_for_mapreduce")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("ERROR")
    df = spark.read.parquet(parquet_dir).select(text_col)
    rows = df.collect()
    spark.stop()

    with open(output_jsonl, "w", encoding="utf-8") as f:
        for r in rows:
            json.dump({text_col: r[text_col]}, f, ensure_ascii=False)
            f.write("\n")
    print(f"[EXPORT] Wrote {len(rows):,} rows -> {output_jsonl}")
    return output_jsonl


def run_local_mapreduce(input_file, output_file, scripts_dir="scripts"):
    """Pipe input through mapper | sort | reducer, like Hadoop Streaming does."""
    mapper = os.path.join(scripts_dir, "mapper.py")
    reducer = os.path.join(scripts_dir, "reducer.py")

    print(f"[MR] Input  : {input_file}")
    print(f"[MR] Mapper : {mapper}")
    print(f"[MR] Reducer: {reducer}")
    print(f"[MR] Output : {output_file}\n")

    cmd = (
        f"cat {input_file} | "
        f"python3 {mapper} | "
        f"sort -t$'\\t' -k1,2 | "
        f"python3 {reducer} > {output_file}"
    )
    subprocess.check_call(cmd, shell=True, executable="/bin/bash")

    line_count = sum(1 for _ in open(output_file, encoding="utf-8"))
    print(f"[MR] Output rows: {line_count:,}")
    return output_file


def summarize_results(output_file, top_n=20):
    """Read the reducer output and print top-N words and bigrams."""
    word_counts = Counter()
    bigram_counts = Counter()

    with open(output_file, encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split("\t")
            if len(parts) != 3:
                continue
            type_, key, count = parts
            try:
                count = int(count)
            except ValueError:
                continue
            if type_ == "WORD":
                word_counts[key] = count
            elif type_ == "BIGRAM":
                bigram_counts[key] = count

    print("\n" + "=" * 80)
    print("CORPUS-WIDE STATISTICS (computed via MapReduce)")
    print("=" * 80)
    print(f"  Unique words   : {len(word_counts):,}")
    print(f"  Unique bigrams : {len(bigram_counts):,}")
    print(f"  Total tokens   : {sum(word_counts.values()):,}")
    print(f"  Total bigrams  : {sum(bigram_counts.values()):,}")

    # Type-Token Ratio (TTR) - vocabulary richness
    if sum(word_counts.values()) > 0:
        ttr = len(word_counts) / sum(word_counts.values())
        print(f"  Type-Token Ratio (vocabulary richness): {ttr:.4f}")

    # Hapax Legomena (words appearing exactly once)
    hapax = sum(1 for c in word_counts.values() if c == 1)
    if word_counts:
        hapax_ratio = hapax / len(word_counts)
        print(f"  Hapax Legomena Count: {hapax:,}")
        print(f"  Hapax Legomena Ratio: {hapax_ratio:.4f}")

    print(f"\nTOP {top_n} MOST FREQUENT WORDS:")
    for word, count in word_counts.most_common(top_n):
        print(f"   {count:>6}  {word}")

    print(f"\nTOP {top_n} MOST FREQUENT BIGRAMS:")
    for bg, count in bigram_counts.most_common(top_n):
        print(f"   {count:>6}  {bg.replace('_', ' ')}")


def main():
    parser = argparse.ArgumentParser(description="Local MapReduce simulation")
    parser.add_argument("--processed-dir", default="data/processed",
                        help="Spark Parquet output of Phase 1&2")
    parser.add_argument("--input-file",  default="data/mapreduce_input.jsonl",
                        help="Where to write the JSONL extracted from Parquet")
    parser.add_argument("--output-file", default="data/mapreduce_output.tsv")
    parser.add_argument("--top-n", type=int, default=20)
    parser.add_argument("--skip-export", action="store_true",
                        help="Reuse existing input-file instead of re-exporting from Parquet")
    args = parser.parse_args()

    if not args.skip_export:
        export_text_to_jsonl(args.processed_dir, args.input_file)

    run_local_mapreduce(args.input_file, args.output_file)
    summarize_results(args.output_file, top_n=args.top_n)


if __name__ == "__main__":
    main()
