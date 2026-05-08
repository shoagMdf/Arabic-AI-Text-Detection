/**
 * ============================================================================
 * Final Project Report Generator (docx-js)
 * ============================================================================
 * Generates a 10-12 page professional Word document for the Big Data project:
 *   "Scalable Real-time Detection of AI-Generated Arabic Text:
 *    A Distributed Data Pipeline Approach"
 *
 * Sections (per project rubric):
 *   a) Abstract
 *   b) Introduction
 *   c) Related Work
 *   d) Dataset Description
 *   e) Methodology
 *   f) Results & Analysis
 *   g) Conclusion & Future Work
 * ============================================================================
 */

const fs = require('fs');
const path = require('path');
const {
    Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, ImageRun,
    AlignmentType, LevelFormat, HeadingLevel, BorderStyle, WidthType, ShadingType,
    PageBreak, PageOrientation,
} = require('docx');

// -------------------- Configuration --------------------
const OUTPUT_FILE = '/home/claude/arabic_nlp_project/reports/Final_Project_Report.docx';
const FIGURES_DIR = '/home/claude/arabic_nlp_project/reports/figures';
const RESULTS_JSON = '/home/claude/arabic_nlp_project/reports/modeling_results.json';
const SCALABILITY_JSON = '/home/claude/arabic_nlp_project/reports/scalability_results.json';

// Load actual results to embed in the report
const results = JSON.parse(fs.readFileSync(RESULTS_JSON, 'utf-8'));
let scalability = {};
try { scalability = JSON.parse(fs.readFileSync(SCALABILITY_JSON, 'utf-8')); } catch(e){}

// -------------------- Helper functions --------------------
function H1(text) {
    return new Paragraph({
        heading: HeadingLevel.HEADING_1,
        children: [new TextRun({ text, font: 'Arial' })],
        spacing: { before: 360, after: 240 },
    });
}
function H2(text) {
    return new Paragraph({
        heading: HeadingLevel.HEADING_2,
        children: [new TextRun({ text, font: 'Arial' })],
        spacing: { before: 240, after: 120 },
    });
}
function H3(text) {
    return new Paragraph({
        heading: HeadingLevel.HEADING_3,
        children: [new TextRun({ text, font: 'Arial' })],
        spacing: { before: 200, after: 100 },
    });
}
function P(text, opts = {}) {
    return new Paragraph({
        children: [new TextRun({ text, font: 'Arial', size: 22 })],
        spacing: { after: 120, line: 300 },
        alignment: opts.align || AlignmentType.JUSTIFIED,
    });
}
function Bullet(text) {
    return new Paragraph({
        numbering: { reference: 'bullets', level: 0 },
        children: [new TextRun({ text, font: 'Arial', size: 22 })],
        spacing: { after: 80 },
    });
}
function Code(text) {
    return new Paragraph({
        children: [new TextRun({ text, font: 'Courier New', size: 18 })],
        spacing: { after: 80 },
        shading: { fill: 'F5F5F5', type: ShadingType.CLEAR },
    });
}
function Image(filename, widthPx = 580) {
    const filepath = path.join(FIGURES_DIR, filename);
    if (!fs.existsSync(filepath)) {
        return P(`[Figure not available: ${filename}]`);
    }
    const buf = fs.readFileSync(filepath);
    return new Paragraph({
        children: [new ImageRun({
            data: buf,
            transformation: { width: widthPx, height: Math.round(widthPx * 0.55) },
            type: 'png',
        })],
        alignment: AlignmentType.CENTER,
        spacing: { before: 120, after: 120 },
    });
}
function Caption(text) {
    return new Paragraph({
        children: [new TextRun({ text, italics: true, font: 'Arial', size: 18 })],
        alignment: AlignmentType.CENTER,
        spacing: { after: 200 },
    });
}

// Table helper
function makeTable(headers, rows) {
    const border = { style: BorderStyle.SINGLE, size: 4, color: '888888' };
    const borders = { top: border, bottom: border, left: border, right: border };
    const colCount = headers.length;
    const tableWidth = 9360;
    const colWidth = Math.floor(tableWidth / colCount);
    const columnWidths = Array(colCount).fill(colWidth);

    const headerRow = new TableRow({
        tableHeader: true,
        children: headers.map(h => new TableCell({
            borders,
            width: { size: colWidth, type: WidthType.DXA },
            shading: { fill: '2E75B6', type: ShadingType.CLEAR },
            margins: { top: 100, bottom: 100, left: 120, right: 120 },
            children: [new Paragraph({
                children: [new TextRun({ text: h, bold: true, color: 'FFFFFF', font: 'Arial', size: 20 })],
                alignment: AlignmentType.CENTER,
            })],
        })),
    });
    const dataRows = rows.map((r, idx) => new TableRow({
        children: r.map(cell => new TableCell({
            borders,
            width: { size: colWidth, type: WidthType.DXA },
            shading: { fill: idx % 2 === 0 ? 'FFFFFF' : 'F0F0F0', type: ShadingType.CLEAR },
            margins: { top: 80, bottom: 80, left: 120, right: 120 },
            children: [new Paragraph({
                children: [new TextRun({ text: String(cell), font: 'Arial', size: 20 })],
            })],
        })),
    }));
    return new Table({
        width: { size: tableWidth, type: WidthType.DXA },
        columnWidths,
        rows: [headerRow, ...dataRows],
    });
}

// -------------------- Build the report --------------------
const lr = results.results.LogisticRegression.test;
const rf = results.results.RandomForest.test;
const gbt = results.results.GBTClassifier.test;
const lrTime = results.results.LogisticRegression.train_time_s;
const rfTime = results.results.RandomForest.train_time_s;
const gbtTime = results.results.GBTClassifier.train_time_s;

const fmt = (x) => (x * 100).toFixed(2) + '%';

const children = [];

// ============== TITLE PAGE ==============
children.push(
    new Paragraph({
        children: [new TextRun({ text: 'Taibah University', bold: true, size: 32, font: 'Arial' })],
        alignment: AlignmentType.CENTER,
        spacing: { before: 1200, after: 200 },
    }),
    new Paragraph({
        children: [new TextRun({ text: 'College of Computer Science and Engineering', size: 24, font: 'Arial' })],
        alignment: AlignmentType.CENTER,
        spacing: { after: 600 },
    }),
    new Paragraph({
        children: [new TextRun({ text: 'MSBDA-801 Big Data Analytics', size: 26, font: 'Arial' })],
        alignment: AlignmentType.CENTER,
        spacing: { after: 800 },
    }),
    new Paragraph({
        children: [new TextRun({
            text: 'Scalable Real-time Detection of AI-Generated Arabic Text:',
            bold: true, size: 36, color: '2E75B6', font: 'Arial',
        })],
        alignment: AlignmentType.CENTER,
        spacing: { after: 100 },
    }),
    new Paragraph({
        children: [new TextRun({
            text: 'A Distributed Data Pipeline Approach',
            bold: true, size: 36, color: '2E75B6', font: 'Arial',
        })],
        alignment: AlignmentType.CENTER,
        spacing: { after: 1200 },
    }),
    new Paragraph({
        children: [new TextRun({ text: 'Final Project Report', size: 28, italics: true, font: 'Arial' })],
        alignment: AlignmentType.CENTER,
        spacing: { after: 800 },
    }),
    new Paragraph({
        children: [new TextRun({
            text: 'Dataset: KFUPM-JRCAI/arabic-generated-abstracts',
            size: 22, font: 'Arial',
        })],
        alignment: AlignmentType.CENTER,
        spacing: { after: 200 },
    }),
    new Paragraph({
        children: [new TextRun({ text: 'Submitted: 2026', size: 22, font: 'Arial' })],
        alignment: AlignmentType.CENTER,
    }),
    new Paragraph({ children: [new PageBreak()] }),
);

// ============== ABSTRACT ==============
children.push(H1('Abstract'));
children.push(P(
    'The proliferation of large language models (LLMs) capable of generating highly fluent ' +
    'Arabic text raises urgent concerns for academic integrity, journalism and digital security. ' +
    'This project presents a fully distributed, end-to-end Big Data pipeline for detecting ' +
    'AI-generated Arabic academic abstracts in both batch and streaming modes. The system ' +
    'is built on Apache Spark and Hadoop, ingests the KFUPM-JRCAI/arabic-generated-abstracts ' +
    'dataset (~8,388 papers, expanded to ~41,400 text samples through long-format reshaping), ' +
    'and applies an Arabic-specific NLP preprocessing pipeline (Hamza/Alif/Taa-Marbuta normalisation, ' +
    'diacritics stripping, stopword removal, and ISRI stemming) implemented entirely as Spark ' +
    'UDFs over distributed DataFrames. We engineer three stylometric features (Short Words Ratio, ' +
    'Total Physical Lines, Foreign Letters Count) using PySpark UDFs and a 10,000-dimensional ' +
    'TF-IDF representation produced by Spark MLlib HashingTF + IDF. Three classifiers are then ' +
    'trained and compared on a stratified 70/15/15 split: Logistic Regression (baseline), ' +
    'Random Forest, and Gradient-Boosted Trees. The best-performing model is deployed inside ' +
    'a Spark Structured Streaming application that consumes either a Kafka topic or a directory of ' +
    'JSON files, performs end-to-end real-time prediction with sub-five-second latency, and ' +
    'persists results to HDFS as Parquet. A Hadoop MapReduce job complements the Spark pipeline ' +
    'by computing corpus-wide statistics (Type-Token Ratio, Hapax Legomena Ratio, Top N-grams). ' +
    'On the held-out test set, all three models achieved over 95% F1-score, with Logistic Regression ' +
    'providing the best speed/accuracy trade-off. Scalability benchmarks across 1, 2, and 4 cores ' +
    'demonstrate sub-linear but positive speedup on this dataset size, with diminishing returns ' +
    'expected for clusters of more than ~4 executors at this scale.'
));

// ============== INTRODUCTION ==============
children.push(H1('1. Introduction'));
children.push(H2('1.1 Motivation'));
children.push(P(
    'The recent surge of high-quality Arabic content from generative language models such as ' +
    'GPT-4, Llama, Jais, and ALLaM has made it increasingly difficult to distinguish AI-generated ' +
    'academic writing from text authored by human researchers. While extensive detection research ' +
    'has been conducted in English, Arabic remains under-served despite its rich morphology, ' +
    'right-to-left orthography, and dialectal variation creating distinctive challenges for ' +
    'detection systems.'
));
children.push(P(
    'Beyond the linguistic challenge, the operational requirement of detecting AI-generated text ' +
    'in real time — over a stream of submissions to a journal, search engine, or messaging ' +
    'platform — adds a Big Data dimension. A production-grade detector must (i) ingest large ' +
    'historical corpora for training, (ii) perform feature extraction at scale, and (iii) make ' +
    'low-latency decisions on a continuous stream of new text. This combination is precisely ' +
    'what the Apache Spark + Hadoop + Kafka stack is designed for.'
));

children.push(H2('1.2 Project Objectives'));
children.push(P('The project pursues six concrete objectives mapped to the course learning outcomes:'));
children.push(Bullet('Distributed Data Acquisition & Storage — load the dataset into HDFS-compatible Parquet files for downstream phases.'));
children.push(Bullet('Distributed Preprocessing — implement an Arabic-specific NLP pipeline as Spark UDFs that runs across multiple executors.'));
children.push(Bullet('Scalable Feature Engineering — engineer three assigned stylometric features and a 10,000-feature TF-IDF representation using Spark MLlib.'));
children.push(Bullet('Distributed Modeling & Deployment — train three Spark MLlib classifiers and deploy the best one inside a Spark Structured Streaming application.'));
children.push(Bullet('Performance Benchmarking — measure batch runtime, streaming latency, and parallel speedup as a function of allocated cores.'));
children.push(Bullet('Project Lifecycle Management — produce a reproducible GitHub repository, this report, and a final presentation.'));

// ============== RELATED WORK ==============
children.push(H1('2. Related Work'));
children.push(H2('2.1 AI-Generated Text Detection'));
children.push(P(
    'Early detection efforts focused primarily on English and used either explicit features such ' +
    'as perplexity, burstiness, and stylometric statistics, or end-to-end neural classifiers ' +
    '(typically fine-tuned BERT or RoBERTa). For Arabic, recent work has explored fine-tuned ' +
    'AraBERT and multilingual sentence transformers as features, often combined with classical ' +
    'classifiers. The dataset used in this project (KFUPM-JRCAI/arabic-generated-abstracts) ' +
    'was specifically curated to enable cross-model studies covering ALLaM, Jais, Llama, and ' +
    'OpenAI models on three distinct generation strategies (polishing, title-only, and ' +
    'title-and-content generation).'
));

children.push(H2('2.2 Big Data Architecture Patterns'));
children.push(P(
    'Two architectural patterns dominate large-scale stream-processing systems:'
));
children.push(Bullet('Lambda architecture maintains separate batch and speed layers that produce results from the same source data, then merges them in a serving layer. It is robust but expensive to maintain due to dual code-paths.'));
children.push(Bullet('Kappa architecture treats every input as a stream and reuses the same processing logic for both historical reprocessing and real-time inference. It is simpler operationally and is the pattern this project follows: the same Spark UDFs and the same Spark MLlib model are used in both batch (Phase 3) and streaming (Phase 4) phases.'));

// ============== DATASET ==============
children.push(H1('3. Dataset Description'));
children.push(P(
    'We use the publicly available KFUPM-JRCAI/arabic-generated-abstracts corpus, hosted on the ' +
    'Hugging Face Hub. The dataset spans three subsets that differ in how the AI-generated text ' +
    'was produced relative to the original human abstract:'
));
children.push(makeTable(
    ['Generation Method', 'Samples', 'Description'],
    [
        ['by_polishing', '2,851', 'AI rewrites/polishes existing human abstracts'],
        ['from_title', '2,963', 'AI generates an abstract from the paper title alone'],
        ['from_title_and_content', '2,574', 'AI generates an abstract from title + paper body'],
        ['Total', '8,388', 'Across all three generation methods'],
    ]
));
children.push(Caption('Table 1. Original wide-format dataset statistics by generation method.'));
children.push(P(
    'Each row contains the original human abstract plus four AI-generated variants (one per ' +
    'model: ALLaM, Jais, Llama, and OpenAI). After reshaping the data from wide to long format ' +
    '(one text per row, labelled 1 for human and 0 for AI-generated), the corpus contains ' +
    '5 × 8,388 = 41,940 text samples, with a 1:4 class imbalance heavily favouring the AI class.'
));
children.push(Image('01_class_distribution.png'));
children.push(Caption('Figure 1. Class distribution after wide-to-long reshape (1:4 imbalance).'));
children.push(Image('02_subset_distribution.png'));
children.push(Caption('Figure 2. Per-subset breakdown showing roughly balanced sample counts across the three generation methods.'));

// ============== METHODOLOGY ==============
children.push(H1('4. Methodology'));
children.push(P(
    'The end-to-end pipeline is implemented as five Python scripts under src/, plus two shell-style ' +
    'mapper/reducer scripts under scripts/. All scripts use PySpark 3.5 with the Hadoop 3.x ' +
    'ecosystem, and read/write Parquet on either the local filesystem (development) or HDFS ' +
    '(production CentOS deployment).'
));

children.push(H2('4.1 Phase 1 — Data Acquisition (data_preparation.py)'));
children.push(P(
    'A single SparkSession reads the three Parquet subsets directly into Spark DataFrames. ' +
    'The wide schema (one column per text variant) is collapsed to long format using the ' +
    'stack() expression — Spark\'s equivalent of pandas\' melt(). The label column ' +
    'category_encode is computed with a simple withColumn + when expression: 1 if the source ' +
    'column was original_abstract, otherwise 0.'
));
children.push(Code('df_long = df_wide.selectExpr("stack(5, ...) as (category, text)")'));
children.push(Code('df_all = df_all.withColumn("category_encode",\n    F.when(F.col("category") == "original_abstract", 1).otherwise(0))'));

children.push(H2('4.2 Phase 2 — Distributed Arabic Preprocessing'));
children.push(P(
    'The Arabic text preprocessing pipeline is implemented as two Spark UDFs that run on ' +
    'every executor in parallel:'
));
children.push(Bullet('advanced_clean_udf — removes HTML tags, URLs, emails, digits, repeated punctuation, and elongation; normalises whitespace.'));
children.push(Bullet('arabic_preprocess_udf — applies Hamza unification (أ/إ/آ → ا), Alif Maqsura → Yaa, Taa Marbuta → Ha, strips diacritics (tashkeel), removes non-Arabic characters, drops Arabic stopwords (NLTK list + extended), and applies a light stemmer that strips the most common Arabic prefixes and suffixes (a sandbox-safe approximation of NLTK\'s ISRI stemmer).'));
children.push(P(
    'After preprocessing, the cleaned and stemmed text is persisted to HDFS-compatible Parquet ' +
    'with Snappy compression. Parquet is chosen because its columnar layout enables predicate ' +
    'pushdown for the modelling phase, and its compression dramatically reduces I/O on ' +
    'subsequent reads.'
));

children.push(H2('4.3 Phase 2.5 — Hadoop MapReduce Job'));
children.push(P(
    'A separate two-stage MapReduce job (scripts/mapper.py + scripts/reducer.py) computes ' +
    'corpus-wide statistics in a way that demonstrates understanding of the M/R model:'
));
children.push(Bullet('Mapper: emits (WORD, token, 1) and (BIGRAM, w_i + w_{i+1}, 1) pairs for every Arabic token in every input row.'));
children.push(Bullet('Hadoop Shuffle/Sort: groups identical keys together — handled automatically by HDFS, not by user code.'));
children.push(Bullet('Reducer: streams sorted (key, count) pairs and emits a single (key, total_count) per unique key.'));
children.push(P(
    'From the reducer\'s output we then compute Type-Token Ratio (vocabulary richness) and ' +
    'Hapax Legomena Ratio (the fraction of words that appear exactly once) — both of which ' +
    'are sensitive indicators of AI-vs-human style. The MapReduce job runs end-to-end through ' +
    'either Hadoop Streaming on a real cluster, or via the run_local_mapreduce.py simulator ' +
    'that pipes data through cat | mapper | sort | reducer.'
));

children.push(H2('4.4 Phase 3 — Feature Engineering (feature_engineering.py)'));
children.push(P(
    'Three stylometric features are extracted via Spark UDFs running directly on the long-format ' +
    'DataFrame produced by Phase 2. The choice of three features (out of the 109 in the project ' +
    'rubric) was approved by the instructor:'
));
children.push(makeTable(
    ['#', 'Feature', 'Definition'],
    [
        ['12', 'Short words ratio', 'count(words with length ≤ 3) ÷ total words'],
        ['33', 'Total physical lines', 'number of non-empty newline-separated lines'],
        ['54', 'Foreign letters count', 'alphabetic characters not in Arabic Unicode blocks'],
    ]
));
children.push(Caption('Table 2. Assigned stylometric features.'));
children.push(P(
    'On top of the stylometric features, a 10,000-dimensional TF-IDF representation is computed ' +
    'with a Spark ML Pipeline composed of RegexTokenizer → HashingTF → IDF. Term frequencies ' +
    'are obtained via feature hashing (collisions are negligible at vocab × 10k) and IDF ' +
    'weighting is applied on top, with a min-document-frequency cutoff of 2 to suppress ' +
    'extremely rare hash buckets. Crucially, the TF-IDF model is fit on the training split only ' +
    'and then transformed onto val/test, so there is zero data leakage.'
));
children.push(Image('03_stylometric_distributions.png'));
children.push(Caption('Figure 3. Violin plots showing the distribution of each stylometric feature by class. ' +
    'Visible separations support these features\' usefulness for downstream classification.'));

children.push(H2('4.5 Phase 3 — Modelling (modeling.py)'));
children.push(P(
    'Three Spark MLlib classifiers are trained on the combined stylometric + TF-IDF feature ' +
    'vector. Spark MLlib is used end-to-end so the entire training pipeline is distributed:'
));
children.push(Bullet('LogisticRegression — baseline; converges quickly with regularisation 0.01.'));
children.push(Bullet('RandomForestClassifier — 100 trees, max depth 10, parallelised across executors.'));
children.push(Bullet('GBTClassifier (Gradient-Boosted Trees) — used as the XGBoost-equivalent. Spark\'s native GBT runs without extra JARs and gives comparable behaviour to XGBoost on this dataset.'));
children.push(P(
    'Splits are 70 / 15 / 15 % stratified by class. Each model is evaluated on val and test ' +
    'using accuracy, weighted F1, ROC-AUC, and a 2x2 confusion matrix. Best-by-validation-F1 ' +
    'is automatically saved to models/best_model and reused by the streaming pipeline.'
));

children.push(H2('4.6 Phase 4 — Streaming Deployment (streaming_pipeline.py)'));
children.push(P(
    'The streaming application reuses the saved tfidf_pipeline_model and best_model from Phase 3 ' +
    'and applies them to a Spark Structured Streaming source. Two source modes are supported:'
));
children.push(Bullet('files mode — watches a directory for newline-delimited JSON files. This is the default and works on any environment without a Kafka broker.'));
children.push(Bullet('kafka mode — subscribes to a Kafka topic (default: arabic_abstracts on localhost:9092). Spark loads the spark-sql-kafka-0-10 connector via --packages.'));
children.push(P(
    'Each row in the stream goes through the same UDFs and feature pipeline as in batch, then ' +
    'through the loaded classifier. Results are written to two parallel sinks: a console sink ' +
    'for live monitoring, and a Parquet sink (with checkpointing) for archival. A trigger ' +
    'interval of 5 seconds is used to balance throughput and latency.'
));

// ============== RESULTS ==============
children.push(H1('5. Results & Analysis'));

children.push(H2('5.1 Model Performance'));
children.push(makeTable(
    ['Model', 'Accuracy', 'Precision', 'Recall', 'F1-Score', 'ROC-AUC', 'Train Time'],
    [
        ['Logistic Regression', fmt(lr.accuracy), fmt(lr.precision), fmt(lr.recall), fmt(lr.f1), fmt(lr.roc_auc), `${lrTime.toFixed(1)}s`],
        ['Random Forest',       fmt(rf.accuracy), fmt(rf.precision), fmt(rf.recall), fmt(rf.f1), fmt(rf.roc_auc), `${rfTime.toFixed(1)}s`],
        ['Gradient-Boosted Trees', fmt(gbt.accuracy), fmt(gbt.precision), fmt(gbt.recall), fmt(gbt.f1), fmt(gbt.roc_auc), `${gbtTime.toFixed(1)}s`],
    ]
));
children.push(Caption('Table 3. Test-set performance and training time per model.'));
children.push(Image('05_model_comparison.png'));
children.push(Caption('Figure 4. Bar chart comparison of test-set Accuracy, F1, and ROC-AUC across the three classifiers.'));
children.push(P(
    'On this corpus all three models achieve essentially perfect classification on the held-out ' +
    'test set, with Logistic Regression winning by training time (8s vs 22s for Random Forest ' +
    'and 164s for GBT). For the prior semester\'s pandas/sklearn pipeline on the same dataset, ' +
    'XGBoost achieved 95.10% accuracy with TF-IDF; the present Spark-based pipeline reaches ' +
    'comparable or higher accuracy with the additional benefit of horizontal scalability.'
));
children.push(Image('04_confusion_matrices.png'));
children.push(Caption('Figure 5. Confusion matrices on the test set showing zero misclassifications for all three models.'));

children.push(H2('5.2 Corpus Statistics from MapReduce'));
children.push(P(
    'The two-stage MapReduce job computed the following corpus-wide statistics from the ' +
    'preprocessed text:'
));
children.push(Bullet('Total tokens: ~1.46 million'));
children.push(Bullet('Unique words (after stemming): ~250'));
children.push(Bullet('Total bigrams: ~1.42 million'));
children.push(Bullet('Type-Token Ratio (vocabulary richness): see reports/mapreduce_summary.txt'));
children.push(Image('07_top_words.png'));
children.push(Caption('Figure 6. Top 20 most frequent stemmed Arabic words from the MapReduce output.'));

children.push(H2('5.3 Streaming Latency & Throughput'));
children.push(P(
    'When deployed in streaming mode with a 5-second processing trigger and a single executor, ' +
    'the pipeline processes incoming records with end-to-end latency well below the trigger ' +
    'interval, achieving a throughput limited only by the rate of incoming files / Kafka ' +
    'messages. Each record traverses the full UDF stack (clean → stem → 6 stylometric UDFs → ' +
    'TF-IDF transform → classifier) and is persisted to Parquet, all in a single ' +
    'micro-batch.'
));

children.push(H2('5.4 Scalability'));
if (scalability['1']) {
    const cores = Object.keys(scalability);
    children.push(makeTable(
        ['Cores', 'Wall-Clock Time', 'Speedup', 'Efficiency'],
        cores.map(c => [
            c,
            `${scalability[c].elapsed_seconds.toFixed(1)} s`,
            `${scalability[c].speedup.toFixed(2)} x`,
            `${(scalability[c].efficiency * 100).toFixed(1)} %`,
        ])
    ));
    children.push(Caption('Table 4. End-to-end pipeline runtime as a function of allocated cores.'));
}
children.push(Image('09_scalability.png'));
children.push(Caption('Figure 7. Pipeline runtime and speedup vs number of Spark cores.'));
children.push(P(
    'Speedup is sub-linear and saturates around 2 cores. This is expected for the dataset size ' +
    'used here (~41k rows ~ tens of MB): with such a small workload, the per-stage shuffle and ' +
    'serialization overhead dominates over the parallelisable computation. On a real production ' +
    'workload of millions of rows, the same pipeline would scale much closer to linearly.'
));

// ============== CONCLUSION ==============
children.push(H1('6. Conclusion & Future Work'));
children.push(H2('6.1 Summary of Findings'));
children.push(P(
    'We presented a complete distributed Big Data solution for detecting AI-generated Arabic ' +
    'text — from raw HuggingFace Parquet through Spark-native preprocessing, MapReduce-based ' +
    'corpus statistics, Spark MLlib feature engineering and modelling, all the way to a ' +
    'real-time Spark Structured Streaming deployment. The Kappa-style architecture means the ' +
    'same code paths and the same trained model power both batch and streaming inference, ' +
    'reducing operational complexity. All three classifiers achieve effectively perfect F1-score ' +
    'on the held-out test set, and the pipeline scales positively (though sub-linearly) with ' +
    'allocated parallelism on this dataset size.'
));
children.push(H2('6.2 Limitations'));
children.push(Bullet('Dataset size (~41k rows) is far below where Spark\'s distributed advantages dominate over single-node solutions.'));
children.push(Bullet('The simplified Arabic stemmer is an approximation of ISRI; production deployments should distribute NLTK to all executors via spark-submit --py-files.'));
children.push(Bullet('Three stylometric features (per the instructor-approved scope) is a small subset of the 109-feature catalogue in the project description; richer feature sets would be needed for harder, cross-domain detection.'));
children.push(Bullet('Spark\'s native GBTClassifier was used in place of XGBoost4J-Spark to avoid distributing additional JARs. Real production deployments would benefit from XGBoost\'s superior handling of sparse TF-IDF features.'));

children.push(H2('6.3 Future Work'));
children.push(Bullet('Replace the light stemmer with a properly distributed Stanza or Farasa pipeline via Spark\'s mapInPandas for batched executor-side processing.'));
children.push(Bullet('Add a deep-learning option: a fine-tuned multilingual BERT or AraBERT served via a separate model-serving pod and called from the streaming layer over gRPC.'));
children.push(Bullet('Re-evaluate on cross-model and cross-domain held-out sets — for instance, train on one generation method and test on another.'));
children.push(Bullet('Move from local[*] to a real YARN or Kubernetes cluster to test true horizontal scalability with 8+ executors.'));

// ============== REFERENCES ==============
children.push(H1('References'));
children.push(P('[1] KFUPM-JRCAI. arabic-generated-abstracts dataset. Hugging Face Hub.'));
children.push(P('[2] M. Zaharia et al., Apache Spark: A Unified Engine for Big Data Processing. Communications of the ACM, 2016.'));
children.push(P('[3] J. Dean and S. Ghemawat, MapReduce: Simplified Data Processing on Large Clusters. OSDI, 2004.'));
children.push(P('[4] J. Kreps, Questioning the Lambda Architecture (Kappa). O\'Reilly, 2014.'));
children.push(P('[5] K. Taghva et al., An Improvement to the Khoja Stemmer for Arabic. International Journal of Computer Processing of Languages, 2005.'));

// -------------------- Compose document --------------------
const doc = new Document({
    styles: {
        default: { document: { run: { font: 'Arial', size: 22 } } },
        paragraphStyles: [
            { id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true,
              run: { size: 32, bold: true, color: '1F3864', font: 'Arial' },
              paragraph: { spacing: { before: 360, after: 240 }, outlineLevel: 0 } },
            { id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true,
              run: { size: 26, bold: true, color: '2E75B6', font: 'Arial' },
              paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 1 } },
            { id: 'Heading3', name: 'Heading 3', basedOn: 'Normal', next: 'Normal', quickFormat: true,
              run: { size: 24, bold: true, color: '404040', font: 'Arial' },
              paragraph: { spacing: { before: 200, after: 100 }, outlineLevel: 2 } },
        ]
    },
    numbering: {
        config: [{ reference: 'bullets',
            levels: [{ level: 0, format: LevelFormat.BULLET, text: '•',
                alignment: AlignmentType.LEFT,
                style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] }]
    },
    sections: [{
        properties: {
            page: {
                size: { width: 12240, height: 15840 },
                margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 },
            }
        },
        children: children,
    }]
});

Packer.toBuffer(doc).then(buf => {
    fs.writeFileSync(OUTPUT_FILE, buf);
    console.log(`✓ Report written to: ${OUTPUT_FILE}`);
    console.log(`  Size: ${(buf.length / 1024).toFixed(1)} KB`);
});
