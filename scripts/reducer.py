#!/usr/bin/env python3
"""
============================================================================
Hadoop MapReduce - Reducer for Corpus Statistics
============================================================================
Aggregates (key, count) pairs from the mapper.

Input format (per line):  TYPE\\tKEY\\tCOUNT
   TYPE in {WORD, BIGRAM}

Output format:            TYPE\\tKEY\\tTOTAL_COUNT

The reducer relies on Hadoop sorting the input by key before delivery,
so identical keys arrive consecutively. We accumulate counts for each
key and emit when the key changes.

Demonstration of the M/R model:
  - Map phase   : (word, 1) pairs (parallelisable, no global state)
  - Shuffle/sort: Hadoop groups identical keys together (handled by HDFS)
  - Reduce phase: simple sum, also parallelisable across keys
============================================================================
"""

import sys

current_key = None
current_count = 0

for raw_line in sys.stdin:
    line = raw_line.strip()
    if not line:
        continue

    parts = line.split("\t")
    if len(parts) != 3:
        continue

    type_, key, value = parts
    composite_key = f"{type_}\t{key}"

    try:
        count = int(value)
    except ValueError:
        continue

    if composite_key == current_key:
        current_count += count
    else:
        if current_key is not None:
            print(f"{current_key}\t{current_count}")
        current_key = composite_key
        current_count = count

# Don't forget the last key
if current_key is not None:
    print(f"{current_key}\t{current_count}")
