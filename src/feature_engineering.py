"""
============================================================================
Phase 3: Scalable Feature Engineering with Spark MLlib
============================================================================
This module engineers three stylometric features from Arabic text using
distributed PySpark UDFs, plus TF-IDF using Spark MLlib's HashingTF + IDF.

Assigned features (per project rubric, after instructor reduction):
  Feature #12: Number of short words / N        (short_words_ratio)
  Feature #33: Total number of lines (L)        (total_physical_lines)
  Feature #54: Number of foreign letters        (foreign_letters_count + ratio)

Plus the standard advanced feature:
  TF-IDF (HashingTF + IDF, max 10000 features, unigrams + bigrams)

All operations run on Spark DataFrames -- no pandas, no driver-side loops.
============================================================================
"""

import os
import re
import argparse
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import IntegerType, FloatType, StructType, StructField

from pyspark.ml import Pipeline
from pyspark.ml.feature import (
    Tokenizer, RegexTokenizer, NGram, HashingTF, IDF,
    StopWordsRemover, VectorAssembler, StandardScaler
)


# ===========================================================================
# 1. SPARK SESSION
# ===========================================================================
def create_spark_session(app_name="ArabicAIDetection_Phase3", master="local[*]"):
    spark = (
        SparkSession.builder
        .appName(app_name)
        .master(master)
        .config("spark.sql.shuffle.partitions", "8")
        .config("spark.driver.memory", "3g")
        .config("spark.executor.memory", "3g")
        .config("spark.sql.execution.arrow.pyspark.enabled", "true")
        .config("spark.driver.extraJavaOptions", "-Dfile.encoding=UTF-8")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")
    return spark


# ===========================================================================
# 2. FEATURE EXTRACTION UDFs
# ===========================================================================
# Arabic Unicode block (matches the original notebook's pattern)
_ARABIC_RE = re.compile(
    r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]"
)

# Sentence boundary markers — Arabic + Latin
_SENTENCE_SPLIT_RE = re.compile(r"[\.!\?؟؛:،\-–()\"\[\]]+")


# ----- Feature #12: short_words_ratio --------------------------------------
def _short_words_ratio(text, short_length=3):
    """
    Ratio of words with length <= 3 to total number of words.
    Operates on the cleaned text (NOT the stemmed version) to preserve
    original word lengths.
    """
    if text is None or not isinstance(text, str) or not text.strip():
        return 0.0
    tokens = text.split()
    total = len(tokens)
    if total == 0:
        return 0.0
    short = sum(1 for tok in tokens if len(tok) <= short_length)
    return float(short) / float(total)


def _total_words(text):
    """Total number of word tokens. Used as denominator and as a feature."""
    if text is None or not isinstance(text, str) or not text.strip():
        return 0
    return len(text.split())


def _short_words_count(text, short_length=3):
    """Raw count of short words (for reporting)."""
    if text is None or not isinstance(text, str) or not text.strip():
        return 0
    return sum(1 for tok in text.split() if len(tok) <= short_length)


# ----- Feature #33: total_physical_lines + total_sentences -----------------
def _total_physical_lines(text):
    """Count non-empty physical lines (split on \\n)."""
    if text is None or not isinstance(text, str) or not text.strip():
        return 1
    lines = [ln.strip() for ln in str(text).splitlines() if ln.strip()]
    return max(1, len(lines))


def _total_sentences(text):
    """Count sentences using Arabic + Latin punctuation as delimiters."""
    if text is None or not isinstance(text, str) or not text.strip():
        return 1
    normalized = re.sub(r"\s+", " ", str(text).strip())
    parts = _SENTENCE_SPLIT_RE.split(normalized)
    cleaned = [
        re.sub(r"[^\w\s]", "", p).strip()
        for p in parts
        if len(p.strip()) > 3
    ]
    return max(1, len([s for s in cleaned if s]))


# ----- Feature #54: foreign_letters_count + foreign_letters_ratio ----------
def _foreign_letters_count(text):
    """Count alphabetic characters that are NOT in the Arabic Unicode range."""
    if text is None or not isinstance(text, str) or not text.strip():
        return 0
    letters = [c for c in text if c.isalpha()]
    return sum(1 for c in letters if not _ARABIC_RE.match(c))


def _foreign_letters_ratio(text):
    """Foreign letters / total letters."""
    if text is None or not isinstance(text, str) or not text.strip():
        return 0.0
    letters = [c for c in text if c.isalpha()]
    total = len(letters)
    if total == 0:
        return 0.0
    foreign = sum(1 for c in letters if not _ARABIC_RE.match(c))
    return float(foreign) / float(total)


# Register UDFs
short_words_ratio_udf = F.udf(_short_words_ratio, FloatType())
total_words_udf       = F.udf(_total_words, IntegerType())
short_words_count_udf = F.udf(_short_words_count, IntegerType())
total_lines_udf       = F.udf(_total_physical_lines, IntegerType())
total_sentences_udf   = F.udf(_total_sentences, IntegerType())
foreign_count_udf     = F.udf(_foreign_letters_count, IntegerType())
foreign_ratio_udf     = F.udf(_foreign_letters_ratio, FloatType())


# ===========================================================================
# 3. STYLOMETRIC FEATURES (THREE ASSIGNED FEATURES)
# ===========================================================================
def add_stylometric_features(df, raw_text_col="text", clean_text_col="cleaned_text"):
    """
    Add the three stylometric features to the DataFrame.

    Note on which text column to use for which feature:
      - Feature #12 (short_words_ratio): use cleaned_text (advanced cleaning
        applied, but BEFORE stemming) so we measure original word lengths.
      - Feature #33 (total_physical_lines): use raw text — line breaks are
        meaningful in the original document.
      - Feature #54 (foreign_letters): use raw text — we want to count ALL
        non-Arabic alphabetic characters, including those removed by cleaning.
    """
    print("\n" + "=" * 80)
    print("PHASE 3 - TASK 3.1: STYLOMETRIC FEATURE EXTRACTION (DISTRIBUTED)")
    print("=" * 80)
    print("\nAssigned Features (3 of 109):")
    print("  #12 Number of short words / N")
    print("  #33 Total number of lines (L)")
    print("  #54 Number of foreign letters")

    # Feature #12 — short words ratio
    df = (
        df.withColumn("total_words",       total_words_udf(F.col(clean_text_col)))
          .withColumn("short_words_count", short_words_count_udf(F.col(clean_text_col)))
          .withColumn("short_words_ratio", short_words_ratio_udf(F.col(clean_text_col)))
    )

    # Feature #33 — total physical lines
    df = (
        df.withColumn("total_physical_lines", total_lines_udf(F.col(raw_text_col)))
          .withColumn("total_sentences",      total_sentences_udf(F.col(raw_text_col)))
    )

    # Feature #54 — foreign letters
    df = (
        df.withColumn("foreign_letters_count", foreign_count_udf(F.col(raw_text_col)))
          .withColumn("foreign_letters_ratio", foreign_ratio_udf(F.col(raw_text_col)))
    )

    print("\n[FEAT] Summary statistics for stylometric features:")
    df.select(
        "short_words_ratio",
        "total_physical_lines",
        "foreign_letters_count",
        "foreign_letters_ratio"
    ).describe().show()

    print("[FEAT] Mean values by class (1=human, 0=AI):")
    df.groupBy("category_encode").agg(
        F.round(F.mean("short_words_ratio"),     4).alias("mean_short_ratio"),
        F.round(F.mean("total_physical_lines"),  2).alias("mean_lines"),
        F.round(F.mean("foreign_letters_count"), 2).alias("mean_foreign_cnt"),
        F.round(F.mean("foreign_letters_ratio"), 4).alias("mean_foreign_ratio"),
        F.count("*").alias("n_samples"),
    ).show()

    return df


# ===========================================================================
# 4. TF-IDF (Spark MLlib HashingTF + IDF)
# ===========================================================================
def build_tfidf_pipeline(input_col="processed_text", num_features=10000):
    """
    Build a Spark ML Pipeline that converts processed_text into a TF-IDF vector.

    Stages:
      1. RegexTokenizer  — split on whitespace
      2. HashingTF       — hash tokens to fixed-size feature vector
      3. IDF             — apply inverse document frequency weighting

    Note: We do NOT add bigrams here (unlike the original sklearn notebook
    which used ngram_range=(1,2)). Bigrams would require an NGram stage
    and ~doubling num_features. We keep unigrams for simplicity & speed.
    Add an NGram stage if higher accuracy is desired.
    """
    print("\n" + "=" * 80)
    print("PHASE 3 - TASK 3.2: TF-IDF FEATURE EXTRACTION (SPARK MLLIB)")
    print("=" * 80)
    print(f"  HashingTF -> {num_features} features")
    print(f"  IDF normalization on top")

    tokenizer = RegexTokenizer(
        inputCol=input_col,
        outputCol="tokens",
        pattern=r"\s+",
        gaps=True
    )
    hashing_tf = HashingTF(
        inputCol="tokens",
        outputCol="raw_tf",
        numFeatures=num_features
    )
    idf = IDF(
        inputCol="raw_tf",
        outputCol="tfidf_features",
        minDocFreq=2  # Ignore terms appearing in fewer than 2 documents
    )

    pipeline = Pipeline(stages=[tokenizer, hashing_tf, idf])
    return pipeline


def fit_and_transform_tfidf(pipeline, df_train, df_full):
    """
    Fit TF-IDF pipeline on training data only (avoid leakage),
    then transform both train and full DataFrame.
    """
    print("[TFIDF] Fitting pipeline on training data only (no leakage)...")
    model = pipeline.fit(df_train)
    print("[TFIDF] Transforming full dataset...")
    df_with_tfidf = model.transform(df_full)
    return df_with_tfidf, model


# ===========================================================================
# 5. ASSEMBLE FINAL FEATURE VECTOR (Stylometric + TF-IDF)
# ===========================================================================
def assemble_feature_vector(df, stylo_cols, tfidf_col="tfidf_features",
                            output_col="features"):
    """
    Combine stylometric features and TF-IDF into a single feature vector.

    Two output columns are produced:
      - 'features_stylo': stylometric only (4-dim, fast baseline)
      - 'features':       stylometric + TF-IDF (high-dim, used by main models)
    """
    print("\n[ASSEMBLE] Combining features into vectors...")

    # Stylometric-only assembler (for quick comparison with TF-IDF version)
    stylo_assembler = VectorAssembler(
        inputCols=stylo_cols,
        outputCol="features_stylo",
        handleInvalid="skip",
    )

    # Combined assembler (stylometric + TF-IDF)
    combined_assembler = VectorAssembler(
        inputCols=stylo_cols + [tfidf_col],
        outputCol=output_col,
        handleInvalid="skip",
    )

    df = stylo_assembler.transform(df)
    df = combined_assembler.transform(df)

    print(f"[ASSEMBLE] Stylometric-only vector: {len(stylo_cols)} dims")
    print(f"[ASSEMBLE] Combined vector: {len(stylo_cols)} stylo + TF-IDF dims")
    return df


# ===========================================================================
# 6. TRAIN/VAL/TEST SPLIT
# ===========================================================================
def stratified_split(df, label_col="category_encode", seed=42,
                     train_frac=0.70, val_frac=0.15):
    """
    Stratified 70/15/15 split — same proportions as the original notebook.

    PySpark doesn't have a built-in stratified split, so we do it per class.
    """
    print("\n[SPLIT] Performing stratified 70/15/15 split...")
    test_frac = 1.0 - train_frac - val_frac

    splits = []
    for label in [0, 1]:
        df_class = df.filter(F.col(label_col) == label)
        train, val, test = df_class.randomSplit(
            [train_frac, val_frac, test_frac],
            seed=seed,
        )
        splits.append((train, val, test))

    train_df = splits[0][0].union(splits[1][0])
    val_df   = splits[0][1].union(splits[1][1])
    test_df  = splits[0][2].union(splits[1][2])

    n_train = train_df.count()
    n_val   = val_df.count()
    n_test  = test_df.count()

    print(f"  Train: {n_train:,} rows")
    print(f"  Val:   {n_val:,} rows")
    print(f"  Test:  {n_test:,} rows")
    return train_df, val_df, test_df


# ===========================================================================
# 7. MAIN
# ===========================================================================
def main():
    parser = argparse.ArgumentParser(description="Phase 3: Feature engineering")
    parser.add_argument("--in-dir",  default="data/processed", help="Input parquet (output of Phase 1&2)")
    parser.add_argument("--out-dir", default="data/features",  help="Output directory for feature parquets")
    parser.add_argument("--master",  default="local[*]")
    parser.add_argument("--num-features", type=int, default=10000)
    args = parser.parse_args()

    spark = create_spark_session(master=args.master)
    try:
        print(f"\n[LOAD] Reading processed data from {args.in_dir}")
        df = spark.read.parquet(args.in_dir)
        print(f"[LOAD] Loaded {df.count():,} rows")

        # Step 1: stylometric features
        df = add_stylometric_features(df)

        # Step 2: split BEFORE fitting TF-IDF (no leakage)
        train_df, val_df, test_df = stratified_split(df)

        # Step 3: fit TF-IDF on train only, transform all splits
        tfidf_pipeline = build_tfidf_pipeline(num_features=args.num_features)
        tfidf_model = tfidf_pipeline.fit(train_df)

        train_df = tfidf_model.transform(train_df)
        val_df   = tfidf_model.transform(val_df)
        test_df  = tfidf_model.transform(test_df)

        # Step 4: assemble final feature vectors
        stylo_cols = [
            "short_words_ratio",
            "total_physical_lines",
            "foreign_letters_count",
            "foreign_letters_ratio",
            "total_words",
            "total_sentences",
        ]

        train_df = assemble_feature_vector(train_df, stylo_cols)
        val_df   = assemble_feature_vector(val_df, stylo_cols)
        test_df  = assemble_feature_vector(test_df, stylo_cols)

        # Step 5: save splits to Parquet for the modeling phase
        os.makedirs(args.out_dir, exist_ok=True)

        # Save only the columns we actually need downstream — keep file size reasonable
        keep_cols = ["category_encode", "processed_text"] + stylo_cols + [
            "tfidf_features", "features_stylo", "features"
        ]

        for name, split_df in [("train", train_df), ("val", val_df), ("test", test_df)]:
            out_path = os.path.join(args.out_dir, name)
            split_df.select(*keep_cols).write.mode("overwrite").parquet(out_path)
            print(f"[SAVE] {name} -> {out_path}")

        # Save the fitted TF-IDF pipeline for downstream loading / streaming reuse
        tfidf_path = os.path.join(args.out_dir, "tfidf_pipeline_model")
        tfidf_model.write().overwrite().save(tfidf_path)
        print(f"[SAVE] TF-IDF pipeline model -> {tfidf_path}")

        print("\n" + "=" * 80)
        print("✅ PHASE 3 COMPLETED SUCCESSFULLY")
        print("=" * 80)

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
