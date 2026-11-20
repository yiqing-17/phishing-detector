"""把外部語料（CSV）轉成本專案評估格式，並與既有資料集去重。

用法：
  python eval/import_external.py --csv nazario.csv --text-col body --label-col label \
      --label-map "phishing=1,ham=0" --split ext --out eval/dataset_ext.jsonl [--max 300]
然後：python eval/evaluate.py all（需改 load 指向）或 python eval/agent_ablation.py --dataset eval/dataset_ext.jsonl --split ext --live

去重：正規化文字（小寫、壓縮空白）的雜湊 + 前 200 字雜湊，對照 eval/*.jsonl 已有的信件。
注意：這不能保證與「ML 訓練集」無重疊；ML 層的洩漏請用 leakage_check.py。
來源建議（皆需自行下載並確認授權）：Nazario phishing corpus、SpamAssassin public corpus、
Enron（正常信）、PhishTank / OpenPhish（只有網址，可用於 URL 層評估）。
"""
import argparse
import glob
import hashlib
import json
import os
import re

import pandas as pd

HERE = os.path.dirname(__file__)


def norm(t):
    return re.sub(r'\s+', ' ', (t or '').lower()).strip()


def keys(t):
    n = norm(t)
    return hashlib.md5(n.encode()).hexdigest(), hashlib.md5(n[:200].encode()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--csv', required=True)
    ap.add_argument('--text-col', required=True)
    ap.add_argument('--label-col', required=True)
    ap.add_argument('--label-map', required=True, help='例：phishing=1,ham=0 或 1=1,0=0')
    ap.add_argument('--from-col', default=None)
    ap.add_argument('--split', default='ext')
    ap.add_argument('--out', required=True)
    ap.add_argument('--max', type=int, default=0, help='每個類別最多取幾封（0=不限）')
    a = ap.parse_args()

    lm = dict(p.split('=') for p in a.label_map.split(','))
    seen = set()
    for f in glob.glob(os.path.join(HERE, 'dataset*.jsonl')):
        if os.path.abspath(f) == os.path.abspath(a.out):
            continue
        for line in open(f, encoding='utf-8'):
            r = json.loads(line)
            seen.update(keys(r['text']))

    df = pd.read_csv(a.csv, on_bad_lines='skip')
    out, dup, per = [], 0, {0: 0, 1: 0}
    for i, row in df.iterrows():
        raw = str(row[a.label_col]).strip()
        if raw not in lm:
            continue
        lab = int(lm[raw])
        text = str(row[a.text_col] or '').strip()
        if len(text) < 30 or (a.max and per[lab] >= a.max):
            continue
        k1, k2 = keys(text)
        if k1 in seen or k2 in seen:
            dup += 1
            continue
        seen.update((k1, k2))
        per[lab] += 1
        out.append({'id': f'X{len(out)+1:05d}', 'label': lab, 'category': 'external', 'split': a.split,
                    'from': str(row[a.from_col]) if a.from_col else '', 'subject': '', 'body': text[:3000],
                    'text': text[:3000]})
    with open(a.out, 'w', encoding='utf-8') as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
    print(f'匯入 {len(out)} 封（正常 {per[0]} / 釣魚 {per[1]}），略過重複 {dup} 封 → {a.out}')


if __name__ == '__main__':
    main()
