"""量化 ML 層 98.4% 的「資料洩漏 / 近似重複」程度，並給出去洩漏後的成績。

為什麼要做：train_phishing_model.py 只用「完全相同文字」去重。公開釣魚語料常含同一封信的
轉寄、引用、換行不同版本，這些「近似重複」會讓 train/test 互相洩漏，準確率被高估。

做法（完全重現訓練腳本的清理與切分：test_size=0.2, random_state=42, stratify）：
  1. 對每封 test 信，找 train 裡 TF-IDF 餘弦相似度最高的一封（用已存的向量器）。
  2. 回報 max-sim >= 0.95 / 0.90 / 0.80 的比例。
  3. 把 test 依 max-sim 分層，分別算準確率。「novel」(<0.80) 那一層才接近真實泛化力。

用法：python eval/leakage_check.py --data dataset/phishing_email.csv
需要 dataset/phishing_email.csv（資料集本身不在 repo 內）與 models/*.joblib。
"""
import argparse
import os
import re
import sys

import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

ROOT = os.path.join(os.path.dirname(__file__), '..')


def load_clean(path):
    df = pd.read_csv(path, encoding='utf-8', on_bad_lines='skip')[['text_combined', 'label']].copy()
    df['text_combined'] = df['text_combined'].fillna('').astype(str)
    df['label'] = pd.to_numeric(df['label'], errors='coerce')
    df = df.dropna(subset=['label'])
    df['label'] = df['label'].astype(int)
    df = df[df['label'].isin([0, 1]) & df['text_combined'].str.strip().ne('')]
    df['text'] = df['text_combined'].map(lambda t: re.sub(r'\s+', ' ', t).strip())
    return df.drop_duplicates(subset=['text', 'label']).reset_index(drop=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', default=os.path.join(ROOT, 'dataset', 'phishing_email.csv'))
    ap.add_argument('--chunk', type=int, default=400)
    a = ap.parse_args()
    if not os.path.exists(a.data):
        sys.exit(f'找不到 {a.data}')
    model = joblib.load(os.path.join(ROOT, 'models', 'phishing_model.joblib'))
    vec = joblib.load(os.path.join(ROOT, 'models', 'phishing_tfidf.joblib'))

    df = load_clean(a.data)
    Xtr, Xte, ytr, yte = train_test_split(df['text'], df['label'], test_size=0.2,
                                          random_state=42, stratify=df['label'])
    Vtr, Vte = vec.transform(Xtr), vec.transform(Xte)
    pred = model.predict(Vte)
    yte = yte.to_numpy()
    ytr = ytr.to_numpy()

    # TF-IDF 向量已 L2 正規化 → 內積即餘弦相似度
    best = np.zeros(Vte.shape[0])
    best_same_label = np.zeros(Vte.shape[0], dtype=bool)
    VtrT = Vtr.T.tocsc()
    for i in range(0, Vte.shape[0], a.chunk):
        sims = (Vte[i:i + a.chunk] @ VtrT).toarray()
        j = sims.argmax(axis=1)
        best[i:i + a.chunk] = sims[np.arange(len(j)), j]
        best_same_label[i:i + a.chunk] = ytr[j] == yte[i:i + a.chunk]

    n = len(yte)
    print(f'test n={n}；整體 accuracy = {(pred == yte).mean():.4f}')
    for t in (0.95, 0.90, 0.80):
        m = best >= t
        print(f'  與 train 最相似 >= {t:.2f} 的 test 信：{m.sum()} 封（{m.mean():.1%}）')
    bins = [(0.95, 1.01, '近乎重複 (>=0.95)'), (0.80, 0.95, '高度相似 (0.80-0.95)'), (0.0, 0.80, '新穎 (<0.80)')]
    print('\n分層準確率：')
    for lo, hi, name in bins:
        m = (best >= lo) & (best < hi)
        if m.sum():
            print(f'  {name:<22} n={m.sum():>6}  accuracy={(pred[m] == yte[m]).mean():.4f}')
    nov = best < 0.80
    if nov.sum():
        print(f"\n去洩漏後（只算新穎層）accuracy = {(pred[nov] == yte[nov]).mean():.4f}，"
              f"n={nov.sum()}（原 {(pred == yte).mean():.4f}）→ 報告請引用此數字或並列兩者。")


if __name__ == '__main__':
    main()
