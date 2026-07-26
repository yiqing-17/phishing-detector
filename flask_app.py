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
HOME_HTML = """<!DOCTYPE html><html lang="zh-TW"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AI 釣魚信件偵測系統</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;background:#0f1117;color:#e8eaf0;min-height:100vh}
.header{background:linear-gradient(135deg,#1a1f35,#0f1117);border-bottom:1px solid #2a3050;padding:20px 40px;display:flex;align-items:center;justify-content:space-between}
.header h1{font-size:20px;font-weight:600;color:#fff}
.nav{display:flex;gap:12px}
.nav a{font-size:13px;color:#8892b0;text-decoration:none;padding:6px 12px;border-radius:6px;border:1px solid #2a3050}
.nav a:hover{background:#1a1f35;color:#fff}
.badge{background:#1e3a5f;color:#64b5f6;font-size:11px;padding:3px 10px;border-radius:20px;border:1px solid #2a5298}
.container{max-width:860px;margin:0 auto;padding:60px 20px;text-align:center}
h2{font-size:38px;font-weight:700;color:#fff;margin-bottom:14px}
.sub{font-size:16px;color:#8892b0;max-width:480px;margin:0 auto 36px;line-height:1.6}
.btn{display:inline-flex;align-items:center;gap:10px;background:#fff;color:#333;font-size:15px;font-weight:500;padding:14px 28px;border-radius:8px;text-decoration:none;transition:all .2s;box-shadow:0 4px 15px rgba(0,0,0,.3)}
.btn:hover{transform:translateY(-2px);box-shadow:0 8px 25px rgba(0,0,0,.4)}
.features{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-top:60px;text-align:left}
.feat{background:#1a1f35;border:1px solid #2a3050;border-radius:12px;padding:24px;text-align:center}
.feat .icon{font-size:30px;margin-bottom:10px}
.feat h3{font-size:14px;font-weight:600;color:#fff;margin-bottom:6px}
.feat p{font-size:12px;color:#8892b0;line-height:1.5}
.wl-note{background:#1a2a1a;border:1px solid #2a4a2a;border-radius:10px;padding:14px 20px;margin-top:30px;font-size:12px;color:#8ab48a;text-align:left}
.wl-note strong{color:#4caf50}
</style></head><body>
<div class="header">
  <h1>🛡️ AI 釣魚信件偵測系統</h1>
  <div class="nav">
    <a href="/history">📋 掃描記錄</a>
    <a href="/whitelist">🔒 白名單設定</a>
  </div>
  <span class="badge">畢業專題</span>
</div>
<div class="container">
  <h2>一鍵掃描你的 Gmail</h2>
  <p class="sub">授權後系統自動掃描最新 15 封信件，用 AI 識別釣魚攻擊並產生詳細分析報告。</p>
  <a href="/login" class="btn">
    <svg width="20" height="20" viewBox="0 0 48 48">
      <path fill="#4285F4" d="M45.12 24.5c0-1.56-.14-3.06-.4-4.5H24v8.51h11.84c-.51 2.75-2.06 5.08-4.39 6.64l7.08 5.51C42.45 36.27 45.12 30.87 45.12 24.5z"/>
      <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/>
      <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.08-5.51c-2.13 1.45-4.84 2.3-8.81 2.3-6.72 0-12.43-4.54-14.47-10.64l-7.98 6.19C5.22 42.79 14.04 48 24 48z"/>
      <path fill="#EA4335" d="M24 4.8L6.4 19.2V43.2h10.4V28.8h14.4v14.4H41.6V19.2z"/>
    </svg>
    使用 Google 帳號授權
  </a>
  <div class="features">
    <div class="feat"><div class="icon">🔍</div><h3>三層 AI 分析</h3><p>規則引擎 + ML + LLaMA 3.3 深度分析</p></div>
    <div class="feat"><div class="icon">🌐</div><h3>HTML 多模態</h3><p>偵測像素追蹤、偽裝連結、隱藏元素</p></div>
    <div class="feat"><div class="icon">📄</div><h3>IR 事件報告</h3><p>高風險信件自動產生資安事件通報</p></div>
  </div>
  <div class="wl-note">
    <strong>✅ 白名單已啟用：</strong>
    SKIMS、lululemon、Alo Yoga、玉山銀行、Google 等已知安全寄件者直接標記為安全。
    可在「白名單設定」頁面自訂。
  </div>
</div>
</body></html>"""

LOADING_HTML = """<!DOCTYPE html><html lang="zh-TW"><head><meta charset="UTF-8">
<title>掃描中...</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,sans-serif;background:#0f1117;color:#e8eaf0;min-height:100vh;display:flex;align-items:center;justify-content:center;flex-direction:column;gap:20px}
.spinner{width:56px;height:56px;border:4px solid #2a3050;border-top:4px solid #64b5f6;border-radius:50%;animation:spin 1s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
h2{font-size:22px;font-weight:600;color:#fff}
p{font-size:14px;color:#8892b0}
.steps{margin-top:10px;display:flex;flex-direction:column;gap:6px;text-align:left}
.step{font-size:13px;color:#8892b0;padding:4px 0}
.step.active{color:#64b5f6}
</style>
<script>
  const steps = ['正在連線 Gmail...','讀取最新信件...','規則引擎分析中...','AI 深度分析中...','產生報告...'];
  let i = 0;
  setInterval(() => {
    if(i < steps.length) {
      document.querySelectorAll('.step')[i].classList.add('active');
      i++;
    }
  }, 2000);
  // 每秒檢查掃描是否完成
  setInterval(() => {
    fetch('/scan_status').then(r=>r.json()).then(d=>{
      if(d.done) window.location.href='/result/'+d.scan_id;
    });
  }, 1000);
</script>
</head><body>
<div class="spinner"></div>
<h2>正在掃描你的 Gmail...</h2>
<div class="steps">
  <div class="step active">正在連線 Gmail...</div>
  <div class="step">讀取最新信件...</div>
  <div class="step">規則引擎分析中...</div>
  <div class="step">AI 深度分析中...</div>
  <div class="step">產生報告...</div>
</div>
</body></html>"""

RESULT_HTML = """<!DOCTYPE html><html lang="zh-TW"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>掃描結果 - AI 釣魚信件偵測系統</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;background:#0f1117;color:#e8eaf0;min-height:100vh}
.header{background:linear-gradient(135deg,#1a1f35,#0f1117);border-bottom:1px solid #2a3050;padding:20px 40px;display:flex;align-items:center;justify-content:space-between}
.header h1{font-size:20px;font-weight:600;color:#fff}
.nav{display:flex;gap:12px}
.nav a{font-size:13px;color:#8892b0;text-decoration:none;padding:6px 12px;border-radius:6px;border:1px solid #2a3050}
.nav a:hover{background:#1a1f35;color:#fff}
.container{max-width:900px;margin:0 auto;padding:32px 20px}
.back{display:inline-flex;align-items:center;gap:6px;background:#1a1f35;color:#64b5f6;font-size:13px;padding:8px 16px;border-radius:8px;text-decoration:none;border:1px solid #2a5298;margin-bottom:20px}
.back:hover{background:#1e3a5f}
.summary{background:#1a1f35;border:1px solid #2a3050;border-radius:12px;padding:24px;margin-bottom:24px;display:flex;gap:40px;flex-wrap:wrap;align-items:center}
.stat{text-align:center}
.stat .num{font-size:36px;font-weight:700}
.stat .lbl{font-size:12px;color:#8892b0;margin-top:4px}
.high .num{color:#f44336}.med .num{color:#ff9800}.low .num{color:#4caf50}.total .num{color:#64b5f6}.wl .num{color:#555}.sk .num{color:#444}
.sec{font-size:17px;font-weight:600;color:#fff;margin:28px 0 14px}
.card{background:#1a1f35;border:1px solid #2a3050;border-radius:12px;padding:18px 20px;margin-bottom:10px;transition:border-color .2s}
.card:hover{border-color:#3a4070}
.card.h{border-left:4px solid #f44336}
.card.m{border-left:4px solid #ff9800}
.card.l{border-left:4px solid #4caf50}
.card.w{border-left:4px solid #333;opacity:.6}
.top{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px}
.subj{font-size:15px;font-weight:600;color:#fff}
.from{font-size:12px;color:#8892b0;margin-top:2px}
.rb{font-size:11px;font-weight:600;padding:4px 12px;border-radius:20px;white-space:nowrap}
.bh{background:#2d1515;color:#f44336;border:1px solid #5c2020}
.bm{background:#2d2010;color:#ff9800;border:1px solid #5c4020}
.bl{background:#152d15;color:#4caf50;border:1px solid #205c20}
.bw{background:#1a1a1a;color:#555;border:1px solid #333}
.exp{font-size:13px;color:#aab4c8;margin-top:8px;line-height:1.6}
.act{font-size:12px;color:#64b5f6;margin-top:6px}
.tags{margin-top:8px;display:flex;flex-wrap:wrap;gap:6px}
.tag{font-size:11px;color:#ff9800;background:#2a1800;padding:3px 8px;border-radius:4px;border:1px solid #5c3000}
.sc{font-size:11px;color:#555e7a;margin-top:6px}
.ir{background:#0d1f0d;border:1px solid #1a3a1a;border-radius:10px;padding:14px 16px;margin-top:10px}
.ir-t{font-size:12px;font-weight:600;color:#4caf50;margin-bottom:6px}
.ir-id{font-size:11px;color:#8892b0;font-family:monospace}
.ir-b{font-size:12px;color:#a8c8a8;margin-top:5px;line-height:1.5}
.ir-acts{margin-top:8px}
.ir-act{font-size:12px;color:#7ec87e;margin-top:3px}
</style></head><body>
<div class="header">
  <h1>🛡️ AI 釣魚信件偵測系統 — 掃描結果</h1>
  <div class="nav">
    <a href="/history">📋 掃描記錄</a>
    <a href="/whitelist">🔒 白名單設定</a>
  </div>
</div>
<div class="container">
  <a href="/" class="back">← 重新掃描</a>
  <div class="summary">
    <div class="stat total"><div class="num">{{total}}</div><div class="lbl">掃描封數</div></div>
    <div class="stat high"><div class="num">{{high}}</div><div class="lbl">🚨 高風險</div></div>
    <div class="stat med"><div class="num">{{med}}</div><div class="lbl">⚠️ 中風險</div></div>
    <div class="stat low"><div class="num">{{low}}</div><div class="lbl">✅ 安全</div></div>
    <div class="stat wl"><div class="num">{{whitelist_count}}</div><div class="lbl">🔒 白名單</div></div>
    <div class="stat sk"><div class="num">{{skipped}}</div><div class="lbl">⏭️ 略過</div></div>
  </div>

  {% if high_emails %}
  <div class="sec">🚨 高風險信件（請立即處理）</div>
  {% for e in high_emails %}
  <div class="card h">
    <div class="top"><div><div class="subj">{{e.subject}}</div><div class="from">{{e.sender}}</div></div>
    <span class="rb bh">HIGH {{e.risk_score}}/100</span></div>
    <div class="exp">{{e.explanation}}</div>
    <div class="act">📋 {{e.recommended_action}}</div>
    {% if e.html_findings %}<div class="tags">{% for f in e.html_findings %}<span class="tag">{{f}}</span>{% endfor %}</div>{% endif %}
    <div class="sc">規則:{{e.rule_score}} | ML:{{e.ml_prob}} | HTML:+{{e.html_score}}</div>
    {% if e.ir_id %}<div class="ir">
      <div class="ir-t">📄 IR 事件通報報告已自動產生</div>
      <div class="ir-id">{{e.ir_id}} | 嚴重等級: {{e.ir_severity}}</div>
      <div class="ir-b">{{e.ir_summary}}</div>
      {% if e.ir_actions %}<div class="ir-acts">{% for a in e.ir_actions %}<div class="ir-act">• {{a}}</div>{% endfor %}</div>{% endif %}
    </div>{% endif %}
  </div>{% endfor %}{% endif %}

  {% if med_emails %}
  <div class="sec">⚠️ 中風險信件</div>
  {% for e in med_emails %}
  <div class="card m">
    <div class="top"><div><div class="subj">{{e.subject}}</div><div class="from">{{e.sender}}</div></div>
    <span class="rb bm">MED {{e.risk_score}}/100</span></div>
    <div class="exp">{{e.explanation}}</div>
    <div class="act">📋 {{e.recommended_action}}</div>
    {% if e.html_findings %}<div class="tags">{% for f in e.html_findings %}<span class="tag">{{f}}</span>{% endfor %}</div>{% endif %}
    <div class="sc">規則:{{e.rule_score}} | ML:{{e.ml_prob}} | HTML:+{{e.html_score}}</div>
  </div>{% endfor %}{% endif %}

  {% if low_emails %}
  <div class="sec">✅ 安全信件</div>
  {% for e in low_emails %}
  <div class="card l">
    <div class="top"><div><div class="subj">{{e.subject}}</div><div class="from">{{e.sender}}</div></div>
    <span class="rb bl">LOW {{e.risk_score}}/100</span></div>
    <div class="exp">{{e.explanation}}</div>
  </div>{% endfor %}{% endif %}

  {% if whitelist_emails %}
  <div class="sec">🔒 白名單信件（已知安全）</div>
  {% for e in whitelist_emails %}
  <div class="card w">
    <div class="top"><div><div class="subj">{{e.subject}}</div><div class="from">{{e.sender}}</div></div>
    <span class="rb bw">白名單</span></div>
  </div>{% endfor %}{% endif %}

</div></body></html>"""

HISTORY_HTML = """<!DOCTYPE html><html lang="zh-TW"><head><meta charset="UTF-8">
<title>掃描記錄</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,sans-serif;background:#0f1117;color:#e8eaf0;min-height:100vh}
.header{background:linear-gradient(135deg,#1a1f35,#0f1117);border-bottom:1px solid #2a3050;padding:20px 40px;display:flex;align-items:center;justify-content:space-between}
.header h1{font-size:20px;font-weight:600;color:#fff}
.nav a{font-size:13px;color:#8892b0;text-decoration:none;padding:6px 12px;border-radius:6px;border:1px solid #2a3050;margin-left:8px}
.container{max-width:900px;margin:0 auto;padding:32px 20px}
.back{display:inline-flex;align-items:center;gap:6px;background:#1a1f35;color:#64b5f6;font-size:13px;padding:8px 16px;border-radius:8px;text-decoration:none;border:1px solid #2a5298;margin-bottom:20px}
table{width:100%;border-collapse:collapse;background:#1a1f35;border-radius:12px;overflow:hidden}
th{background:#1F3864;color:#fff;padding:12px 16px;font-size:13px;text-align:left}
td{padding:12px 16px;font-size:13px;border-bottom:1px solid #2a3050;color:#e8eaf0}
tr:last-child td{border-bottom:none}
tr:hover td{background:#1e2540}
.high{color:#f44336;font-weight:600}
.empty{text-align:center;padding:40px;color:#8892b0}
</style></head><body>
<div class="header">
  <h1>📋 掃描記錄</h1>
  <div class="nav">
    <a href="/">🏠 首頁</a>
    <a href="/whitelist">🔒 白名單設定</a>
  </div>
</div>
<div class="container">
  <a href="/" class="back">← 返回首頁</a>
  {% if history %}
  <table>
    <tr><th>掃描時間</th><th>總計</th><th>高風險</th><th>中風險</th><th>安全</th><th>白名單</th></tr>
    {% for h in history %}
    <tr>
      <td>{{h[1]}}</td>
      <td>{{h[2]}}</td>
      <td class="high">{{h[3]}}</td>
      <td>{{h[4]}}</td>
      <td>{{h[5]}}</td>
      <td>{{h[6]}}</td>
    </tr>
    {% endfor %}
  </table>
  {% else %}
  <div class="empty">還沒有掃描記錄，<a href="/" style="color:#64b5f6">開始掃描</a>！</div>
  {% endif %}
</div></body></html>"""

WHITELIST_HTML = """<!DOCTYPE html><html lang="zh-TW"><head><meta charset="UTF-8">
<title>白名單設定</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,sans-serif;background:#0f1117;color:#e8eaf0;min-height:100vh}
.header{background:linear-gradient(135deg,#1a1f35,#0f1117);border-bottom:1px solid #2a3050;padding:20px 40px;display:flex;align-items:center;justify-content:space-between}
.header h1{font-size:20px;font-weight:600;color:#fff}
.nav a{font-size:13px;color:#8892b0;text-decoration:none;padding:6px 12px;border-radius:6px;border:1px solid #2a3050;margin-left:8px}
.container{max-width:700px;margin:0 auto;padding:32px 20px}
.back{display:inline-flex;align-items:center;gap:6px;background:#1a1f35;color:#64b5f6;font-size:13px;padding:8px 16px;border-radius:8px;text-decoration:none;border:1px solid #2a5298;margin-bottom:20px}
.add-form{background:#1a1f35;border:1px solid #2a3050;border-radius:12px;padding:20px;margin-bottom:24px;display:flex;gap:10px}
.add-form input{flex:1;background:#0f1117;border:1px solid #2a3050;border-radius:6px;padding:10px 14px;color:#fff;font-size:14px}
.add-form input::placeholder{color:#555}
.add-form button{background:#2E75B6;color:#fff;border:none;border-radius:6px;padding:10px 20px;font-size:14px;cursor:pointer}
.add-form button:hover{background:#3a8fd4}
.domain-list{display:flex;flex-direction:column;gap:8px}
.domain-item{background:#1a1f35;border:1px solid #2a3050;border-radius:10px;padding:14px 16px;display:flex;justify-content:space-between;align-items:center}
.domain-name{font-size:14px;color:#fff}
.domain-time{font-size:11px;color:#8892b0}
.del-btn{background:#2d1515;color:#f44336;border:1px solid #5c2020;border-radius:6px;padding:4px 12px;font-size:12px;cursor:pointer}
.del-btn:hover{background:#3d1515}
.sec{font-size:16px;font-weight:600;color:#fff;margin-bottom:14px}
.note{font-size:12px;color:#8892b0;margin-bottom:16px}
</style></head><body>
<div class="header">
  <h1>🔒 白名單設定</h1>
  <div class="nav">
    <a href="/">🏠 首頁</a>
    <a href="/history">📋 掃描記錄</a>
  </div>
</div>
<div class="container">
  <a href="/" class="back">← 返回首頁</a>
  <div class="sec">新增白名單網域</div>
  <p class="note">加入後，來自該網域的信件將直接標記為安全，不進行 AI 分析。</p>
  <div class="add-form">
    <input type="text" id="domain-input" placeholder="輸入網域，例如：example.com">
    <button onclick="addDomain()">新增</button>
  </div>
  <div class="sec">目前白名單（{{count}} 個）</div>
  <div class="domain-list">
    {% for d in domains %}
    <div class="domain-item">
      <div><div class="domain-name">{{d[0]}}</div><div class="domain-time">新增時間：{{d[1][:10]}}</div></div>
      <button class="del-btn" onclick="deleteDomain('{{d[0]}}')">刪除</button>
    </div>{% endfor %}
  </div>
</div>
<script>
function addDomain() {
  const domain = document.getElementById('domain-input').value.trim();
  if (!domain) return alert('請輸入網域');
  fetch('/whitelist/add', {method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({domain})})
    .then(r => r.json()).then(d => {
      if(d.success) location.reload();
      else alert(d.error);
    });
}
function deleteDomain(domain) {
  if (!confirm(`確定要刪除 ${domain}？`)) return;
  fetch('/whitelist/delete', {method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({domain})})
    .then(r => r.json()).then(d => {
      if(d.success) location.reload();
    });
}
</script>
</body></html>"""

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
