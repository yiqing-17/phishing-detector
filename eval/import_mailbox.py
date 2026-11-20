"""把「你自己信箱裡的垃圾信 / 釣魚信」去識別化後，轉成可評估的真實樣本。

兩步驟（人工標註不可省略——垃圾郵件資料夾 ≠ 釣魚信）：
  1) ingest：讀 .eml 資料夾或 .mbox → 去識別化 → 產生 待標註 jsonl + 標註表 CSV
       python eval/import_mailbox.py ingest --src ~/spam_eml/ --my-names "王小明,小明" \
           --my-emails "me@gmail.com,me@school.edu.tw" --max 80
  2) 用 Excel 打開 eval/real_label_sheet.csv，在 kind 欄填：
         phish  = 詐騙／釣魚（含假冒、索資料、誘導匯款、惡意連結）
         spam   = 一般廣告垃圾信（不是詐騙）
         benign = 正常信（建議也放一些：電子報、帳單、收據，才有誤報率）
         留空   = 不採用
  3) merge：套用標註 → eval/dataset_real.jsonl
       python eval/import_mailbox.py merge          # spam 預設排除；加 --spam-as-negative 才當負例
  4) 評估：python eval/evaluate.py real
            python eval/agent_ablation.py --dataset eval/dataset_real.jsonl --split real --live

如何取得 .eml：Gmail 開啟信件 → 右上「⋮」→「顯示原始郵件」→「下載原始郵件」；
或 Google Takeout 匯出標籤「垃圾郵件」「收件匣」得到 .mbox。
標頭（Authentication-Results 等）會保留，Agent 的 check_auth_headers 才有東西可查。

去識別化範圍（務必人工再看一遍標註表與 jsonl 才分享／上傳）：
  收件者信箱與姓名（--my-emails / --my-names）、其他個人信箱的帳號部分、身分證字號、
  信用卡號、手機與市話末碼、網址的查詢字串與長 token。
  寄件者網域、主旨與正文語意「刻意保留」——那正是偵測要用的特徵。
注意：不要把含他人隱私的「正常信」放進公開 repo；公開前請只留你確認已去識別化的樣本。
"""
import argparse
import csv
import glob
import hashlib
import json
import mailbox
import os
import re
import sys
from email import policy
from email.parser import BytesParser

HERE = os.path.dirname(__file__)
PENDING = os.path.join(HERE, 'real_pending.jsonl')
SHEET = os.path.join(HERE, 'real_label_sheet.csv')

EMAIL_RE = re.compile(r'[\w.+\-]+@[\w\-]+(?:\.[\w\-]+)+')
URL_RE = re.compile(r'https?://[^\s<>"\'）)】\]]+', re.I)
TW_ID_RE = re.compile(r'\b[A-Z][12]\d{8}\b')
CARD_RE = re.compile(r'\b(?:\d[ -]?){13,19}\b')
MOBILE_RE = re.compile(r'\b(09\d{2})[- ]?(\d{3})[- ]?(\d{3})\b')
LAND_RE = re.compile(r'\b(0\d{1,2})[- ]?(\d{3,4})[- ]?(\d{3,4})\b')


def _clean_url(m):
    u = m.group(0)
    u = re.sub(r'[?#].*$', '', u)                              # 去查詢字串 / 片段（常含收件者 token）
    u = re.sub(r'/[A-Za-z0-9_\-]{25,}', '/…', u)               # 長路徑 token
    return u


def deidentify(text, names=(), my_emails=(), keep_addrs=()):
    n = {'recipient': 0, 'email': 0, 'id': 0, 'card': 0, 'phone': 0, 'url': 0}
    mine = {e.lower() for e in my_emails}
    keep = {k.lower() for k in keep_addrs}

    def em(m):
        a = m.group(0)
        if a.lower() in mine:
            n['recipient'] += 1
            return 'recipient@example.invalid'
        if a.lower() in keep:
            return a
        n['email'] += 1
        user, dom = a.split('@', 1)
        return f'{user[:1]}***@{dom}'

    t = text or ''
    t = URL_RE.sub(lambda m: (n.__setitem__('url', n['url'] + 1), _clean_url(m))[1], t)
    t = EMAIL_RE.sub(em, t)
    for nm in sorted((x for x in names if x), key=len, reverse=True):
        c = len(re.findall(re.escape(nm), t))
        if c:
            n['recipient'] += c
            t = t.replace(nm, '〔收件人〕')
    t = TW_ID_RE.sub(lambda m: (n.__setitem__('id', n['id'] + 1), m.group(0)[:2] + 'XXXXXXXX')[1], t)
    t = CARD_RE.sub(lambda m: (n.__setitem__('card', n['card'] + 1), 'XXXX-XXXX-XXXX-XXXX')[1], t)
    t = MOBILE_RE.sub(lambda m: (n.__setitem__('phone', n['phone'] + 1), m.group(1) + '-XXX-XXX')[1], t)
    t = LAND_RE.sub(lambda m: (n.__setitem__('phone', n['phone'] + 1), m.group(1) + '-XXXX-XXXX')[1], t)
    return t, n


def _iter_messages(src):
    if os.path.isdir(src):
        for f in sorted(glob.glob(os.path.join(src, '**', '*.eml'), recursive=True)):
            with open(f, 'rb') as fh:
                yield os.path.basename(f), BytesParser(policy=policy.default).parse(fh)
    elif src.lower().endswith('.mbox'):
        for i, m in enumerate(mailbox.mbox(src, factory=lambda fh: BytesParser(policy=policy.default).parse(fh))):
            yield f'mbox#{i}', m
    else:
        with open(src, 'rb') as fh:
            yield os.path.basename(src), BytesParser(policy=policy.default).parse(fh)


def _body(msg, kind):
    part = msg.get_body(preferencelist=(kind,))
    if not part:
        return ''
    try:
        return part.get_content()
    except Exception:
        return ''


def ingest(a):
    from bs4 import BeautifulSoup
    names = [x.strip() for x in a.my_names.split(',') if x.strip()]
    mine = [x.strip() for x in a.my_emails.split(',') if x.strip()]
    rows, seen, stats = [], set(), {'recipient': 0, 'email': 0, 'id': 0, 'card': 0, 'phone': 0, 'url': 0}
    for fname, msg in _iter_messages(a.src):
        if a.max and len(rows) >= a.max:
            break
        plain, html = _body(msg, 'plain'), _body(msg, 'html')
        if not plain and html:
            plain = BeautifulSoup(html, 'html.parser').get_text(' ', strip=True)
        plain = re.sub(r'\s+', ' ', plain or '').strip()[:5000]
        if len(plain) < 30:
            continue
        h = hashlib.md5(plain[:300].lower().encode()).hexdigest()
        if h in seen:
            continue
        seen.add(h)
        frm = str(msg.get('From', ''))
        keep = EMAIL_RE.findall(frm) + EMAIL_RE.findall(str(msg.get('Reply-To', '')))
        subj = str(msg.get('Subject', ''))
        hdr_raw = {'From': frm, 'Reply-To': str(msg.get('Reply-To', '')), 'Return-Path': str(msg.get('Return-Path', '')),
                   'Authentication-Results': '; '.join(str(v) for v in msg.get_all('Authentication-Results', []))}
        out = {}
        for k, v in {'from': frm, 'subject': subj, 'body': plain, 'html': (html or '')[:20000]}.items():
            out[k], n = deidentify(v, names, mine, keep)
            for kk in stats:
                stats[kk] += n[kk]
        headers = {}
        for k, v in hdr_raw.items():
            headers[k], _ = deidentify(v, names, mine, keep)
        rid = f'R{len(rows)+1:04d}'
        rows.append({'id': rid, 'label': None, 'category': 'real', 'split': 'real', 'from': out['from'],
                     'subject': out['subject'], 'body': out['body'], 'html': out['html'], 'headers': headers,
                     'text': f"From: {out['from']}\nSubject: {out['subject']}\nBody: {out['body']}", 'src': fname})
    with open(PENDING, 'w', encoding='utf-8') as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
    with open(SHEET, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f)
        w.writerow(['id', 'kind(phish/spam/benign)', 'from', 'subject', 'snippet', 'note'])
        for r in rows:
            w.writerow([r['id'], '', r['from'][:60], r['subject'][:60], r['body'][:120], ''])
    print(f'讀入 {len(rows)} 封 → {PENDING}\n標註表 → {SHEET}')
    print('去識別化替換次數：' + '、'.join(f'{k}={v}' for k, v in stats.items()))
    print('下一步：用 Excel 填 kind 欄，並人工檢視 jsonl 是否仍有個資，然後執行 merge。')


def merge(a):
    kinds = {}
    with open(SHEET, encoding='utf-8-sig', newline='') as f:
        for row in csv.reader(f):
            if row and row[0].startswith('R'):
                kinds[row[0]] = (row[1] if len(row) > 1 else '').strip().lower()
    out, cnt = [], {'phish': 0, 'benign': 0, 'spam': 0, 'skip': 0}
    for line in open(PENDING, encoding='utf-8'):
        r = json.loads(line)
        k = kinds.get(r['id'], '')
        if k == 'phish':
            r['label'] = 1
        elif k == 'benign' or (k == 'spam' and a.spam_as_negative):
            r['label'] = 0
        else:
            cnt['spam' if k == 'spam' else 'skip'] += 1
            continue
        r['category'] = {'phish': 'real_phish', 'benign': 'real_benign', 'spam': 'real_spam'}[k]
        cnt[k] += 1
        out.append(r)
    path = os.path.join(HERE, 'dataset_real.jsonl')
    with open(path, 'w', encoding='utf-8') as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
    print(f"採用 {len(out)} 封：釣魚 {cnt['phish']}、正常 {cnt['benign']}、spam {cnt['spam']}"
          f"（{'當負例' if a.spam_as_negative else '已排除'}）；未標註略過 {cnt['skip']} → {path}")
    if cnt['phish'] < 20 or (cnt['benign'] + (cnt['spam'] if a.spam_as_negative else 0)) < 20:
        print('⚠ 釣魚或負例少於 20 封：只能當「案例檢視」，不能算比率；報告請逐封列出而非給 Recall/誤報率。')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest='cmd', required=True)
    i = sp.add_parser('ingest')
    i.add_argument('--src', required=True)
    i.add_argument('--my-names', default='')
    i.add_argument('--my-emails', default='')
    i.add_argument('--max', type=int, default=0)
    m = sp.add_parser('merge')
    m.add_argument('--spam-as-negative', action='store_true')
    a = ap.parse_args()
    ingest(a) if a.cmd == 'ingest' else merge(a)
