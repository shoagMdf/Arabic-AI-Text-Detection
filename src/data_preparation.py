"""
============================================================================
Phase 1 & 2: Distributed Data Acquisition and Arabic Text Preprocessing
============================================================================
Project: Scalable Real-time Detection of AI-Generated Arabic Text
Course:  MSBDA-801 Big Data Analytics
Author:  Student (shoagMdf) - Taibah University
============================================================================

This module:
1. Loads the Arabic Generated Abstracts dataset (from HuggingFace or local)
2. Reshapes data from wide format (one row per paper) to long format (one row per text)
3. Encodes the binary label: 1 = human-written, 0 = AI-generated
4. Applies Arabic-specific text preprocessing (normalization, diacritics removal,
   stopwords, ISRI stemming) using Spark UDFs (distributed)
5. Saves the result as Parquet on HDFS (or local) for next phases
============================================================================
"""

import os
import re
import sys
import argparse
from pathlib import Path

# PySpark imports
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StringType, IntegerType, StructType, StructField


# ===========================================================================
# 1. SPARK SESSION INITIALIZATION
# ===========================================================================
def create_spark_session(app_name="ArabicAIDetection_Phase1_2", master="local[*]"):
    """
    Initialize a SparkSession optimized for Arabic NLP workloads.

    Parameters
    ----------
    app_name : str
        Application name shown in Spark UI.
    master : str
        Spark master URL. Use 'local[*]' for local mode (all cores),
        'yarn' for Hadoop cluster, or 'spark://host:7077' for standalone.

    Returns
    -------
    SparkSession
    """
    spark = (
        SparkSession.builder
        .appName(app_name)
        .master(master)
        # Tune for text-heavy Arabic workload:
        .config("spark.sql.shuffle.partitions", "8")
        .config("spark.driver.memory", "2g")
        .config("spark.executor.memory", "2g")
        # Arrow speeds up Pandas <-> Spark conversion:
        .config("spark.sql.execution.arrow.pyspark.enabled", "true")
        # Better UTF-8 handling for Arabic:
        .config("spark.driver.extraJavaOptions", "-Dfile.encoding=UTF-8")
        .config("spark.executor.extraJavaOptions", "-Dfile.encoding=UTF-8")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")
    print(f"[INIT] Spark session created — Spark v{spark.version}")
    print(f"[INIT] Master: {spark.sparkContext.master}")
    print(f"[INIT] Default parallelism: {spark.sparkContext.defaultParallelism}")
    return spark


# ===========================================================================
# 2. DATA LOADING (from HuggingFace or local Parquet)
# ===========================================================================
def load_raw_dataset(spark, raw_data_dir):
    """
    Load all three subsets of the dataset and concatenate into a single
    Spark DataFrame.

    The original dataset has WIDE format:
        original_abstract | allam_generated | jais_generated | llama_generated | openai_generated

    We convert it to LONG format:
        category               | text
        ---------------------- | -----
        original_abstract      | "..."
        allam_generated_abstract | "..."
        ...

    Then we add the binary label `category_encode`:
        original_abstract -> 1 (human)
        anything else     -> 0 (AI-generated)
    """
    print("\n" + "=" * 80)
    print("PHASE 1 — TASK 1.3: DATA INGESTION INTO DISTRIBUTED FILE SYSTEM")
    print("=" * 80)

    subset_files = {
        "by_polishing": "by_polishing.parquet",
        "from_title": "from_title.parquet",
        "from_title_and_content": "from_title_and_content.parquet",
    }

    all_long_dfs = []

    for subset_name, file_name in subset_files.items():
        path = os.path.join(raw_data_dir, file_name)
        # HDFS-compatible: let Spark handle file existence

        # Read Parquet directly into Spark DataFrame (distributed read)
        df_wide = spark.read.parquet(path)
        print(f"\n[LOAD] {subset_name}: {df_wide.count()} rows, "
              f"{len(df_wide.columns)} columns")

        # Reshape from wide to long using stack() — Spark equivalent of pd.melt
        # We stack 5 columns (1 human + 4 AI) into 2 columns (category, text)
        text_columns = [c for c in df_wide.columns if c.endswith("_abstract")]

        # Build the stack expression: stack(N, 'col1', col1, 'col2', col2, ...)
        stack_pairs = ", ".join([f"'{c}', `{c}`" for c in text_columns])
        stack_expr = f"stack({len(text_columns)}, {stack_pairs}) as (category, text)"

        df_long = (
            df_wide.selectExpr(stack_expr)
                   .withColumn("subset", F.lit(subset_name))
        )
        all_long_dfs.append(df_long)

    if not all_long_dfs:
        raise FileNotFoundError(
            f"No subset files found in {raw_data_dir}. "
            f"Run generate_synthetic_data.py or download from HuggingFace."
        )

    # Union all subsets — this is the master long-format DataFrame
    df_all = all_long_dfs[0]
    for df in all_long_dfs[1:]:
        df_all = df_all.unionByName(df)

    # Encode label: 1 if original_abstract, else 0
    df_all = df_all.withColumn(
        "category_encode",
        F.when(F.col("category") == "original_abstract", 1).otherwise(0)
    )

    print(f"\n[INGEST] Total rows after union: {df_all.count():,}")
    print("[INGEST] Class distribution:")
    df_all.groupBy("category_encode").count().show()
    print("[INGEST] Per-subset distribution:")
    df_all.groupBy("subset", "category_encode").count().orderBy("subset", "category_encode").show()

    return df_all


# ===========================================================================
# 3. ARABIC TEXT PREPROCESSING (DISTRIBUTED VIA UDF)
# ===========================================================================
# Arabic Unicode ranges (covers basic + supplement + presentation forms)
ARABIC_UNICODE_PATTERN = re.compile(
    r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]"
)

# Diacritics (tashkeel) Unicode range
DIACRITICS_PATTERN = re.compile(r"[\u064B-\u065F\u0670]")

# A compact Arabic stopword list (subset to keep UDF lightweight)
# Same as used in the original notebook (NLTK Arabic stopwords + extended)
ARABIC_STOPWORDS = {
    "في", "من", "على", "إلى", "عن", "هذا", "هذه", "ذلك", "تلك", "هؤلاء",
    "أولئك", "الذي", "التي", "الذين", "اللاتي", "اللواتي", "ما", "ماذا",
    "متى", "أين", "كيف", "لماذا", "كم", "أو", "أم", "لكن", "بل", "حتى",
    "إذا", "إذ", "إن", "أن", "كان", "كانت", "يكون", "تكون", "هو", "هي",
    "هم", "هن", "نحن", "أنت", "أنتم", "أنا", "قد", "قال", "قالت", "قالوا",
    "كل", "بعض", "غير", "بين", "عند", "منذ", "حول", "قبل", "بعد", "فوق",
    "تحت", "أمام", "خلف", "يمين", "يسار", "الى", "ولا", "وما", "لا",
    "لم", "لن", "ولم", "ولن", "فلا", "فقط", "أيضا", "كذلك", "ثم", "أو",
}


def _arabic_preprocess(text):
    """
    Pure-Python Arabic preprocessing — runs inside Spark UDF on each row.

    Steps (matches original notebook logic):
      1. Normalize Hamza forms:    أ إ آ  ->  ا
      2. Normalize Alif Maqsura:   ى      ->  ي
      3. Normalize Taa Marbuta:    ة      ->  ه  (at end of word)
      4. Strip diacritics (tashkeel)
      5. Remove non-Arabic characters
      6. Tokenize and remove Arabic stopwords (also drop tokens of length 1)
      7. Light stemming: strip common Arabic prefix/suffix patterns
         (drop-in replacement for NLTK ISRI Stemmer — kept simple to avoid
         distributing NLTK to every executor)

    Returns
    -------
    str
        Cleaned, stemmed, space-separated Arabic tokens.
    """
    if text is None or not isinstance(text, str) or not text.strip():
        return ""

    # Step 1: Normalize Hamza
    text = re.sub(r"[أإآ]", "ا", text)

    # Step 2: Alif Maqsura -> Yaa
    text = text.replace("ى", "ي")

    # Step 3: Taa Marbuta -> Ha at end of word
    text = re.sub(r"ة\b", "ه", text)

    # Step 4: Strip diacritics
    text = DIACRITICS_PATTERN.sub("", text)

    # Step 5: Remove non-Arabic characters (keep letters and spaces)
    text = re.sub(r"[^\u0600-\u06FF\s]", "", text)

    # Step 6: Tokenize, remove stopwords, drop tokens shorter than 2 chars
    tokens = [
        tok for tok in text.split()
        if tok not in ARABIC_STOPWORDS and len(tok) > 1
    ]

    # Step 7: Light Arabic stemming — strip common affixes
    # (Approximation of ISRI; full ISRI requires NLTK on every executor.
    # For demonstration purposes this captures most common prefixes/suffixes.)
    common_prefixes = ("ال", "بال", "كال", "فال", "وال", "لل", "و", "ف", "ب", "ل", "ك", "س", "ست", "سي", "ا")
    common_suffixes = ("ون", "ين", "ات", "ها", "هم", "هن", "نا", "كم", "كن", "ك", "ه", "ة", "ت", "ا", "ي")

    def light_stem(word):
        # Strip prefix (longest match first)
        for p in sorted(common_prefixes, key=len, reverse=True):
            if word.startswith(p) and len(word) - len(p) >= 3:
                word = word[len(p):]
                break
        # Strip suffix (longest match first)
        for s in sorted(common_suffixes, key=len, reverse=True):
            if word.endswith(s) and len(word) - len(s) >= 3:
                word = word[:-len(s)]
                break
        return word

    stemmed = [light_stem(tok) for tok in tokens]
    return " ".join(stemmed)


def _advanced_clean(text):
    """
    Apply additional cleaning: HTML, URLs, emails, numbers, repeated punctuation,
    elongation. Same logic as Phase 1&2 notebook (advanced_arabic_text_cleaning).
    """
    if text is None or not isinstance(text, str) or not text.strip():
        return ""
    text = re.sub(r"<[^>]+>", "", text)              # HTML tags
    text = re.sub(r"http\S+|www\S+|https\S+", "", text)  # URLs
    text = re.sub(r"\S+@\S+", "", text)              # Emails
    text = re.sub(r"\d+", "", text)                  # Digits
    text = re.sub(r"([؟!.,])\1+", r"\1", text)       # Repeated punctuation
    text = re.sub(r"(.)\1{2,}", r"\1", text)         # Elongation
    text = re.sub(r"\s+", " ", text).strip()         # Normalize spaces
    return text


# Register UDFs (these get distributed to all Spark executors)
arabic_preprocess_udf = F.udf(_arabic_preprocess, StringType())
advanced_clean_udf = F.udf(_advanced_clean, StringType())


# ===========================================================================
# 4. PIPELINE ORCHESTRATION
# ===========================================================================
def preprocess_dataset(df):
    """
    Apply the full Arabic NLP preprocessing pipeline to a Spark DataFrame.

    Adds two new columns:
      - cleaned_text:   raw text after advanced cleaning (HTML, URLs, etc.)
      - processed_text: fully preprocessed (normalized, stemmed, no stopwords)
    """
    print("\n" + "=" * 80)
    print("PHASE 2 — TASK 2.1: ARABIC TEXT PREPROCESSING (DISTRIBUTED)")
    print("=" * 80)

    # Drop NA and duplicates
    n_before = df.count()
    df = df.dropna(subset=["text", "category"])
    df = df.dropDuplicates(["text"])
    n_after = df.count()
    print(f"[CLEAN] Rows before: {n_before:,}  ->  after: {n_after:,}  "
          f"(dropped {n_before - n_after:,})")

    # Apply distributed preprocessing
    print("[PREP] Applying advanced_clean UDF...")
    df = df.withColumn("cleaned_text", advanced_clean_udf(F.col("text")))

    print("[PREP] Applying Arabic preprocessing UDF (normalize+stem+stopwords)...")
    df = df.withColumn("processed_text", arabic_preprocess_udf(F.col("cleaned_text")))

    # Drop rows where preprocessing produced empty strings
    df = df.filter(F.length(F.col("processed_text")) > 0)

    print(f"[PREP] Final row count: {df.count():,}")
    print("[PREP] Sample of processed output:")
    df.select("category", "text", "processed_text").show(3, truncate=80)
    return df


def save_processed_data(df, output_dir, hdfs=False):
    """
    Save the processed DataFrame as Parquet (compressed columnar format).

    Parameters
    ----------
    df : Spark DataFrame
    output_dir : str
        Local path or HDFS URI (e.g. 'hdfs://localhost:9000/user/student/processed').
    hdfs : bool
        If True, output_dir is treated as an HDFS path.
    """
    print("\n" + "=" * 80)
    print("PHASE 2 — TASK 2.2: SAVE AS PARQUET (COMPRESSED COLUMNAR FORMAT)")
    print("=" * 80)

    out_path = output_dir if hdfs else os.path.abspath(output_dir)
    print(f"[SAVE] Writing to: {out_path}")

    (
        df.write
          .mode("overwrite")
          .option("compression", "snappy")
          .parquet(out_path)
    )

    # Validation: read back and confirm
    n = df.sparkSession.read.parquet(out_path).count()
    print(f"[SAVE] ✓ Saved successfully — verified {n:,} rows in Parquet")


# ===========================================================================
# 5. MAIN ENTRY POINT
# ===========================================================================
def main():
    parser = argparse.ArgumentParser(description="Phase 1 & 2: Data prep + Arabic preprocessing")
    parser.add_argument("--raw-dir", default="data/raw", help="Raw parquet input directory")
    parser.add_argument("--out-dir", default="data/processed", help="Processed parquet output directory")
    parser.add_argument("--master", default="local[*]", help="Spark master URL (local[*], yarn, etc.)")
    parser.add_argument("--hdfs", action="store_true", help="Treat out-dir as HDFS path")
    args = parser.parse_args()

    spark = create_spark_session(master=args.master)

    try:
        # Phase 1: Load raw data into long-format Spark DataFrame
        df_raw = load_raw_dataset(spark, args.raw_dir)

        # Phase 2: Apply distributed Arabic preprocessing
        df_processed = preprocess_dataset(df_raw)

        # Save as Parquet for downstream phases
        save_processed_data(df_processed, args.out_dir, hdfs=args.hdfs)

        print("\n" + "=" * 80)
        print("✅ PHASE 1 & 2 COMPLETED SUCCESSFULLY")
        print("=" * 80)

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
