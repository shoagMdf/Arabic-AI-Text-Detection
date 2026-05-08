# Scalable Real-time Detection of AI-Generated Arabic Text

> **A Distributed Big Data Pipeline Approach**
> MSBDA-801 Final Project — Taibah University

[![Python](https://img.shields.io/badge/Python-3.9-blue)]()
[![Spark](https://img.shields.io/badge/Spark-3.5.0-orange)]()
[![Hadoop](https://img.shields.io/badge/Hadoop-3.3.6-yellow)]()
[![Kafka](https://img.shields.io/badge/Kafka-3.5.0-red)]()

---

## 📊 Overview

This project implements a complete distributed Big Data pipeline for detecting AI-generated Arabic text using the **KFUPM-JRCAI/arabic-generated-abstracts** dataset (8,388 academic abstracts). The pipeline runs on Apache Hadoop (HDFS) and Apache Spark on CentOS Stream 9.

### Key Results

| Model | Accuracy | F1-Score | ROC-AUC | Train Time |
|-------|----------|----------|---------|------------|
| **Logistic Regression** ⭐ | **96.38%** | **96.17%** | **98.34%** | 87.0 s |
| Random Forest | 91.91% | 88.03% | 97.37% | 77.6 s |
| GBT Classifier | 95.19% | 94.83% | 97.51% | 967.6 s |

### Pipeline Stages
---

## 🚀 Quick Start

### Prerequisites

- CentOS Stream 9 (or compatible Linux)
- Java 11, Python 3.9
- Apache Hadoop 3.3.6 + Spark 3.5.0 (see `docs/CentOS_Installation_Guide.md`)
- 6+ GB RAM, 3+ CPU cores

### 1. Clone & Install

```bash
git clone https://github.com/<your-username>/Arabic-AI-Text-Detection.git
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

# Phase 3.1+3.2: Feature Engineering
spark-submit src/feature_engineering.py \
    --in-dir hdfs://localhost:9000/user/$USER/arabic_nlp/data/processed \
    --out-dir data/features

# Phase 3.4+3.5: Train 3 classifiers
spark-submit src/modeling.py

# MapReduce: Corpus statistics
python3 scripts/run_local_mapreduce.py

# Visualizations
python3 src/visualizations.py

# Scalability test
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

## 📊 Dataset

**Source**: [KFUPM-JRCAI/arabic-generated-abstracts](https://huggingface.co/datasets/KFUPM-JRCAI/arabic-generated-abstracts)

| Subset | Papers | Description |
|--------|--------|-------------|
| `by_polishing` | 2,851 | AI polishes existing human abstracts |
| `from_title` | 2,963 | Free generation from paper titles |
| `from_title_and_content` | 2,574 | Generation using title + content |
| **Total** | **8,388** | After wide→long: 41,940 samples |

---

## 🎯 Implemented Features

### Stylometric Features (3 of 109 from project spec)
- Feature #12 — `short_words_ratio` (≤ 3 chars / total words)
- Feature #33 — `total_physical_lines`
- Feature #54 — `foreign_letters_count`

### Distributed TF-IDF
- Spark MLlib `HashingTF` + `IDF`
- 10,000 features per document

### MapReduce Corpus Statistics
- Hadoop Streaming-style: `cat | mapper.py | sort | reducer.py`
- Outputs: word counts, bigram counts, TTR, Hapax Legomena Ratio

---

## 📈 Performance

### Scalability (Amdahl's Law in action)

| Cores | Time (s) | Speedup | Efficiency |
|-------|----------|---------|------------|
| 1 | 288.59 | 1.00× | 100.0% |
| 2 | 180.35 | **1.60×** | **80.0%** |
| 3 | 185.32 | 1.56× | 51.9% |

### MapReduce Statistics

- **Total tokens**: 3,273,484
- **Unique words**: 42,969
- **Unique bigrams**: 907,904
- **Type-Token Ratio**: 0.0131
- **Hapax Legomena Ratio**: 0.3803

### Streaming

- **99 messages** processed across **12 batches**
- **5-second** trigger interval
- Sub-5-second stable latency after warm-up

---

## 📝 License

Academic project — MSBDA-801 — Taibah University.
Code may be used for educational purposes.

---

## 👤 Author

**shoagkhaleel** — Master's student in Big Data Analytics, Taibah University.

