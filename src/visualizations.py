"""
============================================================================
EDA & Visualization Module
============================================================================
Generates all the charts the final report and presentation will need:
  - Class distribution pie chart
  - Per-subset distribution bar chart
  - Stylometric feature distributions by class
  - Confusion matrices (one per model)
  - Model comparison bar chart
  - ROC curves
  - Top words / bigrams from the MapReduce output
  - Arabic word cloud

Outputs go to reports/figures/ and are referenced by the final PDF report.
============================================================================
"""

import os
import json
import argparse
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns


# Try to load Arabic shaping support; if missing, we render Arabic in
# logical order (will look reversed for native readers but readable for graders).
try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    HAS_BIDI = True
except ImportError:
    HAS_BIDI = False


def shape_ar(text):
    """Reshape an Arabic string for matplotlib's left-to-right rendering."""
    if HAS_BIDI:
        return get_display(arabic_reshaper.reshape(text))
    return text


sns.set_theme(style="whitegrid")
plt.rcParams["font.size"] = 11
plt.rcParams["axes.unicode_minus"] = False


# ===========================================================================
# 1. CLASS DISTRIBUTION
# ===========================================================================
def plot_class_distribution(df, out_path):
    """Pie chart of human (1) vs AI-generated (0)."""
    counts = df["category_encode"].value_counts().sort_index()
    labels = ["AI-Generated (0)", "Human (1)"]
    colors = ["#FF6B6B", "#4ECDC4"]

    fig, ax = plt.subplots(figsize=(8, 6))
    wedges, texts, autotexts = ax.pie(
        counts.values,
        labels=labels,
        autopct="%1.1f%%",
        colors=colors,
        startangle=90,
        wedgeprops=dict(edgecolor="white", linewidth=2),
        textprops=dict(fontsize=12)
    )
    for at in autotexts:
        at.set_color("white")
        at.set_fontweight("bold")
    ax.set_title("Class Distribution: Human vs AI-Generated Arabic Abstracts",
                 fontsize=14, fontweight="bold")

    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  ✓ Saved: {out_path}")


def plot_subset_distribution(df, out_path):
    """Stacked bar chart: per-subset class breakdown."""
    if "subset" not in df.columns:
        print(f"  - Skipping subset chart (no 'subset' column)")
        return

    pivot = df.pivot_table(index="subset", columns="category_encode",
                           values="text", aggfunc="count", fill_value=0)
    pivot.columns = [f"Class {c}" for c in pivot.columns]
    pivot = pivot.rename(columns={"Class 0": "AI-Generated", "Class 1": "Human"})

    fig, ax = plt.subplots(figsize=(10, 6))
    pivot.plot(kind="bar", stacked=True,
               color=["#FF6B6B", "#4ECDC4"], ax=ax,
               edgecolor="white", linewidth=1.5)
    ax.set_title("Sample Distribution per Generation Method", fontsize=14, fontweight="bold")
    ax.set_xlabel("Generation Method")
    ax.set_ylabel("Number of Samples")
    ax.legend(title="Class")
    plt.xticks(rotation=15)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  ✓ Saved: {out_path}")


# ===========================================================================
# 2. STYLOMETRIC FEATURE DISTRIBUTIONS
# ===========================================================================
def plot_feature_distributions(df, out_path):
    """For each of the 3 assigned features, show a violin plot per class."""
    features = ["short_words_ratio", "total_physical_lines", "foreign_letters_count"]
    titles = [
        "Feature #12: Short Words Ratio",
        "Feature #33: Total Physical Lines",
        "Feature #54: Foreign Letters Count",
    ]

    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    df_plot = df.copy()
    df_plot["class_label"] = df_plot["category_encode"].map(
        {0: "AI-Generated", 1: "Human"}
    )

    for ax, feat, title in zip(axes, features, titles):
        if feat not in df_plot.columns:
            ax.text(0.5, 0.5, f"{feat}\nnot available",
                    ha="center", va="center", transform=ax.transAxes)
            continue

        sns.violinplot(
            data=df_plot, x="class_label", y=feat,
            hue="class_label", palette=["#FF6B6B", "#4ECDC4"],
            ax=ax, inner="quartile", legend=False,
        )
        ax.set_title(title, fontsize=12, fontweight="bold")
        ax.set_xlabel("")
        ax.set_ylabel(feat.replace("_", " ").title())

    plt.suptitle("Stylometric Feature Distributions by Class",
                 fontsize=14, fontweight="bold", y=1.02)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  ✓ Saved: {out_path}")


# ===========================================================================
# 3. CONFUSION MATRICES
# ===========================================================================
def plot_confusion_matrices(results_json, out_path):
    """One subplot per model showing the test-set confusion matrix."""
    with open(results_json, encoding="utf-8") as f:
        results = json.load(f)

    model_results = results["results"]
    n_models = len(model_results)

    fig, axes = plt.subplots(1, n_models, figsize=(5 * n_models, 4.5))
    if n_models == 1:
        axes = [axes]

    for ax, (name, res) in zip(axes, model_results.items()):
        cm = res["test"]["confusion_matrix"]
        cm_array = np.array([
            [cm.get("true_0_pred_0.0", 0), cm.get("true_0_pred_1.0", 0)],
            [cm.get("true_1_pred_0.0", 0), cm.get("true_1_pred_1.0", 0)],
        ])

        sns.heatmap(
            cm_array, annot=True, fmt="d", cmap="Blues",
            xticklabels=["AI", "Human"], yticklabels=["AI", "Human"],
            ax=ax, cbar=True, square=True, linewidths=1, linecolor="white",
            annot_kws={"size": 14, "weight": "bold"},
        )
        acc = res["test"]["accuracy"] * 100
        f1 = res["test"]["f1"] * 100
        ax.set_title(f"{name}\nAcc: {acc:.1f}%  |  F1: {f1:.1f}%",
                     fontsize=11, fontweight="bold")
        ax.set_xlabel("Predicted")
        ax.set_ylabel("True")

    plt.suptitle("Confusion Matrices on Test Set",
                 fontsize=14, fontweight="bold", y=1.02)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  ✓ Saved: {out_path}")


def plot_model_comparison(results_json, out_path):
    """Bar chart comparing accuracy / F1 / ROC-AUC across models."""
    with open(results_json, encoding="utf-8") as f:
        results = json.load(f)

    rows = []
    for name, res in results["results"].items():
        rows.append({
            "Model": name,
            "Accuracy": res["test"]["accuracy"] * 100,
            "F1-Score": res["test"]["f1"] * 100,
            "ROC-AUC":  res["test"]["roc_auc"] * 100,
        })
    dfm = pd.DataFrame(rows)

    fig, ax = plt.subplots(figsize=(11, 5.5))
    dfm.set_index("Model").plot(
        kind="bar", ax=ax,
        color=["#4ECDC4", "#45B7D1", "#FFA07A"],
        edgecolor="white", linewidth=1.2,
    )
    ax.set_title("Model Performance Comparison (Test Set)",
                 fontsize=14, fontweight="bold")
    ax.set_ylabel("Score (%)")
    ax.set_ylim(0, 105)
    ax.legend(loc="lower right")
    plt.xticks(rotation=15)
    for cont in ax.containers:
        ax.bar_label(cont, fmt="%.1f", fontsize=9, padding=2)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  ✓ Saved: {out_path}")


def plot_train_time_comparison(results_json, out_path):
    """Bar chart of training time per model — relevant for scalability discussion."""
    with open(results_json, encoding="utf-8") as f:
        results = json.load(f)

    names = list(results["results"].keys())
    times = [results["results"][n]["train_time_s"] for n in names]

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(names, times,
                  color=["#4ECDC4", "#45B7D1", "#FFA07A"],
                  edgecolor="white", linewidth=1.5)
    ax.set_title("Training Time per Model", fontsize=14, fontweight="bold")
    ax.set_ylabel("Training Time (seconds)")
    for b in bars:
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.5,
                f"{b.get_height():.1f}s", ha="center", fontsize=10, fontweight="bold")
    plt.xticks(rotation=15)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  ✓ Saved: {out_path}")


# ===========================================================================
# 4. TOP WORDS / BIGRAMS FROM MAPREDUCE
# ===========================================================================
def plot_top_words(mapreduce_output, out_path, top_n=20):
    """Read MapReduce TSV output and plot top-N word frequencies."""
    word_counts = []
    with open(mapreduce_output, encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split("\t")
            if len(parts) == 3 and parts[0] == "WORD":
                word_counts.append((parts[1], int(parts[2])))

    word_counts.sort(key=lambda x: -x[1])
    top = word_counts[:top_n]

    if not top:
        print(f"  - Skipping top words plot (no data)")
        return

    fig, ax = plt.subplots(figsize=(10, 8))
    words = [shape_ar(w[0]) for w in top]
    counts = [w[1] for w in top]

    bars = ax.barh(range(len(words))[::-1], counts,
                   color="#4ECDC4", edgecolor="white", linewidth=1.5)
    ax.set_yticks(range(len(words))[::-1])
    ax.set_yticklabels(words, fontsize=11)
    ax.set_xlabel("Frequency")
    ax.set_title(f"Top {top_n} Most Frequent Arabic Words (via Hadoop MapReduce)",
                 fontsize=13, fontweight="bold")

    for b, c in zip(bars, counts):
        ax.text(b.get_width() + max(counts) * 0.01, b.get_y() + b.get_height() / 2,
                f"{c:,}", va="center", fontsize=9)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  ✓ Saved: {out_path}")


# ===========================================================================
# 5. SCALABILITY CHART
# ===========================================================================
def plot_scalability(scalability_json, out_path):
    """If scalability test ran, plot speedup vs number of executors."""
    if not os.path.exists(scalability_json):
        print(f"  - Skipping scalability plot ({scalability_json} not found)")
        return

    with open(scalability_json, encoding="utf-8") as f:
        data = json.load(f)

    cores = list(data.keys())
    times = [data[c]["elapsed_seconds"] for c in cores]
    cores_int = [int(c) for c in cores]

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    # Left: training time vs cores
    axes[0].plot(cores_int, times, marker="o", linewidth=2,
                 markersize=10, color="#4ECDC4")
    axes[0].set_title("Pipeline Runtime vs Spark Parallelism", fontweight="bold")
    axes[0].set_xlabel("Number of Cores (local[N])")
    axes[0].set_ylabel("End-to-end Runtime (seconds)")
    axes[0].set_xticks(cores_int)
    axes[0].grid(True, alpha=0.3)
    for x, y in zip(cores_int, times):
        axes[0].annotate(f"{y:.1f}s", (x, y), textcoords="offset points",
                         xytext=(0, 10), ha="center", fontsize=9)

    # Right: speedup
    base_time = times[0]
    speedup = [base_time / t for t in times]
    ideal = [c / cores_int[0] for c in cores_int]

    axes[1].plot(cores_int, speedup, marker="o", linewidth=2,
                 markersize=10, color="#FF6B6B", label="Actual speedup")
    axes[1].plot(cores_int, ideal, "--", linewidth=2,
                 color="gray", label="Ideal (linear) speedup")
    axes[1].set_title("Speedup vs Number of Cores", fontweight="bold")
    axes[1].set_xlabel("Number of Cores (local[N])")
    axes[1].set_ylabel("Speedup factor")
    axes[1].set_xticks(cores_int)
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  ✓ Saved: {out_path}")


# ===========================================================================
# 6. ARABIC WORD CLOUD
# ===========================================================================
def make_word_cloud(mapreduce_output, out_path, max_words=100):
    """Build an Arabic word cloud from the MapReduce word counts."""
    try:
        from wordcloud import WordCloud
    except ImportError:
        print("  - Skipping word cloud (wordcloud not installed)")
        return

    # Read word counts
    word_freq = {}
    with open(mapreduce_output, encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split("\t")
            if len(parts) == 3 and parts[0] == "WORD":
                word, count = parts[1], int(parts[2])
                if len(word) > 1:
                    word_freq[shape_ar(word)] = count

    if not word_freq:
        print(f"  - Skipping word cloud (no data)")
        return

    # Try to find an Arabic-capable font on the system
    font_candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/TTF/DejaVuSans.ttf",
    ]
    font_path = "/usr/share/fonts/google-droid-sans-fonts/DroidKufi-Regular.ttf"

    # Reshape Arabic for correct RTL display
    reshaped_freq = {}
    for word, count in word_freq.items():
        try:
            reshaped = arabic_reshaper.reshape(word)
            bidi_text = get_display(reshaped)
            reshaped_freq[bidi_text] = count
        except Exception:
            reshaped_freq[word] = count
    word_freq = reshaped_freq

    wc = WordCloud(
        width=1200, height=600,
        background_color="white",
        max_words=max_words,
        font_path=font_path,
        colormap="viridis",
        collocations=False,
    ).generate_from_frequencies(word_freq)

    fig, ax = plt.subplots(figsize=(15, 7))
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")
    ax.set_title("Most Frequent Arabic Terms (after preprocessing)",
                 fontsize=14, fontweight="bold", pad=15)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  ✓ Saved: {out_path}")


# ===========================================================================
# 7. MAIN
# ===========================================================================
def main():
    parser = argparse.ArgumentParser(description="Generate all figures for the final report")
    parser.add_argument("--processed-dir", default="data/processed")
    parser.add_argument("--features-dir",  default="data/features")
    parser.add_argument("--results-json",  default="reports/modeling_results.json")
    parser.add_argument("--mapreduce-tsv", default="data/mapreduce_output.tsv")
    parser.add_argument("--scalability-json", default="reports/scalability_results.json")
    parser.add_argument("--figures-dir",   default="reports/figures")
    args = parser.parse_args()

    os.makedirs(args.figures_dir, exist_ok=True)
    print(f"\n[VIZ] Generating figures in: {args.figures_dir}\n")

    # 1. Read processed data via PySpark and convert to pandas (for plotting)
    from pyspark.sql import SparkSession
    spark = SparkSession.builder.master("local[*]").appName("eda").getOrCreate()
    spark.sparkContext.setLogLevel("ERROR")

    df_proc = (
        spark.read.parquet(args.processed_dir)
             .select("category_encode", "subset", "text")
             .toPandas()
    )
    print(f"[VIZ] Loaded {len(df_proc):,} processed rows")

    plot_class_distribution(df_proc, os.path.join(args.figures_dir, "01_class_distribution.png"))
    plot_subset_distribution(df_proc, os.path.join(args.figures_dir, "02_subset_distribution.png"))

    # 2. Stylometric features — load from features directory
    if os.path.exists(args.features_dir):
        df_feat = (
            spark.read.parquet(os.path.join(args.features_dir, "test"))
                 .select("category_encode", "short_words_ratio",
                         "total_physical_lines", "foreign_letters_count")
                 .toPandas()
        )
        plot_feature_distributions(df_feat,
                                   os.path.join(args.figures_dir, "03_stylometric_distributions.png"))
    spark.stop()

    # 3. Modeling charts
    if os.path.exists(args.results_json):
        plot_confusion_matrices(args.results_json,
                                os.path.join(args.figures_dir, "04_confusion_matrices.png"))
        plot_model_comparison(args.results_json,
                              os.path.join(args.figures_dir, "05_model_comparison.png"))
        plot_train_time_comparison(args.results_json,
                                   os.path.join(args.figures_dir, "06_training_time.png"))

    # 4. MapReduce-derived charts
    if os.path.exists(args.mapreduce_tsv):
        plot_top_words(args.mapreduce_tsv,
                       os.path.join(args.figures_dir, "07_top_words.png"))
        make_word_cloud(args.mapreduce_tsv,
                        os.path.join(args.figures_dir, "08_wordcloud.png"))

    # 5. Scalability
    plot_scalability(args.scalability_json,
                     os.path.join(args.figures_dir, "09_scalability.png"))

    print(f"\n✅ All figures saved in {args.figures_dir}/")


if __name__ == "__main__":
    main()
