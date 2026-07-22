# ============================================================
# AI 釣魚信件偵測系統 - Flask 網頁版
# 使用方法：在 Colab 執行 !python flask_app.py
# ============================================================

import json, os, uuid, threading, base64, re, pickle
from datetime import datetime
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from groq import Groq
from bs4 import BeautifulSoup
from flask import Flask, redirect, request, render_template_string
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from pyngrok import ngrok

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# ── 設定區（每次啟動只需改這裡）────────────────────────────
GROQ_API_KEY = 'gsk_填入你的key'
NGROK_TOKEN  = '填入你的ngrok_token'
MY_EMAIL     = 'sherry940501@gmail.com'
NGROK_URL = 'https://phishing-detector-n8rv.onrender.com'
SCOPES       = ['https://www.googleapis.com/auth/gmail.readonly']

# ── 白名單：已知安全的寄件者網域 ────────────────────────────
WHITELIST_DOMAINS = [
    'skims.com', 'emails.skims.com', 'links.skims.com',
    'lululemon.com', 'email.lululemon.com', 'e.lululemon.com',
    'aloyoga.com', 'email.aloyoga.com',
    'esunbank.com.tw', 'esun.com.tw', 'esunsec.com.tw',
    'google.com', 'accounts.google.com', 'googlemail.com',
    'googleaistudio-noreply@google.com',
]

# ── 系統報告排除關鍵字 ──────────────────────────────────────
SKIP_SUBJECTS = ['[警告]', '[正常]', 'AI 釣魚偵測報告', 'AI 釣魚信件偵測報告']

# ── Google OAuth 憑證 ───────────────────────────────────────
CRED_DATA = {"web":{"client_id":"727861534469-72ihfsri6r9kpnu56n7541qb2e4ngomk.apps.googleusercontent.com","project_id":"phishing-detector-494720","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_secret":"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","redirect_uris":["https://phishing-detector-n8rv.onrender.com/callback"]}}

# ── 初始化 ──────────────────────────────────────────────────
with open('credentials.json', 'w') as f:
    json.dump(CRED_DATA, f)

groq_client = Groq(api_key=GROQ_API_KEY)

# 訓練 ML 模型
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

# ── 工具函式 ────────────────────────────────────────────────
def is_whitelisted(sender):
    s = sender.lower()
    return any(domain in s for domain in WHITELIST_DOMAINS)

def is_system_report(sender, subject):
    if any(kw in subject for kw in SKIP_SUBJECTS):
        return True
    if MY_EMAIL in sender and any(kw in subject for kw in ['釣魚', '警告', '偵測']):
        return True
    return False

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
HOME_HTML = """<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI 釣魚信件偵測系統</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500&family=Noto+Sans+TC:wght@400;500;700&display=swap" rel="stylesheet">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Inter', 'Noto Sans TC', -apple-system, sans-serif;
            background-color: #07090e;
            color: #d1d5db;
            min-height: 100vh;
            line-height: 1.5;
            background-image: 
                radial-gradient(at 50% 0%, rgba(56, 189, 248, 0.08) 0px, transparent 70%),
                radial-gradient(at 100% 100%, rgba(139, 92, 246, 0.05) 0px, transparent 50%);
        }
        .header {
            background: rgba(7, 9, 14, 0.8);
            backdrop-filter: blur(16px);
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            padding: 16px 36px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            position: sticky;
            top: 0;
            z-index: 50;
        }
        .header h1 {
            font-size: 18px;
            font-weight: 700;
            color: #ffffff;
            letter-spacing: -0.01em;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .badge {
            background: rgba(56, 189, 248, 0.08);
            color: #38bdf8;
            font-size: 11px;
            font-weight: 600;
            padding: 4px 10px;
            border-radius: 6px;
            border: 1px solid rgba(56, 189, 248, 0.25);
            font-family: 'JetBrains Mono', monospace;
            letter-spacing: 0.05em;
        }
        .container {
            max-width: 880px;
            margin: 0 auto;
            padding: 64px 24px;
            text-align: center;
        }
        h2 {
            font-size: 38px;
            font-weight: 700;
            color: #f9fafb;
            margin-bottom: 16px;
            letter-spacing: -0.02em;
            text-shadow: 0 0 30px rgba(255, 255, 255, 0.1);
        }
        .sub {
            font-size: 15px;
            color: #9ca3af;
            max-width: 500px;
            margin: 0 auto 36px;
            line-height: 1.6;
        }
        .btn {
            display: inline-flex;
            align-items: center;
            gap: 12px;
            background: #f9fafb;
            color: #030712;
            font-size: 14px;
            font-weight: 600;
            padding: 14px 28px;
            border-radius: 8px;
            text-decoration: none;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 0 20px rgba(255, 255, 255, 0.15);
        }
        .btn:hover {
            background: #ffffff;
            transform: translateY(-2px);
            box-shadow: 0 0 30px rgba(255, 255, 255, 0.3);
        }
        .features {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 16px;
            margin-top: 60px;
            text-align: left;
        }
        .feat {
            background: rgba(15, 23, 42, 0.4);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 12px;
            padding: 24px;
            text-align: center;
            transition: all 0.2s;
        }
        .feat:hover {
            border-color: rgba(56, 189, 248, 0.3);
            background: rgba(15, 23, 42, 0.6);
            box-shadow: 0 0 20px rgba(56, 189, 248, 0.05);
        }
        .feat .icon {
            font-size: 26px;
            margin-bottom: 12px;
        }
        .feat h3 {
            font-size: 14px;
            font-weight: 600;
            color: #f3f4f6;
            margin-bottom: 6px;
        }
        .feat p {
            font-size: 12px;
            color: #9ca3af;
            line-height: 1.5;
        }
        .whitelist-note {
            background: rgba(16, 185, 129, 0.04);
            border: 1px solid rgba(16, 185, 129, 0.2);
            border-radius: 10px;
            padding: 14px 20px;
            margin-top: 40px;
            font-size: 12px;
            color: #6ee7b7;
            text-align: left;
            line-height: 1.6;
        }
        .whitelist-note strong {
            color: #34d399;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🛡️ AI 釣魚信件偵測系統</h1>
        <span class="badge">PROJ-2026</span>
    </div>
    <div class="container">
        <h2>一鍵掃描你的 Gmail</h2>
        <p class="sub">授權後系統自動掃描最新 15 封信件，用 AI 識別釣魚攻擊並產生詳細分析報告。</p>
        <a href="/login" class="btn">
            <svg width="18" height="18" viewBox="0 0 48 48">
                <path fill="#4285F4" d="M45.12 24.5c0-1.56-.14-3.06-.4-4.5H24v8.51h11.84c-.51 2.75-2.06 5.08-4.39 6.64l7.08 5.51C42.45 36.27 45.12 30.87 45.12 24.5z"/>
                <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/>
                <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.08-5.51c-2.13 1.45-4.84 2.3-8.81 2.3-6.72 0-12.43-4.54-14.47-10.64l-7.98 6.19C5.22 42.79 14.04 48 24 48z"/>
                <path fill="#EA4335" d="M24 4.8L6.4 19.2V43.2h10.4V28.8h14.4v14.4H41.6V19.2z"/>
            </svg>
            使用 Google 帳號授權
        </a>
        <div class="features">
            <div class="feat">
                <div class="icon">🔍</div>
                <h3>三層 AI 分析</h3>
                <p>規則引擎 + ML + LLaMA 3.3 深度分析</p>
            </div>
            <div class="feat">
                <div class="icon">🌐</div>
                <h3>HTML 多模態</h3>
                <p>偵測像素追蹤、偽裝連結、隱藏元素</p>
            </div>
            <div class="feat">
                <div class="icon">📄</div>
                <h3>IR 事件報告</h3>
                <p>高風險信件自動產生資安事件通報</p>
            </div>
        </div>
        <div class="whitelist-note">
            <strong>✅ 白名單機制已啟用：</strong>
            SKIMS、lululemon、Alo Yoga、玉山銀行、Google 等已知安全寄件者將直接標記為安全，不進行 AI 分析。
        </div>
    </div>
</body>
</html>"""

LOADING_HTML = """<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="3;url=/result">
    <title>掃描中...</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@500&display=swap" rel="stylesheet">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Inter', -apple-system, sans-serif;
            background-color: #07090e;
            color: #d1d5db;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-direction: column;
            gap: 20px;
            background-image: radial-gradient(at 50% 50%, rgba(56, 189, 248, 0.06) 0px, transparent 60%);
        }
        .spinner {
            width: 52px;
            height: 52px;
            border: 3px solid rgba(255, 255, 255, 0.08);
            border-top: 3px solid #38bdf8;
            border-radius: 50%;
            animation: spin 0.8s cubic-bezier(0.55, 0.15, 0.45, 0.85) infinite;
            box-shadow: 0 0 20px rgba(56, 189, 248, 0.2);
        }
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        h2 {
            font-size: 20px;
            font-weight: 600;
            color: #f9fafb;
            letter-spacing: -0.01em;
        }
        p {
            font-size: 13px;
            color: #6b7280;
            font-family: 'JetBrains Mono', monospace;
        }
    </style>
</head>
<body>
    <div class="spinner"></div>
    <h2>正在掃描您的 Gmail...</h2>
    <p>> 三層 AI 分析引擎運作中，請稍候</p>
</body>
</html>"""

RESULT_HTML = """<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>掃描結果 — AI 釣魚信件偵測系統</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&family=Noto+Sans+TC:wght@400;500;700&display=swap" rel="stylesheet">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Inter', 'Noto Sans TC', -apple-system, sans-serif;
            background-color: #07090e;
            color: #d1d5db;
            min-height: 100vh;
            line-height: 1.5;
            background-image: radial-gradient(at 50% 0%, rgba(56, 189, 248, 0.05) 0px, transparent 60%);
        }
        .header {
            background: rgba(7, 9, 14, 0.8);
            backdrop-filter: blur(16px);
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            padding: 16px 36px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            position: sticky;
            top: 0;
            z-index: 50;
        }
        .header h1 {
            font-size: 18px;
            font-weight: 700;
            color: #ffffff;
        }
        .header-right {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .scan-time {
            font-size: 11px;
            color: #6b7280;
            font-family: 'JetBrains Mono', monospace;
        }
        .container {
            max-width: 880px;
            margin: 0 auto;
            padding: 32px 24px 60px;
        }
        .back {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: rgba(255, 255, 255, 0.03);
            color: #38bdf8;
            font-size: 12px;
            font-weight: 500;
            padding: 8px 14px;
            border-radius: 6px;
            text-decoration: none;
            border: 1px solid rgba(56, 189, 248, 0.2);
            margin-bottom: 24px;
            transition: all 0.2s;
            font-family: 'JetBrains Mono', monospace;
        }
        .back:hover {
            background: rgba(56, 189, 248, 0.1);
            border-color: rgba(56, 189, 248, 0.4);
        }
        .summary {
            background: rgba(15, 23, 42, 0.4);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 12px;
            padding: 20px 24px;
            margin-bottom: 32px;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
            gap: 16px;
            align-items: center;
        }
        .stat {
            text-align: center;
        }
        .stat .num {
            font-size: 28px;
            font-weight: 700;
            line-height: 1.2;
            font-family: 'JetBrains Mono', monospace;
        }
        .stat .lbl {
            font-size: 11px;
            color: #6b7280;
            margin-top: 4px;
            font-weight: 500;
        }
        .high .num { color: #ff4d4d; text-shadow: 0 0 12px rgba(255, 77, 77, 0.3); }
        .med .num { color: #fbbf24; text-shadow: 0 0 12px rgba(251, 191, 36, 0.2); }
        .low .num { color: #34d399; text-shadow: 0 0 12px rgba(52, 211, 153, 0.2); }
        .total .num { color: #38bdf8; }
        .skip .num { color: #4b5563; }

        .sec-title {
            font-size: 15px;
            font-weight: 600;
            color: #f3f4f6;
            margin: 32px 0 16px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .card {
            background: rgba(15, 23, 42, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 10px;
            padding: 18px 20px;
            margin-bottom: 12px;
            position: relative;
            transition: all 0.2s;
        }
        .card:hover {
            background: rgba(15, 23, 42, 0.5);
        }
        .card.h {
            border-left: 3px solid #ff4d4d;
            box-shadow: inset 4px 0 15px -4px rgba(255, 77, 77, 0.15);
        }
        .card.m {
            border-left: 3px solid #fbbf24;
            box-shadow: inset 4px 0 15px -4px rgba(251, 191, 36, 0.1);
        }
        .card.l {
            border-left: 3px solid #34d399;
        }
        .card.w {
            border-left: 3px solid #4b5563;
            opacity: 0.6;
        }

        .top {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 16px;
            margin-bottom: 8px;
        }
        .subj {
            font-size: 14px;
            font-weight: 600;
            color: #f9fafb;
            line-height: 1.4;
        }
        .from {
            font-size: 12px;
            color: #6b7280;
            margin-top: 3px;
        }
        .rb {
            font-size: 10px;
            font-weight: 600;
            padding: 3px 8px;
            border-radius: 4px;
            white-space: nowrap;
            font-family: 'JetBrains Mono', monospace;
            letter-spacing: 0.05em;
        }
        .bh { background: rgba(255, 77, 77, 0.12); color: #ff4d4d; border: 1px solid rgba(255, 77, 77, 0.3); }
        .bm { background: rgba(251, 191, 36, 0.12); color: #fbbf24; border: 1px solid rgba(251, 191, 36, 0.3); }
        .bl { background: rgba(52, 211, 153, 0.12); color: #34d399; border: 1px solid rgba(52, 211, 153, 0.3); }
        .bw { background: rgba(75, 85, 99, 0.2); color: #9ca3af; border: 1px solid rgba(75, 85, 99, 0.3); }

        .exp {
            font-size: 13px;
            color: #9ca3af;
            margin-top: 8px;
            line-height: 1.6;
        }
        .act {
            font-size: 12px;
            color: #38bdf8;
            margin-top: 10px;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .tags {
            margin-top: 10px;
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
        }
        .tag {
            font-size: 11px;
            color: #fbbf24;
            background: rgba(251, 191, 36, 0.08);
            padding: 2px 7px;
            border-radius: 4px;
            border: 1px solid rgba(251, 191, 36, 0.2);
            font-family: 'JetBrains Mono', monospace;
        }
        .sc {
            font-size: 11px;
            color: #4b5563;
            margin-top: 10px;
            font-family: 'JetBrains Mono', monospace;
        }
        .ir {
            background: rgba(52, 211, 153, 0.03);
            border: 1px solid rgba(52, 211, 153, 0.2);
            border-radius: 6px;
            padding: 12px 14px;
            margin-top: 12px;
        }
        .ir-t {
            font-size: 12px;
            font-weight: 600;
            color: #34d399;
            margin-bottom: 2px;
        }
        .ir-id {
            font-size: 11px;
            color: #6b7280;
            font-family: 'JetBrains Mono', monospace;
        }
        .ir-b {
            font-size: 12px;
            color: #a7f3d0;
            margin-top: 6px;
            line-height: 1.5;
        }
        .ir-actions {
            margin-top: 8px;
        }
        .ir-action {
            font-size: 11px;
            color: #6ee7b7;
            margin-top: 3px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🛡️ AI 釣魚信件偵測系統</h1>
        <div class="header-right">
            <span class="scan-time">SCAN_TIME: {{scan_time}}</span>
        </div>
    </div>
    <div class="container">
        <a href="/" class="back">← RESCAN</a>

        <div class="summary">
            <div class="stat total"><div class="num">{{total}}</div><div class="lbl">掃描封數</div></div>
            <div class="stat high"><div class="num">{{high}}</div><div class="lbl">🚨 高風險</div></div>
            <div class="stat med"><div class="num">{{med}}</div><div class="lbl">⚠️ 中風險</div></div>
            <div class="stat low"><div class="num">{{low}}</div><div class="lbl">✅ 安全</div></div>
            <div class="stat skip"><div class="num">{{whitelist_count}}</div><div class="lbl">🔒 白名單</div></div>
            <div class="stat skip"><div class="num">{{skipped}}</div><div class="lbl">⏭️ 略過</div></div>
        </div>

        {% if high_emails %}
        <div class="sec-title">🚨 高風險信件（請立即處理）</div>
        {% for e in high_emails %}
        <div class="card h">
            <div class="top">
                <div>
                    <div class="subj">{{e.subject}}</div>
                    <div class="from">{{e.sender}}</div>
                </div>
                <span class="rb bh">HIGH {{e.risk_score}}/100</span>
            </div>
            <div class="exp">{{e.explanation}}</div>
            <div class="act">📋 {{e.recommended_action}}</div>
            {% if e.html_findings %}
            <div class="tags">
                {% for f in e.html_findings %}
                <span class="tag">{{f}}</span>
                {% endfor %}
            </div>
            {% endif %}
            <div class="sc">規則: {{e.rule_score}}分 | ML: {{e.ml_prob}} | HTML: +{{e.html_score}}分</div>
            {% if e.ir_id %}
            <div class="ir">
                <div class="ir-t">📄 IR 事件通報報告已自動產生</div>
                <div class="ir-id">{{e.ir_id}} | SEVERITY: {{e.ir_severity}}</div>
                <div class="ir-b">{{e.ir_summary}}</div>
                {% if e.ir_actions %}
                <div class="ir-actions">
                    {% for a in e.ir_actions %}
                    <div class="ir-action">• {{a}}</div>
                    {% endfor %}
                </div>
                {% endif %}
            </div>
            {% endif %}
        </div>
        {% endfor %}
        {% endif %}

        {% if med_emails %}
        <div class="sec-title">⚠️ 中風險信件</div>
        {% for e in med_emails %}
        <div class="card m">
            <div class="top">
                <div>
                    <div class="subj">{{e.subject}}</div>
                    <div class="from">{{e.sender}}</div>
                </div>
                <span class="rb bm">MED {{e.risk_score}}/100</span>
            </div>
            <div class="exp">{{e.explanation}}</div>
            <div class="act">📋 {{e.recommended_action}}</div>
            {% if e.html_findings %}
            <div class="tags">
                {% for f in e.html_findings %}
                <span class="tag">{{f}}</span>
                {% endfor %}
            </div>
            {% endif %}
            <div class="sc">規則: {{e.rule_score}}分 | ML: {{e.ml_prob}} | HTML: +{{e.html_score}}分</div>
        </div>
        {% endfor %}
        {% endif %}

        {% if low_emails %}
        <div class="sec-title">✅ 安全信件</div>
        {% for e in low_emails %}
        <div class="card l">
            <div class="top">
                <div>
                    <div class="subj">{{e.subject}}</div>
                    <div class="from">{{e.sender}}</div>
                </div>
                <span class="rb bl">LOW {{e.risk_score}}/100</span>
            </div>
            <div class="exp">{{e.explanation}}</div>
        </div>
        {% endfor %}
        {% endif %}

        {% if whitelist_emails %}
        <div class="sec-title">🔒 白名單信件（已知安全，略過分析）</div>
        {% for e in whitelist_emails %}
        <div class="card w">
            <div class="top">
                <div>
                    <div class="subj">{{e.subject}}</div>
                    <div class="from">{{e.sender}}</div>
                </div>
                <span class="rb bw">WHITELIST</span>
            </div>
        </div>
        {% endfor %}
        {% endif %}

    </div>
</body>
</html>"""
# ── Flask App ────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = 'phishing2024'
_state_store = {}
_creds_store = {}
_scan_results = {}

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
        redirect_uri=f'{NGROK_URL}/callback')
    auth_url, state = flow.authorization_url(
        prompt='consent',
        access_type='offline',
        code_challenge=code_challenge,
        code_challenge_method='S256'
    )
    _state_store['current'] = state
    return redirect(auth_url)

@app.route('/callback')
def callback():
    try:
        flow = Flow.from_client_secrets_file(
            'credentials.json', scopes=SCOPES,
            redirect_uri=f'{NGROK_URL}/callback',
            state=_state_store.get('current', ''))
        auth_resp = request.url.replace('http://', 'https://')
        code_verifier = _state_store.get('code_verifier', '')
        flow.fetch_token(
            authorization_response=auth_resp,
            code_verifier=code_verifier
        )
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

@app.route('/scan')
def scan():
    try:
        token_data = _creds_store.get('current')
        if not token_data:
            return redirect('/')

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

            # 1. 排除系統報告
            if is_system_report(sender, subject):
                skipped += 1
                continue

            # 2. 白名單
            if is_whitelisted(sender):
                whitelist_emails.append({'sender': sender[:60], 'subject': subject[:55]})
                continue

            # 3. 完整分析
            report, html_score, html_findings = full_multimodal_pipeline(text, html)
            html_tags = [cat for cat, _ in html_findings[:3]]
            ml_vec = vectorizer.transform([text])
            ml_prob = model.predict_proba(ml_vec)[0][list(model.classes_).index('spam')]
            rule_score, _ = rule_based_score(text)

            entry = {
                'sender': sender[:60], 'subject': subject[:55],
                'risk_level': report['risk_level'],
                'risk_score': report['risk_score'],
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
        total = len(high_emails) + len(med_emails) + len(low_emails)

        return render_template_string(RESULT_HTML,
            scan_time=scan_time,
            total=total + len(whitelist_emails),
            high=len(high_emails), med=len(med_emails),
            low=len(low_emails),
            whitelist_count=len(whitelist_emails),
            skipped=skipped,
            high_emails=high_emails, med_emails=med_emails,
            low_emails=low_emails, whitelist_emails=whitelist_emails)

    except Exception as e:
        import traceback
        return f'<h2>掃描錯誤</h2><pre>{traceback.format_exc()}</pre>', 500

# ── 啟動 ────────────────────────────────────────────────────
if __name__ == '__main__':
    os.system('kill -9 $(lsof -t -i:5000) 2>/dev/null || true')
    ngrok.set_auth_token(NGROK_TOKEN)
    tunnel = ngrok.connect(5000, domain='implode-blighted-fling.ngrok-free.dev')
    print(f'\n🌐 網站網址：{tunnel.public_url}')
    print('點擊網址，然後按「使用 Google 帳號授權」開始掃描！\n')
    app.run(port=5000, use_reloader=False, debug=False)
