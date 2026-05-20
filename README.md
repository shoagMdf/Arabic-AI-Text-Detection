# Scalable Real-time Detection of AI-Generated Arabic Text

> **A Distributed Big Data Pipeline Approach** — MSBDA-801 Final Project — Taibah University

![Python](https://img.shields.io/badge/Python-3.9-blue)
![Spark](https://img.shields.io/badge/Spark-3.5.0-orange)
![Hadoop](https://img.shields.io/badge/Hadoop-3.3.6-yellow)
![Kafka](https://img.shields.io/badge/Kafka-3.5.0-red)

---

## Overview

This project implements a complete distributed Big Data pipeline for detecting AI-generated Arabic text using the **KFUPM-JRCAI/arabic-generated-abstracts** dataset (8,388 academic abstracts, expanded to 41,940 wide-to-long samples and filtered to 36,524 clean samples). The pipeline runs on Apache Hadoop (HDFS) and Apache Spark on CentOS Stream 9.

### Key Results

| Model                   | Accuracy   | F1-Score   | ROC-AUC    | Train Time |
| ----------------------- | ---------- | ---------- | ---------- | ---------- |
| **Logistic Regression** | **96.55%** | **96.36%** | **98.61%** | 76.1 s     |
| Random Forest           | 91.91%     | 88.03%     | 98.16%     | 46.6 s     |
| GBT Classifier          | 96.56%     | 96.37%     | 98.53%     | 935.0 s    |

**Best model**: Logistic Regression (12.3× faster training than GBT for indistinguishable accuracy).

### Pipeline Stages

1. **Data Acquisition** — HuggingFace → HDFS Parquet
2. **Arabic Preprocessing** — Spark UDFs (normalization, Tashkeel removal, ISRI stemming)
3. **Feature Engineering** — TF-IDF (10K dims) + 5 stylometric features
4. **Classification** — 3 Spark MLlib classifiers benchmarked
5. **MapReduce Statistics** — Class-aware Hadoop Streaming job
6. **Streaming Deployment** — Spark Structured Streaming with 5-second trigger
7. **Scalability Benchmark** — 1/2/3 core comparison (Amdahl's Law validation)

---

## Quick Start

### Prerequisites

- CentOS Stream 9 (or compatible Linux)
- Java 11, Python 3.9
- Apache Hadoop 3.3.6 + Spark 3.5.0
- 6+ GB RAM, 3+ CPU cores

### 1. Clone & Install

```bash
git clone https://github.com/shoagMdf/Arabic-AI-Text-Detection.git
cd Arabic-AI-Text-Detection
pip3 install -r requirements.txt --user
```

### 2. Download Dataset (from HuggingFace)

```bash
python3 -c "
from datasets import load_dataset
import os
os.makedirs('data/raw', exist_ok=True)
ds = load_dataset('KFUPM-JRCAI/arabic-generated-abstracts')
for split in ds:
    ds[split].to_pandas().to_parquet(f'data/raw/{split}.parquet')
"
```

### 3. Upload to HDFS

```bash
hdfs dfs -mkdir -p /user/$USER/arabic_nlp/data/raw
hdfs dfs -put data/raw/*.parquet /user/$USER/arabic_nlp/data/raw/
```

### 4. Run the Pipeline

```bash
# Phase 1+2: Distributed Preprocessing
spark-submit src/data_preparation.py \
    --raw-dir hdfs://localhost:9000/user/$USER/arabic_nlp/data/raw \
    --out-dir hdfs://localhost:9000/user/$USER/arabic_nlp/data/processed \
    --hdfs

# Phase 3.1+3.2: Feature Engineering (TF-IDF + 5 stylometric features)
spark-submit src/feature_engineering.py \
    --in-dir hdfs://localhost:9000/user/$USER/arabic_nlp/data/processed \
    --out-dir data/features

# Phase 3.4+3.5: Train 3 classifiers (LR, RF, GBT)
spark-submit src/modeling.py

# MapReduce: Class-aware corpus statistics
python3 scripts/run_local_mapreduce.py

# Visualizations & EDA plots
python3 src/visualizations.py

# Scalability test (1, 2, 3 cores)
python3 src/scalability_test.py --cores 1,2,3

# Streaming (in 2 terminals)
python3 src/streaming_pipeline.py produce --n-messages 100 &
spark-submit src/streaming_pipeline.py run \
    --source files \
    --source-dir data/stream_input \
    --output-dir data/stream_output \
    --run-seconds 60
```

---

## Dataset

**Source**: [KFUPM-JRCAI/arabic-generated-abstracts](https://huggingface.co/datasets/KFUPM-JRCAI/arabic-generated-abstracts)

| Subset                   | Papers    | Description                          |
| ------------------------ | --------- | ------------------------------------ |
| `by_polishing`           | 2,851     | AI polishes existing human abstracts |
| `from_title`             | 2,963     | Free generation from paper titles    |
| `from_title_and_content` | 2,574     | Generation using title + content     |
| **Total**                | **8,388** | After wide→long: 41,940 samples      |

After preprocessing and deduplication: **36,524 clean samples** (2,992 Human + 33,532 AI, a 1:11.2 class ratio).

---

## Implemented Features

### Stylometric Features (5 of 109 from project spec)

Each student is assigned a subset using the closed-form index formula `f(k+i) = (k·n) + i`, where `i = 12` (student position) and `n = 21` (class size):

| #     | Feature                  | Description                                       |
| ----- | ------------------------ | ------------------------------------------------- |
| 12    | `short_words_ratio`      | Words ≤ 3 chars / total words                     |
| 33    | `total_physical_lines`   | Non-empty lines in the document                   |
| 54    | `foreign_letters_count`  | Non-Arabic Latin letters                          |
| **75**| `active_voice_count`     | **Novel** — sentences without passive markers     |
| **96**| `redundancy_score`       | **Novel** — 1 − (unique bigrams / total bigrams)  |

The two novel features reveal that AI-generated Arabic text contains:
- **64% more active-voice sentences** (Human 2.94 → AI 4.83 avg)
- **48% more bigram repetition** (Human 0.0342 → AI 0.0506)

### Distributed TF-IDF

- Spark MLlib `RegexTokenizer` → `NGram (n=1,2)` → `HashingTF (10,000 features)` → `IDF`
- Final feature vector: 10,008 dimensions (10,000 TF-IDF + 5 stylometric, padded)

### Class-Aware MapReduce Corpus Statistics

Hadoop Streaming-style: `cat | mapper_by_class.py | sort | reducer_by_class.py`

The mapper emits per-class keys (`WORD_HUMAN`, `WORD_AI`, `BIGRAM_HUMAN`, `BIGRAM_AI`) in a single pass, recovering Combined / Human / AI views simultaneously.

---

## Performance

### Classification Performance (Test Set, 5,326 held-out samples)

Detailed per-class precision and recall:

| Model           | AI Precision | AI Recall | Human Precision | Human Recall |
| --------------- | ------------ | --------- | --------------- | ------------ |
| Logistic Reg.   | 97.3%        | 99.0%     | 86.0%           | 68.4%        |
| Random Forest   | 91.9%        | 100%      | —               | 0.0%         |
| GBT             | 97.2%        | 99.1%     | 86.7%           | 68.0%        |

> **Note on Random Forest**: Human Precision is undefined (—) because the model
> predicted "AI" for all 5,326 test samples — a textbook majority-class collapse.
> Mathematically, Precision = TP / (TP + FP) = 0 / (0 + 0) is undefined. This
> demonstrates why accuracy alone (91.91%) is misleading on imbalanced datasets:
> a trivial "always predict AI" baseline achieves the same accuracy without any
> real classification capability. See the Discussion section of the report for
> the root cause analysis (bootstrap sampling + Gini-on-imbalanced-data +
> majority voting).

- Computed per-class F1 (LR): **F1(AI) = 98.1%**, **F1(Human) = 76.2%**
- Aggregate F1 (sample-weighted) = 96.36% ; unweighted macro-F1 = 87.2%
- Random Forest collapses on the minority class (predicts AI for every sample)

### Scalability (Amdahl's Law in Action)

| Cores | Time (s) | Speedup   | Efficiency |
| ----- | -------- | --------- | ---------- |
| 1     | 288.59   | 1.00×     | 100.0%     |
| **2** | **180.35** | **1.60×** | **80.0%**  |
| 3     | 185.32   | 1.56×     | 51.9%      |

**Amdahl saturation occurs after the second core** — the 3rd core gives no improvement (serial fraction s ≈ 0.29). On a multi-node cluster, data locality would reduce the serial bottleneck substantially.

### Class-Aware MapReduce Statistics

| Metric              | Combined    | Human    | AI         | Δ (AI vs Human) |
| ------------------- | ----------- | -------- | ---------- | --------------- |
| Samples             | 36,524      | 2,992    | 33,532     | —               |
| Total tokens        | 3,273,484   | 300,354  | 2,973,130  | 9.9×            |
| Unique stems        | 42,969      | 27,701   | 34,332     | 1.24×           |
| **TTR (per-doc)**   | —           | 0.8001   | 0.7625     | −4.7%           |
| **TTR (corpus)**    | —           | 0.7915   | 0.7482     | −5.5%           |
| **Hapax %**         | 38.03%      | 52.94%   | 31.57%     | 0.60× (1.68× ↓) |
| Total bigrams       | 3,236,960   | 297,362  | 2,939,598  | 9.9×            |
| Unique bigrams      | 907,904     | 214,582  | 810,788    | 3.78×           |

> **Note on Combined TTR**: The "Combined" column for TTR is intentionally left
> blank ("—") rather than reporting a single value. Two reasons: (1) the
> per-document TTR average is not meaningful when computed across two classes
> with vastly different document counts (2,992 vs 33,532); and (2) the
> corpus-level TTR for the combined corpus (mathematically 42,969 / 3,273,484 =
> 0.0131) is heavily distorted by sample-size bias (Heaps' law) and is
> dominated by AI's 91% token share — it does not reflect either class
> faithfully. The honest comparison is Human vs AI directly, where the
> consistent −4.7% (per-doc) and −5.5% (corpus) gap reveals AI's lower lexical
> diversity.

### Top AI Fingerprint Bigrams

The bigram **"متوقع ان"** ("expected that") appears **304.8× more often** in AI text than in human writing (3,415 AI occurrences vs 1 Human occurrence) — the single strongest discriminator observed in this study.

### Streaming

- **99 messages** processed across **12 batches**
- **5-second** trigger interval
- Cold-start latency: 10.2 s (PipelineModel deserialization)
- **Warm-state latency: ≈4.2 s** end-to-end (under the trigger interval)
- Steady-state throughput: ~0.5 messages/s per executor

---

## Repository Structure

```
.
├── data/                  # Raw and processed data (HDFS-mirrored locally)
├── models/                # Saved Spark MLlib PipelineModels
├── notebooks/             # Jupyter notebooks for EDA and prototyping
├── reports/               # Final Project Report (PDF/DOCX) + figures
├── scripts/               # MapReduce mapper/reducer scripts
├── src/                   # Production pipeline modules
│   ├── data_preparation.py
│   ├── feature_engineering.py
│   ├── modeling.py
│   ├── streaming_pipeline.py
│   ├── scalability_test.py
│   └── visualizations.py
├── README.md
└── requirements.txt
```

---

## Citation

If you use this work, please cite as:

```bibtex
@misc{almodaifer2026arabic,
  author = {Almodaifer, Shoag Khaleel Ibrahim},
  title  = {Detection of AI-Generated Arabic Text:
            A Distributed Data Pipeline Approach},
  year   = {2026},
  note   = {MSBDA-801 Final Project, Taibah University},
  url    = {https://github.com/shoagMdf/Arabic-AI-Text-Detection}
}
```

---

## License

Academic project — MSBDA-801 — Taibah University.
Code may be used for educational purposes.

---

## Author

**Shoag Khaleel Ibrahim Almodaifer** — Master's student in Big Data Analytics,
Department of Information Systems, College of Computer Science and Engineering,
Taibah University, Madinah, Saudi Arabia.

📧 TU4725067@taibahu.edu.sa
