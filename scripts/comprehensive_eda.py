"""
============================================================================
COMPREHENSIVE EDA SCRIPT — Arabic AI-Text Detection Project
============================================================================
Generates 6 publication-ready figures showcasing:
  1. Data structure & schema (printSchema + types + label distribution)
  2. Type-Token Ratio (TTR) Human vs AI
  3. Word Cloud Human vs AI (side-by-side)
  4. N-Gram (Bigram) frequency Human vs AI
  5. Top Words Human vs AI
  6. Distinctive features bar chart

Run from project root:
   python3 scripts/comprehensive_eda.py

Outputs go to reports/figures/eda/
============================================================================
"""

import os
import re
import json
from collections import Counter

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

# Arabic shaping (for matplotlib display)
try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    HAS_BIDI = True
except ImportError:
    HAS_BIDI = False
    print("[WARN] arabic_reshaper/python-bidi not installed — Arabic may display reversed")

# Word cloud
try:
    from wordcloud import WordCloud
    HAS_WC = True
except ImportError:
    HAS_WC = False
    print("[WARN] wordcloud not installed — skipping word cloud")

# PySpark
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import IntegerType, StringType

# ============================================================================
# CONFIGURATION
# ============================================================================
PROCESSED_DIR  = "data/processed"
FIGURES_DIR    = "reports/figures/eda"
ARABIC_FONT    = "/usr/share/fonts/google-droid-sans-fonts/DroidKufi-Regular.ttf"

# Fallback fonts
FONT_CANDIDATES = [
    "/usr/share/fonts/google-droid-sans-fonts/DroidKufi-Regular.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/TTF/DejaVuSans.ttf",
]

# Visual style
HUMAN_COLOR = "#2AA1C2"  # Teal
AI_COLOR    = "#F2C44F"  # Amber
NAVY        = "#0A2E5C"

# ============================================================================
# HELPERS
# ============================================================================
def shape_ar(text):
    """Reshape Arabic for matplotlib's left-to-right rendering."""
    if not HAS_BIDI or not text:
        return text
    try:
        reshaped = arabic_reshaper.reshape(text)
        return get_display(reshaped)
    except Exception:
        return text

def find_arabic_font():
    for p in FONT_CANDIDATES:
        if os.path.exists(p):
            return p
    return None

def setup_matplotlib():
    plt.rcParams['font.family'] = 'DejaVu Sans'
    plt.rcParams['axes.spines.top'] = False
    plt.rcParams['axes.spines.right'] = False
    sns.set_style("whitegrid", {'axes.grid': False})

def save_fig(fig, name, dpi=150):
    out_path = os.path.join(FIGURES_DIR, name)
    fig.savefig(out_path, dpi=dpi, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f"  ✓ Saved: {out_path}")

# ============================================================================
# SPARK SESSION
# ============================================================================
def create_spark():
    spark = (
        SparkSession.builder
            .appName("ComprehensiveEDA")
            .master("local[*]")
            .config("spark.driver.memory", "3g")
            .config("spark.sql.shuffle.partitions", "8")
            .getOrCreate()
    )
    spark.sparkContext.setLogLevel("ERROR")
    return spark

# ============================================================================
# FIGURE 1: DATA STRUCTURE, SCHEMA, AND LABEL DISTRIBUTION
# ============================================================================
def figure_1_data_structure(spark, df):
    """
    Multi-panel figure showing:
      (a) Schema table (column names + types)
      (b) Label distribution pie chart (Human vs AI)
      (c) Subset distribution bar chart
    """
    print("\n[FIG 1] Building data structure overview...")

    # Print schema for the report
    print("\n[SCHEMA]")
    df.printSchema()

    # Get label counts
    label_counts = df.groupBy("category_encode").count().collect()
    label_dict = {row['category_encode']: row['count'] for row in label_counts}
    human_count = label_dict.get(1, 0)
    ai_count    = label_dict.get(0, 0)

    # Get subset distribution
    subset_counts = df.groupBy("subset").count().orderBy("subset").collect()
    subsets = [row['subset'] for row in subset_counts]
    subset_vals = [row['count'] for row in subset_counts]

    # Build the figure
    fig = plt.figure(figsize=(16, 10))
    gs = fig.add_gridspec(2, 2, hspace=0.35, wspace=0.30)

    # ---- Panel (a): Schema table ----
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.axis('off')

    schema_data = [[field.name, str(field.dataType).replace("Type()", "")]
                   for field in df.schema.fields]
    table = ax1.table(
        cellText=schema_data,
        colLabels=['Column', 'Type'],
        cellLoc='left', loc='upper left',
        colWidths=[0.55, 0.45]
    )
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1, 1.8)
    for i in range(len(schema_data[0])):
        table[(0, i)].set_facecolor(NAVY)
        table[(0, i)].set_text_props(color='white', weight='bold')
    ax1.set_title("(a) Spark DataFrame Schema (df.printSchema)",
                  fontsize=13, fontweight='bold', pad=10)

    # ---- Panel (b): Label distribution pie ----
    ax2 = fig.add_subplot(gs[0, 1])
    sizes  = [human_count, ai_count]
    labels = [f'Human\n({human_count:,})', f'AI-Generated\n({ai_count:,})']
    colors = [HUMAN_COLOR, AI_COLOR]
    explode = (0.05, 0)
    wedges, texts, autotexts = ax2.pie(
        sizes, labels=labels, colors=colors, autopct='%1.1f%%',
        explode=explode, startangle=90, textprops={'fontsize': 12, 'fontweight': 'bold'}
    )
    for at in autotexts:
        at.set_color('white')
        at.set_fontsize(13)
        at.set_fontweight('bold')
    ax2.set_title("(b) Label Distribution (Human vs AI)",
                  fontsize=13, fontweight='bold', pad=10)

    # ---- Panel (c): Subset distribution ----
    ax3 = fig.add_subplot(gs[1, :])
    bars = ax3.bar(subsets, subset_vals,
                   color=['#146C94', '#2AA1C2', '#9FE1CB'], edgecolor=NAVY, linewidth=1.5)
    for bar, val in zip(bars, subset_vals):
        ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 100,
                 f'{val:,}', ha='center', va='bottom', fontsize=12, fontweight='bold')
    ax3.set_ylabel('Number of Samples', fontsize=12, fontweight='bold')
    ax3.set_title("(c) Per-Subset Sample Distribution", fontsize=13, fontweight='bold', pad=10)
    ax3.set_ylim(0, max(subset_vals) * 1.15)
    ax3.tick_params(axis='x', labelrotation=0, labelsize=11)

    fig.suptitle('Data Structure, Types, and Label Exploration',
                 fontsize=16, fontweight='bold', y=0.98)
    save_fig(fig, "01_data_structure.png")

    return {'human': human_count, 'ai': ai_count}

# ============================================================================
# FIGURE 2: TYPE-TOKEN RATIO (TTR) HUMAN VS AI
# ============================================================================
def figure_2_ttr_comparison(spark, df):
    """
    Computes per-document and corpus-level TTR for Human vs AI.
    """
    print("\n[FIG 2] Computing TTR for Human vs AI...")

    # UDFs for TTR computation
    def ttr_per_doc(text):
        if not text:
            return 0.0
        tokens = text.split()
        if len(tokens) == 0:
            return 0.0
        return len(set(tokens)) / len(tokens)

    def count_unique(text):
        return len(set(text.split())) if text else 0

    def count_total(text):
        return len(text.split()) if text else 0

    from pyspark.sql.types import FloatType
    ttr_udf    = F.udf(ttr_per_doc, FloatType())
    unique_udf = F.udf(count_unique, IntegerType())
    total_udf  = F.udf(count_total,  IntegerType())

    df_ttr = (df
        .withColumn("ttr",      ttr_udf("processed_text"))
        .withColumn("unique",   unique_udf("processed_text"))
        .withColumn("total",    total_udf("processed_text"))
    )

    # Aggregate per class
    stats = (df_ttr
        .groupBy("category_encode")
        .agg(
            F.avg("ttr").alias("avg_ttr"),
            F.sum("unique").alias("total_unique"),
            F.sum("total").alias("total_tokens"),
            F.count("*").alias("n_docs"),
        )
        .collect()
    )

    stat_dict = {row['category_encode']: row for row in stats}
    human_stats = stat_dict.get(1)
    ai_stats    = stat_dict.get(0)

    # Compute corpus-level TTR
    h_corpus_ttr = (human_stats['total_unique'] / human_stats['total_tokens']
                    if human_stats['total_tokens'] else 0)
    a_corpus_ttr = (ai_stats['total_unique'] / ai_stats['total_tokens']
                    if ai_stats['total_tokens'] else 0)

    # Collect per-doc TTR for distribution plot
    ttr_data = (df_ttr
        .select("category_encode", "ttr")
        .toPandas()
    )

    # ---- Build figure ----
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))

    # Panel (a): Bar chart — corpus-level TTR
    categories = ['Human', 'AI-Generated']
    avg_ttrs   = [human_stats['avg_ttr'], ai_stats['avg_ttr']]
    corp_ttrs  = [h_corpus_ttr, a_corpus_ttr]

    x = np.arange(len(categories))
    width = 0.35
    axes[0].bar(x - width/2, avg_ttrs, width, label='Per-doc Avg TTR',
                color=[HUMAN_COLOR, AI_COLOR], edgecolor=NAVY, alpha=0.85)
    axes[0].bar(x + width/2, corp_ttrs, width, label='Corpus-level TTR',
                color=[HUMAN_COLOR, AI_COLOR], edgecolor=NAVY, hatch='///', alpha=0.6)

    for i, (avg, corp) in enumerate(zip(avg_ttrs, corp_ttrs)):
        axes[0].text(i - width/2, avg + 0.005, f'{avg:.4f}', ha='center', fontsize=10, fontweight='bold')
        axes[0].text(i + width/2, corp + 0.005, f'{corp:.4f}', ha='center', fontsize=10, fontweight='bold')

    axes[0].set_xticks(x)
    axes[0].set_xticklabels(categories, fontsize=12)
    axes[0].set_ylabel('Type-Token Ratio', fontsize=12, fontweight='bold')
    axes[0].set_title('(a) TTR Comparison: Per-Doc Avg vs Corpus-Level',
                      fontsize=13, fontweight='bold', pad=10)
    axes[0].legend(loc='upper right', fontsize=11)
    axes[0].set_ylim(0, max(max(avg_ttrs), max(corp_ttrs)) * 1.25)

    # Panel (b): Distribution of per-doc TTR
    human_ttrs = ttr_data[ttr_data['category_encode'] == 1]['ttr'].values
    ai_ttrs    = ttr_data[ttr_data['category_encode'] == 0]['ttr'].values

    axes[1].hist(human_ttrs, bins=40, color=HUMAN_COLOR, alpha=0.7,
                 label=f'Human (n={len(human_ttrs):,})', edgecolor='white')
    axes[1].hist(ai_ttrs, bins=40, color=AI_COLOR, alpha=0.7,
                 label=f'AI (n={len(ai_ttrs):,})', edgecolor='white')
    axes[1].axvline(np.mean(human_ttrs), color=HUMAN_COLOR, linestyle='--', linewidth=2)
    axes[1].axvline(np.mean(ai_ttrs),    color=AI_COLOR,    linestyle='--', linewidth=2)
    axes[1].set_xlabel('Per-Document TTR', fontsize=12, fontweight='bold')
    axes[1].set_ylabel('Frequency', fontsize=12, fontweight='bold')
    axes[1].set_title('(b) Per-Document TTR Distribution',
                      fontsize=13, fontweight='bold', pad=10)
    axes[1].legend(loc='upper left', fontsize=11)

    fig.suptitle('Type-Token Ratio (TTR): Human vs AI',
                 fontsize=15, fontweight='bold', y=1.02)
    plt.tight_layout()
    save_fig(fig, "02_ttr_human_vs_ai.png")

    print(f"  Human TTR (avg): {human_stats['avg_ttr']:.4f}  |  corpus: {h_corpus_ttr:.4f}")
    print(f"  AI    TTR (avg): {ai_stats['avg_ttr']:.4f}  |  corpus: {a_corpus_ttr:.4f}")

    return {
        'human_avg_ttr':   human_stats['avg_ttr'],
        'ai_avg_ttr':      ai_stats['avg_ttr'],
        'human_corp_ttr':  h_corpus_ttr,
        'ai_corp_ttr':     a_corpus_ttr,
    }

# ============================================================================
# FIGURE 3: WORD CLOUDS — HUMAN VS AI
# ============================================================================
def figure_3_wordclouds(spark, df):
    """Side-by-side word clouds for Human and AI."""
    if not HAS_WC:
        print("[FIG 3] Skipped — wordcloud not installed")
        return

    print("\n[FIG 3] Building word clouds for Human vs AI...")

    font_path = find_arabic_font()
    if not font_path:
        print("[WARN] No Arabic font found — wordcloud will look strange")

    # Aggregate tokens per class (driver-side counting)
    print("  - Collecting Human tokens...")
    human_texts = (df.filter(F.col("category_encode") == 1)
                     .select("processed_text").rdd
                     .flatMap(lambda r: (r[0] or "").split()).collect())
    print(f"    Human tokens collected: {len(human_texts):,}")

    print("  - Collecting AI tokens...")
    ai_texts = (df.filter(F.col("category_encode") == 0)
                     .select("processed_text").rdd
                     .flatMap(lambda r: (r[0] or "").split()).collect())
    print(f"    AI tokens collected: {len(ai_texts):,}")

    human_counter = Counter(t for t in human_texts if len(t) > 1)
    ai_counter    = Counter(t for t in ai_texts    if len(t) > 1)

    # Reshape Arabic
    human_freq = {shape_ar(w): c for w, c in human_counter.most_common(200)}
    ai_freq    = {shape_ar(w): c for w, c in ai_counter.most_common(200)}

    # Build word clouds
    wc_human = WordCloud(
        width=900, height=500, background_color='white',
        max_words=100, font_path=font_path,
        colormap='Blues', collocations=False, prefer_horizontal=0.9,
    ).generate_from_frequencies(human_freq)

    wc_ai = WordCloud(
        width=900, height=500, background_color='white',
        max_words=100, font_path=font_path,
        colormap='YlOrBr', collocations=False, prefer_horizontal=0.9,
    ).generate_from_frequencies(ai_freq)

    # Plot
    fig, axes = plt.subplots(1, 2, figsize=(18, 7))
    axes[0].imshow(wc_human, interpolation='bilinear')
    axes[0].axis('off')
    axes[0].set_title(f'Human-Written Abstracts (n={human_stats_count(human_counter)} unique stems)',
                      fontsize=14, fontweight='bold', color=HUMAN_COLOR, pad=15)

    axes[1].imshow(wc_ai, interpolation='bilinear')
    axes[1].axis('off')
    axes[1].set_title(f'AI-Generated Abstracts (n={human_stats_count(ai_counter)} unique stems)',
                      fontsize=14, fontweight='bold', color='#B57A0E', pad=15)

    fig.suptitle('Word Cloud Comparison: Most Frequent Arabic Stems',
                 fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    save_fig(fig, "03_wordcloud_human_vs_ai.png")

    return human_counter, ai_counter

def human_stats_count(counter):
    return f"{len(counter):,}"

# ============================================================================
# FIGURE 4: TOP-20 WORDS HUMAN VS AI
# ============================================================================
def figure_4_top_words(human_counter, ai_counter, top_n=20):
    """Side-by-side bar charts of top-N words for Human vs AI."""
    print(f"\n[FIG 4] Plotting top-{top_n} words for Human vs AI...")

    human_top = human_counter.most_common(top_n)
    ai_top    = ai_counter.most_common(top_n)

    h_words  = [shape_ar(w) for w, _ in human_top][::-1]
    h_counts = [c for _, c in human_top][::-1]
    a_words  = [shape_ar(w) for w, _ in ai_top][::-1]
    a_counts = [c for _, c in ai_top][::-1]

    fig, axes = plt.subplots(1, 2, figsize=(18, 9))

    # Human
    bars_h = axes[0].barh(h_words, h_counts, color=HUMAN_COLOR, edgecolor=NAVY, alpha=0.85)
    for bar, val in zip(bars_h, h_counts):
        axes[0].text(val + max(h_counts)*0.01, bar.get_y() + bar.get_height()/2,
                     f'{val:,}', va='center', fontsize=10, fontweight='bold')
    axes[0].set_xlabel('Frequency', fontsize=12, fontweight='bold')
    axes[0].set_title(f'Top-{top_n} Words — Human', fontsize=14, fontweight='bold',
                      color=HUMAN_COLOR, pad=10)
    axes[0].tick_params(axis='y', labelsize=12)

    # AI
    bars_a = axes[1].barh(a_words, a_counts, color=AI_COLOR, edgecolor=NAVY, alpha=0.85)
    for bar, val in zip(bars_a, a_counts):
        axes[1].text(val + max(a_counts)*0.01, bar.get_y() + bar.get_height()/2,
                     f'{val:,}', va='center', fontsize=10, fontweight='bold')
    axes[1].set_xlabel('Frequency', fontsize=12, fontweight='bold')
    axes[1].set_title(f'Top-{top_n} Words — AI', fontsize=14, fontweight='bold',
                      color='#B57A0E', pad=10)
    axes[1].tick_params(axis='y', labelsize=12)

    fig.suptitle('Top-20 Most Frequent Arabic Stems: Human vs AI',
                 fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    save_fig(fig, "04_top_words_human_vs_ai.png")

# ============================================================================
# FIGURE 5: TOP-20 BIGRAMS HUMAN VS AI
# ============================================================================
def figure_5_top_bigrams(spark, df, top_n=20):
    """Side-by-side bar charts of top-N bigrams for Human vs AI."""
    print(f"\n[FIG 5] Computing top-{top_n} bigrams for Human vs AI...")

    def extract_bigrams(text):
        if not text:
            return []
        tokens = text.split()
        return [f"{tokens[i]} {tokens[i+1]}" for i in range(len(tokens)-1)
                if len(tokens[i]) > 1 and len(tokens[i+1]) > 1]

    print("  - Collecting Human bigrams...")
    human_bigrams = (df.filter(F.col("category_encode") == 1)
                       .select("processed_text").rdd
                       .flatMap(lambda r: extract_bigrams(r[0])).collect())
    print(f"    Human bigrams: {len(human_bigrams):,}")

    print("  - Collecting AI bigrams...")
    ai_bigrams = (df.filter(F.col("category_encode") == 0)
                       .select("processed_text").rdd
                       .flatMap(lambda r: extract_bigrams(r[0])).collect())
    print(f"    AI bigrams: {len(ai_bigrams):,}")

    human_bg_counter = Counter(human_bigrams)
    ai_bg_counter    = Counter(ai_bigrams)

    human_top = human_bg_counter.most_common(top_n)
    ai_top    = ai_bg_counter.most_common(top_n)

    h_bigs   = [shape_ar(bg) for bg, _ in human_top][::-1]
    h_counts = [c for _, c in human_top][::-1]
    a_bigs   = [shape_ar(bg) for bg, _ in ai_top][::-1]
    a_counts = [c for _, c in ai_top][::-1]

    fig, axes = plt.subplots(1, 2, figsize=(20, 10))

    # Human
    bars_h = axes[0].barh(h_bigs, h_counts, color=HUMAN_COLOR, edgecolor=NAVY, alpha=0.85)
    for bar, val in zip(bars_h, h_counts):
        axes[0].text(val + max(h_counts)*0.01, bar.get_y() + bar.get_height()/2,
                     f'{val:,}', va='center', fontsize=9, fontweight='bold')
    axes[0].set_xlabel('Frequency', fontsize=12, fontweight='bold')
    axes[0].set_title(f'Top-{top_n} Bigrams — Human', fontsize=14, fontweight='bold',
                      color=HUMAN_COLOR, pad=10)
    axes[0].tick_params(axis='y', labelsize=11)

    # AI
    bars_a = axes[1].barh(a_bigs, a_counts, color=AI_COLOR, edgecolor=NAVY, alpha=0.85)
    for bar, val in zip(bars_a, a_counts):
        axes[1].text(val + max(a_counts)*0.01, bar.get_y() + bar.get_height()/2,
                     f'{val:,}', va='center', fontsize=9, fontweight='bold')
    axes[1].set_xlabel('Frequency', fontsize=12, fontweight='bold')
    axes[1].set_title(f'Top-{top_n} Bigrams — AI', fontsize=14, fontweight='bold',
                      color='#B57A0E', pad=10)
    axes[1].tick_params(axis='y', labelsize=11)

    fig.suptitle('Top-20 Most Frequent Bigrams (N-Grams, n=2): Human vs AI',
                 fontsize=16, fontweight='bold', y=1.01)
    plt.tight_layout()
    save_fig(fig, "05_bigrams_human_vs_ai.png")

    return human_bg_counter, ai_bg_counter

# ============================================================================
# FIGURE 6: DISTINCTIVE BIGRAMS (AI-FINGERPRINTS)
# ============================================================================
def figure_6_distinctive_bigrams(human_bg, ai_bg, n_human, n_ai, top_n=15):
    """Bigrams with the highest AI/Human frequency ratio (AI fingerprints)."""
    print(f"\n[FIG 6] Computing distinctive bigrams (AI fingerprints)...")

    # Per-document normalization to compare fairly
    distinctive = []
    for bigram, ai_count in ai_bg.most_common(500):
        h_count = human_bg.get(bigram, 0)
        # Smooth to avoid division-by-zero
        ai_norm = ai_count / n_ai
        h_norm  = (h_count + 1) / (n_human + 1)
        ratio   = ai_norm / h_norm if h_norm > 0 else float('inf')
        if ai_count >= 100:
            distinctive.append((bigram, h_count, ai_count, ratio))

    distinctive.sort(key=lambda x: x[3], reverse=True)
    top = distinctive[:top_n]

    bigs    = [shape_ar(d[0]) for d in top][::-1]
    h_cnts  = [d[1] for d in top][::-1]
    a_cnts  = [d[2] for d in top][::-1]
    ratios  = [d[3] for d in top][::-1]

    fig, ax = plt.subplots(figsize=(14, 9))
    y_pos = np.arange(len(bigs))
    width = 0.4

    bars_h = ax.barh(y_pos - width/2, h_cnts, width,
                     label='Human', color=HUMAN_COLOR, edgecolor=NAVY, alpha=0.85)
    bars_a = ax.barh(y_pos + width/2, a_cnts, width,
                     label='AI',    color=AI_COLOR,    edgecolor=NAVY, alpha=0.85)

    for bar, val, ratio in zip(bars_a, a_cnts, ratios):
        ax.text(val + max(a_cnts)*0.01, bar.get_y() + bar.get_height()/2,
                f'{val:,}  ({ratio:.1f}×)', va='center', fontsize=10, fontweight='bold')

    ax.set_yticks(y_pos)
    ax.set_yticklabels(bigs, fontsize=11)
    ax.set_xlabel('Frequency (with AI/Human Ratio)', fontsize=12, fontweight='bold')
    ax.set_title(f'Top-{top_n} AI-Distinctive Bigrams (Highest AI/Human Ratio)',
                 fontsize=14, fontweight='bold', pad=15)
    ax.legend(loc='lower right', fontsize=12)

    fig.suptitle('AI Fingerprints: Bigrams Disproportionately Used by AI',
                 fontsize=16, fontweight='bold', y=1.00)
    plt.tight_layout()
    save_fig(fig, "06_distinctive_bigrams.png")

# ============================================================================
# MAIN
# ============================================================================
def main():
    os.makedirs(FIGURES_DIR, exist_ok=True)
    setup_matplotlib()

    print("=" * 78)
    print("COMPREHENSIVE EDA — Arabic AI-Text Detection")
    print("=" * 78)

    spark = create_spark()

    try:
        # Load processed data
        df = spark.read.parquet(PROCESSED_DIR)
        total = df.count()
        print(f"\n[LOAD] Loaded {total:,} processed rows from {PROCESSED_DIR}")

        # Figure 1: Schema + label + subset
        counts = figure_1_data_structure(spark, df)

        # Figure 2: TTR
        ttr_results = figure_2_ttr_comparison(spark, df)

        # Figure 3: Word clouds (and capture word counters)
        human_counter, ai_counter = figure_3_wordclouds(spark, df)

        # Figure 4: Top words
        figure_4_top_words(human_counter, ai_counter, top_n=20)

        # Figure 5: Top bigrams
        human_bg, ai_bg = figure_5_top_bigrams(spark, df, top_n=20)

        # Figure 6: Distinctive bigrams
        figure_6_distinctive_bigrams(human_bg, ai_bg,
                                     n_human=counts['human'], n_ai=counts['ai'],
                                     top_n=15)

        # Save results metadata
        results = {
            'total_samples': total,
            'human_count':   counts['human'],
            'ai_count':      counts['ai'],
            'ttr':           ttr_results,
        }
        with open(os.path.join(FIGURES_DIR, 'eda_summary.json'), 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)

        print("\n" + "=" * 78)
        print(f"✅ ALL FIGURES SAVED TO: {FIGURES_DIR}/")
        print("=" * 78)
        for fname in sorted(os.listdir(FIGURES_DIR)):
            print(f"   - {fname}")

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
