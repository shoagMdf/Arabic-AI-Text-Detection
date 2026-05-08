"""
Generate a more diverse synthetic Arabic dataset for development & testing.

This file is purely for code-development. The real data will be fetched
from HuggingFace KFUPM-JRCAI/arabic-generated-abstracts when running on
CentOS (which has full internet access).
"""
import pandas as pd
import os
import random

random.seed(42)

HUMAN_INTROS = [
    "تتناول هذه الدراسة", "تهدف هذه الورقة البحثية إلى",
    "يقدم هذا البحث", "تستعرض هذه الدراسة",
    "ناقش الباحثون في هذه الورقة", "تركز هذه الدراسة على",
    "يستكشف هذا البحث", "تبحث هذه الدراسة في",
    "تسعى هذه الورقة إلى", "تحلل هذه الدراسة"
]

AI_INTROS = [
    "في هذه الدراسة، نقدم", "في هذا البحث، نقترح",
    "نقدم في هذه الورقة", "تقدم هذه الدراسة",
    "هذه الدراسة تستعرض", "في هذا العمل البحثي",
    "نطرح في هذه الورقة", "تتناول هذه المقالة",
    "نستعرض في هذه الدراسة", "نقوم في هذا البحث"
]

TOPICS = [
    "تحليل البيانات الضخمة", "معالجة اللغة العربية الطبيعية",
    "تطبيقات الذكاء الاصطناعي", "تقنيات التعلم العميق",
    "الكشف عن النصوص المولدة", "تصنيف النصوص العربية",
    "الترجمة الآلية للغة العربية", "استخراج المعلومات",
    "تحليل المشاعر في النصوص", "نمذجة الموضوعات",
    "البحث الدلالي", "التعرف على الكيانات المسماة",
    "تلخيص النصوص العربية", "أنظمة الإجابة على الأسئلة",
    "تحليل الشبكات الاجتماعية", "أمن المعلومات الرقمية",
    "الحوسبة السحابية", "إنترنت الأشياء",
    "الواقع الافتراضي والمعزز", "تقنيات البلوكتشين"
]

METHODS = [
    "خوارزميات التعلم الآلي", "الشبكات العصبية الاصطناعية",
    "نماذج المحولات", "تقنيات التعلم العميق",
    "أساليب الإحصاء التطبيقي", "تقنيات معالجة اللغة الطبيعية",
    "خوارزميات التجميع", "أشجار القرار",
    "آلات المتجهات الداعمة", "الانحدار اللوجستي",
    "نماذج بايز الساذجة", "الغابات العشوائية",
    "خوارزميات التعزيز", "تقنيات التضمين الدلالي",
    "نماذج الانتباه الذاتي"
]

DATA_AMOUNTS = [
    "مجموعة بيانات تحتوي على ألف نص",
    "بيانات شاملة من أكثر من خمسة آلاف وثيقة",
    "عينة من ثلاثة آلاف ومئتي نص",
    "مجموعة قياسية من عشرة آلاف مثال",
    "بيانات تجريبية من ألفين وخمسمئة عينة",
    "مجموعة كبيرة من خمسة عشر ألف نص",
    "بيانات متنوعة من سبعة آلاف وثيقة",
    "عينة تمثيلية من أربعة آلاف نص"
]

RESULT_HUMAN = [
    "أظهرت النتائج دقة عالية في تصنيف النصوص بنسبة فاقت التسعين بالمائة",
    "كشفت الدراسة عن نتائج واعدة في هذا المجال البحثي",
    "تفوقت الطريقة المقترحة على الأساليب التقليدية بفارق كبير",
    "حققت الخوارزمية المقترحة أداء متميزا مقارنة بالنماذج الأخرى",
    "أثبتت التجارب فعالية النموذج المقترح على بيانات متعددة",
    "بينت النتائج أن الطريقة الجديدة تتفوق بشكل ملحوظ",
    "أكدت النتائج صحة الفرضية الرئيسية للبحث",
    "أوضحت النتائج التطبيقية أهمية المنهج المقترح"
]

RESULT_AI = [
    "النتائج التي تم الحصول عليها تظهر تحسنا ملحوظا في الأداء",
    "أظهرت النتائج تحسنا كبيرا مقارنة بالطرق السابقة",
    "النتائج تشير إلى وجود تأثير إيجابي للنموذج المقترح",
    "حقق النموذج نتائج متفوقة في جميع المعايير المستخدمة",
    "النتائج تؤكد فعالية الأساليب المقترحة في هذا المجال",
    "النتائج تشير إلى تفوق النهج الجديد على الطرق الأخرى",
    "تشير النتائج التجريبية إلى نجاح الطريقة المقترحة",
    "النتائج المحصلة تدل على كفاءة النموذج المقترح"
]

CONCLUSION_HUMAN = [
    "تقدم هذه الدراسة إسهاما مهما في تطوير المجال",
    "تفتح هذه النتائج آفاقا جديدة للأبحاث المستقبلية",
    "يمكن تطبيق المنهج المقترح في سياقات بحثية متنوعة",
    "تساهم هذه الدراسة في إثراء الأدبيات البحثية في هذا المجال",
    "توصي الدراسة بمواصلة البحث في هذا الاتجاه الواعد",
    "تقدم الورقة توصيات عملية للباحثين والمطورين"
]

CONCLUSION_AI = [
    "هذا العمل يساهم في تطوير المجال البحثي",
    "الدراسة تقدم توصيات للباحثين والممارسين",
    "يفتح هذا البحث آفاقا جديدة للأبحاث المستقبلية",
    "التوصيات تساعد في تطوير الأبحاث المستقبلية",
    "يمكن تعميم النتائج على نطاق أوسع",
    "هذا البحث يقدم إسهاما قيما في هذا المجال"
]


def make_human_abstract():
    intro = random.choice(HUMAN_INTROS)
    topic = random.choice(TOPICS)
    method = random.choice(METHODS)
    data = random.choice(DATA_AMOUNTS)
    result = random.choice(RESULT_HUMAN)
    conclusion = random.choice(CONCLUSION_HUMAN)
    extra = random.choice([
        "تم استخدام منهجية متعددة المراحل للتحقق من النتائج.",
        "اعتمد البحث على أساليب التحقق المتقاطع.",
        "تمت مراجعة النتائج من خلال خبراء متخصصين.",
        "استخدمت الدراسة معايير تقييم صارمة."
    ])
    return f"{intro} {topic}. اعتمد البحث على {method}. تم استخدام {data}. {extra} {result}. {conclusion}."


def make_ai_abstract():
    intro = random.choice(AI_INTROS)
    topic = random.choice(TOPICS)
    method = random.choice(METHODS)
    data = random.choice(DATA_AMOUNTS)
    result = random.choice(RESULT_AI)
    conclusion = random.choice(CONCLUSION_AI)
    return f"{intro} نهجا جديدا في {topic}. يستخدم النهج المقترح {method}. تم تطبيق المنهج على {data}. {result}. {conclusion}."


def generate_subset(n_samples):
    rows = []
    for _ in range(n_samples):
        rows.append({
            "original_abstract":         make_human_abstract(),
            "allam_generated_abstract":  make_ai_abstract(),
            "jais_generated_abstract":   make_ai_abstract(),
            "llama_generated_abstract":  make_ai_abstract(),
            "openai_generated_abstract": make_ai_abstract(),
        })
    return pd.DataFrame(rows)


print("Generating diverse synthetic Arabic dataset...")

subsets = {
    "by_polishing": generate_subset(2851),
    "from_title": generate_subset(2963),
    "from_title_and_content": generate_subset(2574),
}

os.makedirs("data/raw", exist_ok=True)
for name, df in subsets.items():
    out_path = f"data/raw/{name}.parquet"
    df.to_parquet(out_path, index=False)
    print(f"  v {name}.parquet -- {len(df)} rows")

total = sum(len(df) for df in subsets.values())
print(f"\nSynthetic dataset ready: {total:,} rows")
print(f"After reshape (5 texts/row): ~{total*5:,} text samples")
