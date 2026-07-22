# ============================================================
# AI 釣魚信件偵測系統 - Flask 網頁版 (Render 穩定防 502 崩潰版)
# ============================================================

import json, os, uuid, base64, re, secrets, hashlib
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from groq import Groq
from bs4 import BeautifulSoup
from flask import Flask, redirect, request, render_template_string, session, jsonify
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# ── 1. 初始化 Flask App ──────────────────────────────────────
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', secrets.token_hex(16))
_ir_reports_store = {}

# ── 2. 環境變數與設定 ────────────────────────────────────────
GROQ_API_KEY = os.getenv('GROQ_API_KEY', 'gsk_填入你的key')
MY_EMAIL     = os.getenv('MY_EMAIL', 'sherry940501@gmail.com')
SCOPES       = ['https://www.googleapis.com/auth/gmail.readonly']

WHITELIST_DOMAINS = [
    'skims.com', 'emails.skims.com', 'links.skims.com',
    'lululemon.com', 'email.lululemon.com', 'e.lululemon.com',
    'aloyoga.com', 'email.aloyoga.com',
    'esunbank.com.tw', 'esun.com.tw', 'esunsec.com.tw',
    'google.com', 'accounts.google.com', 'googlemail.com',
    'googleaistudio-noreply@google.com',
]

SKIP_SUBJECTS = ['[警告]', '[正常]', 'AI 釣魚偵測報告', 'AI 釣魚信件偵測報告']

CRED_DATA = {
    "web": {
        "client_id": "727861534469-72ihfsri6r9kpnu56n7541qb2e4ngomk.apps.googleusercontent.com",
        "project_id": "phishing-detector-494720",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_secret": "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",
        "redirect_uris": ["https://phishing-detector-n8rv.onrender.com/callback"]
    }
}

with open('credentials.json', 'w') as f:
    json.dump(CRED_DATA, f)

groq_client = Groq(api_key=GROQ_API_KEY)

# ── 3. 輕量化中英文分詞與 ML 模型初始化 ──────────────────────
def fast_tokenizer(text):
    """輕量化分詞，不依賴重型套件，避免 Render 502 Timeout"""
    return re.findall(r'[\u4e00-\u9fa5]|\w+', text.lower())

print('⚡ 初始化 ML 垃圾信件分類模型...')
try:
    url = 'https://raw.githubusercontent.com/justmarkham/pycon-2016-tutorial/master/data/sms.tsv'
    df = pd.read_csv(url, sep='\t', header=None, names=['label', 'text'], timeout=5)
    X_train, _, y_train, _ = train_test_split(df['text'], df['label'], test_size=0.1, random_state=42)
except Exception as e:
    print(f'⚠️ 遠端資料集載入失敗 ({e})，切換至本地預設數據引擎...')
    X_train = pd.Series([
        "Free entry in 2 a wkly comp to win FA Cup final tkts 21st May 2005",
        "URGENT! Your Mobile number has been awarded a $2000 prize",
        "Dear customer, please verify your account immediately at http://secure-bank.xyz",
        "恭喜您獲得免費中獎禮券，請點擊連結領取：http://free-gift.xyz",
        "您的銀行帳戶因異常操作已被暫停，請立即輸入密碼驗證",
        "Hey, are we still meeting for lunch today?",
        "Your Amazon order has been shipped and will arrive tomorrow.",
        "請問明天的會議時間有更改嗎？謝謝",
        "玉山銀行提醒您：本月帳單已寄出，感謝您的使用。"
    ])
    y_train = pd.Series(["spam", "spam", "spam", "spam", "spam", "ham", "ham", "ham", "ham"])

vectorizer = TfidfVectorizer(tokenizer=fast_tokenizer, max_features=1500, token_pattern=None)
X_train_vec = vectorizer.fit_transform(X_train)
model = LogisticRegression(max_iter=500, random_state=42)
model.fit(X_train_vec, y_train)
print('✅ ML 模型快速初始化完成！')

# ── 4. 分析引擎與工具函式 ──────────────────────────────────
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

def analyze_html(html_content):
    findings = []; score = 0
    soup = BeautifulSoup(html_content, 'html.parser')
    links = soup.find_all('a', href=True)
    
    for link in links:
        href = link.get('href', '').strip()
        text = link.get_text().strip()
        if ('http://' in text or 'https://' in text) and text != href:
            score += 5
            findings.append(('偽裝連結', [f'文字:{text[:20]} -> 實際:{href[:20]}']))
        for d in ['xyz','biz','secure-','login-','verify']:
            if d in href.lower():
                score += 3; findings.append(('可疑網域', [href[:30]])); break

    imgs = soup.find_all('img')
    trackers = []
    for img in imgs:
        if str(img.get('width', '')) in ['1', '0'] or str(img.get('height', '')) in ['1', '0']:
            trackers.append(img.get('src', '')[:30]); score += 2
    if trackers: findings.append(('像素追蹤', trackers[:2]))

    hidden = soup.find_all(style=re.compile(r'display\s*:\s*none', re.I))
    if hidden: findings.append(('隱藏元素', [f'{len(hidden)} 個'])); score += 3

    brand_keywords = ['paypal','microsoft','apple','amazon','facebook','netflix','玉山']
    found = [b for b in brand_keywords if b in soup.get_text().lower()]
    if found: findings.append(('品牌關鍵字', [', '.join(found)])); score += 2

    return score, findings

def ai_agent_analyze(text, rule_score, triggered_rules):
    rules_str = ', '.join(triggered_rules) if triggered_rules else 'none'
    prompt = (
        "You are a cybersecurity analyst. Analyze this message and reply ONLY with valid JSON.\n"
        f"Message: {text}\nRule score: {rule_score}, Triggered: {rules_str}\n"
        'JSON format:\n'
        '{\n'
        '  "risk_level": "high/medium/low",\n'
        '  "risk_score": 0-100,\n'
        '  "category": "釣魚信件/詐騙簡訊/正常信件/商業詐騙",\n'
        '  "suspicious_points": ["點1", "點2"],\n'
        '  "explanation": "繁體中文2-3句說明",\n'
        '  "recommended_action": "繁體中文處置建議"\n'
        '}'
    )
    try:
        resp = groq_client.chat.completions.create(
            model='llama-3.3-70b-versatile',
            messages=[{'role': 'user', 'content': prompt}],
            response_format={"type": "json_object"},
            temperature=0.1)
        return json.loads(resp.choices[0].message.content)
    except Exception as e:
        return {'risk_level': 'low', 'risk_score': 0, 'category': '分析失敗',
                'suspicious_points': [], 'explanation': f'AI 分析異常: {str(e)}',
                'recommended_action': '請手動檢查'}

def full_multimodal_pipeline(text, html=''):
    score, rules = rule_based_score(text)
    vec = vectorizer.transform([text])
    spam_prob = model.predict_proba(vec)[0][list(model.classes_).index('spam')]
    html_score = 0; html_findings = []
    if html: html_score, html_findings = analyze_html(html)
    total = score + (html_score // 2)
    
    needs_ai = total >= 3 or spam_prob >= 0.3
    if needs_ai:
        report = ai_agent_analyze(text, total, rules)
    else:
        report = {'risk_level': 'low', 'risk_score': int(spam_prob * 100),
                  'category': '正常信件', 'explanation': '經規則引擎與機器學習檢視無異常誘騙特徵。',
                  'recommended_action': '可安全閱讀', 'suspicious_points': []}
                  
    for cat, items in html_findings:
        for item in items:
            report['suspicious_points'].append(f'[HTML] {cat}: {item}')
    return report, html_score, html_findings

def generate_incident_report(email_data, report):
    now = datetime.now()
    incident_id = f"IR-{now.strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"
    prompt = (
        "You are a SOC cybersecurity responder. Reply ONLY with valid JSON.\n"
        f"Email from: {email_data['sender']}\nSubject: {email_data['subject']}\n"
        f"Risk: {report['risk_score']}/100, Category: {report['category']}\n"
        'JSON format:\n'
        '{\n'
        '  "severity": "Critical/High/Medium",\n'
        '  "attack_type": "Credential Harvesting / Financial Fraud / Phishing",\n'
        '  "impact_assessment": "繁體中文評估分析",\n'
        '  "immediate_actions": ["步驟1", "步驟2", "步驟3"]\n'
        '}'
    )
    try:
        resp = groq_client.chat.completions.create(
            model='llama-3.3-70b-versatile',
            messages=[{'role': 'user', 'content': prompt}],
            response_format={"type": "json_object"},
            temperature=0.1)
        ir = json.loads(resp.choices[0].message.content)
    except:
        ir = {'severity': 'High', 'attack_type': 'Phishing Attack',
              'impact_assessment': '可能導致帳號憑證外洩或遭受進一步社交工程攻擊',
              'immediate_actions': ['切勿點擊信件內任何連結', '勿輸入任何個人密碼或資訊', '通報企業資安團隊隔離該郵件']}
    return incident_id, ir

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

# ── 5. 前端 HTML 模板 ────────────────────────────────────────
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
        body { font-family: 'Inter', 'Noto Sans TC', sans-serif; background-color: #07090e; color: #d1d5db; min-height: 100vh; line-height: 1.5; }
        .header { background: rgba(7, 9, 14, 0.8); backdrop-filter: blur(16px); border-bottom: 1px solid rgba(255, 255, 255, 0.08); padding: 16px 36px; display: flex; align-items: center; justify-content: space-between; position: sticky; top: 0; z-index: 50; }
        .header h1 { font-size: 18px; font-weight: 700; color: #ffffff; }
        .badge { background: rgba(56, 189, 248, 0.08); color: #38bdf8; font-size: 11px; font-weight: 600; padding: 4px 10px; border-radius: 6px; border: 1px solid rgba(56, 189, 248, 0.25); font-family: 'JetBrains Mono', monospace; }
        .container { max-width: 880px; margin: 0 auto; padding: 64px 24px; text-align: center; }
        h2 { font-size: 38px; font-weight: 700; color: #f9fafb; margin-bottom: 16px; }
        .sub { font-size: 15px; color: #9ca3af; max-width: 500px; margin: 0 auto 36px; }
        .btn { display: inline-flex; align-items: center; gap: 12px; background: #f9fafb; color: #030712; font-size: 14px; font-weight: 600; padding: 14px 28px; border-radius: 8px; text-decoration: none; }
        .btn:hover { background: #ffffff; transform: translateY(-2px); }
        .features { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 16px; margin-top: 60px; text-align: left; }
        .feat { background: rgba(15, 23, 42, 0.4); border: 1px solid rgba(255, 255, 255, 0.06); border-radius: 12px; padding: 24px; text-align: center; }
        .feat h3 { font-size: 14px; font-weight: 600; color: #f3f4f6; margin-bottom: 6px; }
        .feat p { font-size: 12px; color: #9ca3af; }
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
        <a href="/login" class="btn">使用 Google 帳號授權</a>
        <div class="features">
            <div class="feat"><h3>🔍 三層 AI 分析</h3><p>規則引擎 + ML + LLaMA 3.3 深度分析</p></div>
            <div class="feat"><h3>🌐 HTML 多模態</h3><p>偵測像素追蹤、偽裝連結、隱藏元素</p></div>
            <div class="feat"><h3>📄 IR 事件報告</h3><p>高風險信件自動產生資安事件通報</p></div>
        </div>
    </div>
</body>
</html>"""

RESULT_HTML = """<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>掃描結果 — AI 釣魚信件偵測系統</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&family=Noto+Sans+TC:wght@400;500;700&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: 'Inter', 'Noto Sans TC', sans-serif; background-color: #07090e; color: #d1d5db; min-height: 100vh; }
        .header { background: rgba(7, 9, 14, 0.8); padding: 16px 36px; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid rgba(255, 255, 255, 0.08); }
        .header h1 { font-size: 18px; font-weight: 700; color: #ffffff; }
        .container { max-width: 880px; margin: 0 auto; padding: 32px 24px 60px; }
        .back { display: inline-flex; color: #38bdf8; font-size: 12px; padding: 8px 14px; text-decoration: none; border: 1px solid rgba(56, 189, 248, 0.2); border-radius: 6px; margin-bottom: 24px; }
        .dashboard-grid { display: grid; grid-template-columns: 2fr 1fr; gap: 20px; margin-bottom: 32px; align-items: center; }
        .summary { background: rgba(15, 23, 42, 0.4); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 12px; padding: 20px; display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; text-align: center; }
        .chart-card { background: rgba(15, 23, 42, 0.4); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 12px; padding: 12px; display: flex; justify-content: center; height: 160px; }
        .stat .num { font-size: 24px; font-weight: 700; font-family: 'JetBrains Mono', monospace; }
        .stat .lbl { font-size: 11px; color: #6b7280; margin-top: 4px; }
        .high .num { color: #ff4d4d; } .med .num { color: #fbbf24; } .low .num { color: #34d399; } .total .num { color: #38bdf8; } .skip .num { color: #4b5563; }
        .sec-title { font-size: 15px; font-weight: 600; color: #f3f4f6; margin: 32px 0 16px; }
        .card { background: rgba(15, 23, 42, 0.3); border: 1px solid rgba(255, 255, 255, 0.06); border-radius: 10px; padding: 18px 20px; margin-bottom: 12px; }
        .card.h { border-left: 3px solid #ff4d4d; } .card.m { border-left: 3px solid #fbbf24; } .card.l { border-left: 3px solid #34d399; } .card.w { border-left: 3px solid #4b5563; opacity: 0.6; }
        .top { display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; }
        .subj { font-size: 14px; font-weight: 600; color: #f9fafb; }
        .from { font-size: 12px; color: #6b7280; margin-top: 3px; }
        .exp { font-size: 13px; color: #9ca3af; margin-top: 8px; line-height: 1.6; }
        .act { font-size: 12px; color: #38bdf8; margin-top: 10px; font-weight: 500; }
        .ir { background: rgba(52, 211, 153, 0.03); border: 1px solid rgba(52, 211, 153, 0.2); border-radius: 6px; padding: 12px; margin-top: 12px; }
        .export-btn { background: rgba(52, 211, 153, 0.1); color: #34d399; border: 1px solid rgba(52, 211, 153, 0.3); padding: 2px 8px; border-radius: 4px; font-size: 11px; text-decoration: none; }
    </style>
</head>
<body>
    <div class="header"><h1>🛡️ AI 釣魚信件偵測系統</h1><span>{{scan_time}}</span></div>
    <div class="container">
        <a href="/" class="back">← RESCAN</a>
        <div class="dashboard-grid">
            <div class="summary">
                <div class="stat total"><div class="num">{{total}}</div><div class="lbl">總掃描數</div></div>
                <div class="stat high"><div class="num">{{high}}</div><div class="lbl">🚨 高風險</div></div>
                <div class="stat med"><div class="num">{{med}}</div><div class="lbl">⚠️ 中風險</div></div>
                <div class="stat low"><div class="num">{{low}}</div><div class="lbl">✅ 安全</div></div>
                <div class="stat skip"><div class="num">{{whitelist_count}}</div><div class="lbl">🔒 白名單</div></div>
                <div class="stat skip"><div class="num">{{skipped}}</div><div class="lbl">⏭️ 略過</div></div>
            </div>
            <div class="chart-card"><canvas id="riskChart"></canvas></div>
        </div>

        {% if high_emails %}
        <div class="sec-title">🚨 高風險信件</div>
        {% for e in high_emails %}
        <div class="card h">
            <div class="top"><div><div class="subj">{{e.subject}}</div><div class="from">{{e.sender}}</div></div></div>
            <div class="exp">{{e.explanation}}</div>
            <div class="act">📋 {{e.recommended_action}}</div>
            {% if e.ir_id %}
            <div class="ir">
                <div style="display:flex;justify-content:space-between;"><span>📄 IR 事件報告已生成</span><a href="/export_ir/{{e.ir_id}}" class="export-btn">匯出 JSON</a></div>
                <div style="font-size:11px;color:#6b7280;margin-top:4px;">{{e.ir_id}} | {{e.ir_severity}}</div>
                <div style="font-size:12px;color:#a7f3d0;margin-top:4px;">{{e.ir_summary}}</div>
            </div>
            {% endif %}
        </div>
        {% endfor %}
        {% endif %}

        {% if med_emails %}
        <div class="sec-title">⚠️ 中風險信件</div>
        {% for e in med_emails %}
        <div class="card m">
            <div class="top"><div><div class="subj">{{e.subject}}</div><div class="from">{{e.sender}}</div></div></div>
            <div class="exp">{{e.explanation}}</div>
            <div class="act">📋 {{e.recommended_action}}</div>
        </div>
        {% endfor %}
        {% endif %}

        {% if low_emails %}
        <div class="sec-title">✅ 安全信件</div>
        {% for e in low_emails %}
        <div class="card l">
            <div class="top"><div><div class="subj">{{e.subject}}</div><div class="from">{{e.sender}}</div></div></div>
            <div class="exp">{{e.explanation}}</div>
        </div>
        {% endfor %}
        {% endif %}
    </div>
    <script>
        const ctx = document.getElementById('riskChart').getContext('2d');
        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['高風險', '中風險', '安全', '白名單'],
                datasets: [{ data: [{{high}}, {{med}}, {{low}}, {{whitelist_count}}], backgroundColor: ['#ff4d4d', '#fbbf24', '#34d399', '#4b5563'], borderWidth: 0 }]
            },
            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } }
        });
    </script>
</body>
</html>"""

# ── 6. Flask 路由 ─────────────────────────────────────────────
@app.route('/')
def index():
    return render_template_string(HOME_HTML)

@app.route('/login')
def login():
    code_verifier = secrets.token_urlsafe(64)
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).rstrip(b'=').decode()

    session['code_verifier'] = code_verifier
    flow = Flow.from_client_secrets_file(
        'credentials.json', scopes=SCOPES,
        redirect_uri=request.url_root.rstrip('/') + '/callback')
    
    auth_url, state = flow.authorization_url(
        prompt='consent', access_type='offline',
        code_challenge=code_challenge, code_challenge_method='S256'
    )
    session['oauth_state'] = state
    return redirect(auth_url)

@app.route('/callback')
def callback():
    try:
        flow = Flow.from_client_secrets_file(
            'credentials.json', scopes=SCOPES,
            redirect_uri=request.url_root.rstrip('/') + '/callback',
            state=session.get('oauth_state'))
            
        auth_resp = request.url.replace('http://', 'https://')
        flow.fetch_token(
            authorization_response=auth_resp,
            code_verifier=session.get('code_verifier')
        )
        
        creds = flow.credentials
        session['tokens'] = {
            'token': creds.token, 'refresh_token': creds.refresh_token,
            'token_uri': creds.token_uri, 'client_id': creds.client_id,
            'client_secret': creds.client_secret, 'scopes': list(creds.scopes)
        }
        return redirect('/scan')
    except Exception as e:
        import traceback
        return f'<h2>授權失敗</h2><pre>{traceback.format_exc()}</pre>', 500

def process_single_email(service, msg_ref):
    try:
        msg = service.users().messages().get(
            userId='me', id=msg_ref['id'], format='full').execute()
        sender  = get_header(msg, 'From')
        subject = get_header(msg, 'Subject') or '(無主旨)'
        
        if is_system_report(sender, subject):
            return 'skipped', None
        if is_whitelisted(sender):
            return 'whitelist', {'sender': sender[:60], 'subject': subject[:55]}

        body = get_email_body(msg)
        html = get_email_html(msg)
        text = f"From: {sender}\nSubject: {subject}\nBody: {body}"

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
            'ir_id': None, 'ir_severity': None, 'ir_summary': None
        }

        if report['risk_level'] == 'high':
            ir_id, ir_detail = generate_incident_report({'sender': sender, 'subject': subject}, report)
            entry.update({
                'ir_id': ir_id,
                'ir_severity': ir_detail.get('severity', 'High'),
                'ir_summary': ir_detail.get('impact_assessment', '')[:120]
            })
            _ir_reports_store[ir_id] = ir_detail
            return 'high', entry
        elif report['risk_level'] == 'medium':
            return 'med', entry
        else:
            return 'low', entry
            
    except Exception:
        return 'error', None

@app.route('/scan')
def scan():
    try:
        tokens = session.get('tokens')
        if not tokens: return redirect('/')

        creds = Credentials(**tokens)
        service = build('gmail', 'v1', credentials=creds)
        results_api = service.users().messages().list(
            userId='me', maxResults=15, labelIds=['INBOX']).execute()
        messages = results_api.get('messages', [])

        high_emails, med_emails, low_emails = [], [], []
        whitelist_emails = []
        skipped = 0

        # 控制為 3 個 Workers 避免爆記憶體
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(process_single_email, service, m) for m in messages]
            for future in futures:
                status, result = future.result()
                if status == 'high': high_emails.append(result)
                elif status == 'med': med_emails.append(result)
                elif status == 'low': low_emails.append(result)
                elif status == 'whitelist': whitelist_emails.append(result)
                elif status == 'skipped': skipped += 1

        scan_time = datetime.now().strftime('%Y-%m-%d %H:%M')
        total = len(high_emails) + len(med_emails) + len(low_emails)

        return render_template_string(RESULT_HTML,
            scan_time=scan_time,
            total=total + len(whitelist_emails),
            high=len(high_emails), med=len(med_emails), low=len(low_emails),
            whitelist_count=len(whitelist_emails), skipped=skipped,
            high_emails=high_emails, med_emails=med_emails,
            low_emails=low_emails, whitelist_emails=whitelist_emails)

    except Exception as e:
        import traceback
        return f'<h2>掃描失敗</h2><pre>{traceback.format_exc()}</pre>', 500

@app.route('/export_ir/<ir_id>')
def export_ir(ir_id):
    report = _ir_reports_store.get(ir_id)
    if not report: return "Report not found", 404
    return jsonify({"incident_id": ir_id, "report_details": report})

if __name__ == '__main__':
    app.run(port=5000, use_reloader=False, debug=False)
