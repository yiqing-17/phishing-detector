"""用「真實詐騙網域清單」評估系統的網址層（URL-level），資料來源以 165 開放資料為主。

為什麼是網址層：165 / PhishTank 類資料只有「網址」，沒有信件本文。誠實的做法不是替它們
編造信件，而是用「中性載體信」（只有一句話 + 該網址）檢驗：光靠網址特徵，系統能抓到多少？

資料來源（政府資料開放授權條款第 1 版，可自由使用，需標示來源）：
  * data.gov.tw/dataset/176455  165反詐騙諮詢專線_遭停止解析涉詐網站（欄位：民國年月、網域、網站性質…）
  * data.gov.tw/dataset/160055  165反詐騙諮詢專線_假投資(博弈)網站（欄位：網站名稱、網址、件數…）
  下載 CSV 後：
      python eval/url_eval.py --scam-csv 165_stopped.csv --limit 200
  正例 = 詐騙網域；負例 = 內建的常見正當網域（可用 --benign-file 換成你自己的，一行一個網域）。

輸出：Recall / 誤報率（含 Wilson 95% CI）、各網址特徵命中次數、並可 --emit 產生
      eval/dataset_url.jsonl，餵給 agent_ablation.py --live 做 domain_age/dns 的真實實驗。

誠實的限制（解讀時必讀）：
  1. 165 清單的網域多半「已被停止解析」→ DNS 查不到，Agent 的 no_dns 會對每一筆觸發，
     這是清單性質造成的，不是偵測力；domain_age（RDAP）才較有意義。
  2. 清單是「已被舉報／已被處置」的網域，偏向容易被發現的那一類（倖存者偏差）。
  3. 中性載體信沒有任何詐騙話術，所以這測的是「網址本身」；真實信件同時有話術與網址，
     分數通常更高。把這裡的 Recall 當成「網址特徵的下限」而非整體 Recall。
"""
import argparse
import csv
import json
import math
import os
import random
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import analysis  # noqa: E402

HERE = os.path.dirname(__file__)
CARRIERS = [
    '您好，請參考以下連結了解詳情：{u}',
    '通知：請至 {u} 查看內容。',
    'Hi, please see the details here: {u}',
]
BENIGN = ['www.google.com', 'www.youtube.com', 'www.facebook.com', 'www.momoshop.com.tw', 'shopee.tw', 'www.pchome.com.tw',
          'www.books.com.tw', 'www.ruten.com.tw', 'tw.yahoo.com', 'www.cathaybk.com.tw', 'www.esunbank.com.tw', 'www.ctbcbank.com',
          'www.post.gov.tw', 'www.nhi.gov.tw', 'www.etax.nat.gov.tw', 'www.einvoice.nat.gov.tw', 'www.ntu.edu.tw',
          'www.nthu.edu.tw', 'www.nycu.edu.tw', 'www.ncku.edu.tw', 'github.com', 'www.apple.com', 'www.microsoft.com',
          'www.amazon.com', 'www.netflix.com', 'zh.wikipedia.org', 'www.104.com.tw', 'www.pxmart.com.tw', 'www.7-11.com.tw',
          'www.family.com.tw', 'www.t-cat.com.tw', 'www.evaair.com', 'www.china-airlines.com', 'www.taiwanrailways.com',
          'www.thsrc.com.tw', 'www.cwb.gov.tw', 'www.ithome.com.tw', 'www.ettoday.net', 'www.udn.com', 'www.ltn.com.tw']
DOMAIN_COLS = ('網域', '網址', 'domain', 'url', 'host', '網站網址', '網站')
HOST_RE = re.compile(r'^[A-Za-z0-9][A-Za-z0-9\-\.]*\.[A-Za-z]{2,}$')


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (max(0.0, (c - h) / d), min(1.0, (c + h) / d))


def read_domains(path):
    out = []
    with open(path, encoding='utf-8-sig', newline='') as f:
        rd = csv.DictReader(f)
        col = next((c for c in (rd.fieldnames or []) if c and c.strip().lower() in DOMAIN_COLS), None)
        if not col:
            sys.exit(f'找不到網域欄位；欄位為 {rd.fieldnames}，請用 --col 指定')
        for r in rd:
            v = (r.get(col) or '').strip()
            v = re.sub(r'^https?://', '', v, flags=re.I).split('/')[0].split(':')[0].lower()
            if HOST_RE.match(v):
                out.append(v)
    return list(dict.fromkeys(out))   # 去重、保序


def build(scam, benign, seed=7):
    rnd = random.Random(seed)
    rows = []
    for lab, hosts, tag in ((1, scam, 'S'), (0, benign, 'B')):
        for i, h in enumerate(hosts, 1):
            url = f'https://{h}/'
            body = rnd.choice(CARRIERS).format(u=url)
            rows.append({'id': f'U{tag}{i:04d}', 'label': lab, 'category': 'url_scam' if lab else 'url_benign',
                         'split': 'url', 'from': '', 'subject': '', 'body': body,
                         'text': f'From: \nSubject: \nBody: {body}', 'host': h})
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--scam-csv', required=True)
    ap.add_argument('--benign-file', default=None)
    ap.add_argument('--limit', type=int, default=0, help='詐騙網域最多取幾筆（隨機抽樣，固定 seed）')
    ap.add_argument('--emit', action='store_true', help='輸出 eval/dataset_url.jsonl 供 agent_ablation 使用')
    a = ap.parse_args()
    scam = read_domains(a.scam_csv)
    benign = [l.strip() for l in open(a.benign_file, encoding='utf-8')] if a.benign_file else BENIGN
    benign = [b for b in benign if b and b not in scam]
    if a.limit and len(scam) > a.limit:
        scam = random.Random(7).sample(scam, a.limit)
    rows = build(scam, benign)
    analysis.groq_client = None
    sc = {'tp': 0, 'fn': 0, 'fp': 0, 'tn': 0}
    hits = {0: Counter(), 1: Counter()}
    miss, fps = [], []
    for r in rows:
        rep = analysis.full_pipeline(r['text'], sender='')[0]
        pos = rep['risk_score'] >= 40
        key = ('tp' if pos else 'fn') if r['label'] else ('fp' if pos else 'tn')
        sc[key] += 1
        for f in analysis.rule_based_score(r['text'])[1]:
            hits[r['label']][f[:28]] += 1
        (miss if key == 'fn' else fps if key == 'fp' else []).append((r['host'], rep['risk_score']))
    P, N = sc['tp'] + sc['fn'], sc['fp'] + sc['tn']
    lo, hi = wilson(sc['tp'], P)
    flo, fhi = wilson(sc['fp'], N)
    print(f"詐騙網域 {P} 筆、正當網域 {N} 筆；門檻 40；載體信僅含網址")
    print(f"網址層 Recall = {sc['tp']/max(1,P):.2f}（95%CI {lo:.2f}–{hi:.2f}）   誤報率 = {sc['fp']/max(1,N):.2f}（95%CI {flo:.2f}–{fhi:.2f}）")
    print('詐騙網域命中的規則（前 8）：', hits[1].most_common(8))
    print('正當網域命中的規則（前 5）：', hits[0].most_common(5))
    print('漏掉的詐騙網域（前 10）：', miss[:10])
    print('誤報的正當網域：', fps[:10])
    print('※ 解讀前請讀本檔開頭的「誠實的限制」。')
    if a.emit:
        out = os.path.join(HERE, 'dataset_url.jsonl')
        with open(out, 'w', encoding='utf-8') as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + '\n')
        print('已輸出', out, '→ python eval/agent_ablation.py --dataset', out, '--split url --live')


if __name__ == '__main__':
    main()
