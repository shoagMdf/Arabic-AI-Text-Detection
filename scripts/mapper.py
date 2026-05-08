#!/usr/bin/env python3
"""
============================================================================
Hadoop MapReduce - Mapper for Corpus Statistics
============================================================================
Reads Arabic text from stdin (one record per line, JSON or plain text)
and emits (word, 1) and (n-gram, 1) pairs.

Run with Hadoop Streaming:
  hadoop jar $HADOOP_HOME/share/hadoop/tools/lib/hadoop-streaming-*.jar \\
    -input /user/student/processed_text \\
    -output /user/student/wordcount_out \\
    -mapper "python3 mapper.py" \\
    -reducer "python3 reducer.py" \\
    -file scripts/mapper.py \\
    -file scripts/reducer.py
============================================================================
"""

import sys
import re
import json

# Same Arabic Unicode pattern used elsewhere in the project
ARABIC_RE = re.compile(
    r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]+"
)

# Read input line by line from stdin
for raw_line in sys.stdin:
    line = raw_line.strip()
    if not line:
        continue

    # Try JSON first (when input comes from a Spark write of processed_text rows),
    # else treat the whole line as text.
    text = None
    try:
        record = json.loads(line)
        # Pick the most appropriate text field if present
        for col in ("processed_text", "cleaned_text", "text"):
            if col in record and record[col]:
                text = record[col]
                break
    except (json.JSONDecodeError, TypeError):
        text = line

    if not text:
        continue

    # Tokenize: keep only Arabic word tokens
    tokens = ARABIC_RE.findall(text)
    if not tokens:
        continue

    # Emit unigrams: word\t1
    for tok in tokens:
        if len(tok) > 1:                      # skip 1-char noise
            print(f"WORD\t{tok}\t1")

    # Emit bigrams: bigram\t1
    for i in range(len(tokens) - 1):
        if len(tokens[i]) > 1 and len(tokens[i + 1]) > 1:
            print(f"BIGRAM\t{tokens[i]}_{tokens[i+1]}\t1")
