"""
============================================================================
Phase 4: Stream Processing & Real-time Deployment
============================================================================
Implements a real-time AI-Arabic-text detection pipeline using
Spark Structured Streaming with TWO supported input modes:

  1. File-based stream  (default; works on any environment, including
                         CentOS without Kafka installed)
  2. Kafka stream       (production-grade; requires Kafka broker running
                         on localhost:9092 with topic 'arabic_abstracts')

How streaming works here:
  - The trained Phase-3 best_model + tfidf_pipeline_model are loaded once
    on driver, broadcast to executors
  - Incoming text rows are passed through the same UDF preprocessing
    + TF-IDF transform + classifier
  - Predictions are written to a sink (console + Parquet for archival)

This satisfies Tasks 4.1 (stream simulation) and 4.2 (real-time deployment).
============================================================================
"""

import os
import re
import time
import argparse
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StringType, StructType, StructField, IntegerType, FloatType
from pyspark.ml import PipelineModel
from pyspark.ml.classification import (
    LogisticRegressionModel, RandomForestClassificationModel, GBTClassificationModel
)

# Reuse the SAME UDFs / patterns as in data_preparation.py and feature_engineering.py
# Add parent directory to path so we can import as siblings
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from src.data_preparation import arabic_preprocess_udf, advanced_clean_udf
    from src.feature_engineering import (
        short_words_ratio_udf, total_words_udf, short_words_count_udf,
        total_lines_udf, total_sentences_udf,
        foreign_count_udf, foreign_ratio_udf,
    )
except ImportError:
    from data_preparation import arabic_preprocess_udf, advanced_clean_udf
    from feature_engineering import (
        short_words_ratio_udf, total_words_udf, short_words_count_udf,
        total_lines_udf, total_sentences_udf,
        foreign_count_udf, foreign_ratio_udf,
    )
from pyspark.ml.feature import VectorAssembler


# ===========================================================================
# 1. SPARK SESSION FOR STREAMING
# ===========================================================================
def create_spark_session(app_name="ArabicAIDetection_Streaming",
                         master="local[*]", with_kafka=False):
    """
    Build a SparkSession configured for Structured Streaming.

    If with_kafka=True, the Kafka source connector JAR is loaded.
    """
    builder = (
        SparkSession.builder
        .appName(app_name)
        .master(master)
        .config("spark.sql.shuffle.partitions", "4")
        .config("spark.driver.memory", "2g")
        .config("spark.executor.memory", "2g")
        .config("spark.streaming.stopGracefullyOnShutdown", "true")
    )

    if with_kafka:
        # When running on CentOS, this triggers Spark to fetch the Kafka
        # connector from Maven Central. Run with --packages to include it.
        builder = builder.config(
            "spark.jars.packages",
            "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0"
        )

    spark = builder.getOrCreate()
    spark.sparkContext.setLogLevel("WARN")
    return spark


# ===========================================================================
# 2. LOAD TRAINED MODELS (saved in Phase 3)
# ===========================================================================
def load_trained_artifacts(features_dir, models_dir):
    """
    Load the TF-IDF pipeline and the best classifier.

    Returns
    -------
    tfidf_model : PipelineModel
    classifier  : (one of LR / RF / GBT) — auto-detected from disk
    """
    tfidf_path = os.path.join(features_dir, "tfidf_pipeline_model")
    print(f"[LOAD] TF-IDF pipeline from: {tfidf_path}")
    tfidf_model = PipelineModel.load(tfidf_path)

    best_path = os.path.join(models_dir, "best_model")
    print(f"[LOAD] Best classifier from: {best_path}")

    # Try each classifier type — only one will succeed
    last_err = None
    for ModelCls in (LogisticRegressionModel, RandomForestClassificationModel, GBTClassificationModel):
        try:
            clf = ModelCls.load(best_path)
            print(f"[LOAD] Loaded {ModelCls.__name__}")
            return tfidf_model, clf
        except Exception as e:
            last_err = e
            continue

    raise RuntimeError(f"Could not load classifier from {best_path}: {last_err}")


# ===========================================================================
# 3. STREAMING TRANSFORMATION FUNCTION
# ===========================================================================
STYLO_COLS = [
    "short_words_ratio", "total_physical_lines",
    "foreign_letters_count", "foreign_letters_ratio",
    "total_words", "total_sentences",
]


def add_features_for_streaming(df):
    """
    Apply the same feature engineering as Phase 3, but inline so that
    Structured Streaming can apply it row-by-row to the streaming DataFrame.
    """
    # Cleaning
    df = df.withColumn("cleaned_text", advanced_clean_udf(F.col("text")))
    df = df.withColumn("processed_text", arabic_preprocess_udf(F.col("cleaned_text")))

    # Stylometric features
    df = (
        df.withColumn("total_words",       total_words_udf(F.col("cleaned_text")))
          .withColumn("short_words_count", short_words_count_udf(F.col("cleaned_text")))
          .withColumn("short_words_ratio", short_words_ratio_udf(F.col("cleaned_text")))
          .withColumn("total_physical_lines", total_lines_udf(F.col("text")))
          .withColumn("total_sentences",      total_sentences_udf(F.col("text")))
          .withColumn("foreign_letters_count", foreign_count_udf(F.col("text")))
          .withColumn("foreign_letters_ratio", foreign_ratio_udf(F.col("text")))
    )
    return df


def assemble_features(df, tfidf_model):
    """
    Apply the loaded TF-IDF pipeline + concat with stylometric features
    to produce the final 'features' column expected by the classifier.
    """
    # Apply TF-IDF
    df = tfidf_model.transform(df)

    # Combine stylometric + TF-IDF
    assembler = VectorAssembler(
        inputCols=STYLO_COLS + ["tfidf_features"],
        outputCol="features",
        handleInvalid="skip"
    )
    return assembler.transform(df)


# ===========================================================================
# 4. STREAMING SOURCES
# ===========================================================================
def stream_from_files(spark, source_dir):
    """
    Read newline-delimited JSON files dropped into source_dir as a stream.
    Schema: {'text': '...', 'true_label': 0|1}
    """
    schema = StructType([
        StructField("text", StringType(), True),
        StructField("true_label", IntegerType(), True),
    ])

    print(f"[STREAM] Watching directory: {source_dir} (file-based stream)")
    return (
        spark.readStream
             .schema(schema)
             .option("maxFilesPerTrigger", 1)
             .json(source_dir)
    )


def stream_from_kafka(spark, kafka_servers="localhost:9092", topic="arabic_abstracts"):
    """
    Read from a Kafka topic. Each Kafka message value should be:
        {"text": "...", "true_label": 0|1}
    """
    print(f"[STREAM] Subscribing to Kafka topic '{topic}' on {kafka_servers}")

    kafka_df = (
        spark.readStream
             .format("kafka")
             .option("kafka.bootstrap.servers", kafka_servers)
             .option("subscribe", topic)
             .option("startingOffsets", "latest")
             .load()
    )

    # Decode the JSON value
    schema = StructType([
        StructField("text", StringType(), True),
        StructField("true_label", IntegerType(), True),
    ])
    return (
        kafka_df.selectExpr("CAST(value AS STRING) AS json_str")
                .select(F.from_json(F.col("json_str"), schema).alias("data"))
                .select("data.*")
    )


# ===========================================================================
# 5. MAIN STREAMING PIPELINE
# ===========================================================================
def run_streaming(args):
    spark = create_spark_session(
        master=args.master,
        with_kafka=(args.source == "kafka"),
    )

    try:
        # Load trained artifacts
        tfidf_model, classifier = load_trained_artifacts(args.features_dir, args.models_dir)
        print(f"[INIT] Models loaded successfully\n")

        # Build streaming source
        if args.source == "kafka":
            stream_df = stream_from_kafka(spark, args.kafka_servers, args.kafka_topic)
        else:
            os.makedirs(args.source_dir, exist_ok=True)
            stream_df = stream_from_files(spark, args.source_dir)

        # Apply preprocessing + featurisation + prediction
        stream_df = add_features_for_streaming(stream_df)
        stream_df = assemble_features(stream_df, tfidf_model)
        stream_df = classifier.transform(stream_df)

        # Spark MLlib's `probability` column is a Vector, not an Array.
        # Extract P(class=1) via a tiny UDF so we can write it to a sink.
        from pyspark.ml.linalg import VectorUDT, DenseVector
        from pyspark.sql.types import DoubleType
        @F.udf(DoubleType())
        def _vec_to_p_human(v):
            try:
                # Vector.toArray() works for both DenseVector and SparseVector
                return float(v.toArray()[1])
            except Exception:
                return None
        stream_df = stream_df.withColumn("p_human_score", _vec_to_p_human(F.col("probability")))

        # Build a clean output schema
        output = stream_df.select(
            F.current_timestamp().alias("processed_at"),
            F.col("text").substr(1, 100).alias("text_preview"),
            F.col("true_label").alias("true_label"),
            F.col("prediction").cast("int").alias("predicted_label"),
            F.col("p_human_score").alias("p_human"),
            F.col("short_words_ratio"),
            F.col("total_physical_lines"),
            F.col("foreign_letters_count"),
        )

        # Two parallel sinks: console (for live monitoring) + parquet (for archival)
        os.makedirs(args.output_dir, exist_ok=True)
        os.makedirs(args.checkpoint_dir, exist_ok=True)

        console_query = (
            output.writeStream
                  .outputMode("append")
                  .format("console")
                  .option("truncate", "false")
                  .option("numRows", 10)
                  .trigger(processingTime=f"{args.trigger_seconds} seconds")
                  .start()
        )

        parquet_query = (
            output.writeStream
                  .outputMode("append")
                  .format("parquet")
                  .option("path", args.output_dir)
                  .option("checkpointLocation", args.checkpoint_dir)
                  .trigger(processingTime=f"{args.trigger_seconds} seconds")
                  .start()
        )

        print("\n" + "=" * 80)
        print("STREAMING PIPELINE STARTED")
        print("=" * 80)
        if args.source == "kafka":
            print(f"  Source     : Kafka  ({args.kafka_servers}, topic={args.kafka_topic})")
        else:
            print(f"  Source     : Files  ({args.source_dir})")
        print(f"  Output     : {args.output_dir}")
        print(f"  Checkpoint : {args.checkpoint_dir}")
        print(f"  Trigger    : every {args.trigger_seconds}s")
        print(f"  Run time   : {args.run_seconds}s (set 0 for indefinite)")
        print("=" * 80 + "\n")

        if args.run_seconds > 0:
            time.sleep(args.run_seconds)
            console_query.stop()
            parquet_query.stop()
            print("\n[STREAM] Stopped after timeout — checking output...")
            n_processed = spark.read.parquet(args.output_dir).count() if os.path.exists(args.output_dir) else 0
            print(f"[STREAM] Total records processed: {n_processed}")
        else:
            console_query.awaitTermination()

    finally:
        spark.stop()


# ===========================================================================
# 6. SIMPLE PRODUCER FOR FILE-BASED STREAM (testing helper)
# ===========================================================================
def produce_test_stream(args):
    """
    Standalone helper that simulates a stream by writing JSON files into
    the source directory at a fixed rate.
    """
    import json
    import random

    sample_human = [
        "تتناول هذه الدراسة موضوع تحليل البيانات الضخمة باستخدام تقنيات التعلم الآلي المتقدمة.",
        "تبحث هذه الورقة في تطوير خوارزميات لمعالجة اللغة العربية الطبيعية بكفاءة عالية.",
        "تركز الدراسة على الكشف عن النصوص المولدة آلياً باستخدام ميزات أسلوبية متنوعة.",
    ]
    sample_ai = [
        "في هذه الدراسة، نقدم نهجاً جديداً يستخدم تقنيات متقدمة في مجال التعلم الآلي.",
        "نقترح في هذا البحث طريقة جديدة لمعالجة اللغة العربية. النتائج تظهر تحسناً ملحوظاً.",
        "هذه الدراسة تستعرض الحلول الحديثة. النتائج تؤكد فعالية الأساليب المقترحة في هذا المجال.",
    ]

    os.makedirs(args.source_dir, exist_ok=True)

    print(f"[PRODUCE] Writing {args.n_messages} messages to {args.source_dir}, "
          f"one every {args.message_interval}s")
    for i in range(args.n_messages):
        is_human = random.random() < 0.5
        text = random.choice(sample_human if is_human else sample_ai)
        record = {"text": text, "true_label": 1 if is_human else 0}
        path = os.path.join(args.source_dir, f"msg_{int(time.time()*1000)}_{i}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False)
        print(f"  [{i+1}/{args.n_messages}] -> {path}  (label={record['true_label']})")
        time.sleep(args.message_interval)

    print("[PRODUCE] Done.")


# ===========================================================================
# 7. ENTRY POINT
# ===========================================================================
def main():
    parser = argparse.ArgumentParser(description="Phase 4: Streaming pipeline")

    sub = parser.add_subparsers(dest="cmd", required=True)

    # Consumer / pipeline
    p_run = sub.add_parser("run", help="Run the streaming pipeline")
    p_run.add_argument("--source", choices=["files", "kafka"], default="files")
    p_run.add_argument("--source-dir", default="data/stream/input",
                       help="Input directory for file-based stream")
    p_run.add_argument("--kafka-servers", default="localhost:9092")
    p_run.add_argument("--kafka-topic",   default="arabic_abstracts")
    p_run.add_argument("--features-dir",  default="data/features")
    p_run.add_argument("--models-dir",    default="models")
    p_run.add_argument("--output-dir",    default="data/stream/output")
    p_run.add_argument("--checkpoint-dir", default="data/stream/checkpoint")
    p_run.add_argument("--trigger-seconds", type=int, default=5)
    p_run.add_argument("--run-seconds",     type=int, default=60,
                       help="Stop the stream after this many seconds (0 = run forever)")
    p_run.add_argument("--master", default="local[*]")

    # Producer (test helper)
    p_prod = sub.add_parser("produce", help="Simulate a stream by writing files")
    p_prod.add_argument("--source-dir", default="data/stream/input")
    p_prod.add_argument("--n-messages", type=int, default=20)
    p_prod.add_argument("--message-interval", type=float, default=2.0)

    args = parser.parse_args()

    if args.cmd == "run":
        run_streaming(args)
    elif args.cmd == "produce":
        produce_test_stream(args)


if __name__ == "__main__":
    main()
