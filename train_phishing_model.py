"""Train the V5 phishing-email text classifier.

Input:
    dataset/phishing_email.csv
Columns:
    text_combined : email subject/body text
    label         : 0 = legitimate, 1 = phishing

Output:
    models/phishing_model.joblib
    models/phishing_tfidf.joblib
    models/phishing_metrics.json
"""
import json
import os
import re
import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, classification_report

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "dataset", "phishing_email.csv")
MODEL_DIR = os.path.join(BASE_DIR, "models")
os.makedirs(MODEL_DIR, exist_ok=True)

if not os.path.exists(DATA_PATH):
    raise FileNotFoundError(
        f"找不到資料集：{DATA_PATH}\n"
        "請先下載 Phishing Email Dataset，並放到 dataset/phishing_email.csv"
    )

print("[1/6] 載入資料集...")
df = pd.read_csv(DATA_PATH, encoding="utf-8", on_bad_lines="skip")
required = {"text_combined", "label"}
if not required.issubset(df.columns):
    raise ValueError(f"資料集需要欄位 {required}，目前欄位：{list(df.columns)}")

df = df[["text_combined", "label"]].copy()
df["text_combined"] = df["text_combined"].fillna("").astype(str)
df["label"] = pd.to_numeric(df["label"], errors="coerce")
df = df.dropna(subset=["label"])
df["label"] = df["label"].astype(int)
df = df[df["label"].isin([0, 1])]
df = df[df["text_combined"].str.strip().ne("")]

def clean_text(text):
    text = re.sub(r"\s+", " ", text)
    return text.strip()

df["text"] = df["text_combined"].map(clean_text)
df = df.drop_duplicates(subset=["text", "label"]).reset_index(drop=True)

print(f"資料筆數：{len(df):,}")
print(f"合法信件：{(df.label == 0).sum():,}")
print(f"釣魚信件：{(df.label == 1).sum():,}")

print("[2/6] 切分訓練集 / 測試集...")
X_train, X_test, y_train, y_test = train_test_split(
    df["text"], df["label"],
    test_size=0.2,
    random_state=42,
    stratify=df["label"]
)

print("[3/6] TF-IDF 特徵轉換...")
vectorizer = TfidfVectorizer(
    max_features=5000,
    ngram_range=(1, 2),
    min_df=2,
    sublinear_tf=True,
    stop_words="english"
)
X_train_vec = vectorizer.fit_transform(X_train)
X_test_vec = vectorizer.transform(X_test)

print("[4/6] 訓練 Logistic Regression...")
model = LogisticRegression(
    C=10,
    max_iter=2000,
    class_weight="balanced",
    random_state=42
)
model.fit(X_train_vec, y_train)

print("[5/6] 評估模型...")
pred = model.predict(X_test_vec)
prob = model.predict_proba(X_test_vec)[:, list(model.classes_).index(1)]
cm = confusion_matrix(y_test, pred, labels=[0, 1])
metrics = {
    "dataset": "Phishing Email Dataset",
    "dataset_rows_after_cleaning": int(len(df)),
    "train_rows": int(len(X_train)),
    "test_rows": int(len(X_test)),
    "features": int(X_train_vec.shape[1]),
    "model": "TF-IDF + Logistic Regression",
    "positive_label": "1 = phishing",
    "accuracy": round(float(accuracy_score(y_test, pred)), 6),
    "precision": round(float(precision_score(y_test, pred, zero_division=0)), 6),
    "recall": round(float(recall_score(y_test, pred, zero_division=0)), 6),
    "f1": round(float(f1_score(y_test, pred, zero_division=0)), 6),
    "confusion_matrix": cm.tolist(),
    "classification_report": classification_report(y_test, pred, output_dict=True, zero_division=0)
}

print(classification_report(y_test, pred, target_names=["legitimate", "phishing"], zero_division=0))
print("Confusion Matrix:")
print(cm)

print("[6/6] 儲存模型...")
joblib.dump(model, os.path.join(MODEL_DIR, "phishing_model.joblib"), compress=3)
joblib.dump(vectorizer, os.path.join(MODEL_DIR, "phishing_tfidf.joblib"), compress=3)
with open(os.path.join(MODEL_DIR, "phishing_metrics.json"), "w", encoding="utf-8") as f:
    json.dump(metrics, f, ensure_ascii=False, indent=2)

print("\n完成！")
print(f"Model: {os.path.join(MODEL_DIR, 'phishing_model.joblib')}")
print(f"Vectorizer: {os.path.join(MODEL_DIR, 'phishing_tfidf.joblib')}")
print(f"Metrics: {os.path.join(MODEL_DIR, 'phishing_metrics.json')}")
print(f"F1 = {metrics['f1']:.4f}, Recall = {metrics['recall']:.4f}")
