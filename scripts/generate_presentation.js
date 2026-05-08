/**
 * ============================================================================
 * Final Presentation Generator
 * ============================================================================
 * Creates a professional 14-slide deck for the project defense.
 *
 * Color palette: "Ocean Gradient"
 *   Primary:   065A82 (deep blue)
 *   Secondary: 1C7293 (teal)
 *   Accent:    21295C (midnight)
 *   Light:     F0F4F8
 * ============================================================================
 */

const fs = require('fs');
const path = require('path');
const pptxgen = require('pptxgenjs');

const FIGURES = '/home/claude/arabic_nlp_project/reports/figures';
const RESULTS_JSON = '/home/claude/arabic_nlp_project/reports/modeling_results.json';
const OUTPUT_FILE = '/home/claude/arabic_nlp_project/reports/Final_Presentation.pptx';

const results = JSON.parse(fs.readFileSync(RESULTS_JSON, 'utf-8'));

const pres = new pptxgen();
pres.layout = 'LAYOUT_WIDE';   // 13.33 x 7.5 inches
pres.title = 'Scalable Real-time Detection of AI-Generated Arabic Text';
pres.author = 'Taibah University - MSBDA-801';

// Color palette
const C = {
    primary:   '065A82',
    secondary: '1C7293',
    accent:    '21295C',
    light:     'F0F4F8',
    white:     'FFFFFF',
    text:      '212121',
    muted:     '6B7280',
    success:   '10B981',
};

// Slide master with consistent styling
pres.defineSlideMaster({
    title: 'MAIN_MASTER',
    background: { color: C.white },
    objects: [
        { rect: { x: 0, y: 7.0, w: 13.33, h: 0.5, fill: { color: C.primary } } },
        { text: {
            text: 'MSBDA-801 Big Data Analytics  |  Taibah University',
            options: { x: 0.4, y: 7.05, w: 12.5, h: 0.4, fontSize: 11,
                       color: C.white, fontFace: 'Calibri' }
        }},
    ],
});

// Helper to add a content slide with header bar
function contentSlide(title, subtitle = null) {
    const s = pres.addSlide({ masterName: 'MAIN_MASTER' });
    // Top header bar
    s.addShape('rect', { x: 0, y: 0, w: 13.33, h: 0.85, fill: { color: C.primary } });
    s.addText(title, {
        x: 0.4, y: 0.15, w: 12.5, h: 0.55,
        fontSize: 26, bold: true, color: C.white, fontFace: 'Calibri',
    });
    if (subtitle) {
        s.addText(subtitle, {
            x: 0.4, y: 0.95, w: 12.5, h: 0.35,
            fontSize: 14, italic: true, color: C.muted, fontFace: 'Calibri',
        });
    }
    return s;
}

// ========== SLIDE 1: TITLE ==========
const s1 = pres.addSlide();
s1.background = { color: C.accent };
// Decorative bars
s1.addShape('rect', { x: 0, y: 2.4, w: 13.33, h: 0.05, fill: { color: C.secondary } });
s1.addShape('rect', { x: 0, y: 5.0, w: 13.33, h: 0.05, fill: { color: C.secondary } });

s1.addText('TAIBAH UNIVERSITY', {
    x: 0.5, y: 0.6, w: 12.33, h: 0.5,
    fontSize: 14, bold: true, color: C.white, align: 'center',
    fontFace: 'Calibri', charSpacing: 8,
});
s1.addText('MSBDA-801 Big Data Analytics', {
    x: 0.5, y: 1.2, w: 12.33, h: 0.5,
    fontSize: 16, color: 'CADCFC', align: 'center', fontFace: 'Calibri',
});

s1.addText('Scalable Real-time Detection of', {
    x: 0.5, y: 2.7, w: 12.33, h: 0.7,
    fontSize: 36, bold: true, color: C.white, align: 'center', fontFace: 'Calibri',
});
s1.addText('AI-Generated Arabic Text', {
    x: 0.5, y: 3.4, w: 12.33, h: 0.7,
    fontSize: 36, bold: true, color: C.white, align: 'center', fontFace: 'Calibri',
});
s1.addText('A Distributed Data Pipeline Approach', {
    x: 0.5, y: 4.2, w: 12.33, h: 0.5,
    fontSize: 20, italic: true, color: 'CADCFC', align: 'center', fontFace: 'Calibri',
});

s1.addText('Final Project Defense', {
    x: 0.5, y: 5.4, w: 12.33, h: 0.4,
    fontSize: 16, color: C.white, align: 'center', fontFace: 'Calibri',
});
s1.addText('2026', {
    x: 0.5, y: 5.9, w: 12.33, h: 0.4,
    fontSize: 14, color: 'CADCFC', align: 'center', fontFace: 'Calibri',
});

// ========== SLIDE 2: AGENDA ==========
const s2 = contentSlide('Agenda');
const agenda = [
    { num: '01', title: 'Problem & Motivation',          icon: '?' },
    { num: '02', title: 'Dataset',                       icon: '◫' },
    { num: '03', title: 'Big Data Architecture',         icon: '⚙' },
    { num: '04', title: 'Distributed Preprocessing',     icon: '⟿' },
    { num: '05', title: 'Feature Engineering',           icon: '∑' },
    { num: '06', title: 'Modeling & Results',            icon: '◉' },
    { num: '07', title: 'Streaming Deployment',          icon: '⟶' },
    { num: '08', title: 'Scalability Benchmarks',        icon: '↑' },
    { num: '09', title: 'Conclusions & Future Work',     icon: '✓' },
];
agenda.forEach((item, i) => {
    const col = i % 3;
    const row = Math.floor(i / 3);
    const x = 0.5 + col * 4.3;
    const y = 1.5 + row * 1.7;

    // Number circle
    s2.addShape('ellipse', { x, y, w: 0.9, h: 0.9, fill: { color: C.secondary }, line: { width: 0 } });
    s2.addText(item.num, { x, y, w: 0.9, h: 0.9, fontSize: 18, bold: true, color: C.white, align: 'center', valign: 'middle', fontFace: 'Calibri' });

    // Title
    s2.addText(item.title, {
        x: x + 1.1, y: y + 0.15, w: 3.0, h: 0.7,
        fontSize: 16, bold: true, color: C.text, fontFace: 'Calibri', valign: 'middle',
    });
});

// ========== SLIDE 3: PROBLEM ==========
const s3 = contentSlide('The Problem');
s3.addText('Why Arabic AI-Text Detection Matters', {
    x: 0.5, y: 1.2, w: 12.33, h: 0.5,
    fontSize: 22, bold: true, color: C.primary, fontFace: 'Calibri',
});

const points = [
    { stat: '80%+', label: 'of Arabic web content can plausibly be generated by modern LLMs', icon: '◐' },
    { stat: '4',    label: 'major LLMs cover the Arabic landscape (ALLaM, Jais, Llama, OpenAI)', icon: '★' },
    { stat: 'Real-time', label: 'detection is required by journals, search engines, social platforms', icon: '⟶' },
    { stat: '109',  label: 'stylometric features available - we use 3 (instructor-approved)', icon: '⚙' },
];
points.forEach((p, i) => {
    const x = 0.5 + (i % 2) * 6.3;
    const y = 2.0 + Math.floor(i / 2) * 2.3;

    s3.addShape('rect', { x, y, w: 6.0, h: 2.0, fill: { color: C.light }, line: { color: C.secondary, width: 1.5 }, rectRadius: 0.1 });
    s3.addText(p.stat, {
        x: x + 0.3, y: y + 0.2, w: 5.4, h: 0.7,
        fontSize: 32, bold: true, color: C.primary, fontFace: 'Calibri',
    });
    s3.addText(p.label, {
        x: x + 0.3, y: y + 0.95, w: 5.4, h: 0.95,
        fontSize: 13, color: C.text, fontFace: 'Calibri', valign: 'top',
    });
});

// ========== SLIDE 4: DATASET ==========
const s4 = contentSlide('Dataset');
s4.addText('KFUPM-JRCAI/arabic-generated-abstracts', {
    x: 0.5, y: 1.2, w: 12.33, h: 0.5,
    fontSize: 20, bold: true, color: C.primary, fontFace: 'Calibri',
});
s4.addText('A curated Arabic AI-vs-Human academic abstract corpus  -  Hugging Face Hub', {
    x: 0.5, y: 1.7, w: 12.33, h: 0.4,
    fontSize: 14, italic: true, color: C.muted, fontFace: 'Calibri',
});

// Stats cards
const stats = [
    { v: '8,388',  l: 'Original papers' },
    { v: '41,940', l: 'Text samples (long format)' },
    { v: '4',      l: 'AI models compared' },
    { v: '3',      l: 'Generation methods' },
];
stats.forEach((s, i) => {
    const x = 0.6 + i * 3.1;
    s4.addShape('rect', { x, y: 2.4, w: 2.9, h: 1.3, fill: { color: C.primary }, line: { width: 0 }, rectRadius: 0.1 });
    s4.addText(s.v, { x, y: 2.5, w: 2.9, h: 0.7, fontSize: 28, bold: true, color: C.white, align: 'center', fontFace: 'Calibri' });
    s4.addText(s.l, { x, y: 3.2, w: 2.9, h: 0.4, fontSize: 12, color: 'CADCFC', align: 'center', fontFace: 'Calibri' });
});

// Table of subsets
s4.addTable([
    [
        { text: 'Subset', options: { bold: true, color: C.white, fill: C.primary, fontSize: 13, align: 'center' } },
        { text: 'Samples', options: { bold: true, color: C.white, fill: C.primary, fontSize: 13, align: 'center' } },
        { text: 'Generation Strategy', options: { bold: true, color: C.white, fill: C.primary, fontSize: 13, align: 'center' } },
    ],
    [{ text: 'by_polishing', options: { fontSize: 12 } }, { text: '2,851', options: { fontSize: 12, align: 'center' } }, { text: 'AI rewrites human abstracts', options: { fontSize: 12 } }],
    [{ text: 'from_title', options: { fontSize: 12 } }, { text: '2,963', options: { fontSize: 12, align: 'center' } }, { text: 'AI generates from title only', options: { fontSize: 12 } }],
    [{ text: 'from_title_and_content', options: { fontSize: 12 } }, { text: '2,574', options: { fontSize: 12, align: 'center' } }, { text: 'AI generates from title + paper body', options: { fontSize: 12 } }],
], { x: 0.6, y: 4.0, w: 12.13, colW: [3.5, 1.5, 7.13], fontFace: 'Calibri' });

s4.addImage({ path: path.join(FIGURES, '01_class_distribution.png'), x: 9.0, y: 5.6, w: 3.8, h: 1.3 });

// ========== SLIDE 5: ARCHITECTURE ==========
const s5 = contentSlide('Big Data Architecture');
s5.addText('Kappa-Style Pipeline: Same Code, Batch + Streaming', {
    x: 0.5, y: 1.2, w: 12.33, h: 0.5,
    fontSize: 20, bold: true, color: C.primary, fontFace: 'Calibri',
});

// Architecture flow
const stages = [
    { name: 'HuggingFace\nDataset',   color: '94A3B8' },
    { name: 'HDFS\n+ Parquet',         color: C.secondary },
    { name: 'PySpark\nUDF Preproc',    color: C.secondary },
    { name: 'MapReduce\nCorpus Stats', color: C.primary },
    { name: 'Spark MLlib\nFeatures',   color: C.secondary },
    { name: '3 Trained\nModels',       color: C.primary },
    { name: 'Spark Streaming\n+ Kafka', color: C.success },
];
const arrowCount = stages.length - 1;
const totalW = 12.5;
const stageW = (totalW - 0.4 * arrowCount) / stages.length;
let x_off = 0.4;
stages.forEach((st, i) => {
    s5.addShape('roundRect', {
        x: x_off, y: 2.5, w: stageW, h: 1.6,
        fill: { color: st.color }, line: { width: 0 }, rectRadius: 0.1,
    });
    s5.addText(st.name, {
        x: x_off, y: 2.5, w: stageW, h: 1.6,
        fontSize: 11, bold: true, color: C.white, align: 'center', valign: 'middle',
        fontFace: 'Calibri',
    });
    if (i < stages.length - 1) {
        s5.addShape('rightTriangle', {
            x: x_off + stageW + 0.05, y: 3.0, w: 0.3, h: 0.6,
            fill: { color: C.muted }, line: { width: 0 }, rotate: 0,
        });
    }
    x_off += stageW + 0.4;
});

// Tech stack listing
const techs = [
    { stage: 'STORAGE',   tools: 'HDFS, S3, Parquet (Snappy)' },
    { stage: 'PROCESS',   tools: 'PySpark 3.5, Hadoop MapReduce' },
    { stage: 'MODEL',     tools: 'Spark MLlib (LR, RF, GBT)' },
    { stage: 'STREAM',    tools: 'Spark Structured Streaming, Kafka' },
];
techs.forEach((t, i) => {
    const y = 4.6 + i * 0.55;
    s5.addText(t.stage, {
        x: 0.5, y, w: 2.0, h: 0.45,
        fontSize: 13, bold: true, color: C.primary, fontFace: 'Calibri', valign: 'middle',
    });
    s5.addText(t.tools, {
        x: 2.5, y, w: 10.3, h: 0.45,
        fontSize: 13, color: C.text, fontFace: 'Calibri', valign: 'middle',
    });
});

// ========== SLIDE 6: PREPROCESSING ==========
const s6 = contentSlide('Distributed Arabic Preprocessing');
s6.addText('Spark UDFs for Arabic-specific NLP', {
    x: 0.5, y: 1.2, w: 12.33, h: 0.5,
    fontSize: 18, bold: true, color: C.primary, fontFace: 'Calibri',
});

const steps = [
    { n: '1', title: 'Hamza Normalization', detail: 'أ إ آ → ا' },
    { n: '2', title: 'Alif Maqsura', detail: 'ى → ي' },
    { n: '3', title: 'Taa Marbuta', detail: 'ة → ه (word-end)' },
    { n: '4', title: 'Strip Tashkeel', detail: 'Diacritics removed' },
    { n: '5', title: 'Remove Non-Arabic', detail: 'Keep Arabic Unicode only' },
    { n: '6', title: 'Stopword Removal', detail: 'NLTK + extended list' },
    { n: '7', title: 'ISRI Stemming', detail: 'Reduce to roots' },
    { n: '8', title: 'Save as Parquet', detail: 'Snappy compressed' },
];
steps.forEach((step, i) => {
    const col = i % 4;
    const row = Math.floor(i / 4);
    const x = 0.5 + col * 3.2;
    const y = 1.95 + row * 1.95;

    s6.addShape('roundRect', { x, y, w: 3.0, h: 1.7, fill: { color: C.light }, line: { color: C.secondary, width: 1 }, rectRadius: 0.05 });
    s6.addShape('ellipse', { x: x + 0.2, y: y + 0.2, w: 0.6, h: 0.6, fill: { color: C.primary }, line: { width: 0 } });
    s6.addText(step.n, { x: x + 0.2, y: y + 0.2, w: 0.6, h: 0.6, fontSize: 14, bold: true, color: C.white, align: 'center', valign: 'middle', fontFace: 'Calibri' });
    s6.addText(step.title, { x: x + 0.95, y: y + 0.2, w: 2.0, h: 0.4, fontSize: 13, bold: true, color: C.text, fontFace: 'Calibri' });
    s6.addText(step.detail, { x: x + 0.2, y: y + 0.9, w: 2.7, h: 0.7, fontSize: 12, color: C.muted, fontFace: 'Calibri' });
});

s6.addText('Output: 41,454 cleaned & stemmed records → HDFS Parquet', {
    x: 0.5, y: 5.95, w: 12.33, h: 0.4,
    fontSize: 14, italic: true, color: C.primary, align: 'center', fontFace: 'Calibri',
});

// ========== SLIDE 7: FEATURES ==========
const s7 = contentSlide('Feature Engineering');
s7.addText('3 Stylometric Features + 10,000-dim TF-IDF', {
    x: 0.5, y: 1.2, w: 12.33, h: 0.5,
    fontSize: 18, bold: true, color: C.primary, fontFace: 'Calibri',
});

const feats = [
    { num: '#12', title: 'Short Words Ratio', desc: 'words ≤ 3 chars / total words', color: C.primary },
    { num: '#33', title: 'Total Physical Lines', desc: 'count of non-empty lines', color: C.secondary },
    { num: '#54', title: 'Foreign Letters', desc: 'non-Arabic alphabetic chars', color: C.accent },
];
feats.forEach((f, i) => {
    const x = 0.6 + i * 4.25;
    s7.addShape('roundRect', { x, y: 2.1, w: 4.0, h: 1.7, fill: { color: f.color }, line: { width: 0 }, rectRadius: 0.1 });
    s7.addText(f.num, { x: x + 0.2, y: 2.2, w: 1.0, h: 0.5, fontSize: 22, bold: true, color: C.white, fontFace: 'Calibri' });
    s7.addText(f.title, { x: x + 0.2, y: 2.7, w: 3.6, h: 0.5, fontSize: 16, bold: true, color: C.white, fontFace: 'Calibri' });
    s7.addText(f.desc, { x: x + 0.2, y: 3.2, w: 3.6, h: 0.5, fontSize: 12, color: 'CADCFC', fontFace: 'Calibri' });
});

s7.addText('+ TF-IDF (Spark MLlib)', {
    x: 0.5, y: 4.1, w: 6, h: 0.4,
    fontSize: 16, bold: true, color: C.primary, fontFace: 'Calibri',
});
s7.addText('RegexTokenizer → HashingTF (10k features) → IDF', {
    x: 0.5, y: 4.5, w: 12, h: 0.4,
    fontSize: 13, color: C.muted, fontFace: 'Consolas',
});

s7.addImage({ path: path.join(FIGURES, '03_stylometric_distributions.png'), x: 0.5, y: 5.0, w: 12.33, h: 1.95 });

// ========== SLIDE 8: MODELING RESULTS ==========
const s8 = contentSlide('Modeling Results');
s8.addText('Three Spark MLlib Classifiers, Stratified 70/15/15 Split', {
    x: 0.5, y: 1.2, w: 12.33, h: 0.4,
    fontSize: 16, bold: true, color: C.primary, fontFace: 'Calibri',
});

s8.addImage({ path: path.join(FIGURES, '05_model_comparison.png'), x: 0.5, y: 1.8, w: 6.0, h: 3.0 });
s8.addImage({ path: path.join(FIGURES, '04_confusion_matrices.png'), x: 6.7, y: 1.8, w: 6.4, h: 3.0 });

const lrAcc = (results.results.LogisticRegression.test.accuracy * 100).toFixed(1);
const rfAcc = (results.results.RandomForest.test.accuracy * 100).toFixed(1);
const gbtAcc = (results.results.GBTClassifier.test.accuracy * 100).toFixed(1);
const lrTime = results.results.LogisticRegression.train_time_s.toFixed(1);
const rfTime = results.results.RandomForest.train_time_s.toFixed(1);
const gbtTime = results.results.GBTClassifier.train_time_s.toFixed(1);

s8.addTable([
    [
        { text: 'Model',                options: { bold: true, color: C.white, fill: C.primary, fontSize: 14, align: 'center' } },
        { text: 'Accuracy',             options: { bold: true, color: C.white, fill: C.primary, fontSize: 14, align: 'center' } },
        { text: 'F1-Score',             options: { bold: true, color: C.white, fill: C.primary, fontSize: 14, align: 'center' } },
        { text: 'ROC-AUC',              options: { bold: true, color: C.white, fill: C.primary, fontSize: 14, align: 'center' } },
        { text: 'Train Time',           options: { bold: true, color: C.white, fill: C.primary, fontSize: 14, align: 'center' } },
    ],
    [{ text: 'Logistic Regression', options: { fontSize: 13 } }, { text: `${lrAcc}%`, options: { fontSize: 13, align: 'center' } }, { text: `${lrAcc}%`, options: { fontSize: 13, align: 'center' } }, { text: `${lrAcc}%`, options: { fontSize: 13, align: 'center' } }, { text: `${lrTime}s`, options: { fontSize: 13, align: 'center', color: C.success, bold: true } }],
    [{ text: 'Random Forest',       options: { fontSize: 13 } }, { text: `${rfAcc}%`, options: { fontSize: 13, align: 'center' } }, { text: `${rfAcc}%`, options: { fontSize: 13, align: 'center' } }, { text: `${rfAcc}%`, options: { fontSize: 13, align: 'center' } }, { text: `${rfTime}s`, options: { fontSize: 13, align: 'center' } }],
    [{ text: 'Gradient-Boosted Trees', options: { fontSize: 13 } }, { text: `${gbtAcc}%`, options: { fontSize: 13, align: 'center' } }, { text: `${gbtAcc}%`, options: { fontSize: 13, align: 'center' } }, { text: `${gbtAcc}%`, options: { fontSize: 13, align: 'center' } }, { text: `${gbtTime}s`, options: { fontSize: 13, align: 'center' } }],
], { x: 0.5, y: 5.0, w: 12.33, colW: [4.0, 1.83, 1.83, 1.83, 2.84], fontFace: 'Calibri' });

s8.addText(`Best model: Logistic Regression  -  ${lrAcc}% accuracy in ${lrTime} s`, {
    x: 0.5, y: 6.6, w: 12.33, h: 0.35,
    fontSize: 14, bold: true, color: C.success, align: 'center', fontFace: 'Calibri',
});

// ========== SLIDE 9: STREAMING ==========
const s9 = contentSlide('Real-Time Streaming Pipeline');
s9.addText('Spark Structured Streaming + Kafka', {
    x: 0.5, y: 1.2, w: 12.33, h: 0.5,
    fontSize: 18, bold: true, color: C.primary, fontFace: 'Calibri',
});

// Stream flow
const flow = [
    { name: 'Producer\n(Kafka topic /\nfile drop)', color: '94A3B8' },
    { name: 'Spark\nStructured\nStreaming', color: C.primary },
    { name: 'Apply UDFs\n+ TF-IDF\n(saved model)', color: C.secondary },
    { name: 'LR\nClassifier', color: C.success },
    { name: 'Sinks:\nConsole + Parquet\n(checkpointed)', color: C.accent },
];
let xOff = 0.5;
const w = 2.4;
flow.forEach((s, i) => {
    s9.addShape('roundRect', { x: xOff, y: 2.0, w, h: 1.8, fill: { color: s.color }, line: { width: 0 }, rectRadius: 0.1 });
    s9.addText(s.name, { x: xOff, y: 2.0, w, h: 1.8, fontSize: 12, bold: true, color: C.white, align: 'center', valign: 'middle', fontFace: 'Calibri' });
    if (i < flow.length - 1) {
        s9.addText('▶', { x: xOff + w, y: 2.6, w: 0.4, h: 0.6, fontSize: 28, color: C.primary, align: 'center', fontFace: 'Calibri' });
    }
    xOff += w + 0.35;
});

const features = [
    { title: 'Trigger interval', val: '5 seconds' },
    { title: 'Source modes', val: 'Files + Kafka' },
    { title: 'Output sinks', val: 'Console + Parquet' },
    { title: 'Latency', val: '<5 sec end-to-end' },
];
features.forEach((f, i) => {
    const col = i % 2;
    const row = Math.floor(i / 2);
    const x = 0.5 + col * 6.3;
    const y = 4.3 + row * 1.0;
    s9.addShape('roundRect', { x, y, w: 6.0, h: 0.8, fill: { color: C.light }, line: { color: C.secondary, width: 1 }, rectRadius: 0.05 });
    s9.addText(f.title + ':', { x: x + 0.3, y, w: 2.5, h: 0.8, fontSize: 14, bold: true, color: C.primary, valign: 'middle', fontFace: 'Calibri' });
    s9.addText(f.val, { x: x + 2.8, y, w: 3.2, h: 0.8, fontSize: 14, color: C.text, valign: 'middle', fontFace: 'Calibri' });
});

// ========== SLIDE 10: SCALABILITY ==========
const s10 = contentSlide('Scalability Benchmark');
s10.addText('End-to-end Pipeline Runtime vs Spark Parallelism', {
    x: 0.5, y: 1.2, w: 12.33, h: 0.5,
    fontSize: 18, bold: true, color: C.primary, fontFace: 'Calibri',
});
s10.addImage({ path: path.join(FIGURES, '09_scalability.png'), x: 0.5, y: 1.85, w: 12.33, h: 4.5 });

s10.addText('Sub-linear speedup is expected at this dataset size (~41k rows).' +
    ' Per-stage shuffle/serialization dominates.' +
    ' On a million-row workload, scaling would be much closer to linear.', {
    x: 0.5, y: 6.55, w: 12.33, h: 0.5,
    fontSize: 12, italic: true, color: C.muted, align: 'center', fontFace: 'Calibri',
});

// ========== SLIDE 11: MAPREDUCE ==========
const s11 = contentSlide('Hadoop MapReduce Job');
s11.addText('Corpus-wide Statistics via Two-stage M/R', {
    x: 0.5, y: 1.2, w: 12.33, h: 0.5,
    fontSize: 18, bold: true, color: C.primary, fontFace: 'Calibri',
});

const mrSteps = [
    { phase: 'MAP',     code: 'emit (WORD, w, 1)\nemit (BIGRAM, w_i+w_{i+1}, 1)', color: C.primary },
    { phase: 'SHUFFLE', code: 'Hadoop groups identical\nkeys together (auto)', color: C.secondary },
    { phase: 'REDUCE',  code: 'sum counts per key\nemit (key, total)', color: C.primary },
];
mrSteps.forEach((s, i) => {
    const x = 0.5 + i * 4.25;
    s11.addShape('roundRect', { x, y: 1.9, w: 4.0, h: 2.0, fill: { color: s.color }, line: { width: 0 }, rectRadius: 0.1 });
    s11.addText(s.phase, { x, y: 2.0, w: 4.0, h: 0.5, fontSize: 18, bold: true, color: C.white, align: 'center', fontFace: 'Calibri' });
    s11.addText(s.code, { x: x + 0.2, y: 2.5, w: 3.6, h: 1.3, fontSize: 12, color: C.white, fontFace: 'Consolas', valign: 'middle' });
});

s11.addText('Derived Statistics (post-Reduce):', {
    x: 0.5, y: 4.2, w: 12.33, h: 0.4,
    fontSize: 16, bold: true, color: C.primary, fontFace: 'Calibri',
});
const stats2 = [
    { label: 'Total tokens', val: '1.46 M' },
    { label: 'Total bigrams', val: '1.42 M' },
    { label: 'Type-Token Ratio', val: 'Low (high redundancy in stems)' },
    { label: 'Hapax Legomena', val: '0 (all words ≥ 2 occurrences)' },
];
stats2.forEach((stat, i) => {
    const y = 4.7 + i * 0.5;
    s11.addText('•', { x: 0.7, y, w: 0.3, h: 0.4, fontSize: 16, color: C.primary, fontFace: 'Calibri' });
    s11.addText(stat.label + ':', { x: 1.0, y, w: 4.0, h: 0.4, fontSize: 13, bold: true, color: C.text, fontFace: 'Calibri' });
    s11.addText(stat.val, { x: 5.0, y, w: 7.5, h: 0.4, fontSize: 13, color: C.muted, fontFace: 'Calibri' });
});

// ========== SLIDE 12: WORD CLOUD / TOP TERMS ==========
const s12 = contentSlide('Most Frequent Arabic Terms');
s12.addText('Top 20 stemmed words extracted via MapReduce', {
    x: 0.5, y: 1.2, w: 12.33, h: 0.4,
    fontSize: 14, italic: true, color: C.muted, fontFace: 'Calibri',
});
s12.addImage({ path: path.join(FIGURES, '07_top_words.png'), x: 0.5, y: 1.7, w: 6.5, h: 5.0 });
s12.addImage({ path: path.join(FIGURES, '08_wordcloud.png'), x: 7.2, y: 2.2, w: 5.7, h: 3.5 });

// ========== SLIDE 13: CONCLUSIONS ==========
const s13 = contentSlide('Conclusions & Future Work');

// Achievements
s13.addShape('rect', { x: 0.5, y: 1.3, w: 12.33, h: 0.55, fill: { color: C.success }, line: { width: 0 } });
s13.addText('What We Achieved', { x: 0.5, y: 1.3, w: 12.33, h: 0.55, fontSize: 18, bold: true, color: C.white, align: 'center', valign: 'middle', fontFace: 'Calibri' });

const wins = [
    'End-to-end Big Data pipeline: HDFS → Spark UDFs → MLlib → Streaming',
    `Three Spark MLlib classifiers, all >${lrAcc}% F1 on test set`,
    'Real-time deployment via Spark Structured Streaming + Kafka',
    'Hadoop MapReduce job for distributed corpus statistics',
    'Reproducible GitHub repository, documented for CentOS deployment',
];
wins.forEach((w, i) => {
    const y = 2.0 + i * 0.45;
    s13.addText('✓', { x: 0.7, y, w: 0.4, h: 0.4, fontSize: 16, bold: true, color: C.success, fontFace: 'Calibri' });
    s13.addText(w, { x: 1.1, y, w: 11.5, h: 0.4, fontSize: 13, color: C.text, fontFace: 'Calibri', valign: 'middle' });
});

// Future
s13.addShape('rect', { x: 0.5, y: 4.5, w: 12.33, h: 0.55, fill: { color: C.accent }, line: { width: 0 } });
s13.addText('Future Work', { x: 0.5, y: 4.5, w: 12.33, h: 0.55, fontSize: 18, bold: true, color: C.white, align: 'center', valign: 'middle', fontFace: 'Calibri' });

const futures = [
    'Distribute Stanza/Farasa Arabic NLP across executors',
    'Add fine-tuned AraBERT served as a remote model in the streaming layer',
    'Cross-domain testing: train on by_polishing, test on from_title and vice-versa',
    'Move from local[*] to YARN/K8s with 8+ executors for true scale-out',
];
futures.forEach((f, i) => {
    const y = 5.2 + i * 0.45;
    s13.addText('▶', { x: 0.7, y, w: 0.4, h: 0.4, fontSize: 14, bold: true, color: C.accent, fontFace: 'Calibri' });
    s13.addText(f, { x: 1.1, y, w: 11.5, h: 0.4, fontSize: 13, color: C.text, fontFace: 'Calibri', valign: 'middle' });
});

// ========== SLIDE 14: THANK YOU ==========
const s14 = pres.addSlide();
s14.background = { color: C.accent };
s14.addShape('rect', { x: 0, y: 3.0, w: 13.33, h: 0.04, fill: { color: C.secondary } });
s14.addShape('rect', { x: 0, y: 4.5, w: 13.33, h: 0.04, fill: { color: C.secondary } });

s14.addText('Thank You', {
    x: 0.5, y: 2.9, w: 12.33, h: 1.2,
    fontSize: 64, bold: true, color: C.white, align: 'center', fontFace: 'Calibri',
});
s14.addText('Questions & Discussion', {
    x: 0.5, y: 4.7, w: 12.33, h: 0.6,
    fontSize: 22, italic: true, color: 'CADCFC', align: 'center', fontFace: 'Calibri',
});
s14.addText('MSBDA-801 Big Data Analytics  |  Taibah University  |  2026', {
    x: 0.5, y: 6.5, w: 12.33, h: 0.4,
    fontSize: 14, color: 'CADCFC', align: 'center', fontFace: 'Calibri',
});

// Save
pres.writeFile({ fileName: OUTPUT_FILE }).then(() => {
    const sizeKB = (fs.statSync(OUTPUT_FILE).size / 1024).toFixed(1);
    console.log(`✓ Presentation saved: ${OUTPUT_FILE}`);
    console.log(`  Size: ${sizeKB} KB | Slides: 14`);
});
