# دليل تشغيل المشروع على CentOS 9 (خطوة بخطوة)

> هذا الدليل يفترض أنكِ بدأتِ من نظام CentOS 9 stream نظيف داخل VirtualBox
> وأن لديكِ صلاحيات `sudo`. كل أمر بالأسفل قابل للنسخ واللصق مباشرة في Terminal.

---

## الجزء 1: التحقق من النظام

افتحي **Terminal** (الطرفية) ونفّذي الأوامر التالية واحداً تلو الآخر:

```bash
# 1.1 - تأكيد إصدار النظام
cat /etc/redhat-release

# 1.2 - تأكيد الذاكرة المتاحة (يجب أن تكون 4GB أو أكثر)
free -h

# 1.3 - تأكيد المساحة المتاحة (يجب 20GB حر على الأقل)
df -h /

# 1.4 - اختبار الإنترنت
ping -c 3 google.com
```

---

## الجزء 2: تحديث النظام وتثبيت الأدوات الأساسية

```bash
# 2.1 - تحديث جميع الحزم
sudo dnf update -y

# 2.2 - تثبيت أدوات التطوير الأساسية
sudo dnf install -y \
    wget curl tar gzip unzip vim git \
    gcc gcc-c++ make \
    openssh-server openssh-clients \
    net-tools

# 2.3 - تشغيل خدمة SSH (مفيدة للنسخ والاتصال)
sudo systemctl enable --now sshd

# 2.4 - تأكيد تشغيل SSH
sudo systemctl status sshd
```

---

## الجزء 3: تثبيت Java 11 (مطلوب لـ Hadoop و Spark)

```bash
# 3.1 - تثبيت OpenJDK 11
sudo dnf install -y java-11-openjdk java-11-openjdk-devel

# 3.2 - التحقق من التثبيت
java -version
javac -version

# 3.3 - معرفة مسار Java (نحتاجه لاحقاً)
readlink -f $(which java) | sed 's|/jre/bin/java||;s|/bin/java||'
# هذا سيظهر شيئاً مثل: /usr/lib/jvm/java-11-openjdk-...
```

نسخي الناتج من أمر 3.3 — ستحتاجينه في الخطوة التالية.

---

## الجزء 4: تثبيت Python 3 و pip

```bash
# 4.1 - تأكيد Python 3 موجود
python3 --version

# 4.2 - تثبيت pip
sudo dnf install -y python3-pip python3-devel

# 4.3 - ترقية pip
python3 -m pip install --upgrade pip --user

# 4.4 - تثبيت المكتبات المطلوبة
pip3 install --user \
    pyspark==3.5.0 \
    pandas numpy \
    scikit-learn \
    matplotlib seaborn \
    arabic-reshaper python-bidi \
    wordcloud \
    datasets \
    pyarrow \
    nltk
```

---

## الجزء 5: تثبيت Hadoop 3.3.6

```bash
# 5.1 - الانتقال إلى /opt
cd /opt

# 5.2 - تحميل Hadoop
sudo wget https://archive.apache.org/dist/hadoop/common/hadoop-3.3.6/hadoop-3.3.6.tar.gz

# 5.3 - فك الضغط
sudo tar -xzf hadoop-3.3.6.tar.gz
sudo mv hadoop-3.3.6 hadoop
sudo rm hadoop-3.3.6.tar.gz

# 5.4 - تغيير ملكية المجلد لمستخدمكِ
sudo chown -R $(whoami):$(whoami) /opt/hadoop

# 5.5 - التحقق
ls /opt/hadoop/
```

### إعداد متغيرات البيئة

```bash
# 5.6 - فتح ملف ~/.bashrc
vim ~/.bashrc
```

أضيفي السطور التالية في **نهاية الملف** (بعد `i` للدخول في وضع التعديل، ثم `Esc` ثم `:wq` للحفظ):

```bash
# Java
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk
export PATH=$JAVA_HOME/bin:$PATH

# Hadoop
export HADOOP_HOME=/opt/hadoop
export HADOOP_INSTALL=$HADOOP_HOME
export HADOOP_MAPRED_HOME=$HADOOP_HOME
export HADOOP_COMMON_HOME=$HADOOP_HOME
export HADOOP_HDFS_HOME=$HADOOP_HOME
export YARN_HOME=$HADOOP_HOME
export HADOOP_COMMON_LIB_NATIVE_DIR=$HADOOP_HOME/lib/native
export PATH=$PATH:$HADOOP_HOME/sbin:$HADOOP_HOME/bin
export HADOOP_OPTS="-Djava.library.path=$HADOOP_HOME/lib/native"
```

> **مهم:** غيّري `JAVA_HOME` ليطابق الناتج من الخطوة 3.3 إذا كان مختلفاً.

```bash
# 5.7 - تحميل المتغيرات
source ~/.bashrc

# 5.8 - التحقق
echo $JAVA_HOME
echo $HADOOP_HOME
hadoop version
```

---

## الجزء 6: إعداد Hadoop (وضع Pseudo-Distributed)

### 6.1 - تعديل hadoop-env.sh

```bash
vim /opt/hadoop/etc/hadoop/hadoop-env.sh
```

ابحثي عن السطر `# export JAVA_HOME=` وغيّريه إلى:

```bash
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk
```

### 6.2 - تعديل core-site.xml

```bash
vim /opt/hadoop/etc/hadoop/core-site.xml
```

استبدلي محتوى `<configuration>` بما يلي:

```xml
<configuration>
    <property>
        <name>fs.defaultFS</name>
        <value>hdfs://localhost:9000</value>
    </property>
</configuration>
```

### 6.3 - تعديل hdfs-site.xml

```bash
vim /opt/hadoop/etc/hadoop/hdfs-site.xml
```

```xml
<configuration>
    <property>
        <name>dfs.replication</name>
        <value>1</value>
    </property>
    <property>
        <name>dfs.namenode.name.dir</name>
        <value>file:///opt/hadoop/data/namenode</value>
    </property>
    <property>
        <name>dfs.datanode.data.dir</name>
        <value>file:///opt/hadoop/data/datanode</value>
    </property>
</configuration>
```

### 6.4 - إنشاء مجلدات البيانات

```bash
mkdir -p /opt/hadoop/data/namenode
mkdir -p /opt/hadoop/data/datanode
```

### 6.5 - إعداد SSH localhost (لـ Hadoop)

```bash
ssh-keygen -t rsa -P "" -f ~/.ssh/id_rsa
cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
ssh localhost  # اختبار - اكتبي 'yes' إذا سُئلت، ثم 'exit' للخروج
```

### 6.6 - تهيئة HDFS

```bash
hdfs namenode -format
```

### 6.7 - تشغيل Hadoop

```bash
start-dfs.sh

# تأكدي أن الخدمات شغالة:
jps
# يجب أن تظهر: NameNode, DataNode, SecondaryNameNode
```

### 6.8 - التحقق من Web UI

افتحي المتصفح داخل CentOS واذهبي إلى:

- **HDFS UI:** `http://localhost:9870`

> **خذي screenshot لهذه الصفحة!** ستحتاجينها للتقرير.

---

## الجزء 7: تثبيت Apache Spark 3.5.0

```bash
# 7.1 - الانتقال إلى /opt
cd /opt

# 7.2 - تحميل Spark
sudo wget https://archive.apache.org/dist/spark/spark-3.5.0/spark-3.5.0-bin-hadoop3.tgz

# 7.3 - فك الضغط
sudo tar -xzf spark-3.5.0-bin-hadoop3.tgz
sudo mv spark-3.5.0-bin-hadoop3 spark
sudo chown -R $(whoami):$(whoami) /opt/spark
sudo rm spark-3.5.0-bin-hadoop3.tgz
```

### 7.4 - إضافة Spark إلى ~/.bashrc

```bash
vim ~/.bashrc
```

أضيفي:

```bash
# Spark
export SPARK_HOME=/opt/spark
export PATH=$PATH:$SPARK_HOME/bin:$SPARK_HOME/sbin
export PYSPARK_PYTHON=python3
```

```bash
source ~/.bashrc
spark-shell --version
```

---

## الجزء 8: تثبيت Apache Kafka 3.5.0 (للبث الحقيقي)

```bash
cd /opt
sudo wget https://archive.apache.org/dist/kafka/3.5.0/kafka_2.13-3.5.0.tgz
sudo tar -xzf kafka_2.13-3.5.0.tgz
sudo mv kafka_2.13-3.5.0 kafka
sudo chown -R $(whoami):$(whoami) /opt/kafka
sudo rm kafka_2.13-3.5.0.tgz
```

### 8.1 - تشغيل ZooKeeper

افتحي **Terminal جديد** (سيظل مفتوحاً):

```bash
/opt/kafka/bin/zookeeper-server-start.sh /opt/kafka/config/zookeeper.properties
```

### 8.2 - تشغيل Kafka broker

افتحي **Terminal آخر**:

```bash
/opt/kafka/bin/kafka-server-start.sh /opt/kafka/config/server.properties
```

### 8.3 - إنشاء topic

في **Terminal ثالث**:

```bash
/opt/kafka/bin/kafka-topics.sh --create \
    --bootstrap-server localhost:9092 \
    --replication-factor 1 \
    --partitions 3 \
    --topic arabic_abstracts
```

> **خذي screenshot للأوامر السابقة وللخرج بعد التنفيذ!**

---

## الجزء 9: نسخ المشروع وتشغيله

### 9.1 - استنساخ مستودع GitHub

```bash
cd ~
git clone https://github.com/shoagMdf/ArabicNLP_BigData.git
cd ArabicNLP_BigData
```

> ضعي روابط مستودعك الجديد هنا. إذا كنتِ تستخدمين نفس المستودع القديم،
> أنشئي branch جديد للمشروع: `git checkout -b bigdata-pipeline`

### 9.2 - تحميل الداتا من Hugging Face (مرة واحدة)

```bash
python3 -c "
from datasets import load_dataset
import os
os.makedirs('data/raw', exist_ok=True)
for cfg in ['by_polishing', 'from_title', 'from_title_and_content']:
    ds = load_dataset('KFUPM-JRCAI/arabic-generated-abstracts', cfg)
    df = ds[list(ds.keys())[0]].to_pandas()
    df.to_parquet(f'data/raw/{cfg}.parquet')
    print(f'  Saved {cfg}: {len(df)} rows')
"
```

### 9.3 - رفع الداتا إلى HDFS

```bash
hdfs dfs -mkdir -p /user/$(whoami)/arabic_nlp/data/raw
hdfs dfs -put data/raw/*.parquet /user/$(whoami)/arabic_nlp/data/raw/
hdfs dfs -ls /user/$(whoami)/arabic_nlp/data/raw/
```

### 9.4 - تشغيل المراحل

```bash
# Phase 1 & 2
spark-submit src/data_preparation.py \
    --raw-dir hdfs://localhost:9000/user/$(whoami)/arabic_nlp/data/raw \
    --out-dir hdfs://localhost:9000/user/$(whoami)/arabic_nlp/data/processed \
    --hdfs

# Phase 3
spark-submit src/feature_engineering.py \
    --in-dir hdfs://localhost:9000/user/$(whoami)/arabic_nlp/data/processed \
    --out-dir data/features

# Modeling
spark-submit src/modeling.py

# MapReduce
python3 scripts/run_local_mapreduce.py

# Visualizations
python3 src/visualizations.py

# Scalability
python3 src/scalability_test.py --cores 1,2,4
```

### 9.5 - تشغيل البث (Streaming)

في **Terminal منفصل**:

```bash
# المنتج (يكتب رسائل إلى Kafka)
python3 -c "
import json, time, random
from kafka import KafkaProducer
producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode('utf-8')
)
samples = [
    'تتناول هذه الدراسة تحليل البيانات الضخمة...',
    'في هذا البحث، نقدم نهجاً جديداً...',
]
for i in range(20):
    record = {'text': random.choice(samples), 'true_label': random.choice([0, 1])}
    producer.send('arabic_abstracts', record)
    print(f'Sent: {record}')
    time.sleep(2)
producer.flush()
"
```

في Terminal آخر — تشغيل الـ consumer:

```bash
spark-submit \
    --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 \
    src/streaming_pipeline.py run \
    --source kafka \
    --kafka-servers localhost:9092 \
    --kafka-topic arabic_abstracts \
    --run-seconds 120
```

---

## الجزء 10: التقاط الـ Screenshots المطلوبة للتقرير

خذي صور للأمور التالية أثناء التشغيل:

1. ✅ **Terminal**: `jps` يظهر NameNode, DataNode, etc.
2. ✅ **Browser**: HDFS UI على `http://localhost:9870`
3. ✅ **Browser**: Spark UI أثناء تشغيل job (`http://localhost:4040`)
4. ✅ **Terminal**: `hdfs dfs -ls` يظهر ملفات Parquet في HDFS
5. ✅ **Terminal**: `spark-submit` أثناء التشغيل
6. ✅ **Terminal**: ZooKeeper + Kafka + Producer + Consumer (4 terminals مفتوحة)
7. ✅ **Terminal**: نتائج النماذج النهائية (المخرجات النصية)

ضعي كل الصور في مجلد `reports/screenshots/` وارفعيها على GitHub.

---

## استكشاف الأخطاء

### مشكلة: `command not found: hadoop`
```bash
source ~/.bashrc
which hadoop
```

### مشكلة: `port 9000 already in use`
```bash
sudo lsof -i :9000
sudo kill -9 <PID>
```

### مشكلة: `JAVA_HOME is not set`
```bash
echo $JAVA_HOME
# إذا فاضي:
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk
```

### مشكلة: HDFS لا يبدأ
```bash
# أعيدي تهيئة NameNode
stop-dfs.sh
rm -rf /opt/hadoop/data/namenode/*
hdfs namenode -format
start-dfs.sh
jps
```

### مشكلة: ImportError في Python
```bash
# فعّلي PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$(pwd)
```

---

## الملخص

عند الانتهاء، ستكون لديكِ:

- ✅ Hadoop HDFS شغال على `localhost:9000`
- ✅ Spark 3.5.0 جاهز للعمل
- ✅ Kafka topic `arabic_abstracts` يعمل
- ✅ كل ملفات Parquet في HDFS
- ✅ النماذج المدربة + النتائج
- ✅ Screenshots للتقرير

**وقت الإعداد المتوقع:** 3-5 ساعات (مع توقع مشاكل صغيرة).

---

## ملاحظات مهمة

1. **احفظي حالة VM** بعد كل خطوة كبيرة (Snapshot في VirtualBox)
2. **لا تغلقي Terminals** إذا كانت تشغّل Kafka أو ZooKeeper
3. **عند إعادة التشغيل**، يجب تشغيل Hadoop و Kafka يدوياً مرة أخرى:
   - `start-dfs.sh`
   - تشغيل ZooKeeper
   - تشغيل Kafka broker

بالتوفيق! 💪
