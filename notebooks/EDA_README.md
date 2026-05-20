# Comprehensive EDA Scripts — Arabic AI-Text Detection

This package provides **two ways** to generate the 6 EDA figures required by:
- **Task 1.4**: Initial data exploration (structure, types, label distribution)
- **Task 2.3**: Word clouds, n-gram frequency, vocabulary richness (TTR)

## 📦 Contents

| File | Purpose |
|------|---------|
| `comprehensive_eda.py` | Standalone Python script (run from terminal) |
| `Comprehensive_EDA_Zeppelin.json` | Zeppelin notebook (import into Zeppelin UI) |
| `README.md` | This file |

## 🎯 What Gets Generated

Both scripts produce the same **6 publication-ready figures**:

| # | Figure | What It Shows |
|---|--------|---------------|
| 1 | `01_data_structure.png` | Schema table + label pie + subset bar chart |
| 2 | `02_ttr_human_vs_ai.png` | TTR comparison (per-doc avg + corpus-level + distribution) |
| 3 | `03_wordcloud_human_vs_ai.png` | Side-by-side Arabic word clouds |
| 4 | `04_top_words_human_vs_ai.png` | Top-20 words bar charts (Human vs AI) |
| 5 | `05_bigrams_human_vs_ai.png` | Top-20 bigrams (n-grams, n=2) bar charts |
| 6 | `06_distinctive_bigrams.png` | AI-fingerprint bigrams (highest AI/Human ratio) |

## 🚀 Method 1: Standalone Python Script

### Requirements
```bash
pip install pyspark matplotlib seaborn wordcloud arabic-reshaper python-bidi
```

### Run
```bash
cd ~/arabic_nlp_project
cp /path/to/comprehensive_eda.py scripts/
python3 scripts/comprehensive_eda.py
```

### Output location
```
reports/figures/eda/
├── 01_data_structure.png
├── 02_ttr_human_vs_ai.png
├── 03_wordcloud_human_vs_ai.png
├── 04_top_words_human_vs_ai.png
├── 05_bigrams_human_vs_ai.png
├── 06_distinctive_bigrams.png
└── eda_summary.json
```

### Customization
Edit these constants at the top of `comprehensive_eda.py`:
```python
PROCESSED_DIR = "data/processed"       # Spark Parquet input
FIGURES_DIR   = "reports/figures/eda"  # Output dir
HUMAN_COLOR   = "#2AA1C2"              # Teal
AI_COLOR      = "#F2C44F"              # Amber
```

## 🌐 Method 2: Apache Zeppelin Notebook

### Import the notebook

1. Open Zeppelin UI at `http://localhost:8080`
2. Click **Import note**
3. Choose **Select JSON File**
4. Upload `Comprehensive_EDA_Zeppelin.json`
5. The notebook will appear in your notebook list

### Configure HDFS path

In paragraph **#2 (Load Processed Data from HDFS)**, update:
```python
PROCESSED_PATH = 'hdfs://localhost:9000/user/shoagkhaleel/arabic_nlp/data/processed'
```

Replace `shoagkhaleel` with your username if different.

### Run all paragraphs

Click **Run All Paragraphs** (▶ icon at the top).

### Output location
Figures are saved to `/tmp/eda_figures/` on the Zeppelin server.

### To download figures from Zeppelin server
```bash
# In a terminal on the Zeppelin host:
ls /tmp/eda_figures/
cp /tmp/eda_figures/*.png ~/arabic_nlp_project/reports/figures/eda/
```

## 📊 What Each Figure Demonstrates for the Project Report

### Figure 1: Data Structure
**Addresses Task 1.4** completely:
- ✅ Structure (column names)
- ✅ Types (data types per column)
- ✅ Label distribution (pie chart)
- ✅ Per-subset distribution

### Figure 2: TTR Human vs AI
**Addresses Task 2.3** (vocabulary richness):
- Shows that AI has *lower* per-doc TTR (more repetitive)
- Provides both per-doc and corpus-level metrics
- Distribution plot reveals the variance

### Figure 3: Word Clouds Human vs AI
**Addresses Task 2.3** (word clouds):
- Visual comparison of vocabulary
- Reveals which words dominate each class
- Arabic text properly reshaped for matplotlib

### Figure 4: Top Words Human vs AI
**Addresses Task 2.3** (vocabulary richness):
- Most frequent stems per class
- Quantitative ranking with counts

### Figure 5: Top Bigrams Human vs AI
**Addresses Task 2.3** (n-gram frequency):
- Most frequent 2-grams per class
- Reveals phrase-level patterns

### Figure 6: AI-Distinctive Bigrams ⭐
**Bonus analysis** that strengthens the report:
- Shows bigrams that AI uses 10×–100× more than humans
- Directly supports the Redundancy Score finding (Feature #96)
- Provides "AI fingerprints" — formulaic templates AI prefers

## 💡 Recommended Caption Text for the Report

```markdown
**Fig. 1.** Spark DataFrame schema and class distribution after preprocessing.
  Panel (a) shows the column types; (b) reveals the 91.8% / 8.2% AI/Human
  imbalance; (c) decomposes the 36,524 samples across the three generation methods.

**Fig. 2.** Type-Token Ratio (TTR) for human versus AI-generated abstracts.
  Per-document and corpus-level TTR are both lower for AI, consistent with
  the hypothesis that LLM output is more lexically repetitive.

**Fig. 3.** Word cloud comparison. The top-100 most frequent Arabic stems
  for human (left, blue) versus AI (right, amber) abstracts after ISRI
  stemming and stopword removal.

**Fig. 4.** Top-20 unigram frequencies per class. While many stems are shared
  (e.g., دراس, بحث, تحليل), AI shows pronounced over-use of formulaic terms.

**Fig. 5.** Top-20 bigram frequencies per class. The bigrams (تهدف دراس,
  ورق بحثي, متوقع ان) appear orders of magnitude more often in AI output,
  supporting our redundancy-based detection hypothesis.

**Fig. 6.** AI-distinctive bigrams. The 15 bigrams with the highest AI-to-Human
  per-document frequency ratio. These constitute interpretable "AI fingerprints"
  exploited by the stylometric classifier.
```

## ⚙️ Troubleshooting

### `arabic_reshaper` not found
```bash
pip install arabic-reshaper python-bidi
```

### Arabic text appears reversed in figures
This means `arabic_reshaper` is installed but Python-bidi is missing:
```bash
pip install python-bidi
```

### No Arabic font on the system
Install at least one:
```bash
# Ubuntu/Debian
sudo apt install fonts-dejavu fonts-noto-arabic

# CentOS/RHEL/Fedora
sudo dnf install dejavu-sans-fonts google-noto-sans-arabic-fonts
sudo dnf install google-droid-sans-fonts   # Best for Arabic word clouds

# After install
fc-cache -fv
```

### Spark out-of-memory error
Reduce input or increase driver memory:
```python
# In comprehensive_eda.py, edit create_spark():
.config("spark.driver.memory", "4g")   # Was 3g
```

### Wordcloud fails: "No frequencies found"
Verify the processed_text column has data:
```python
df.filter(F.length("processed_text") > 0).count()
```

## 📌 Citation in Report

Include this in your Methodology section:

> "Exploratory Data Analysis was conducted on the distributed Parquet
> corpus using **Spark DataFrames** within an **Apache Zeppelin** notebook
> environment. Six figures were generated: schema/label exploration,
> Type-Token Ratio comparison, side-by-side word clouds, top-20 unigrams
> and bigrams per class, and AI-distinctive bigrams. The full notebook
> (`Comprehensive_EDA_Zeppelin.json`) is available in the project
> repository under `notebooks/`."

## 🎯 Integration with Existing Project

Place these files in your project:

```
arabic_nlp_project/
├── scripts/
│   └── comprehensive_eda.py        ← Method 1
├── notebooks/
│   └── Comprehensive_EDA_Zeppelin.json   ← Method 2
└── reports/
    └── figures/
        └── eda/                    ← Outputs land here
            ├── 01_data_structure.png
            ├── 02_ttr_human_vs_ai.png
            ├── 03_wordcloud_human_vs_ai.png
            ├── 04_top_words_human_vs_ai.png
            ├── 05_bigrams_human_vs_ai.png
            └── 06_distinctive_bigrams.png
```

## ✅ Final Checklist

- [ ] Both scripts run without errors
- [ ] All 6 PNG figures appear in output directory
- [ ] Arabic text displays correctly (not reversed)
- [ ] Word counts make sense (Human ~2,992 docs, AI ~33,532 docs)
- [ ] Figures inserted into the final report
- [ ] Captions written in the appropriate sections
- [ ] Zeppelin notebook committed to the GitHub repo

---

**Project:** MSBDA-801 — Arabic AI-Text Detection
**Author:** shoagkhaleel
**Institution:** Taibah University
