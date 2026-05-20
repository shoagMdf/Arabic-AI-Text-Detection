#!/usr/bin/env python3
"""
============================================================================
Local MapReduce Driver — Class-Aware Corpus Statistics (Human vs AI)
============================================================================
Runs the canonical Hadoop Streaming pipeline locally:

    cat input.jsonl | mapper_by_class.py | sort | reducer_by_class.py > output.tsv

Then reads the aggregated output and computes per-class corpus statistics:
    - Total tokens (Human vs AI vs Combined)
    - Unique stems
    - Type-Token Ratio (TTR)
    - Hapax Legomena Ratio
    - Hapax Dislegomena Ratio
    - Top-20 most frequent words and bigrams per class

Saves:
    - data/mapreduce_output_by_class.tsv  (full reducer output)
    - reports/per_class_corpus_stats.json (numerical summary)
============================================================================
"""

import os
import sys
import json
import subprocess
from collections import Counter
from pathlib import Path


# ============================================================================
# Configuration
# ============================================================================
PROJECT_ROOT = Path.home() / "arabic_nlp_project"
SCRIPTS_DIR  = PROJECT_ROOT / "scripts"
DATA_DIR     = PROJECT_ROOT / "data"
REPORTS_DIR  = PROJECT_ROOT / "reports"

MAPPER  = SCRIPTS_DIR / "mapper_by_class.py"
REDUCER = SCRIPTS_DIR / "reducer_by_class.py"
INPUT   = DATA_DIR / "mapreduce_input_by_class.jsonl"
OUTPUT  = DATA_DIR / "mapreduce_output_by_class.tsv"
STATS   = REPORTS_DIR / "per_class_corpus_stats.json"

TOP_N = 20

# ============================================================================
# Step 1: Run the MapReduce pipeline locally
# ============================================================================

def run_mapreduce():
    """Run: cat input | mapper | sort | reducer > output"""
    print("=" * 72)
    print("  STEP 1: Running MapReduce pipeline (Hadoop Streaming pattern)")
    print("=" * 72)
    print(f"  cat {INPUT.name} | {MAPPER.name} | sort | {REDUCER.name} > {OUTPUT.name}")
    print()

    if not INPUT.exists():
        print(f"ERROR: Input file not found: {INPUT}")
        print(f"       Run regenerate_jsonl.py first to create it.")
        sys.exit(1)

    if not MAPPER.exists() or not REDUCER.exists():
        print(f"ERROR: Mapper or reducer missing in {SCRIPTS_DIR}")
        sys.exit(1)

    cmd = (
        f"cat '{INPUT}' | "
        f"python3 '{MAPPER}' | "
        f"sort | "
        f"python3 '{REDUCER}' > '{OUTPUT}'"
    )

    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"ERROR during MapReduce execution:\n{result.stderr}")
        sys.exit(1)

    size_mb = OUTPUT.stat().st_size / (1024 * 1024)
    print(f"OK output file size: {size_mb:.1f} MB")
    print()


# ============================================================================
# Step 2: Parse the reducer output into per-class Counters
# ============================================================================

def parse_output():
    """Read OUTPUT and split into per-class Counters."""
    print("=" * 72)
    print("  STEP 2: Parsing MapReduce output into per-class structures")
    print("=" * 72)

    counters = {
        "WORD_ALL":     Counter(),
        "WORD_HUMAN":   Counter(),
        "WORD_AI":      Counter(),
        "BIGRAM_ALL":   Counter(),
        "BIGRAM_HUMAN": Counter(),
        "BIGRAM_AI":    Counter(),
    }

    lines_read = 0
    with open(OUTPUT, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) != 3:
                continue
            key_type, value, count = parts
            try:
                count = int(count)
            except ValueError:
                continue
            if key_type in counters:
                counters[key_type][value] = count
            lines_read += 1

    print(f"  Lines read : {lines_read:,}")
    print(f"  Word_ALL   : {len(counters['WORD_ALL']):,} unique")
    print(f"  Word_HUMAN : {len(counters['WORD_HUMAN']):,} unique")
    print(f"  Word_AI    : {len(counters['WORD_AI']):,} unique")
    print(f"  Bigram_ALL : {len(counters['BIGRAM_ALL']):,} unique")
    print(f"  Bigram_HUMAN: {len(counters['BIGRAM_HUMAN']):,} unique")
    print(f"  Bigram_AI  : {len(counters['BIGRAM_AI']):,} unique")
    print()

    return counters


# ============================================================================
# Step 3: Compute corpus-level statistics per class
# ============================================================================

def compute_stats(words: Counter, bigrams: Counter):
    """Compute TTR, Hapax, Dislegomena, totals for one class."""
    total_tokens = sum(words.values())
    unique_words = len(words)
    hapax = sum(1 for c in words.values() if c == 1)
    dislegomena = sum(1 for c in words.values() if c == 2)

    return {
        "total_tokens":        total_tokens,
        "unique_words":        unique_words,
        "ttr":                 unique_words / total_tokens if total_tokens else 0,
        "hapax_count":         hapax,
        "hapax_ratio":         hapax / unique_words if unique_words else 0,
        "dislegomena_count":   dislegomena,
        "dislegomena_ratio":   dislegomena / unique_words if unique_words else 0,
        "total_bigrams":       sum(bigrams.values()),
        "unique_bigrams":      len(bigrams),
    }


# ============================================================================
# Step 4: Print a readable report
# ============================================================================

def print_report(counters):
    print("=" * 72)
    print("  STEP 3: Per-Class Corpus Statistics")
    print("=" * 72)
    print()

    stats = {
        "combined": compute_stats(counters["WORD_ALL"],   counters["BIGRAM_ALL"]),
        "human":    compute_stats(counters["WORD_HUMAN"], counters["BIGRAM_HUMAN"]),
        "ai":       compute_stats(counters["WORD_AI"],    counters["BIGRAM_AI"]),
    }

    # Pretty table
    print(f"{'Metric':<28} {'Combined':>14} {'Human':>14} {'AI':>14}")
    print("-" * 72)
    rows = [
        ("Total tokens",        "total_tokens"),
        ("Unique stems",        "unique_words"),
        ("Type-Token Ratio",    "ttr"),
        ("Hapax count",         "hapax_count"),
        ("Hapax ratio",         "hapax_ratio"),
        ("Dislegomena count",   "dislegomena_count"),
        ("Dislegomena ratio",   "dislegomena_ratio"),
        ("Total bigrams",       "total_bigrams"),
        ("Unique bigrams",      "unique_bigrams"),
    ]
    for label, key in rows:
        c = stats["combined"][key]
        h = stats["human"][key]
        a = stats["ai"][key]
        if "ratio" in key or key == "ttr":
            print(f"{label:<28} {c:>14.4f} {h:>14.4f} {a:>14.4f}")
        else:
            print(f"{label:<28} {c:>14,} {h:>14,} {a:>14,}")
    print()

    # Top N per class
    print("=" * 72)
    print(f"  STEP 4: TOP-{TOP_N} most frequent tokens (per class)")
    print("=" * 72)
    for klass in ("HUMAN", "AI", "ALL"):
        print(f"\n--- WORD_{klass} ---")
        for word, count in counters[f"WORD_{klass}"].most_common(TOP_N):
            print(f"  {word:<25} {count:>8,}")

    print()
    print("=" * 72)
    print(f"  STEP 5: TOP-{TOP_N} most frequent bigrams (per class)")
    print("=" * 72)
    for klass in ("HUMAN", "AI", "ALL"):
        print(f"\n--- BIGRAM_{klass} ---")
        for bigram, count in counters[f"BIGRAM_{klass}"].most_common(TOP_N):
            print(f"  {bigram:<35} {count:>8,}")

    return stats


# ============================================================================
# Step 5: Persist results
# ============================================================================

def save_results(counters, stats):
    print()
    print("=" * 72)
    print("  STEP 6: Saving per-class statistics")
    print("=" * 72)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # Compose JSON payload
    payload = {
        "stats": stats,
        "top_words": {
            "combined": counters["WORD_ALL"].most_common(TOP_N),
            "human":    counters["WORD_HUMAN"].most_common(TOP_N),
            "ai":       counters["WORD_AI"].most_common(TOP_N),
        },
        "top_bigrams": {
            "combined": counters["BIGRAM_ALL"].most_common(TOP_N),
            "human":    counters["BIGRAM_HUMAN"].most_common(TOP_N),
            "ai":       counters["BIGRAM_AI"].most_common(TOP_N),
        },
    }

    with open(STATS, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"  Saved: {STATS}")
    size_kb = STATS.stat().st_size / 1024
    print(f"  Size : {size_kb:.1f} KB")
    print()
    print("Done.")


# ============================================================================
# Entry
# ============================================================================

def main():
    run_mapreduce()
    counters = parse_output()
    stats = print_report(counters)
    save_results(counters, stats)


if __name__ == "__main__":
    main()
