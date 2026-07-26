# ============================================================
# AI 釣魚信件偵測系統 - Flask 網頁版 v2（優化版）
# 優化項目：
#   1. 非同步掃描 + Loading 畫面
#   2. 使用者可自訂白名單
#   3. 掃描歷史記錄
#   4. 高風險 Email 通知
# ============================================================

import json, os, uuid, threading, base64, re, pickle, sqlite3, smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from groq import Groq
from bs4 import BeautifulSoup
from flask import Flask, redirect, request, render_template_string, jsonify
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# ── 設定區 ───────────────────────────────────────────────────
GROQ_API_KEY = 'gsk_填入你的key'
MY_EMAIL     = 'sherry940501@gmail.com'
BASE_URL     = 'https://phishing-detector-n8rv.onrender.com'
SCOPES       = ['https://www.googleapis.com/auth/gmail.readonly']

# ── 預設白名單 ───────────────────────────────────────────────
DEFAULT_WHITELIST = [
    'skims.com', 'emails.skims.com', 'links.skims.com',
    'lululemon.com', 'email.lululemon.com', 'e.lululemon.com',
    'aloyoga.com', 'email.aloyoga.com',
    'esunbank.com.tw', 'esun.com.tw', 'esunsec.com.tw',
    'google.com', 'accounts.google.com', 'googlemail.com',
]

SKIP_SUBJECTS = ['[警告]', '[正常]', 'AI 釣魚偵測報告', 'AI 釣魚信件偵測報告']

# ── Google OAuth 憑證 ────────────────────────────────────────
CRED_DATA = {"web":{"client_id":"727861534469-72ihfsri6r9kpnu56n7541qb2e4ngomk.apps.googleusercontent.com","project_id":"phishing-detector-494720","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_secret":"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","redirect_uris":["https://phishing-detector-n8rv.onrender.com/callback"]}}

with open('credentials.json', 'w') as f:
    json.dump(CRED_DATA, f)

# ── 資料庫初始化 ─────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect('phishing.db')
    c = conn.cursor()
    # 掃描歷史
    c.execute('''CREATE TABLE IF NOT EXISTS scan_history (
        id TEXT PRIMARY KEY,
        scan_time TEXT,
        total INTEGER,
        high INTEGER,
        medium INTEGER,
        low INTEGER,
        whitelist INTEGER,
        skipped INTEGER
    )''')
    # 掃描結果
    c.execute('''CREATE TABLE IF NOT EXISTS scan_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        scan_id TEXT,
        sender TEXT,
        subject TEXT,
        risk_level TEXT,
        risk_score INTEGER,
        category TEXT,
        explanation TEXT,
        recommended_action TEXT
    )''')
    # 白名單
    c.execute('''CREATE TABLE IF NOT EXISTS whitelist (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        domain TEXT UNIQUE,
        added_time TEXT
    )''')
    # 加入預設白名單
    for domain in DEFAULT_WHITELIST:
        try:
            c.execute('INSERT OR IGNORE INTO whitelist (domain, added_time) VALUES (?, ?)',
                     (domain, datetime.now().isoformat()))
        except: pass
    conn.commit()
    conn.close()

init_db()

# ── 工具函式 ─────────────────────────────────────────────────
def get_whitelist():
    conn = sqlite3.connect('phishing.db')
    c = conn.cursor()
    c.execute('SELECT domain FROM whitelist')
    domains = [row[0] for row in c.fetchall()]
    conn.close()
    return domains

def is_whitelisted(sender):
    domains = get_whitelist()
    s = sender.lower()
    return any(domain in s for domain in domains)

def is_system_report(sender, subject):
    if any(kw in subject for kw in SKIP_SUBJECTS): return True
    if MY_EMAIL in sender and any(kw in subject for kw in ['釣魚','警告','偵測']): return True
    return False

def save_scan(scan_id, scan_time, results, high, med, low, whitelist_count, skipped):
    conn = sqlite3.connect('phishing.db')
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO scan_history VALUES (?,?,?,?,?,?,?,?)',
             (scan_id, scan_time, len(results)+whitelist_count+skipped,
              len(high), len(med), len(low), whitelist_count, skipped))
    for e in high + med + low:
        c.execute('INSERT INTO scan_results (scan_id,sender,subject,risk_level,risk_score,category,explanation,recommended_action) VALUES (?,?,?,?,?,?,?,?)',
                 (scan_id, e['sender'], e['subject'], e['risk_level'],
                  e['risk_score'], e['category'], e['explanation'], e['recommended_action']))
    conn.commit()
    conn.close()

def get_history():
    conn = sqlite3.connect('phishing.db')
    c = conn.cursor()
    c.execute('SELECT * FROM scan_history ORDER BY scan_time DESC LIMIT 20')
    rows = c.fetchall()
    conn.close()
    return rows

def send_alert_email(high_emails):
    """發現高風險信件時寄送 Email 通知"""
    if not high_emails: return
    try:
        # 使用 Gmail SMTP（需要在 Render 設定環境變數）
        smtp_user = os.environ.get('SMTP_USER', '')
        smtp_pass = os.environ.get('SMTP_PASS', '')
        if not smtp_user or not smtp_pass: return

        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = MY_EMAIL
        msg['Subject'] = f'[警告] 發現 {len(high_emails)} 封高風險信件 - AI 釣魚偵測系統'

        body = f'掃描時間：{datetime.now().strftime("%Y-%m-%d %H:%M")}\n\n'
        body += f'發現 {len(high_emails)} 封高風險信件：\n\n'
        for i, e in enumerate(high_emails, 1):
            body += f'[{i}] {e["subject"]}\n'
            body += f'    寄件者：{e["sender"]}\n'
            body += f'    風險分數：{e["risk_score"]}/100\n'
            body += f'    說明：{e["explanation"]}\n\n'

        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
    except Exception as e:
        print(f'Email 通知失敗：{e}')

# ── ML 模型 ──────────────────────────────────────────────────
print('載入資料集並訓練模型...')
url = 'https://raw.githubusercontent.com/justmarkham/pycon-2016-tutorial/master/data/sms.tsv'
df = pd.read_csv(url, sep='\t', header=None, names=['label', 'text'])
X_train, X_test, y_train, y_test = train_test_split(
    df['text'], df['label'], test_size=0.2, random_state=42, stratify=df['label'])
vectorizer = TfidfVectorizer(max_features=3000, stop_words='english')
X_train_vec = vectorizer.fit_transform(X_train)
model = LogisticRegression(max_iter=1000, random_state=42)
model.fit(X_train_vec, y_train)
print('OK - ML 模型訓練完成')

groq_client = Groq(api_key=GROQ_API_KEY)

# ── 分析函式 ─────────────────────────────────────────────────
def rule_based_score(text):
    score = 0; triggered = []; t = text.lower()
    urgent = ['urgent','immediately','expire','suspended','verify now','act now',
              '立即','緊急','即將停用','馬上','限時','暫停','停用']
    hits = [w for w in urgent if w in t]
    if hits: score += len(hits)*2; triggered.append(f'緊急語句: {hits}')
    urls = re.findall(r'http[s]?://\S+', t)
    if urls: score += 3; triggered.append(f'含有連結: {urls[:2]}')
    for url in urls:
        for d in ['xyz','biz','click','login-','secure-','verify','update','account-','bank-']:
            if d in url: score += 3; triggered.append(f'可疑網域: {url}'); break
    bait = ['free','winner','won','prize','claim','lucky','reward','gift',
            '中獎','免費','領取','恭喜','退款','補助']
    hits2 = [w for w in bait if w in t]
    if hits2: score += len(hits2)*2; triggered.append(f'誘騙話術: {hits2}')
    personal = ['password','credit card','bank account','pin',
                '密碼','帳號','信用卡','身分證','帳戶']
    hits3 = [w for w in personal if w in t]
    if hits3: score += len(hits3)*3; triggered.append(f'索取個資: {hits3}')
    money = ['$','cash','money','transfer','wire','payment','invoice',
             '匯款','轉帳','付款','NT$','退款']
    hits4 = [w for w in money if w in t]
    if hits4: score += len(hits4)*2; triggered.append(f'金錢相關: {hits4}')
    return score, triggered

def ai_agent_analyze(text, rule_score, triggered_rules):
    rules_str = ', '.join(triggered_rules) if triggered_rules else 'none'
    prompt = (
        "You are a cybersecurity analyst. Analyze this message and reply ONLY with JSON.\n"
        f"Message: {text}\nRule score: {rule_score}, Triggered: {rules_str}\n"
        'JSON: {"risk_level":"high/medium/low","risk_score":0-100,'
        '"category":"釣魚信件/詐騙簡訊/正常信件/商業詐騙",'
        '"suspicious_points":["點1","點2"],'
        '"explanation":"繁體中文2-3句說明",'
        '"recommended_action":"繁體中文建議"}'
    )
    try:
        resp = groq_client.chat.completions.create(
            model='llama-3.3-70b-versatile',
            messages=[{'role': 'user', 'content': prompt}],
            temperature=0.2)
        raw = resp.choices[0].message.content.strip().replace('```json','').replace('```','').strip()
        return json.loads(raw)
    except Exception as e:
        return {'risk_level': 'low', 'risk_score': 0, 'category': '分析失敗',
                'suspicious_points': [], 'explanation': str(e),
                'recommended_action': '請手動檢查'}

def analyze_html(html_content):
    findings = []; score = 0
    soup = BeautifulSoup(html_content, 'html.parser')
    links = soup.find_all('a', href=True)
    for link in links:
        href = link.get('href', '')
        for d in ['xyz','biz','secure-','login-','verify']:
            if d in href.lower():
                score += 3; findings.append(('可疑連結', [href[:50]])); break
    imgs = soup.find_all('img')
    trackers = []
    for img in imgs:
        if str(img.get('width', '')) in ['1', '0']:
            trackers.append(img.get('src', '')[:50]); score += 2
    if trackers: findings.append(('像素追蹤', trackers[:2]))
    hidden = soup.find_all(style=re.compile(r'display\s*:\s*none', re.I))
    if hidden: findings.append(('隱藏元素', [f'{len(hidden)} 個'])); score += 3
    brand_keywords = ['paypal','microsoft','apple','amazon','facebook','netflix']
    found = [b for b in brand_keywords if b in soup.get_text().lower()]
    if found: findings.append(('品牌偵測', [', '.join(found)])); score += 4
    return score, findings

def full_multimodal_pipeline(text, html=''):
    score, rules = rule_based_score(text)
    vec = vectorizer.transform([text])
    spam_prob = model.predict_proba(vec)[0][list(model.classes_).index('spam')]
    html_score = 0; html_findings = []
    if html: html_score, html_findings = analyze_html(html)
    total = score + (html_score // 2)
    needs_ai = total >= 4 or spam_prob >= 0.3
    if needs_ai:
        report = ai_agent_analyze(text, total, rules)
    else:
        report = {'risk_level': 'low', 'risk_score': int(spam_prob * 100),
                  'category': '正常信件', 'explanation': '安全信件',
                  'recommended_action': '可安全閱讀', 'suspicious_points': []}
    for cat, items in html_findings:
        for item in items:
            report['suspicious_points'].append(f'[HTML] {cat}: {item}')
    return report, html_score, html_findings

def generate_incident_report(email_data, report):
    now = datetime.now()
    incident_id = f"IR-{now.strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"
    prompt = (
        "You are a cybersecurity analyst. Reply ONLY with JSON.\n"
        f"Email from: {email_data['sender']}\nSubject: {email_data['subject']}\n"
        f"Risk: {report['risk_score']}/100, Category: {report['category']}\n"
        'JSON: {"severity":"Critical/High/Medium","attack_type":"str",'
        '"impact_assessment":"繁體中文",'
        '"immediate_actions":["1","2","3"]}'
    )
    try:
        resp = groq_client.chat.completions.create(
            model='llama-3.3-70b-versatile',
            messages=[{'role': 'user', 'content': prompt}], temperature=0.2)
        raw = resp.choices[0].message.content.strip().replace('```json','').replace('```','').strip()
        ir = json.loads(raw)
    except:
        ir = {'severity': 'High', 'attack_type': 'Phishing',
              'impact_assessment': '可能導致個資外洩或財務損失',
              'immediate_actions': ['不要點擊連結', '不要提供個資', '向資安人員通報']}
    return incident_id, '', ir

def get_header(msg, name):
    for h in msg['payload']['headers']:
        if h['name'].lower() == name.lower(): return h['value']
    return ''

def get_email_body(msg):
    body = ''
    if 'parts' in msg['payload']:
        for part in msg['payload']['parts']:
            if part['mimeType'] == 'text/plain':
                data = part['body'].get('data', '')
                if data: body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore'); break
    else:
        data = msg['payload']['body'].get('data', '')
        if data: body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
    return body[:500]

def get_email_html(msg):
    html = ''
    if 'parts' in msg['payload']:
        for part in msg['payload']['parts']:
            if part['mimeType'] == 'text/html':
                data = part['body'].get('data', '')
                if data: html = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore'); break
            if 'parts' in part:
                for sub in part['parts']:
                    if sub['mimeType'] == 'text/html':
                        data = sub['body'].get('data', '')
                        if data: html = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore'); break
    return html

# ── HTML 模板 ────────────────────────────────────────────────

<h2 class="sr-only">AI 釣魚信件偵測系統 — 暗色優雅風格預覽，左右分欄佈局</h2>
<style>
:root {
  --gold: #C9A84C;
  --gold-light: #E8C97A;
  --gold-dim: #8A6E2F;
  --bg-deep: #141414;
  --bg-card: #1C1C1C;
  --bg-hover: #242424;
  --border-subtle: #2A2A2A;
  --border-gold: #3A3020;
  --text-main: #F0EDE8;
  --text-muted: #888070;
  --text-dim: #555045;
  --red: #C0392B;
  --red-bg: #1E1010;
  --orange: #D4874A;
  --orange-bg: #1E1508;
  --green: #4A9B6F;
  --green-bg: #0E1A12;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
.shell { background: var(--bg-deep); min-height: 580px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; display: flex; flex-direction: column; }

/* Header */
.hdr { border-bottom: 0.5px solid var(--border-gold); padding: 14px 24px; display: flex; align-items: center; justify-content: space-between; background: var(--bg-deep); }
.hdr-left { display: flex; align-items: center; gap: 10px; }
.shield { width: 28px; height: 28px; background: linear-gradient(135deg, var(--gold-dim), var(--gold)); border-radius: 6px; display: flex; align-items: center; justify-content: center; font-size: 14px; }
.hdr h1 { font-size: 14px; font-weight: 500; color: var(--text-main); letter-spacing: 0.02em; }
.hdr-nav { display: flex; gap: 6px; }
.hdr-nav a { font-size: 11px; color: var(--text-muted); text-decoration: none; padding: 4px 10px; border-radius: 4px; border: 0.5px solid var(--border-subtle); }
.gold-tag { font-size: 10px; color: var(--gold); background: var(--border-gold); padding: 3px 8px; border-radius: 20px; border: 0.5px solid var(--gold-dim); letter-spacing: 0.05em; }

/* Summary bar */
.summary { display: flex; gap: 0; border-bottom: 0.5px solid var(--border-subtle); }
.stat { flex: 1; padding: 14px 20px; border-right: 0.5px solid var(--border-subtle); }
.stat:last-child { border-right: none; }
.stat-num { font-size: 22px; font-weight: 500; margin-bottom: 2px; }
.stat-lbl { font-size: 10px; color: var(--text-muted); letter-spacing: 0.06em; text-transform: uppercase; }
.s-total .stat-num { color: var(--gold); }
.s-high .stat-num { color: var(--red); }
.s-med .stat-num { color: var(--orange); }
.s-low .stat-num { color: var(--green); }
.s-wl .stat-num { color: var(--text-dim); }

/* Main layout */
.main { display: flex; flex: 1; }

/* Left panel */
.left { width: 300px; border-right: 0.5px solid var(--border-subtle); overflow-y: auto; flex-shrink: 0; }
.list-sec { padding: 10px 16px 6px; font-size: 10px; color: var(--gold-dim); letter-spacing: 0.08em; text-transform: uppercase; border-bottom: 0.5px solid var(--border-subtle); }
.email-item { padding: 12px 16px; border-bottom: 0.5px solid var(--border-subtle); cursor: pointer; transition: background 0.1s; display: flex; align-items: flex-start; gap: 10px; }
.email-item:hover { background: var(--bg-hover); }
.email-item.active { background: var(--bg-hover); border-left: 2px solid var(--gold); }
.risk-dot { width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; margin-top: 5px; }
.dot-high { background: var(--red); box-shadow: 0 0 6px var(--red); }
.dot-med  { background: var(--orange); }
.dot-low  { background: var(--green); }
.dot-wl   { background: var(--text-dim); }
.item-content { flex: 1; min-width: 0; }
.item-subj { font-size: 12px; color: var(--text-main); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-bottom: 2px; font-weight: 500; }
.item-from { font-size: 11px; color: var(--text-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.item-score { font-size: 10px; color: var(--text-dim); margin-top: 2px; }

/* Right panel */
.right { flex: 1; padding: 24px 28px; overflow-y: auto; }
.detail-badge { display: inline-flex; align-items: center; gap: 6px; padding: 4px 12px; border-radius: 20px; font-size: 11px; font-weight: 500; margin-bottom: 16px; }
.badge-high { background: var(--red-bg); color: var(--red); border: 0.5px solid #3A1010; }
.badge-med  { background: var(--orange-bg); color: var(--orange); border: 0.5px solid #3A2008; }
.badge-low  { background: var(--green-bg); color: var(--green); border: 0.5px solid #0E2A1A; }
.detail-subj { font-size: 18px; font-weight: 500; color: var(--text-main); margin-bottom: 4px; }
.detail-from { font-size: 12px; color: var(--text-muted); margin-bottom: 20px; }
.detail-divider { height: 0.5px; background: var(--border-subtle); margin: 16px 0; }
.detail-sec { font-size: 10px; color: var(--gold-dim); letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 8px; }
.detail-text { font-size: 13px; color: var(--text-main); line-height: 1.6; }
.tag-row { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; }
.htag { font-size: 11px; color: var(--orange); background: var(--orange-bg); padding: 3px 8px; border-radius: 4px; border: 0.5px solid #3A2008; }
.score-row { display: flex; gap: 16px; margin-top: 10px; }
.score-item { font-size: 11px; color: var(--text-muted); }
.score-item span { color: var(--text-main); font-weight: 500; }
.ir-box { background: #0E1A0E; border: 0.5px solid #1A3A1A; border-radius: 8px; padding: 14px 16px; margin-top: 16px; }
.ir-label { font-size: 10px; color: var(--green); letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 6px; }
.ir-id { font-size: 11px; color: var(--text-dim); font-family: monospace; margin-bottom: 6px; }
.ir-impact { font-size: 12px; color: #7EC87E; line-height: 1.5; }
.action-text { font-size: 12px; color: #64A8E8; margin-top: 8px; }
.recommend { font-size: 13px; color: var(--text-main); background: var(--bg-card); border: 0.5px solid var(--border-subtle); border-radius: 6px; padding: 10px 14px; margin-top: 10px; line-height: 1.5; }
.gold-line { width: 32px; height: 1px; background: var(--gold); margin: 20px 0 16px; opacity: 0.4; }
</style>

<div class="shell">
  <!-- Header -->
  <div class="hdr">
    <div class="hdr-left">
      <div class="shield">🛡️</div>
      <h1>AI 釣魚信件偵測系統</h1>
    </div>
    <div class="hdr-nav">
      <a href="#">掃描記錄</a>
      <a href="#">白名單設定</a>
    </div>
    <span class="gold-tag">CAPSTONE</span>
  </div>

  <!-- Summary bar -->
  <div class="summary">
    <div class="stat s-total"><div class="stat-num">15</div><div class="stat-lbl">掃描封數</div></div>
    <div class="stat s-high"><div class="stat-num">3</div><div class="stat-lbl">高風險</div></div>
    <div class="stat s-med"><div class="stat-num">2</div><div class="stat-lbl">中風險</div></div>
    <div class="stat s-low"><div class="stat-num">7</div><div class="stat-lbl">安全</div></div>
    <div class="stat s-wl"><div class="stat-num">3</div><div class="stat-lbl">白名單</div></div>
  </div>

  <!-- Main -->
  <div class="main">
    <!-- Left list -->
    <div class="left">
      <div class="list-sec">高風險</div>
      <div class="email-item active" onclick="showDetail(0)">
        <div class="risk-dot dot-high"></div>
        <div class="item-content">
          <div class="item-subj">URGENT: Bank account suspended</div>
          <div class="item-from">security@bank-secure.xyz</div>
          <div class="item-score">90/100 · 釣魚信件</div>
        </div>
      </div>
      <div class="email-item" onclick="showDetail(1)">
        <div class="risk-dot dot-high"></div>
        <div class="item-content">
          <div class="item-subj">安全性快訊 — 立即驗證</div>
          <div class="item-from">no-reply@accounts.google.xyz</div>
          <div class="item-score">85/100 · 品牌偽裝</div>
        </div>
      </div>
      <div class="email-item" onclick="showDetail(2)">
        <div class="risk-dot dot-high"></div>
        <div class="item-content">
          <div class="item-subj">退款通知 NT$3,200</div>
          <div class="item-from">service@nhi-refund.biz</div>
          <div class="item-score">88/100 · 詐騙簡訊</div>
        </div>
      </div>
      <div class="list-sec">中風險</div>
      <div class="email-item" onclick="showDetail(3)">
        <div class="risk-dot dot-med"></div>
        <div class="item-content">
          <div class="item-subj">You Left Something Behind</div>
          <div class="item-from">no-reply@emails.skims.com</div>
          <div class="item-score">55/100 · 商業行銷</div>
        </div>
      </div>
      <div class="email-item" onclick="showDetail(3)">
        <div class="risk-dot dot-med"></div>
        <div class="item-content">
          <div class="item-subj">Your password expires soon</div>
          <div class="item-from">it-admin@company-internal.net</div>
          <div class="item-score">60/100 · 待確認</div>
        </div>
      </div>
      <div class="list-sec">安全</div>
      <div class="email-item" onclick="showDetail(4)">
        <div class="risk-dot dot-low"></div>
        <div class="item-content">
          <div class="item-subj">明天的組會時間確認</div>
          <div class="item-from">prof.chen@ntu.edu.tw</div>
          <div class="item-score">5/100 · 正常信件</div>
        </div>
      </div>
      <div class="email-item" onclick="showDetail(4)">
        <div class="risk-dot dot-wl"></div>
        <div class="item-content">
          <div class="item-subj">Your weekly recap is ready</div>
          <div class="item-from">newsletter@lululemon.com</div>
          <div class="item-score">白名單 · 略過分析</div>
        </div>
      </div>
    </div>

    <!-- Right detail -->
    <div class="right" id="detail-panel">
      <span class="detail-badge badge-high">🚨 高風險 &nbsp;·&nbsp; 90 / 100</span>
      <div class="detail-subj">URGENT: Your bank account has been suspended</div>
      <div class="detail-from">來自：security@bank-secure.xyz</div>

      <div class="detail-sec">AI 分析說明</div>
      <div class="detail-text">此信件使用緊急語句製造恐慌，要求使用者立即點擊可疑連結驗證帳戶。寄件者網域 bank-secure.xyz 並非任何正規金融機構的官方網域，屬於典型的釣魚攻擊手法。</div>

      <div class="tag-row">
        <span class="htag">⚠️ 緊急語句</span>
        <span class="htag">🔗 可疑網域</span>
        <span class="htag">🔐 索取個資</span>
        <span class="htag">[HTML] 像素追蹤</span>
      </div>

      <div class="score-row">
        <div class="score-item">規則引擎 <span>14分</span></div>
        <div class="score-item">ML 機率 <span>87.3%</span></div>
        <div class="score-item">HTML <span>+8分</span></div>
      </div>

      <div class="detail-divider"></div>
      <div class="detail-sec">建議行動</div>
      <div class="recommend">請勿點擊信件中任何連結，直接聯繫您的銀行官方客服確認帳戶狀態。可將此信件標記為垃圾郵件並封鎖寄件者。</div>

      <div class="ir-box">
        <div class="ir-label">IR 事件通報報告已自動產生</div>
        <div class="ir-id">IR-20260723-A4F2B1 &nbsp;|&nbsp; 嚴重等級：Critical</div>
        <div class="ir-impact">此攻擊可能導致使用者帳戶憑證遭竊取，進而造成財務損失或身份盜用風險。</div>
        <div class="action-text">• 立即變更銀行密碼 &nbsp;• 啟用雙重驗證 &nbsp;• 向資安人員通報</div>
      </div>
    </div>
  </div>
</div>

<script>
const details = [
  {
    badge: '🚨 高風險 · 90 / 100', badgeClass: 'badge-high',
    subj: 'URGENT: Your bank account has been suspended',
    from: '來自：security@bank-secure.xyz',
    explain: '此信件使用緊急語句製造恐慌，要求使用者立即點擊可疑連結驗證帳戶。寄件者網域 bank-secure.xyz 並非任何正規金融機構的官方網域，屬於典型的釣魚攻擊手法。',
    tags: ['⚠️ 緊急語句','🔗 可疑網域','🔐 索取個資','[HTML] 像素追蹤'],
    scores: [['規則引擎','14分'],['ML 機率','87.3%'],['HTML','+8分']],
    action: '請勿點擊信件中任何連結，直接聯繫您的銀行官方客服確認帳戶狀態。可將此信件標記為垃圾郵件並封鎖寄件者。',
    ir: true, irId: 'IR-20260723-A4F2B1', sev: 'Critical',
    impact: '此攻擊可能導致使用者帳戶憑證遭竊取，進而造成財務損失或身份盜用風險。',
    actions: '• 立即變更銀行密碼 &nbsp;• 啟用雙重驗證 &nbsp;• 向資安人員通報'
  },
  {
    badge: '🚨 高風險 · 85 / 100', badgeClass: 'badge-high',
    subj: '安全性快訊 — 立即驗證您的帳戶',
    from: '來自：no-reply@accounts.google.xyz',
    explain: '此信件偽裝成 Google 官方安全通知，但寄件者網域為 google.xyz，並非正規的 google.com，屬於品牌偽裝釣魚攻擊。信件內的連結指向可疑的第三方網站。',
    tags: ['🎭 品牌偽裝','🔗 可疑網域','⚠️ 緊急語句'],
    scores: [['規則引擎','10分'],['ML 機率','79.1%'],['HTML','+4分']],
    action: '請勿點擊連結。直接前往 google.com 登入確認帳戶安全狀態。',
    ir: true, irId: 'IR-20260723-B8C3D2', sev: 'High',
    impact: '可能導致 Google 帳戶遭入侵，影響所有關聯服務。',
    actions: '• 直接登入 Google 帳戶 &nbsp;• 檢查帳戶活動 &nbsp;• 開啟兩步驟驗證'
  },
  {
    badge: '🚨 高風險 · 88 / 100', badgeClass: 'badge-high',
    subj: '【健保署通知】退款 NT$3,200 待領取',
    from: '來自：service@nhi-refund.biz',
    explain: '此信件冒充衛生福利部健保署，以退款為由要求提供銀行帳戶資訊。nhi-refund.biz 非政府官方網域，此為典型的詐騙手法，目的在竊取個人金融資料。',
    tags: ['🎁 誘騙話術','💰 金錢相關','🔐 索取個資','🔗 可疑網域'],
    scores: [['規則引擎','16分'],['ML 機率','91.2%'],['HTML','+6分']],
    action: '立即刪除此信件，切勿提供任何個人或金融資訊。如需確認退款，請直接電洽健保署官方電話。',
    ir: true, irId: 'IR-20260723-C9E5F3', sev: 'Critical',
    impact: '可能導致銀行帳戶資料外洩，進而遭受財務損失。',
    actions: '• 勿提供任何帳戶資訊 &nbsp;• 封鎖寄件者 &nbsp;• 向165反詐騙專線通報'
  },
  {
    badge: '⚠️ 中風險 · 55 / 100', badgeClass: 'badge-med',
    subj: 'You Left Something Major Behind',
    from: '來自：no-reply@emails.skims.com',
    explain: '此信件為商業行銷郵件，含有大量追蹤連結與促銷話術。雖來自已知品牌，但 HTML 結構中偵測到像素追蹤與大量外部連結，建議留意隱私問題。',
    tags: ['🎁 行銷話術','[HTML] 像素追蹤','[HTML] 大量外部連結'],
    scores: [['規則引擎','4分'],['ML 機率','43.2%'],['HTML','+12分']],
    action: '此為已知品牌的行銷信件，可安全閱讀。如不希望收到追蹤，可透過信件底部取消訂閱。',
    ir: false, irId: '', sev: '', impact: '', actions: ''
  },
  {
    badge: '✅ 安全 · 5 / 100', badgeClass: 'badge-low',
    subj: '明天的組會時間確認',
    from: '來自：prof.chen@ntu.edu.tw',
    explain: '此信件來自台大教育網域，內容為正常的學術通訊，無任何可疑特徵。規則引擎與 ML 模型均判定為安全信件。',
    tags: [],
    scores: [['規則引擎','0分'],['ML 機率','3.1%'],['HTML','+0分']],
    action: '可安全閱讀此信件。',
    ir: false, irId: '', sev: '', impact: '', actions: ''
  }
];

function showDetail(idx) {
  const d = details[idx];
  const panel = document.getElementById('detail-panel');
  panel.innerHTML = `
    <span class="detail-badge ${d.badgeClass}">${d.badge}</span>
    <div class="detail-subj">${d.subj}</div>
    <div class="detail-from">${d.from}</div>
    <div class="gold-line"></div>
    <div class="detail-sec">AI 分析說明</div>
    <div class="detail-text">${d.explain}</div>
    ${d.tags.length ? `<div class="tag-row">${d.tags.map(t=>`<span class="htag">${t}</span>`).join('')}</div>` : ''}
    <div class="score-row">${d.scores.map(s=>`<div class="score-item">${s[0]} <span>${s[1]}</span></div>`).join('')}</div>
    <div class="detail-divider"></div>
    <div class="detail-sec">建議行動</div>
    <div class="recommend">${d.action}</div>
    ${d.ir ? `
    <div class="ir-box">
      <div class="ir-label">IR 事件通報報告已自動產生</div>
      <div class="ir-id">${d.irId} &nbsp;|&nbsp; 嚴重等級：${d.sev}</div>
      <div class="ir-impact">${d.impact}</div>
      <div class="action-text">${d.actions}</div>
    </div>` : ''}
  `;
  document.querySelectorAll('.email-item').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.email-item')[idx].classList.add('active');
}
</script>


# ── Flask App ─────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = 'phishing2024'
_state_store = {}
_creds_store = {}
_scan_store = {}  # 非同步掃描結果

@app.route('/')
def index():
    return render_template_string(HOME_HTML)

@app.route('/login')
def login():
    import secrets, hashlib, base64 as _b64
    code_verifier = secrets.token_urlsafe(64)
    code_challenge = _b64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).rstrip(b'=').decode()
    _state_store['code_verifier'] = code_verifier
    flow = Flow.from_client_secrets_file(
        'credentials.json', scopes=SCOPES,
        redirect_uri=f'{BASE_URL}/callback')
    auth_url, state = flow.authorization_url(
        prompt='consent', access_type='offline',
        code_challenge=code_challenge, code_challenge_method='S256')
    _state_store['current'] = state
    return redirect(auth_url)

@app.route('/callback')
def callback():
    try:
        flow = Flow.from_client_secrets_file(
            'credentials.json', scopes=SCOPES,
            redirect_uri=f'{BASE_URL}/callback',
            state=_state_store.get('current', ''))
        auth_resp = request.url.replace('http://', 'https://')
        code_verifier = _state_store.get('code_verifier', '')
        flow.fetch_token(authorization_response=auth_resp, code_verifier=code_verifier)
        creds = flow.credentials
        _creds_store['current'] = {
            'token': creds.token, 'refresh_token': creds.refresh_token,
            'token_uri': creds.token_uri, 'client_id': creds.client_id,
            'client_secret': creds.client_secret, 'scopes': list(creds.scopes)
        }
        return redirect('/scan')
    except Exception as e:
        import traceback
        return f'<h2>授權錯誤</h2><pre>{traceback.format_exc()}</pre>', 500

def do_scan(token_data, scan_id):
    """非同步掃描函式，在背景執行"""
    try:
        creds = Credentials(**token_data)
        service = build('gmail', 'v1', credentials=creds)
        results_api = service.users().messages().list(
            userId='me', maxResults=15, labelIds=['INBOX']).execute()
        messages = results_api.get('messages', [])

        high_emails, med_emails, low_emails = [], [], []
        whitelist_emails = []
        skipped = 0

        for msg_ref in messages:
            msg = service.users().messages().get(
                userId='me', id=msg_ref['id'], format='full').execute()
            sender  = get_header(msg, 'From')
            subject = get_header(msg, 'Subject') or '(無主旨)'
            body    = get_email_body(msg)
            html    = get_email_html(msg)
            text    = f"From: {sender}\nSubject: {subject}\nBody: {body}"

            if is_system_report(sender, subject):
                skipped += 1
                continue

            if is_whitelisted(sender):
                whitelist_emails.append({'sender': sender[:60], 'subject': subject[:55]})
                continue

            report, html_score, html_findings = full_multimodal_pipeline(text, html)
            html_tags = [cat for cat, _ in html_findings[:3]]
            ml_vec = vectorizer.transform([text])
            ml_prob = model.predict_proba(ml_vec)[0][list(model.classes_).index('spam')]
            rule_score, _ = rule_based_score(text)

            entry = {
                'sender': sender[:60], 'subject': subject[:55],
                'risk_level': report['risk_level'],
                'risk_score': report['risk_score'],
                'category': report.get('category', ''),
                'explanation': report.get('explanation', '')[:150],
                'recommended_action': report.get('recommended_action', '')[:100],
                'html_findings': html_tags, 'html_score': html_score,
                'rule_score': rule_score, 'ml_prob': f'{ml_prob:.1%}',
                'ir_id': None, 'ir_severity': None,
                'ir_summary': None, 'ir_actions': [],
            }

            if report['risk_level'] == 'high':
                ir_id, _, ir_detail = generate_incident_report(
                    {'sender': sender, 'subject': subject}, report)
                entry.update({
                    'ir_id': ir_id,
                    'ir_severity': ir_detail.get('severity', 'High'),
                    'ir_summary': ir_detail.get('impact_assessment', '')[:120],
                    'ir_actions': ir_detail.get('immediate_actions', [])[:3],
                })
                high_emails.append(entry)
            elif report['risk_level'] == 'medium':
                med_emails.append(entry)
            else:
                low_emails.append(entry)

        scan_time = datetime.now().strftime('%Y-%m-%d %H:%M')
        save_scan(scan_id, scan_time, high_emails+med_emails+low_emails,
                  high_emails, med_emails, low_emails, len(whitelist_emails), skipped)

        # Email 通知
        if high_emails:
            threading.Thread(target=send_alert_email, args=(high_emails,)).start()

        _scan_store[scan_id] = {
            'done': True,
            'scan_time': scan_time,
            'total': len(high_emails)+len(med_emails)+len(low_emails)+len(whitelist_emails),
            'high': len(high_emails), 'med': len(med_emails),
            'low': len(low_emails), 'whitelist_count': len(whitelist_emails),
            'skipped': skipped,
            'high_emails': high_emails, 'med_emails': med_emails,
            'low_emails': low_emails, 'whitelist_emails': whitelist_emails,
        }
    except Exception as e:
        import traceback
        _scan_store[scan_id] = {'done': True, 'error': traceback.format_exc()}

@app.route('/scan')
def scan():
    token_data = _creds_store.get('current')
    if not token_data:
        return redirect('/')
    scan_id = str(uuid.uuid4())[:8]
    _scan_store[scan_id] = {'done': False}
    threading.Thread(target=do_scan, args=(token_data, scan_id)).start()
    _state_store['last_scan_id'] = scan_id
    return render_template_string(LOADING_HTML)

@app.route('/scan_status')
def scan_status():
    scan_id = _state_store.get('last_scan_id', '')
    if scan_id and scan_id in _scan_store:
        done = _scan_store[scan_id].get('done', False)
        return jsonify({'done': done, 'scan_id': scan_id})
    return jsonify({'done': False, 'scan_id': ''})

@app.route('/result/<scan_id>')
def result(scan_id):
    data = _scan_store.get(scan_id)
    if not data or not data.get('done'):
        return redirect('/')
    if 'error' in data:
        return f'<h2>掃描錯誤</h2><pre>{data["error"]}</pre>', 500
    return render_template_string(RESULT_HTML, **data)

@app.route('/history')
def history():
    rows = get_history()
    return render_template_string(HISTORY_HTML, history=rows)

@app.route('/whitelist')
def whitelist_page():
    conn = sqlite3.connect('phishing.db')
    c = conn.cursor()
    c.execute('SELECT domain, added_time FROM whitelist ORDER BY added_time DESC')
    domains = c.fetchall()
    conn.close()
    return render_template_string(WHITELIST_HTML, domains=domains, count=len(domains))

@app.route('/whitelist/add', methods=['POST'])
def whitelist_add():
    data = request.get_json()
    domain = data.get('domain', '').strip().lower()
    if not domain:
        return jsonify({'success': False, 'error': '請輸入網域'})
    try:
        conn = sqlite3.connect('phishing.db')
        c = conn.cursor()
        c.execute('INSERT INTO whitelist (domain, added_time) VALUES (?, ?)',
                 (domain, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/whitelist/delete', methods=['POST'])
def whitelist_delete():
    data = request.get_json()
    domain = data.get('domain', '')
    conn = sqlite3.connect('phishing.db')
    c = conn.cursor()
    c.execute('DELETE FROM whitelist WHERE domain = ?', (domain,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'time': datetime.now().isoformat()})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
