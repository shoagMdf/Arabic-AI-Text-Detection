#!/usr/bin/env python3
"""
============================================================================
Hadoop MapReduce — Reducer with Class Labels (Human vs AI)
============================================================================
Aggregates (key_type, value, 1) tuples emitted by mapper_by_class.py.

The mapper emits the following key types:
    WORD_ALL, WORD_HUMAN, WORD_AI
    BIGRAM_ALL, BIGRAM_HUMAN, BIGRAM_AI

Hadoop guarantees that all values with the same key arrive together
after `sort`. This reducer simply sums them.

Output TSV format:
    <key_type>\t<value>\t<total_count>
============================================================================
"""

import sys

current_key = None
current_total = 0


def flush(key, total):
    """Emit the accumulated count for the current key."""
    if key is not None:
        # key is "TYPE\tVALUE" (mapper emits TYPE\tVALUE\t1)
        print(f"{key}\t{total}")


for raw_line in sys.stdin:
    line = raw_line.rstrip("\n")
    if not line:
        continue

    parts = line.split("\t")
    if len(parts) < 3:
        continue

    key_type = parts[0]
    value = parts[1]
    try:
        count = int(parts[2])
    except ValueError:
        continue

    # Combined key (TYPE + VALUE)
    full_key = f"{key_type}\t{value}"

    if full_key == current_key:
        current_total += count
    else:
        # Flush previous group
        flush(current_key, current_total)
        current_key = full_key
        current_total = count

# Flush the last group
flush(current_key, current_total)
