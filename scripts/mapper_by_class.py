#!/usr/bin/env python3
"""
============================================================================
Hadoop MapReduce — Mapper with Class Labels (Human vs AI)
============================================================================
Reads JSONL records of the form:
    {"processed_text": "...", "category_encode": 0 or 1}

where category_encode = 1 means HUMAN and 0 means AI.

Emits four key types per record so the reducer can aggregate per class
AND keep the combined corpus statistics:

    WORD_ALL    <token>     1
    WORD_HUMAN  <token>     1     (only if category=1)
    WORD_AI     <token>     1     (only if category=0)
    BIGRAM_ALL    <w1>_<w2>   1
    BIGRAM_HUMAN  <w1>_<w2>   1   (only if category=1)
    BIGRAM_AI     <w1>_<w2>   1   (only if category=0)
============================================================================
"""

import sys
import re
import json

# Arabic Unicode word pattern (same as elsewhere in the project)
ARABIC_RE = re.compile(
    r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]+"
)


def emit(key_type: str, value: str, count: int = 1) -> None:
    """Emit a key/value pair to stdout in MapReduce TSV format."""
    print(f"{key_type}\t{value}\t{count}")


for raw_line in sys.stdin:
    line = raw_line.strip()
    if not line:
        continue

    # Parse JSON record
    try:
        record = json.loads(line)
    except (json.JSONDecodeError, TypeError):
        continue

    text = record.get("processed_text")
    if not text:
        continue

    category = record.get("category_encode")
    if category == 1:
        class_label = "HUMAN"
    elif category == 0:
        class_label = "AI"
    else:
        class_label = "UNKNOWN"

    # Tokenize: keep only Arabic word tokens, skip 1-char noise
    tokens = [t for t in ARABIC_RE.findall(text) if len(t) > 1]
    if not tokens:
        continue

    # === Emit unigrams ===
    for tok in tokens:
        emit("WORD_ALL", tok)
        if class_label != "UNKNOWN":
            emit(f"WORD_{class_label}", tok)

    # === Emit bigrams ===
    for i in range(len(tokens) - 1):
        bigram = f"{tokens[i]}_{tokens[i + 1]}"
        emit("BIGRAM_ALL", bigram)
        if class_label != "UNKNOWN":
            emit(f"BIGRAM_{class_label}", bigram)
