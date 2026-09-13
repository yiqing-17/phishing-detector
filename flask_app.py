# ============================================================
# AI 釣魚信件偵測系統 - Flask 網頁版 v8（可疑特徵解釋版）
# ============================================================

import json, os, uuid, threading, base64, re, sqlite3, smtplib
import joblib
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

# ── 設定區 ───────────────────────────────────────────────────
# 敏感資訊一律由 Render Environment Variables 提供，不寫死在程式碼。
GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')
MY_EMAIL     = os.environ.get('MY_EMAIL', '')
BASE_URL     = os.environ.get('BASE_URL', 'http://localhost:5000')
SCOPES       = ['https://www.googleapis.com/auth/gmail.readonly']

# 本機 HTTP 測試才允許 OAuthlib；Render HTTPS 不需要。
if BASE_URL.startswith('http://'):
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

DEFAULT_WHITELIST = [
    'skims.com', 'emails.skims.com', 'links.skims.com',
    'lululemon.com', 'email.lululemon.com', 'e.lululemon.com',
    'aloyoga.com', 'email.aloyoga.com',
    'esunbank.com.tw', 'esun.com.tw', 'esunsec.com.tw',
    'google.com', 'accounts.google.com', 'googlemail.com',
]

SKIP_SUBJECTS = ['[警告]', '[正常]', 'AI 釣魚偵測報告', 'AI 釣魚信件偵測報告']

GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')
GOOGLE_PROJECT_ID = os.environ.get('GOOGLE_PROJECT_ID', 'phishing-detector')

if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
    CRED_DATA = {
        "web": {
            "client_id": GOOGLE_CLIENT_ID,
            "project_id": GOOGLE_PROJECT_ID,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uris": [f"{BASE_URL}/callback"]
        }
    }
    with open('credentials.json', 'w', encoding='utf-8') as f:
        json.dump(CRED_DATA, f)
else:
    print('WARNING: GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET 尚未設定，Gmail OAuth 將無法使用。')

# ── CSS 共用樣式 (全站統一風格：極簡深藍黑主題 + 自訂精緻微型捲軸) ───────────────────
COMMON_CSS = """
<style>
:root {
  --bg-main: #0b0d12;
  --bg-card: rgba(15, 23, 42, 0.5);
  --bg-hover: rgba(30, 41, 59, 0.6);
  --border-subtle: rgba(255, 255, 255, 0.07);
  --border-accent: rgba(255, 255, 255, 0.15);
  --text-main: #f8fafc;
  --text-muted: #8a99ad;
  --text-dim: #64748b;
  --red: #ef4444; --red-bg: rgba(239, 68, 68, 0.1); --red-border: rgba(239, 68, 68, 0.25);
  --orange: #f97316; --orange-bg: rgba(249, 115, 22, 0.1); --orange-border: rgba(249, 115, 22, 0.25);
  --green: #10b981; --green-bg: rgba(16, 185, 129, 0.1); --green-border: rgba(16, 185, 129, 0.25);
  --blue: #3b82f6; --blue-bg: rgba(59, 130, 246, 0.1);
}
* { 
  box-sizing: border-box; 
  margin: 0; 
  padding: 0; 
  scrollbar-width: thin;
  scrollbar-color: rgba(255, 255, 255, 0.12) transparent;
}
body { 
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: var(--bg-main); 
  color: var(--text-main); 
  min-height: 100vh; 
}

/* ── 全站自訂精緻捲軸樣式 (Webkit Custom Scrollbars) ── */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}
::-webkit-scrollbar-track {
  background: transparent;
}
::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.12);
  border-radius: 99px;
  transition: background 0.2s ease;
}
::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.28);
}

/* 全站統一導航列 */
.hdr { 
  border-bottom: 1px solid var(--border-subtle); 
  padding: 16px 32px;
  display: flex; 
  align-items: center; 
  justify-content: space-between; 
}
.hdr-left { display: flex; align-items: center; gap: 10px; font-weight: 600; font-size: 15px; letter-spacing: 0.3px; }
.shield-icon { font-size: 16px; display: inline-flex; align-items: center; }
.hdr h1 { font-size: 15px; font-weight: 600; color: var(--text-main); letter-spacing: 0.3px; }
.hdr-nav { display: flex; gap: 8px; align-items: center; }
.hdr-nav a { 
  font-size: 12px; 
  color: var(--text-muted); 
  text-decoration: none;
  padding: 6px 12px; 
  border-radius: 6px; 
  border: 1px solid var(--border-subtle);
  transition: all 0.2s ease; 
}
.hdr-nav a:hover { color: var(--text-main); border-color: var(--border-accent); background: var(--bg-hover); }
.proj-tag { 
  background: rgba(255, 255, 255, 0.04); 
  border: 1px solid var(--border-subtle);
  color: var(--text-dim); 
  font-size: 11px; 
  padding: 4px 10px; 
  border-radius: 4px; 
  font-family: monospace; 
}
.back { 
  display: inline-flex; align-items: center; gap: 6px; font-size: 12px;
  color: var(--text-muted); text-decoration: none; padding: 6px 14px;
  border-radius: 6px; border: 1px solid var(--border-subtle);
  margin-bottom: 20px; transition: all 0.2s ease; 
}
.back:hover { color: var(--text-main); border-color: var(--border-accent); background: var(--bg-hover); }

.score-breakdown{margin-top:14px;padding:14px;border:1px solid #dbe3ef;border-radius:12px;background:#f8fafc}.score-breakdown h4{margin:0 0 10px}.score-row{display:flex;justify-content:space-between;gap:12px;padding:7px 0;border-bottom:1px solid #e8edf3;font-size:13px}.score-total{margin-top:10px;font-weight:700}
</style>
"""

# ── 首頁 HTML (單頁固定 100vh 滿版，無滾輪) ───────────────────
HOME_HTML = COMMON_CSS + """
<style>
html, body {
  height: 100vh;
  overflow: hidden !important;
  margin: 0;
  padding: 0;
}

.landing-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100vw;
  background-color: var(--bg-main);
  color: #e2e8f0;
  box-sizing: border-box;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 0 20px;
  max-width: 860px;
  margin: 0 auto;
  width: 100%;
}

.title {
  font-size: 34px;
  font-weight: 700;
  color: #ffffff;
  margin-bottom: 12px;
  letter-spacing: -0.5px;
  text-align: center;
}

.subtitle {
  font-size: 13.5px;
  color: var(--text-muted);
  line-height: 1.6;
  text-align: center;
  margin-bottom: 32px;
  max-width: 560px;
}

.google-btn-white {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  background: #ffffff;
  color: #1f2937;
  font-size: 14px;
  font-weight: 600;
  padding: 11px 24px;
  border-radius: 8px;
  text-decoration: none;
  box-shadow: 0 2px 12px rgba(255, 255, 255, 0.12);
  transition: all 0.2s ease;
  margin-bottom: 44px;
  border: 1px solid #ffffff;
}
.google-btn-white:hover {
  background: #f8fafc;
  transform: translateY(-2px);
  box-shadow: 0 4px 18px rgba(255, 255, 255, 0.22);
}
.google-icon-svg {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
  display: block;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  width: 100%;
  margin-bottom: 24px;
}
.feature-card {
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: 10px;
  padding: 20px 16px;
  text-align: center;
}
.feature-icon {
  font-size: 18px;
  margin-bottom: 10px;
  opacity: 0.9;
}
.feature-card h3 {
  font-size: 14px;
  font-weight: 600;
  color: #f1f5f9;
  margin-bottom: 6px;
}
.feature-card p {
  font-size: 12px;
  color: var(--text-dim);
  line-height: 1.5;
  margin: 0;
}

.whitelist-banner {
  width: 100%;
  background: var(--green-bg);
  border: 1px solid var(--green-border);
  border-radius: 8px;
  padding: 11px 18px;
  font-size: 12px;
  color: var(--green);
  display: flex;
  align-items: center;
  gap: 8px;
  box-sizing: border-box;
}
.banner-icon { font-size: 13px; flex-shrink: 0; }
.paste-link { display: inline-block; font-size: 12.5px; color: var(--text-muted);
              text-decoration: none; margin-top: -28px; margin-bottom: 36px;
              border-bottom: 1px dashed var(--border-accent); padding-bottom: 1px;
              transition: color 0.2s ease; }
.paste-link:hover { color: var(--text-main); }
</style>

<div class="landing-container">
  <div class="hdr">
    <div class="hdr-left">
      <span class="shield-icon">🛡️</span>
      <span>AI 釣魚信件偵測系統</span>
    </div>
    <div class="hdr-nav">
      <span class="proj-tag">PROJ-2026</span>
    </div>
  </div>

  <div class="main-content">
    <h1 class="title">一鍵掃描你的 Gmail</h1>
    <p class="subtitle">
      授權後系統自動掃描最新 15 封信件，用 AI 識別釣魚攻擊並產生詳細分析報告。
    </p>

    <a href="/login" class="google-btn-white">
      <svg class="google-icon-svg" viewBox="0 0 24 24">
        <path fill="#4285F4" d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.82-2.4 3.68v3.05h3.88c2.27-2.09 3.665-5.17 3.665-9.17z"/>
        <path fill="#34A853" d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.88-3.05c-1.08.72-2.45 1.16-4.05 1.16-3.12 0-5.77-2.1-6.72-4.93H1.29v3.15C3.26 21.3 7.31 24 12 24z"/>
        <path fill="#FBBC05" d="M5.28 14.27c-.25-.72-.38-1.49-.38-2.27s.13-1.55.38-2.27V6.58H1.29C.47 8.21 0 10.05 0 12s.47 3.79 1.29 5.42l3.99-3.15z"/>
        <path fill="#EA4335" d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.31 0 3.26 2.7 1.29 6.58l3.99 3.15c.95-2.83 3.6-4.98 6.72-4.98z"/>
      </svg>
      使用 Google 帳號授權
    </a>

    <a href="/paste" class="paste-link">或直接貼上郵件內容分析 →</a>

    <div class="features-grid">
      <div class="feature-card">
        <div class="feature-icon">🔍</div>
        <h3>三層式智慧分析</h3>
        <p>規則引擎 + ML + HTML / URL + AI 深度分析</p>
      </div>
      <div class="feature-card">
        <div class="feature-icon">🌐</div>
        <h3>HTML 多模態</h3>
        <p>偵測像素追蹤、偽裝連結、隱藏元素</p>
      </div>
      <div class="feature-card">
        <div class="feature-icon">📄</div>
        <h3>IR 事件報告</h3>
        <p>高風險信件自動產生資安事件通報</p>
      </div>
    </div>

    <div class="whitelist-banner">
      <span class="banner-icon">✅</span>
      <div><strong>白名單機制已啟用：</strong> SKIMS、lululemon、Alo Yoga、玉山銀行、Google 等已知安全寄件者將直接標記為安全，不進行 AI 分析。</div>
    </div>
  </div>
</div>
"""

# ── Loading HTML ─────────────────────────────────────────────
LOADING_HTML = COMMON_CSS + """
<style>
.loading-wrap { display: flex; flex-direction: column; align-items: center;
                justify-content: center; min-height: calc(100vh - 57px); gap: 24px; }
.spinner { width: 44px; height: 44px; border: 3px solid var(--border-subtle);
           border-top: 3px solid var(--blue); border-radius: 50%;
           animation: spin 0.9s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.loading-title { font-size: 17px; font-weight: 600; color: var(--text-main); }
.steps { display: flex; flex-direction: column; gap: 10px; }
.step { font-size: 13px; color: var(--text-dim); display: flex; align-items: center; gap: 10px; }
.step.active { color: var(--blue); font-weight: 500; }
.step-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--border-subtle); flex-shrink: 0; }
.step.active .step-dot { background: var(--blue); box-shadow: 0 0 8px var(--blue); }
</style>
<script>
const stepLabels = ['連線 Gmail...','讀取最新信件...','規則引擎分析中...','AI 深度分析中...','產生報告...'];
let i = 0;
setInterval(() => {
  if (i < stepLabels.length) {
    document.querySelectorAll('.step')[i].classList.add('active');
    i++;
  }
}, 2500);
setInterval(() => {
  fetch('/scan_status').then(r => r.json()).then(d => {
    if (d.done) window.location.href = '/result/' + d.scan_id;
  });
}, 1000);
</script>

<div class="hdr">
  <div class="hdr-left">
    <span class="shield-icon">🛡️</span>
    <h1>AI 釣魚信件偵測系統</h1>
  </div>
  <span class="proj-tag">SCANNING...</span>
</div>
<div class="loading-wrap">
  <div class="spinner"></div>
  <div class="loading-title">正在掃描你的 Gmail...</div>
  <div class="steps">
    <div class="step active"><div class="step-dot"></div>連線 Gmail...</div>
    <div class="step"><div class="step-dot"></div>讀取最新信件...</div>
    <div class="step"><div class="step-dot"></div>規則引擎分析中...</div>
    <div class="step"><div class="step-dot"></div>AI 深度分析中...</div>
    <div class="step"><div class="step-dot"></div>產生報告...</div>
  </div>
</div>
"""

# ── 貼上郵件內容分析 HTML（免登入）───────────────────────────
PASTE_HTML = COMMON_CSS + """
<style>
.paste-wrap { max-width: 640px; margin: 0 auto; padding: 40px 20px 60px; }
.paste-title { font-size: 22px; font-weight: 700; color: #fff; margin-bottom: 6px; }
.paste-sub { font-size: 13px; color: var(--text-muted); margin-bottom: 28px; line-height: 1.6; }
.field-label { font-size: 12px; color: var(--text-dim); margin-bottom: 6px;
               display: block; letter-spacing: 0.03em; }
.field-input, .field-textarea {
  width: 100%; background: var(--bg-card); border: 1px solid var(--border-subtle);
  border-radius: 8px; color: var(--text-main); font-size: 13.5px;
  padding: 10px 14px; margin-bottom: 18px; font-family: inherit;
}
.field-input:focus, .field-textarea:focus { outline: none; border-color: var(--border-accent); }
.field-textarea { resize: vertical; min-height: 140px; line-height: 1.6; }
.field-hint { font-size: 11px; color: var(--text-dim); margin: -12px 0 18px; }
.submit-btn {
  background: #ffffff; color: #1f2937; font-size: 14px; font-weight: 600;
  padding: 11px 26px; border-radius: 8px; border: none; cursor: pointer;
  transition: all 0.2s ease;
}
.submit-btn:hover { background: #f1f5f9; transform: translateY(-1px); }
.err-box { background: var(--red-bg); border: 1px solid var(--red-border);
           color: var(--red); font-size: 12.5px; padding: 10px 14px;
           border-radius: 8px; margin-bottom: 18px; }
</style>

<div class="hdr">
  <div class="hdr-left">
    <span class="shield-icon">🛡️</span>
    <h1>AI 釣魚信件偵測系統 — 貼上分析</h1>
  </div>
  <div class="hdr-nav"><a href="/">回首頁</a></div>
  <span class="proj-tag">PROJ-2026</span>
</div>

<div class="paste-wrap">
  <div class="paste-title">貼上郵件內容進行分析</div>
  <div class="paste-sub">不需要 Google 帳號授權，將郵件的寄件者、主旨與內文貼上即可，系統會以相同的三層式（規則引擎 + ML + HTML / URL + AI）架構進行分析。</div>

  ERROR_PLACEHOLDER

  <form method="POST" action="/paste_analyze">
    <label class="field-label">寄件者（選填，用於白名單比對）</label>
    <input class="field-input" type="text" name="sender" placeholder="例如：service@example.com">

    <label class="field-label">主旨</label>
    <input class="field-input" type="text" name="subject" placeholder="郵件主旨">

    <label class="field-label">郵件內文（必填）</label>
    <textarea class="field-textarea" name="body" placeholder="貼上郵件的純文字內容..." required></textarea>

    <label class="field-label">HTML 原始碼（選填，用於偵測像素追蹤／偽裝連結等）</label>
    <textarea class="field-textarea" name="html" placeholder="若有郵件的 HTML 原始碼，可貼於此處以啟用多模態偵測..."></textarea>
    <div class="field-hint">在大部分信箱可透過「顯示原始郵件 / 檢視原始碼」取得 HTML 內容。</div>

    <button class="submit-btn" type="submit">開始分析</button>
  </form>
</div>
"""

# ── 結果頁 HTML (修正點擊與高亮同步邏輯) ─────────────────────
RESULT_HTML = COMMON_CSS + """
<style>
.summary { display: flex; border-bottom: 1px solid var(--border-subtle); background: rgba(15, 23, 42, 0.3); }
.stat { flex: 1; padding: 14px 24px; border-right: 1px solid var(--border-subtle); }
.stat:last-child { border-right: none; }
.stat-num { font-size: 22px; font-weight: 700; margin-bottom: 2px; }
.stat-lbl { font-size: 11px; color: var(--text-dim); letter-spacing: 0.05em; text-transform: uppercase; }
.s-total .stat-num { color: var(--text-main); }
.s-high  .stat-num { color: var(--red); }
.s-med   .stat-num { color: var(--orange); }
.s-low   .stat-num { color: var(--green); }
.s-wl    .stat-num { color: var(--text-muted); }
.s-sk    .stat-num { color: var(--text-dim); }

.main { display: flex; height: calc(100vh - 120px); }
.left { width: 320px; border-right: 1px solid var(--border-subtle); overflow-y: auto; flex-shrink: 0; }
.list-sec { padding: 12px 18px 8px; font-size: 10px; color: var(--text-dim);
            letter-spacing: 0.08em; text-transform: uppercase; font-weight: 600;
            border-bottom: 1px solid var(--border-subtle); }

.email-item { padding: 14px 18px; border-bottom: 1px solid var(--border-subtle);
              cursor: pointer; transition: all 0.15s ease;
              display: flex; align-items: flex-start; gap: 10px; border-left: 3px solid transparent; }
.email-item:hover { background: var(--bg-hover); }
.email-item.active { background: var(--bg-hover); border-left-color: var(--blue); }

.risk-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; margin-top: 5px; }
.dot-high { background: var(--red); box-shadow: 0 0 6px var(--red); }
.dot-med  { background: var(--orange); }
.dot-low  { background: var(--green); }
.dot-wl   { background: var(--text-dim); }
.item-body { flex: 1; min-width: 0; }
.item-subj { font-size: 13px; color: var(--text-main); white-space: nowrap;
              overflow: hidden; text-overflow: ellipsis; margin-bottom: 3px; font-weight: 500; }
.item-from { font-size: 11px; color: var(--text-muted); white-space: nowrap;
              overflow: hidden; text-overflow: ellipsis; }
.item-score { font-size: 10px; color: var(--text-dim); margin-top: 3px; }

.right { flex: 1; overflow-y: auto; padding: 28px 36px; }
.detail-badge { display: inline-flex; align-items: center; gap: 6px;
                padding: 4px 12px; border-radius: 20px; font-size: 11px;
                font-weight: 600; margin-bottom: 14px; }
.badge-high { background: var(--red-bg); color: var(--red); border: 1px solid var(--red-border); }
.badge-med  { background: var(--orange-bg); color: var(--orange); border: 1px solid var(--orange-border); }
.badge-low  { background: var(--green-bg); color: var(--green); border: 1px solid var(--green-border); }
.badge-wl   { background: var(--bg-card); color: var(--text-muted); border: 1px solid var(--border-subtle); }

.detail-subj { font-size: 20px; font-weight: 700; color: #ffffff;
                margin-bottom: 6px; letter-spacing: -0.3px; line-height: 1.3; }
.detail-from { font-size: 12px; color: var(--text-muted); margin-bottom: 22px; }
.gold-line { width: 100%; height: 1px; background: var(--border-subtle); margin: 18px 0; }
.sec-label { font-size: 10px; color: var(--text-dim); letter-spacing: 0.08em;
              text-transform: uppercase; margin-bottom: 8px; font-weight: 600; }
.detail-text { font-size: 13.5px; color: #e2e8f0; line-height: 1.7; }
.tag-row { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 12px; }
.htag { font-size: 11px; color: var(--orange); background: var(--orange-bg);
        padding: 3px 8px; border-radius: 4px; border: 1px solid var(--orange-border); }

.layer-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; margin-top: 14px; }
.layer-card { background: rgba(15, 23, 42, 0.45); border: 1px solid var(--border-subtle);
               border-radius: 9px; padding: 13px 14px; }
.layer-head { display: flex; align-items: center; justify-content: space-between; gap: 10px; margin-bottom: 8px; }
.layer-name { font-size: 12px; color: var(--text-main); font-weight: 600; }
.layer-score { font-size: 12px; color: var(--text-main); font-weight: 700; }
.layer-status { font-size: 11px; color: var(--text-muted); margin-bottom: 7px; line-height: 1.45; }
.bar { height: 5px; background: rgba(255,255,255,.06); border-radius: 99px; overflow: hidden; }
.bar-fill { height: 100%; border-radius: 99px; background: var(--blue); transition: width .25s ease; }
.layer-meta { display: flex; justify-content: space-between; gap: 8px; margin-top: 7px; font-size: 10px; color: var(--text-dim); }

.evidence-box { margin-top: 14px; background: rgba(15,23,42,.32); border: 1px solid var(--border-subtle);
                border-radius: 9px; padding: 14px 16px; }
.evidence-title { font-size: 12px; color: var(--text-main); font-weight: 600; margin-bottom: 9px; }
.evidence-list { display: flex; flex-direction: column; gap: 6px; }
.evidence-item { font-size: 12px; color: var(--text-muted); line-height: 1.55; padding-left: 13px; position: relative; }
.evidence-item::before { content: ''; position: absolute; left: 0; top: 8px; width: 5px; height: 5px; border-radius: 50%; background: var(--orange); }
.fusion-note { margin-top: 12px; font-size: 10.5px; color: var(--text-dim); }

.recommend { font-size: 13px; color: var(--text-main); background: var(--bg-card);
             border: 1px solid var(--border-subtle); border-radius: 8px;
             padding: 14px 18px; line-height: 1.6; }
.ir-box { background: rgba(16, 185, 129, 0.05); border: 1px solid var(--green-border);
          border-left: 3px solid var(--green); border-radius: 8px;
          padding: 16px 20px; margin-top: 20px; }
.ir-label { font-size: 10px; color: var(--green); letter-spacing: 0.08em;
            text-transform: uppercase; margin-bottom: 6px; font-weight: 600; }
.ir-id { font-size: 11px; color: var(--text-dim); font-family: monospace; margin-bottom: 6px; }
.ir-impact { font-size: 12px; color: #a7f3d0; line-height: 1.6; }
.ir-actions { margin-top: 10px; display: flex; flex-direction: column; gap: 4px; }
.ir-action { font-size: 12px; color: #93c5fd; }
.ir-meta { display:grid; grid-template-columns: repeat(3, 1fr); gap:8px; margin-top:12px; }
.ir-meta-item { background: rgba(15,23,42,.35); border:1px solid var(--border-subtle); border-radius:6px; padding:8px; }
.ir-meta-label { font-size:9px; color:var(--text-dim); text-transform:uppercase; }
.ir-meta-value { font-size:11px; color:var(--text-main); margin-top:3px; }
.ir-section { margin-top:12px; }
.ir-section-title { font-size:10px; color:var(--text-dim); font-weight:600; margin-bottom:5px; }
.ir-text { font-size:12px; color:var(--text-muted); line-height:1.6; }
.empty-detail { display: flex; align-items: center; justify-content: center;
                height: 100%; color: var(--text-dim); font-size: 13px;
                flex-direction: column; gap: 10px; }
.empty-icon { font-size: 32px; opacity: 0.4; }

.why-box { margin-top: 14px; }
.why-title { font-size: 13px; color: var(--text-main); font-weight: 700; margin-bottom: 10px; }
.why-list { display: flex; flex-direction: column; gap: 8px; }
.why-item { display: flex; gap: 10px; align-items: flex-start; padding: 11px 12px;
            border: 1px solid var(--border-subtle); border-radius: 8px;
            background: rgba(15,23,42,.3); }
.why-badge { min-width: 42px; text-align: center; font-size: 9px; font-weight: 700;
             border-radius: 4px; padding: 3px 5px; margin-top: 1px; }
.why-high { color: var(--red); background: var(--red-bg); border: 1px solid var(--red-border); }
.why-medium { color: var(--orange); background: var(--orange-bg); border: 1px solid var(--orange-border); }
.why-low { color: var(--green); background: var(--green-bg); border: 1px solid var(--green-border); }

.safety-box { margin-top: 14px; padding: 14px 16px; border-radius: 10px;
              background: var(--bg-card); border: 1px solid var(--border-subtle); }
.safety-title { font-size: 12px; font-weight: 600; color: var(--text-main); margin-bottom: 9px; }
.safety-list { display: flex; flex-direction: column; gap: 7px; }
.safety-item { display: flex; gap: 8px; font-size: 11.5px; color: var(--text-muted); line-height: 1.55; }
.safety-num { width: 18px; height: 18px; border-radius: 50%; border: 1px solid var(--border-subtle);
              display: inline-flex; align-items: center; justify-content: center; flex: 0 0 18px;
              font-size: 10px; color: var(--text-dim); }
.why-content { min-width: 0; }
.why-source { font-size: 10px; color: var(--text-dim); margin-bottom: 2px; }
.why-head { font-size: 12px; color: var(--text-main); font-weight: 600; margin-bottom: 3px; }
.why-detail { font-size: 11.5px; color: var(--text-muted); line-height: 1.5; word-break: break-word; }

@media (max-width: 900px) {
  .summary { overflow-x: auto; }
  .stat { min-width: 95px; padding: 12px 14px; }
  .main { height: auto; min-height: calc(100vh - 120px); }
  .left { width: 280px; }
  .right { padding: 22px 20px; }
}
@media (max-width: 680px) {
  .main { display: block; }
  .left { width: 100%; max-height: 310px; border-right: none; border-bottom: 1px solid var(--border-subtle); }
  .right { min-height: 520px; }
  .layer-grid { grid-template-columns: 1fr; }
}
</style>

<script>
const emailData = PLACEHOLDER_DATA;

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, c => ({
    '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'
  }[c]));
}

function downloadPdf(){
  const idx = window.currentDetailIndex;
  if (idx === undefined || idx === null) return;
  window.location.href = '/report/' + encodeURIComponent(SCAN_ID) + '/' + idx + '/pdf';
}

function showDetail(idx, element) {
  const d = emailData[idx];
  if (!d) return;

  document.querySelectorAll('.email-item').forEach(el => el.classList.remove('active'));
  if (element) {
    element.classList.add('active');
  } else {
    const target = document.querySelector(`.email-item[data-idx="${idx}"]`);
    if (target) target.classList.add('active');
  }

  const panel = document.getElementById('right-panel');
  let badgeClass = d.level === 'high' ? 'badge-high' : d.level === 'medium' ? 'badge-med' : d.level === 'low' ? 'badge-low' : 'badge-wl';
  let badgeText = d.level === 'high' ? '🚨 高風險' : d.level === 'medium' ? '⚠️ 中風險' : d.level === 'low' ? '✅ 安全' : '🔒 白名單';
  let scoreStr = d.risk_score >= 0 ? ` &nbsp;·&nbsp; ${d.risk_score} / 100` : '';

  const layers = d.layers || {};
  const layerOrder = ['rule', 'ml', 'html', 'llm'];
  const layerIcons = {rule:'🔍', ml:'🤖', html:'🌐', llm:'🧠'};

  let layerHtml = '';
  let evidenceHtml = '';

  layerOrder.forEach(key => {
    const x = layers[key];
    if (!x) return;

    const score = x.score == null ? 0 : Math.max(0, Math.min(100, Number(x.score)));
    const scoreText = x.score == null ? '—' : `${Number(x.score).toFixed(0)} / 100`;
    const meta = key === 'ml' && x.probability != null
      ? `釣魚機率 ${Number(x.probability).toFixed(1)}%`
      : `融合權重 ${Number(x.weight || 0).toFixed(1)}%`;

    layerHtml += `
      <div class="layer-card">
        <div class="layer-head">
          <div class="layer-name">${layerIcons[key]} ${escapeHtml(x.name)}</div>
          <div class="layer-score">${scoreText}</div>
        </div>
        <div class="layer-status">${escapeHtml(x.status || '—')}</div>
        <div class="bar"><div class="bar-fill" style="width:${score}%"></div></div>
        <div class="layer-meta"><span>${escapeHtml(meta)}</span><span>${key === 'llm' && x.score == null ? '未提供分數' : '分析完成'}</span></div>
      </div>`;
  });

  layerOrder.forEach(key => {
    const x = layers[key];
    if (!x || !x.findings || !x.findings.length) return;

    const items = x.findings.slice(0, 6).map(v =>
      `<div class="evidence-item">${escapeHtml(v)}</div>`
    ).join('');

    evidenceHtml += `
      <div class="evidence-box">
        <div class="evidence-title">${layerIcons[key]} ${escapeHtml(x.name)} — 偵測證據</div>
        <div class="evidence-list">${items}</div>
      </div>`;
  });

  const explainable = d.explainable_findings || [];
  const whyHtml = explainable.length ? `
    <div class="why-box">
      <div class="why-title">🔎 為什麼會被判定為可疑？</div>
      <div class="why-list">
        ${explainable.map(x => {
          const cls = x.severity === 'high' ? 'why-high' : x.severity === 'low' ? 'why-low' : 'why-medium';
          const label = x.severity === 'high' ? '高風險' : x.severity === 'low' ? '低風險' : '注意';
          return `<div class="why-item">
            <div class="why-badge ${cls}">${label}</div>
            <div class="why-content">
              <div class="why-source">${escapeHtml(x.source || '')}</div>
              <div class="why-head">${escapeHtml(x.title || '')}</div>
              <div class="why-detail">${escapeHtml(x.detail || '')}</div>
            </div>
          </div>`;
        }).join('')}
      </div>
    </div>` : '';

  let tagsHtml = d.tags && d.tags.length
    ? `<div class="tag-row">${d.tags.map(t=>`<span class="htag">${escapeHtml(t)}</span>`).join('')}</div>`
    : '';

  const safetyActions = d.safety_actions || [];
  const safetyHtml = safetyActions.length ? `
    <div class="safety-box">
      <div class="safety-title">🛡️ 安全處置建議</div>
      <div class="safety-list">
        ${safetyActions.map((x, i) => `<div class="safety-item"><span class="safety-num">${i + 1}</span><span>${escapeHtml(x)}</span></div>`).join('')}
      </div>
    </div>` : '';

  let irHtml = d.ir ? `
    <div class="ir-box">
      <div class="ir-label">IR 事件通報報告已自動產生</div>
      <button class="pdf-btn" onclick="downloadPdf()">📄 下載 PDF 資安報告</button>
      <div class="ir-id">${escapeHtml(d.ir.id)} &nbsp;|&nbsp; 嚴重等級：${escapeHtml(d.ir.severity)}</div>
      <div class="ir-impact">${escapeHtml(d.ir.impact)}</div>
      ${d.ir.actions && d.ir.actions.length ? `<div class="ir-actions">${d.ir.actions.map(a=>`<div class="ir-action">• ${escapeHtml(a)}</div>`).join('')}</div>` : ''}
       <div class="ir-meta">
         <div class="ir-meta-item"><div class="ir-meta-label">Status</div><div class="ir-meta-value">${escapeHtml(d.ir.status || 'Open')}</div></div>
         <div class="ir-meta-item"><div class="ir-meta-label">Risk</div><div class="ir-meta-value">${escapeHtml(String(d.ir.risk_score ?? '—'))}/100</div></div>
         <div class="ir-meta-item"><div class="ir-meta-label">Created</div><div class="ir-meta-value">${escapeHtml(d.ir.created_at || '—')}</div></div>
       </div>
       <div class="ir-section"><div class="ir-section-title">隔離 / Containment</div><div class="ir-text">${escapeHtml(d.ir.containment || '—')}</div></div>
       <div class="ir-section"><div class="ir-section-title">驗證 / Verification</div><div class="ir-text">${escapeHtml(d.ir.verification || '—')}</div></div>
       <div class="ir-section"><div class="ir-section-title">復原 / Recovery</div><div class="ir-text">${escapeHtml(d.ir.recovery || '—')}</div></div>
    </div>` : '';

  panel.innerHTML = `
    <span class="detail-badge ${badgeClass}">${badgeText}${scoreStr}</span>
    <div class="detail-subj">${escapeHtml(d.subject)}</div>
    <div class="detail-from">來自：${escapeHtml(d.sender)}</div>

    <div class="gold-line"></div>

    <div class="sec-label">多層式智慧分析</div>
    <div class="layer-grid">${layerHtml}</div>
    ${d.fusion_formula ? `<div class="fusion-note">風險融合公式：${escapeHtml(d.fusion_formula)}。最終分數由系統固定公式計算，不直接採用單一模型結果。</div>` : ''}
      ${d.risk_breakdown ? `<div class="score-breakdown"><h4>📊 分數組成</h4>${d.risk_breakdown.components.map(x => `<div class="score-row"><span>${escapeHtml(x.name)}</span><span>${x.score.toFixed(1)} × ${x.weight}% = ${x.contribution.toFixed(1)}</span></div>`).join('')}<div class="score-total">公式計算值：${d.risk_breakdown.raw_total.toFixed(1)} → 最終 ${d.risk_breakdown.rounded_final}/100</div></div>` : ''}

    <div class="gold-line"></div>

    <div class="sec-label">AI 分析說明</div>
    <div class="detail-text">${escapeHtml(d.explanation || '—')}</div>
    ${tagsHtml}
    ${whyHtml}

    ${evidenceHtml}

    <div class="divider"></div>
    <div class="sec-label">建議行動</div>
    <div class="recommend">${escapeHtml(d.action || '—')}</div>
    ${safetyHtml}
    ${irHtml}
  `;
}

window.addEventListener('DOMContentLoaded', () => {
  if (Array.isArray(emailData) && emailData.length > 0) {
    showDetail(0);
  }
});
</script>

<div class="hdr">
  <div class="hdr-left">
    <span class="shield-icon">🛡️</span>
    <h1>AI 釣魚信件偵測系統 — 掃描結果</h1>
  </div>
  <div class="hdr-nav">
    <a href="/history">掃描記錄</a>
    <a href="/whitelist">白名單設定</a>
    <a href="/">重新掃描</a>
  </div>
  <span class="proj-tag">PROJ-2026</span>
</div>

<div class="summary">
  <div class="stat s-total"><div class="stat-num">TOTAL_COUNT</div><div class="stat-lbl">掃描封數</div></div>
  <div class="stat s-high"><div class="stat-num">HIGH_COUNT</div><div class="stat-lbl">高風險</div></div>
  <div class="stat s-med"><div class="stat-num">MED_COUNT</div><div class="stat-lbl">中風險</div></div>
  <div class="stat s-low"><div class="stat-num">LOW_COUNT</div><div class="stat-lbl">安全</div></div>
  <div class="stat s-wl"><div class="stat-num">WL_COUNT</div><div class="stat-lbl">白名單</div></div>
  <div class="stat s-sk"><div class="stat-num">SK_COUNT</div><div class="stat-lbl">略過</div></div>
</div>

<div class="main">
  <div class="left" id="left-panel">LIST_PLACEHOLDER</div>
  <div class="right" id="right-panel">
    <div class="empty-detail">
      <div class="empty-icon">🛡️</div>
      <div>點擊左側信件查看詳細分析</div>
    </div>
  </div>
</div>
"""

# ── 歷史記錄 HTML ────────────────────────────────────────────
HISTORY_HTML = COMMON_CSS + """
<style>
.container { max-width: 860px; margin: 0 auto; padding: 40px 20px; }
.page-title { font-size: 18px; font-weight: 600; color: var(--text-main); margin-bottom: 24px; }
table { width: 100%; border-collapse: collapse; background: var(--bg-card); border-radius: 10px; border: 1px solid var(--border-subtle); overflow: hidden; }
thead tr { border-bottom: 1px solid var(--border-subtle); background: rgba(255, 255, 255, 0.02); }
th { padding: 14px 18px; font-size: 11px; color: var(--text-dim); letter-spacing: 0.05em;
     text-transform: uppercase; text-align: left; font-weight: 600; }
td { padding: 14px 18px; font-size: 13px; color: var(--text-main);
     border-bottom: 1px solid var(--border-subtle); }
tr:last-child td { border-bottom: none; }
tr:hover td { background: var(--bg-hover); }
.cell-high { color: var(--red); font-weight: 600; }
.cell-med { color: var(--orange); }
.cell-low { color: var(--green); }
.empty { padding: 60px; text-align: center; color: var(--text-dim); font-size: 13px; background: var(--bg-card); border-radius: 10px; border: 1px solid var(--border-subtle); }
</style>

<div class="hdr">
  <div class="hdr-left">
    <span class="shield-icon">🛡️</span>
    <h1>AI 釣魚信件偵測系統</h1>
  </div>
  <div class="hdr-nav">
    <a href="/">首頁</a>
    <a href="/whitelist">白名單設定</a>
  </div>
  <span class="proj-tag">PROJ-2026</span>
</div>

<div class="container">
  <a href="/" class="back">← 返回首頁</a>
  <div class="page-title">掃描記錄</div>
  {% if history %}
  <table>
    <thead><tr><th>掃描時間</th><th>總計</th><th>高風險</th><th>中風險</th><th>安全</th><th>白名單</th></tr></thead>
    <tbody>
    {% for h in history %}
    <tr>
      <td>{{h[1]}}</td>
      <td>{{h[2]}}</td>
      <td class="cell-high">{{h[3]}}</td>
      <td class="cell-med">{{h[4]}}</td>
      <td class="cell-low">{{h[5]}}</td>
      <td style="color:var(--text-dim)">{{h[6]}}</td>
    </tr>
    {% endfor %}
    </tbody>
  </table>
  {% else %}
  <div class="empty">還沒有掃描記錄，<a href="/" style="color:var(--blue); text-decoration:none;">開始掃描</a>！</div>
  {% endif %}
</div>
"""

# ── 白名單 HTML ──────────────────────────────────────────────
WHITELIST_HTML = COMMON_CSS + """
<style>
.container { max-width: 680px; margin: 0 auto; padding: 40px 20px; }
.page-title { font-size: 18px; font-weight: 600; color: var(--text-main); margin-bottom: 6px; }
.page-sub { font-size: 13px; color: var(--text-muted); margin-bottom: 24px; line-height: 1.5; }
.add-row { display: flex; gap: 10px; margin-bottom: 32px; }
.add-row input { flex: 1; background: var(--bg-card); border: 1px solid var(--border-subtle);
                 border-radius: 8px; padding: 11px 16px; color: var(--text-main);
                 font-size: 13.5px; outline: none; transition: border-color 0.2s; }
.add-row input::placeholder { color: var(--text-dim); }
.add-row input:focus { border-color: var(--border-accent); }
.add-btn { background: #ffffff; color: #0f172a; border: none;
           border-radius: 8px; padding: 11px 22px; font-size: 13.5px; font-weight: 600; cursor: pointer;
           transition: all 0.2s ease; white-space: nowrap; }
.add-btn:hover { background: #f8fafc; transform: translateY(-1px); }
.sec-label { font-size: 11px; color: var(--text-dim); letter-spacing: 0.05em;
             text-transform: uppercase; margin-bottom: 12px; font-weight: 600; }
.domain-item { display: flex; justify-content: space-between; align-items: center;
               background: var(--bg-card); border: 1px solid var(--border-subtle);
               border-radius: 8px; padding: 14px 18px; margin-bottom: 10px;
               transition: border-color 0.2s; }
.domain-item:hover { border-color: var(--border-accent); }
.domain-name { font-size: 13.5px; color: var(--text-main); font-family: monospace; font-weight: 500; }
.domain-time { font-size: 11px; color: var(--text-dim); margin-top: 3px; }
.del-btn { background: var(--red-bg); color: var(--red); border: 1px solid var(--red-border);
           border-radius: 6px; padding: 5px 12px; font-size: 12px; cursor: pointer;
           transition: all 0.2s ease; }
.del-btn:hover { background: rgba(239, 68, 68, 0.2); }
</style>
<script>
function addDomain() {
  const domain = document.getElementById('domain-input').value.trim();
  if (!domain) return alert('請輸入網域');
  fetch('/whitelist/add', {method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({domain})}).then(r => r.json()).then(d => {
    if (d.success) location.reload();
    else alert(d.error || '新增失敗');
  });
}
function deleteDomain(domain) {
  if (!confirm('確定要刪除 ' + domain + '？')) return;
  fetch('/whitelist/delete', {method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({domain})}).then(r => r.json()).then(d => {
    if (d.success) location.reload();
  });
}
document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('domain-input').addEventListener('keydown', e => {
    if (e.key === 'Enter') addDomain();
  });
});
</script>

<div class="hdr">
  <div class="hdr-left">
    <span class="shield-icon">🛡️</span>
    <h1>AI 釣魚信件偵測系統</h1>
  </div>
  <div class="hdr-nav">
    <a href="/">首頁</a>
    <a href="/history">掃描記錄</a>
  </div>
  <span class="proj-tag">PROJ-2026</span>
</div>

<div class="container">
  <a href="/" class="back">← 返回首頁</a>
  <div class="page-title">白名單設定</div>
  <p class="page-sub">加入白名單後，來自該網域的信件將直接標記為安全，不進行 AI 分析。</p>

  <div class="add-row">
    <input type="text" id="domain-input" placeholder="輸入網域，例如：example.com">
    <button class="add-btn" onclick="addDomain()">新增</button>
  </div>

  <div class="sec-label">目前白名單（{{count}} 個）</div>
  {% for d in domains %}
  <div class="domain-item">
    <div>
      <div class="domain-name">{{d[0]}}</div>
      <div class="domain-time">新增時間：{{d[1][:10] if d[1] else '—'}}</div>
    </div>
    <button class="del-btn" onclick="deleteDomain('{{d[0]}}')">刪除</button>
  </div>
  {% endfor %}
</div>
"""
# ── 資料庫 ───────────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect('phishing.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS scan_history
        (id TEXT PRIMARY KEY, scan_time TEXT, total INTEGER,
         high INTEGER, medium INTEGER, low INTEGER, whitelist INTEGER, skipped INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS whitelist
        (id INTEGER PRIMARY KEY AUTOINCREMENT, domain TEXT UNIQUE, added_time TEXT)''')
    for domain in DEFAULT_WHITELIST:
        try:
            c.execute('INSERT OR IGNORE INTO whitelist (domain, added_time) VALUES (?, ?)',
                     (domain, datetime.now().isoformat()))
        except: pass
    conn.commit()
    conn.close()

init_db()

def get_whitelist():
    conn = sqlite3.connect('phishing.db')
    c = conn.cursor()
    c.execute('SELECT domain FROM whitelist')
    domains = [row[0] for row in c.fetchall()]
    conn.close()
    return domains

def extract_sender_domain(sender):
    """從 From 標頭取出真正的 email domain。"""
    m = re.search(r'<([^>]+)>', sender or '')
    email_addr = (m.group(1) if m else sender or '').strip().lower()
    if '@' not in email_addr:
        return ''
    return email_addr.rsplit('@', 1)[1].strip().rstrip('.')

def is_whitelisted(sender):
    domain = extract_sender_domain(sender)
    if not domain:
        return False
    return any(
        domain == d or domain.endswith('.' + d)
        for d in get_whitelist()
    )

def is_system_report(sender, subject):
    if any(kw in subject for kw in SKIP_SUBJECTS): return True
    if MY_EMAIL in sender and any(kw in subject for kw in ['釣魚','警告','偵測']): return True
    return False

def save_scan(scan_id, scan_time, total, high, med, low, wl, skipped):
    conn = sqlite3.connect('phishing.db')
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO scan_history VALUES (?,?,?,?,?,?,?,?)',
             (scan_id, scan_time, total, len(high), len(med), len(low), wl, skipped))
    conn.commit()
    conn.close()

def get_history():
    conn = sqlite3.connect('phishing.db')
    c = conn.cursor()
    c.execute('SELECT * FROM scan_history ORDER BY scan_time DESC LIMIT 20')
    rows = c.fetchall()
    conn.close()
    return rows

# ── ML 模型：Phishing Email Dataset ───────────────────────────
# V5 不再使用 SMS Spam/ham 資料。
# 模型由 train_phishing_model.py 預先訓練後，以 joblib 載入。
MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'models')
MODEL_PATH = os.path.join(MODEL_DIR, 'phishing_model.joblib')
VECTORIZER_PATH = os.path.join(MODEL_DIR, 'phishing_tfidf.joblib')
METRICS_PATH = os.path.join(MODEL_DIR, 'phishing_metrics.json')

model = None
vectorizer = None
model_metrics = {}

try:
    if os.path.exists(MODEL_PATH) and os.path.exists(VECTORIZER_PATH):
        model = joblib.load(MODEL_PATH)
        vectorizer = joblib.load(VECTORIZER_PATH)
        if os.path.exists(METRICS_PATH):
            with open(METRICS_PATH, 'r', encoding='utf-8') as f:
                model_metrics = json.load(f)
        print('OK - Phishing Email ML 模型已載入')
    else:
        print('WARNING - 尚未找到 Phishing Email ML 模型，ML 分析將暫停。請先執行 train_phishing_model.py')
except Exception as e:
    model = None
    vectorizer = None
    print(f'WARNING - ML 模型載入失敗：{e}')

groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
print('OK - 模型就緒' if GROQ_API_KEY else 'WARNING - Groq API Key 未設定，將跳過 LLM 深度分析')

# ── 分析函式 ─────────────────────────────────────────────────
def analyze_url(url):
    """分析 URL 結構，不連線、不開啟目標網站。"""
    from urllib.parse import urlparse
    import ipaddress

    findings = []
    try:
        parsed = urlparse(url.strip().rstrip('.,);]'))
        host = (parsed.hostname or '').lower()
        if not host:
            return findings

        try:
            ipaddress.ip_address(host)
            findings.append('URL 使用 IP 位址')
        except ValueError:
            pass

        if '@' in parsed.netloc:
            findings.append('URL 含有 @，可能隱藏真正目的地')

        if host.startswith('xn--') or '.xn--' in host:
            findings.append('網域含有 Punycode')

        suspicious_tlds = ('.xyz', '.top', '.click', '.zip', '.mov', '.work', '.biz')
        if any(host.endswith(tld) for tld in suspicious_tlds):
            findings.append('使用較高風險網域後綴')

        if len(url) > 100:
            findings.append('URL 過長')

        if host.count('.') >= 4:
            findings.append('子網域層級過深')

        shorteners = {
            'bit.ly', 'tinyurl.com', 't.co', 'is.gd', 'goo.gl',
            'ow.ly', 'buff.ly', 'rebrand.ly', 'cutt.ly'
        }
        if host in shorteners:
            findings.append('使用短網址服務')

        suspicious_words = [
            'login', 'verify', 'secure', 'update', 'account',
            'password', 'signin', 'confirm', 'wallet'
        ]
        if any(w in (host + parsed.path).lower() for w in suspicious_words):
            findings.append('URL 含有登入或驗證誘導字樣')

    except Exception:
        findings.append('URL 格式異常')

    return findings


def rule_based_score(text):
    score = 0
    triggered = []
    t = (text or '').lower()

    urgent = [
        'urgent', 'immediately', 'expire', 'suspended', 'verify now', 'act now',
        '立即', '緊急', '即將停用', '馬上', '限時', '暫停', '停用'
    ]
    hits = [w for w in urgent if w in t]
    if hits:
        score += len(hits) * 2
        triggered.append(f'緊急語句: {hits}')

    urls = re.findall(r'https?://[^\s<>"\']+', t)
    if urls:
        score += min(3 + len(urls), 8)
        triggered.append(f'含有連結: {urls[:2]}')

        for url in urls[:10]:
            url_findings = analyze_url(url)
            if url_findings:
                score += min(len(url_findings) * 2, 8)
                triggered.append(f'URL 風險: {url_findings[:4]}')

    bait = [
        'free', 'winner', 'won', 'prize', 'claim', 'lucky', 'reward', 'gift',
        '中獎', '免費', '領取', '恭喜', '退款', '補助'
    ]
    hits2 = [w for w in bait if w in t]
    if hits2:
        score += len(hits2) * 2
        triggered.append(f'誘騙話術: {hits2}')

    personal = [
        'password', 'credit card', 'bank account', 'pin',
        '密碼', '帳號', '信用卡', '身分證', '帳戶'
    ]
    hits3 = [w for w in personal if w in t]
    if hits3:
        score += len(hits3) * 3
        triggered.append(f'索取個資: {hits3}')

    money = [
        '$', 'cash', 'money', 'transfer', 'wire', 'payment', 'invoice',
        '匯款', '轉帳', '付款', 'NT$', '退款'
    ]
    hits4 = [w for w in money if w in t]
    if hits4:
        score += len(hits4) * 2
        triggered.append(f'金錢相關: {hits4}')

    return score, triggered


def ai_agent_analyze(text, rule_score, triggered_rules):
    rules_str = ', '.join(triggered_rules) if triggered_rules else 'none'
    prompt = (
        "You are a cybersecurity analyst. Analyze this email and reply ONLY with JSON.\\n"
        f"Message: {text}\\n"
        f"Deterministic rule score: {rule_score}, Triggered evidence: {rules_str}\\n"
        "Do not invent URLs, sender facts, or technical evidence.\\n"
        'JSON: {"risk_level":"high/medium/low","risk_score":0-100,'
        '"category":"釣魚信件/詐騙簡訊/正常信件/商業詐騙",'
        '"suspicious_points":["點1","點2"],'
        '"explanation":"繁體中文2-3句說明",'
        '"recommended_action":"繁體中文建議"}'
    )
    try:
        if not GROQ_API_KEY:
            raise RuntimeError('GROQ_API_KEY 未設定')
        resp = groq_client.chat.completions.create(
            model='openai/gpt-oss-120b',
            messages=[{'role': 'user', 'content': prompt}],
            temperature=0.2
        )
        raw = resp.choices[0].message.content.strip()
        raw = raw.replace('```json', '').replace('```', '').strip()
        result = json.loads(raw)

        result['risk_score'] = float(result.get('risk_score', 0))
        result['suspicious_points'] = result.get('suspicious_points', []) or []
        return result
    except Exception as e:
        return {
            'risk_level': 'unknown',
            'risk_score': None,
            'category': '分析失敗',
            'suspicious_points': [],
            'explanation': f'AI 深度分析暫時失敗：{e}',
            'recommended_action': '請依規則與 ML 結果人工檢查，不要直接點擊信件中的連結。'
        }


def build_explainable_findings(rules, html_findings, spam_prob, report):
    """把各分析層的原始證據整理成使用者看得懂的「為什麼可疑」。"""
    findings = []

    for item in rules or []:
        s = str(item)
        if s.startswith('緊急語句'):
            findings.append({
                'severity': 'high',
                'source': '規則引擎',
                'title': '偵測到緊急／施壓語句',
                'detail': s
            })
        elif s.startswith('索取個資'):
            findings.append({
                'severity': 'high',
                'source': '規則引擎',
                'title': '出現帳號或敏感資訊要求',
                'detail': s
            })
        elif s.startswith('URL 風險'):
            findings.append({
                'severity': 'high',
                'source': 'URL 分析',
                'title': '連結具有可疑結構',
                'detail': s
            })
        elif s.startswith('含有連結'):
            findings.append({
                'severity': 'medium',
                'source': '規則引擎',
                'title': '郵件包含外部連結',
                'detail': s
            })
        elif s.startswith('誘騙話術'):
            findings.append({
                'severity': 'medium',
                'source': '規則引擎',
                'title': '偵測到誘因／獎勵型話術',
                'detail': s
            })
        elif s.startswith('金錢相關'):
            findings.append({
                'severity': 'high',
                'source': '規則引擎',
                'title': '出現金錢或付款相關內容',
                'detail': s
            })
        else:
            findings.append({
                'severity': 'medium',
                'source': '規則引擎',
                'title': '偵測到可疑文字特徵',
                'detail': s
            })

    for category, items in html_findings or []:
        for item in items[:3]:
            title = {
                'URL 結構風險': 'URL 結構存在風險',
                '偽裝連結': '顯示網址與實際連結不一致',
                '像素追蹤': '發現可能的追蹤像素',
                '隱藏元素': 'HTML 含有隱藏元素',
                '表單元素': '郵件內含表單',
                '密碼輸入欄位': '郵件內含密碼輸入欄位'
            }.get(category, f'HTML 偵測到{category}')
            findings.append({
                'severity': 'high' if category in ('偽裝連結', '密碼輸入欄位') else 'medium',
                'source': 'HTML / URL',
                'title': title,
                'detail': f'{category}：{item}'
            })

    if spam_prob >= 0.70:
        findings.append({
            'severity': 'high',
            'source': 'ML 模型',
            'title': '模型高度偏向釣魚信件',
            'detail': f'釣魚信件機率為 {spam_prob:.1%}。此結果代表模型在目前輸入文字上的分類傾向，並非單獨作為最終判定。'
        })
    elif spam_prob >= 0.30:
        findings.append({
            'severity': 'medium',
            'source': 'ML 模型',
            'title': '模型偏向釣魚信件',
            'detail': f'釣魚信件機率為 {spam_prob:.1%}，需要搭配其他分析層判斷。'
        })
    else:
        findings.append({
            'severity': 'low',
            'source': 'ML 模型',
            'title': '模型未明顯偏向釣魚信件',
            'detail': f'釣魚信件機率為 {spam_prob:.1%}，仍會搭配規則與 HTML / URL 分析。'
        })

    # LLM 的理由保留為「AI 輔助說明」，避免把 LLM 生成內容誤標成確定技術證據。
    llm_points = report.get('suspicious_points', []) or []
    for point in llm_points[:5]:
        point = str(point)
        if point.startswith('[HTML]'):
            continue
        findings.append({
            'severity': 'medium',
            'source': 'AI 深度分析',
            'title': 'AI 輔助判讀',
            'detail': point
        })

    # 去除完全重複項目，最多保留 10 個，讓畫面不會過長。
    unique = []
    seen = set()
    for item in findings:
        key = (item['source'], item['title'], item['detail'])
        if key not in seen:
            seen.add(key)
            unique.append(item)

    return unique[:10]


def analyze_html(html_content):
    findings = []
    score = 0
    soup = BeautifulSoup(html_content, 'html.parser')

    links = soup.find_all('a', href=True)
    for link in links:
        href = link.get('href', '')
        text_label = link.get_text(' ', strip=True)

        url_findings = analyze_url(href)
        if url_findings:
            score += min(len(url_findings) * 3, 10)
            findings.append(('URL 結構風險', url_findings[:4]))

        # 顯示文字與實際連結網域不同時提高風險。
        visible_urls = re.findall(r'https?://[^\s<>"\']+', text_label.lower())
        if visible_urls:
            from urllib.parse import urlparse
            try:
                visible_host = urlparse(visible_urls[0]).hostname or ''
                actual_host = urlparse(href).hostname or ''
                if visible_host and actual_host and visible_host.lower() != actual_host.lower():
                    score += 6
                    findings.append(('偽裝連結', [f'{visible_host} → {actual_host}']))
            except Exception:
                pass

    trackers = [
        img.get('src', '')[:80]
        for img in soup.find_all('img')
        if str(img.get('width', '')).lower() in ['1', '0']
        or str(img.get('height', '')).lower() in ['1', '0']
    ]
    if trackers:
        findings.append(('像素追蹤', trackers[:2]))
        score += min(len(trackers) * 2, 8)

    hidden = soup.find_all(style=re.compile(r'display\\s*:\\s*none|visibility\\s*:\\s*hidden', re.I))
    if hidden:
        findings.append(('隱藏元素', [f'{len(hidden)} 個']))
        score += 3

    forms = soup.find_all('form')
    password_inputs = soup.find_all('input', attrs={'type': re.compile(r'password', re.I)})
    if forms:
        findings.append(('表單元素', [f'{len(forms)} 個']))
        score += 3
    if password_inputs:
        findings.append(('密碼輸入欄位', [f'{len(password_inputs)} 個']))
        score += 5

    found_brands = [
        b for b in ['paypal', 'microsoft', 'apple', 'amazon', 'facebook', 'netflix', 'google']
        if b in soup.get_text(' ').lower()
    ]
    if found_brands:
        findings.append(('品牌偵測', [', '.join(found_brands)]))
        score += 2

    return score, findings


def calculate_risk_score(rule_score, spam_prob, html_score, llm_score=None):
    """固定融合規則、ML、HTML 與 LLM，避免單一模型直接決定最終分數。"""
    rule_component = min(rule_score * 5, 100)
    html_component = min(html_score * 8, 100)
    ml_component = max(0, min(float(spam_prob) * 100, 100))

    components = [
        (0.35, rule_component),
        (0.35, ml_component),
        (0.15, html_component)
    ]

    if llm_score is not None:
        components.append((0.15, max(0, min(float(llm_score), 100))))
    else:
        # LLM 未啟用時，把其權重平均分配給規則與 ML。
        components = [
            (0.425, rule_component),
            (0.425, ml_component),
            (0.15, html_component)
        ]

    return int(round(sum(weight * value for weight, value in components)))



def build_risk_breakdown(rule_score, spam_prob, html_score, llm_score=None):
    rule_component = min(max(float(rule_score), 0) * 5, 100)
    ml_component = max(0, min(float(spam_prob) * 100, 100))
    html_component = min(max(float(html_score), 0) * 8, 100)

    if llm_score is not None:
        llm_component = max(0, min(float(llm_score), 100))
        rows = [
            ('規則引擎', rule_component, 35.0),
            ('ML 模型', ml_component, 35.0),
            ('HTML / URL', html_component, 15.0),
            ('AI 深度分析', llm_component, 15.0),
        ]
    else:
        llm_component = None
        rows = [
            ('規則引擎', rule_component, 42.5),
            ('ML 模型', ml_component, 42.5),
            ('HTML / URL', html_component, 15.0),
        ]

    total = sum(score * weight / 100 for _, score, weight in rows)
    return {
        'components': [
            {
                'name': name,
                'score': round(score, 2),
                'weight': weight,
                'contribution': round(score * weight / 100, 2)
            }
            for name, score, weight in rows
        ],
        'raw_total': round(total, 2),
        'rounded_final': int(round(total)),
        'llm_used': llm_component is not None,
        'thresholds': {'low': '< 40', 'medium': '40 - 69', 'high': '>= 70'}
    }


def run_risk_score_self_test():
    cases = [
        ('zero', calculate_risk_score(0, 0, 0, None), 0),
        ('maximum_without_llm', calculate_risk_score(20, 1, 13, None), 100),
        ('maximum_with_llm', calculate_risk_score(20, 1, 13, 100), 100),
        ('ml_50pct_without_llm', calculate_risk_score(0, 0.5, 0, None), 21),
        ('llm_100pct', calculate_risk_score(0, 0, 0, 100), 15),
    ]
    results = []
    for name, actual, expected in cases:
        results.append({'name': name, 'actual': actual, 'expected': expected, 'passed': actual == expected})

    level_cases = [(39, 'low'), (40, 'medium'), (69, 'medium'), (70, 'high'), (100, 'high')]
    for score, expected in level_cases:
        report = apply_risk_level({}, score)
        results.append({'name': f'level_{score}', 'actual': report['risk_level'], 'expected': expected, 'passed': report['risk_level'] == expected})

    return results


def apply_risk_level(report, final_score):
    final_score = max(0, min(int(final_score), 100))
    report['risk_score'] = final_score

    if final_score >= 70:
        report['risk_level'] = 'high'
    elif final_score >= 40:
        report['risk_level'] = 'medium'
    else:
        report['risk_level'] = 'low'

    return report



def build_safety_actions(risk_level, rules=None, html_findings=None, category=''):
    """依風險等級與偵測特徵產生可直接執行的安全處置建議。"""
    rules = rules or []
    html_findings = html_findings or []
    high_signal = any(
        str(x).startswith(('緊急語句', '索取個資', 'URL 風險', '金錢相關'))
        for x in rules
    )
    has_phishing_link = any(cat in ('URL 結構風險', '偽裝連結', '密碼輸入欄位')
                            for cat, _ in html_findings)

    if risk_level == 'high':
        actions = [
            '不要點擊郵件中的連結、附件，也不要回覆或提供帳號密碼。',
            '將郵件標記為垃圾郵件／釣魚郵件，並依組織規範進行通報或隔離。',
            '若需要確認通知內容，請自行開啟官方網站或使用既有官方聯絡方式，不要使用郵件提供的連結。'
        ]
        if high_signal or has_phishing_link:
            actions.append('若已輸入密碼或敏感資訊，請立即從官方網站變更密碼並檢查帳號安全設定。')
        return actions

    if risk_level == 'medium':
        actions = [
            '先不要點擊連結或開啟附件，確認寄件者與郵件內容是否合理。',
            '若涉及帳號、付款或驗證，請透過官方網站或其他可信管道獨立確認。',
            '不確定時可將郵件標記為垃圾郵件／釣魚郵件，並請管理者或資安人員協助判斷。'
        ]
        return actions

    return [
        '目前未發現明顯高風險訊號，但仍不建議點擊未知來源的連結或附件。',
        '若郵件要求提供密碼、付款或敏感資訊，請改用官方管道再次確認。'
    ]

def full_pipeline(text, html=''):
    rule_score, rules = rule_based_score(text)

    # ML 模型使用 1 = phishing、0 = legitimate。
    if model is not None and vectorizer is not None:
        vec = vectorizer.transform([text])
        classes = list(model.classes_)
        phishing_index = classes.index(1) if 1 in classes else classes.index('1')
        spam_prob = float(model.predict_proba(vec)[0][phishing_index])
    else:
        spam_prob = 0.0

    html_score, html_findings = (0, [])
    if html:
        html_score, html_findings = analyze_html(html)

    # 有明顯證據才呼叫 LLM，降低不必要 API 成本。
    should_call_llm = (
        rule_score >= 4 or
        spam_prob >= 0.30 or
        html_score >= 4
    )

    if should_call_llm:
        report = ai_agent_analyze(text, rule_score, rules)
        llm_score = report.get('risk_score')
    else:
        report = {
            'risk_level': 'low',
            'risk_score': None,
            'category': '正常信件',
            'explanation': '目前規則與 ML 模型未發現明顯異常訊號。',
            'recommended_action': '可正常閱讀，但仍不建議點擊未知連結。',
            'suspicious_points': []
        }
        llm_score = None

    # 保存各層的「原始證據」與「融合用分數」。
    rule_component = min(rule_score * 5, 100)
    ml_component = max(0, min(float(spam_prob) * 100, 100))
    html_component = min(html_score * 8, 100)
    llm_component = None if llm_score is None else max(0, min(float(llm_score), 100))

    # 最終風險分數由固定公式融合，不直接採用 LLM 自己的分數。
    final_score = calculate_risk_score(
        rule_score, spam_prob, html_score, llm_score
    )
    report = apply_risk_level(report, final_score)
    report['risk_breakdown'] = build_risk_breakdown(
        rule_score, spam_prob, html_score, llm_score
    )
    report['score_validation'] = {
        'formula_total': report['risk_breakdown']['raw_total'],
        'final_score': final_score,
        'consistent': report['risk_breakdown']['rounded_final'] == final_score,
        'threshold_rule': '高風險 >= 70；中風險 40-69；低風險 < 40'
    }

    # 將 HTML 證據加入可疑特徵。
    for cat, items in html_findings:
        for item in items:
            report.setdefault('suspicious_points', []).append(
                f'[HTML] {cat}: {item}'
            )

    # 給前端的「為什麼可疑」證據清單。
    report['explainable_findings'] = build_explainable_findings(
        rules, html_findings, spam_prob, report
    )

    # 依最終風險產生可執行的安全處置建議。
    report['safety_actions'] = build_safety_actions(
        report['risk_level'], rules, html_findings, report.get('category', '')
    )

    # 給前端的多層分析資料。
    report['analysis_layers'] = {
        'rule': {
            'name': '規則引擎',
            'score': round(rule_component, 1),
            'raw_score': rule_score,
            'weight': 42.5 if llm_score is None else 35,
            'status': '偵測到可疑規則' if rules else '未發現明顯規則異常',
            'findings': rules[:6]
        },
        'ml': {
            'name': 'ML 模型',
            'score': round(ml_component, 1),
            'probability': round(spam_prob * 100, 1),
            'weight': 42.5 if llm_score is None else 35,
            'status': '高度偏向釣魚信件' if spam_prob >= 0.7 else ('偏向釣魚信件' if spam_prob >= 0.3 else '偏向正常信件'),
            'findings': [
                f'釣魚信件機率：{spam_prob:.1%}'
            ]
        },
        'html': {
            'name': 'HTML / URL',
            'score': round(html_component, 1),
            'raw_score': html_score,
            'weight': 15,
            'status': '偵測到 HTML / URL 風險' if html_findings else '未發現明顯 HTML / URL 異常',
            'findings': [
                f'{cat}：{item}'
                for cat, items in html_findings[:6]
                for item in items[:2]
            ]
        },
        'llm': {
            'name': 'AI 深度分析',
            'score': round(llm_component, 1) if llm_component is not None else None,
            'weight': 15 if llm_score is not None else 0,
            'status': 'AI 分析完成' if llm_score is not None else '本次未呼叫或分析失敗',
            'findings': report.get('suspicious_points', [])[:6]
        }
    }

    report['fusion_formula'] = (
        '規則 35% + ML 35% + HTML 15% + AI 15%'
        if llm_score is not None
        else '規則 42.5% + ML 42.5% + HTML 15%'
    )

    return report, html_score, html_findings, rule_score, spam_prob

def gen_ir(email_data, report):
    incident_id = f"IR-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"
    risk = int(report.get('risk_score', 0))
    if risk >= 85:
        default_severity = 'Critical'
    elif risk >= 70:
        default_severity = 'High'
    else:
        default_severity = 'Medium'

    findings = report.get('explainable_findings', [])[:8]
    finding_text = '\n'.join(
        f"- {x.get('title','可疑特徵')}：{x.get('detail','')}" for x in findings
    ) or '- 未提供額外可疑特徵'

    prompt = (
        "You are a cybersecurity incident response analyst. Reply ONLY with valid JSON.\n"
        "Do not invent facts. Base the assessment only on the supplied email and detection evidence.\n"
        f"Email from: {email_data.get('sender','未知')}\n"
        f"Subject: {email_data.get('subject','未知')}\n"
        f"Risk score: {risk}/100\n"
        f"Detection evidence:\n{finding_text}\n"
        'JSON: {"severity":"Critical/High/Medium","impact_assessment":"繁體中文",'
        '"immediate_actions":["行動1","行動2","行動3"],'
        '"containment":"繁體中文", "verification":"繁體中文", "recovery":"繁體中文"}'
    )
    try:
        if not groq_client:
            raise RuntimeError('AI client unavailable')
        resp = groq_client.chat.completions.create(
            model='openai/gpt-oss-120b',
            messages=[{'role':'user','content':prompt}], temperature=0.2)
        raw = resp.choices[0].message.content.strip().replace('```json','').replace('```','').strip()
        ir = json.loads(raw)
    except Exception:
        ir = {
            'severity': default_severity,
            'impact_assessment': '依目前偵測結果，可能存在帳號遭竊、個資外洩或財務損失風險；實際影響仍需人工確認。',
            'immediate_actions': ['不要點擊連結或附件', '不要回覆或提供帳號密碼與個資', '依組織流程標記、隔離並通報可疑郵件'],
            'containment': '先停止與郵件中連結、附件及要求的外部服務互動；若已點擊或輸入資料，應立即通知資安人員。',
            'verification': '透過官方網站、已知電話或其他可信管道獨立確認寄件者與事件真實性。',
            'recovery': '若確認已受影響，依組織流程進行密碼重設、工作階段撤銷及必要的帳號與端點檢查。'
        }

    ir['incident_id'] = incident_id
    ir['created_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ir['risk_score'] = risk
    ir['email_sender'] = email_data.get('sender', '')
    ir['email_subject'] = email_data.get('subject', '')
    ir['status'] = 'Open'
    ir.setdefault('severity', default_severity)
    ir.setdefault('immediate_actions', [])
    ir.setdefault('containment', '依組織資安事件處理流程進行隔離與通報。')
    ir.setdefault('verification', '使用可信管道確認事件。')
    ir.setdefault('recovery', '確認影響範圍後依流程復原。')
    return incident_id, ir

def create_pdf_report(email_data, scan_id, index, entry):
    """產生單封郵件的 PDF 分析報告。"""
    from io import BytesIO
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
    from reportlab.lib import colors

    try:
        pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
    except Exception:
        pass

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=42, leftMargin=42, topMargin=42, bottomMargin=42)
    styles = getSampleStyleSheet()
    font = 'STSong-Light'
    title = ParagraphStyle('zhTitle', parent=styles['Title'], fontName=font, fontSize=18, leading=24, alignment=TA_CENTER, spaceAfter=16)
    h2 = ParagraphStyle('zhH2', parent=styles['Heading2'], fontName=font, fontSize=13, leading=18, spaceBefore=10, spaceAfter=7)
    body = ParagraphStyle('zhBody', parent=styles['BodyText'], fontName=font, fontSize=9.5, leading=15, spaceAfter=5)
    small = ParagraphStyle('zhSmall', parent=body, fontSize=8.5, leading=13)

    risk = int(entry.get('risk_score', 0))
    level_map = {'high':'高風險', 'medium':'中風險', 'low':'低風險', 'wl':'白名單'}
    level = level_map.get(entry.get('level'), entry.get('level', '未知'))
    story = [
        Paragraph('AI 釣魚信件偵測系統｜分析報告', title),
        Paragraph(f'報告編號：{scan_id}-{index+1:02d}', small),
        Spacer(1, 6),
        Paragraph('一、郵件資訊', h2)
    ]
    info = [
        ['項目', '內容'],
        ['寄件者', str(email_data.get('sender','未提供'))],
        ['主旨', str(email_data.get('subject','無主旨'))],
        ['風險等級', level],
        ['風險分數', f'{risk}/100' if risk >= 0 else '白名單'],
    ]
    t=Table(info, colWidths=[90, 390], repeatRows=1)
    t.setStyle(TableStyle([('FONTNAME',(0,0),(-1,-1),font),('FONTSIZE',(0,0),(-1,-1),9),('LEADING',(0,0),(-1,-1),13),('GRID',(0,0),(-1,-1),0.5,colors.grey),('BACKGROUND',(0,0),(-1,0),colors.lightgrey),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
    story += [t, Paragraph('二、風險分析', h2)]

    rb = entry.get('risk_breakdown') or {}
    rows=[['分析層', '分數', '權重', '貢獻']]
    for c in rb.get('components', []):
        rows.append([str(c.get('name','')), f"{float(c.get('score',0)):.1f}", f"{c.get('weight',0)}%", f"{float(c.get('contribution',0)):.1f}"])
    if len(rows)>1:
        tt=Table(rows, colWidths=[150,90,90,90], repeatRows=1)
        tt.setStyle(TableStyle([('FONTNAME',(0,0),(-1,-1),font),('FONTSIZE',(0,0),(-1,-1),9),('GRID',(0,0),(-1,-1),0.5,colors.grey),('BACKGROUND',(0,0),(-1,0),colors.lightgrey),('ALIGN',(1,1),(-1,-1),'CENTER'),('VALIGN',(0,0),(-1,-1),'MIDDLE')]))
        story.append(tt)
    story.append(Paragraph(f"融合公式：{entry.get('fusion_formula','—')}", small))
    story.append(Paragraph(f"最終風險分數：{risk}/100", body))

    story.append(Paragraph('三、可疑特徵與分析說明', h2))
    findings=entry.get('explainable_findings') or []
    if findings:
        for x in findings[:10]:
            story.append(Paragraph(f"• {x.get('title','可疑特徵')}：{x.get('detail','')}", body))
    else:
        story.append(Paragraph('未提供額外可疑特徵。', body))
    story.append(Paragraph(f"AI 分析說明：{entry.get('explanation','—')}", body))

    story.append(Paragraph('四、安全處置建議', h2))
    actions=entry.get('safety_actions') or []
    for i,a in enumerate(actions[:8],1):
        story.append(Paragraph(f'{i}. {a}', body))
    if not actions:
        story.append(Paragraph('請依目前風險等級進行人工確認。', body))

    ir=entry.get('ir')
    if ir:
        story.append(Paragraph('五、資安事件回應（IR）', h2))
        ir_rows=[
            ['事件 ID', str(ir.get('id','—'))],
            ['嚴重等級', str(ir.get('severity','—'))],
            ['狀態', str(ir.get('status','Open'))],
            ['建立時間', str(ir.get('created_at','—'))],
            ['影響評估', str(ir.get('impact','—'))],
            ['隔離 / Containment', str(ir.get('containment','—'))],
            ['驗證 / Verification', str(ir.get('verification','—'))],
            ['復原 / Recovery', str(ir.get('recovery','—'))],
        ]
        it=Table(ir_rows, colWidths=[125,355])
        it.setStyle(TableStyle([('FONTNAME',(0,0),(-1,-1),font),('FONTSIZE',(0,0),(-1,-1),8.8),('LEADING',(0,0),(-1,-1),13),('GRID',(0,0),(-1,-1),0.5,colors.grey),('BACKGROUND',(0,0),(0,-1),colors.lightgrey),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
        story.append(it)
        if ir.get('actions'):
            story.append(Spacer(1,6))
            story.append(Paragraph('立即處置：' + '；'.join(str(x) for x in ir['actions'][:5]), body))

    story += [Spacer(1,12), Paragraph('※ 本報告為 AI 與規則式偵測之輔助結果，不能取代人工資安判斷。請勿因低風險結果而直接信任未知郵件。', small)]
    doc.build(story)
    buf.seek(0)
    return buf

def get_header(msg, name):
    for h in msg['payload']['headers']:
        if h['name'].lower() == name.lower(): return h['value']
    return ''

def get_body(msg):
    body = ''
    if 'parts' in msg['payload']:
        for part in msg['payload']['parts']:
            if part['mimeType'] == 'text/plain':
                data = part['body'].get('data','')
                if data: body = base64.urlsafe_b64decode(data).decode('utf-8',errors='ignore'); break
    else:
        data = msg['payload']['body'].get('data','')
        if data: body = base64.urlsafe_b64decode(data).decode('utf-8',errors='ignore')
    return body[:500]

def get_html(msg):
    html = ''
    if 'parts' in msg['payload']:
        for part in msg['payload']['parts']:
            if part['mimeType'] == 'text/html':
                data = part['body'].get('data','')
                if data: html = base64.urlsafe_b64decode(data).decode('utf-8',errors='ignore'); break
            if 'parts' in part:
                for sub in part['parts']:
                    if sub['mimeType'] == 'text/html':
                        data = sub['body'].get('data','')
                        if data: html = base64.urlsafe_b64decode(data).decode('utf-8',errors='ignore'); break
    return html

# ── Flask ─────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-only-change-me')
_state = {}
_creds = {}
_scans = {}

@app.route('/')
def index():
    return HOME_HTML

def create_google_flow(state=None):
    """建立 Google OAuth Flow。優先使用環境變數，沒有才讀 credentials.json。"""
    redirect_uri = f'{BASE_URL}/callback'
    if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
        config = {
            'web': {
                'client_id': GOOGLE_CLIENT_ID,
                'project_id': GOOGLE_PROJECT_ID,
                'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
                'token_uri': 'https://oauth2.googleapis.com/token',
                'auth_provider_x509_cert_url': 'https://www.googleapis.com/oauth2/v1/certs',
                'client_secret': GOOGLE_CLIENT_SECRET,
                'redirect_uris': [redirect_uri]
            }
        }
        return Flow.from_client_config(config, scopes=SCOPES,
                                       redirect_uri=redirect_uri, state=state)

    if os.path.exists('credentials.json'):
        return Flow.from_client_secrets_file(
            'credentials.json', scopes=SCOPES,
            redirect_uri=redirect_uri, state=state)

    raise RuntimeError(
        '找不到 Google OAuth 設定。請設定 GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET，'
        '或放置 credentials.json。'
    )

@app.route('/login')
def login():
    import secrets, hashlib, base64 as _b64
    cv = secrets.token_urlsafe(64)
    cc = _b64.urlsafe_b64encode(hashlib.sha256(cv.encode()).digest()).rstrip(b'=').decode()
    _state['code_verifier'] = cv
    flow = create_google_flow()
    auth_url, state = flow.authorization_url(prompt='consent', access_type='offline',
                                              code_challenge=cc, code_challenge_method='S256')
    _state['current'] = state
    return redirect(auth_url)

@app.route('/callback')
def callback():
    try:
        flow = create_google_flow(state=_state.get('current',''))
        auth_resp = request.url.replace('http://','https://')
        flow.fetch_token(authorization_response=auth_resp,
                         code_verifier=_state.get('code_verifier',''))
        creds = flow.credentials
        _creds['current'] = {
            'token': creds.token, 'refresh_token': creds.refresh_token,
            'token_uri': creds.token_uri, 'client_id': creds.client_id,
            'client_secret': creds.client_secret, 'scopes': list(creds.scopes)
        }
        return redirect('/scan')
    except Exception as e:
        import traceback
        return f'<h2 style="color:#fff;background:#141414;padding:20px">授權錯誤</h2><pre style="background:#1c1c1c;color:#f0ede8;padding:20px">{traceback.format_exc()}</pre>', 500

def do_scan(token_data, scan_id):
    try:
        creds = Credentials(**token_data)
        service = build('gmail','v1',credentials=creds)
        results_api = service.users().messages().list(
            userId='me', maxResults=15, labelIds=['INBOX']).execute()
        messages = results_api.get('messages',[])

        all_emails = []
        high_list, med_list, low_list = [], [], []
        wl_list = []
        skipped = 0

        for msg_ref in messages:
            msg = service.users().messages().get(
                userId='me', id=msg_ref['id'], format='full').execute()
            sender  = get_header(msg, 'From')
            subject = get_header(msg, 'Subject') or '(無主旨)'
            body    = get_body(msg)
            html    = get_html(msg)
            text    = f"From: {sender}\nSubject: {subject}\nBody: {body}"

            if is_system_report(sender, subject):
                skipped += 1
                continue

            if is_whitelisted(sender):
                entry = {'level':'wl','risk_score':-1,'subject':subject[:55],
                         'sender':sender[:60],'explanation':'來自白名單寄件者，系統判定為安全。',
                         'action':'可安全閱讀','tags':[],'scores':[],
                         'category':'白名單安全信件','ir':None}
                wl_list.append(entry)
                all_emails.append(entry)
                continue

            report, html_score, html_findings, rule_score, spam_prob = full_pipeline(text, html)
            html_tags = [cat for cat,_ in html_findings[:3]]
            tags = report.get('suspicious_points',[])[:5]

            entry = {
                'level': report['risk_level'],
                'risk_score': report['risk_score'],
                'subject': subject[:55],
                'sender': sender[:60],
                'explanation': report.get('explanation','')[:200],
                'action': report.get('recommended_action','')[:120],
                'tags': tags,
                'scores': [
                    ['規則引擎', f'{rule_score}分'],
                    ['ML 機率', f'{spam_prob:.1%}'],
                    ['HTML', f'+{html_score}分']
                ],
                'layers': report.get('analysis_layers', {}),
                'fusion_formula': report.get('fusion_formula', ''),
                'risk_breakdown': report.get('risk_breakdown', {}),
                'explainable_findings': report.get('explainable_findings', []),
                'safety_actions': report.get('safety_actions', []),
                'category': report.get('category',''),
                'ir': None
            }

            if report['risk_level'] == 'high':
                ir_id, ir_detail = gen_ir({'sender':sender,'subject':subject}, report)
                entry['ir'] = {
                    'id': ir_id,
                    'severity': ir_detail.get('severity','High'),
                    'impact': ir_detail.get('impact_assessment','')[:150],
                    'actions': ir_detail.get('immediate_actions',[])[:3],
                    'status': ir_detail.get('status','Open'),
                    'risk_score': ir_detail.get('risk_score', report.get('risk_score',0)),
                    'created_at': ir_detail.get('created_at',''),
                    'containment': ir_detail.get('containment',''),
                    'verification': ir_detail.get('verification',''),
                    'recovery': ir_detail.get('recovery',''),
                }
                high_list.append(entry)
            elif report['risk_level'] == 'medium':
                med_list.append(entry)
            else:
                low_list.append(entry)
            all_emails.append(entry)

        scan_time = datetime.now().strftime('%Y-%m-%d %H:%M')
        save_scan(scan_id, scan_time,
                  len(high_list)+len(med_list)+len(low_list)+len(wl_list),
                  high_list, med_list, low_list, len(wl_list), skipped)

        _scans[scan_id] = {
            'done': True,
            'all_emails': all_emails,
            'high': len(high_list), 'med': len(med_list),
            'low': len(low_list), 'wl': len(wl_list), 'skipped': skipped,
            'total': len(all_emails)
        }
    except Exception as e:
        import traceback
        _scans[scan_id] = {'done': True, 'error': traceback.format_exc()}

@app.route('/scan')
def scan():
    token_data = _creds.get('current')
    if not token_data: return redirect('/')
    scan_id = str(uuid.uuid4())[:8]
    _scans[scan_id] = {'done': False}
    _state['last_scan_id'] = scan_id
    threading.Thread(target=do_scan, args=(token_data, scan_id)).start()
    return LOADING_HTML

@app.route('/scan_status')
def scan_status():
    scan_id = _state.get('last_scan_id','')
    if scan_id and scan_id in _scans:
        return jsonify({'done': _scans[scan_id].get('done',False), 'scan_id': scan_id})
    return jsonify({'done': False, 'scan_id': ''})

@app.route('/paste')
def paste_page():
    return PASTE_HTML.replace('ERROR_PLACEHOLDER', '')

@app.route('/paste_analyze', methods=['POST'])
def paste_analyze():
    sender  = request.form.get('sender', '').strip() or '(未提供寄件者)'
    subject = request.form.get('subject', '').strip() or '(無主旨)'
    body    = request.form.get('body', '').strip()
    html    = request.form.get('html', '').strip()

    if not body:
        err = '<div class="err-box">請貼上郵件內文再送出。</div>'
        return PASTE_HTML.replace('ERROR_PLACEHOLDER', err)

    text = f"From: {sender}\nSubject: {subject}\nBody: {body}"

    try:
        if is_whitelisted(sender):
            entry = {'level': 'wl', 'risk_score': -1, 'subject': subject[:55],
                     'sender': sender[:60], 'explanation': '來自白名單寄件者，系統判定為安全。',
                     'action': '可安全閱讀', 'tags': [], 'scores': [],
                     'category': '白名單安全信件', 'ir': None}
            high = med = low = 0
            wl = 1
        else:
            report, html_score, html_findings, rule_score, spam_prob = full_pipeline(text, html)
            html_tags = [cat for cat, _ in html_findings[:3]]
            tags = report.get('suspicious_points', [])[:5]
            entry = {
                'level': report['risk_level'],
                'risk_score': report['risk_score'],
                'subject': subject[:55],
                'sender': sender[:60],
                'explanation': report.get('explanation', '')[:200],
                'action': report.get('recommended_action', '')[:120],
                'tags': tags,
                'scores': [
                    ['規則引擎', f'{rule_score}分'],
                    ['ML 機率', f'{spam_prob:.1%}'],
                    ['HTML', f'+{html_score}分']
                ],
                'layers': report.get('analysis_layers', {}),
                'fusion_formula': report.get('fusion_formula', ''),
                'risk_breakdown': report.get('risk_breakdown', {}),
                'explainable_findings': report.get('explainable_findings', []),
                'safety_actions': report.get('safety_actions', []),
                'category': report.get('category', ''),
                'ir': None
            }
            high = med = low = wl = 0
            if report['risk_level'] == 'high':
                ir_id, ir_detail = gen_ir({'sender': sender, 'subject': subject}, report)
                entry['ir'] = {
                    'id': ir_id,
                    'severity': ir_detail.get('severity', 'High'),
                    'impact': ir_detail.get('impact_assessment', '')[:150],
                    'actions': ir_detail.get('immediate_actions', [])[:3],
                    'status': ir_detail.get('status','Open'),
                    'risk_score': ir_detail.get('risk_score', report.get('risk_score',0)),
                    'created_at': ir_detail.get('created_at',''),
                    'containment': ir_detail.get('containment',''),
                    'verification': ir_detail.get('verification',''),
                    'recovery': ir_detail.get('recovery',''),

                }
                high = 1
            elif report['risk_level'] == 'medium':
                med = 1
            else:
                low = 1

        scan_id = str(uuid.uuid4())[:8]
        _scans[scan_id] = {
            'done': True,
            'all_emails': [entry],
            'high': high, 'med': med, 'low': low, 'wl': wl, 'skipped': 0,
            'total': 1
        }
        scan_time = datetime.now().strftime('%Y-%m-%d %H:%M')
        save_scan(scan_id, scan_time, 1, ['x'] * high, ['x'] * med, ['x'] * low, wl, 0)
        return redirect(f'/result/{scan_id}')
    except Exception:
        import traceback
        err = f'<div class="err-box"><pre>{traceback.format_exc()}</pre></div>'
        return PASTE_HTML.replace('ERROR_PLACEHOLDER', err)

@app.route('/result/<scan_id>')
def result(scan_id):
    data = _scans.get(scan_id)
    if not data or not data.get('done'): return redirect('/')
    if 'error' in data:
        return f'<pre style="background:#1c1c1c;color:#f0ede8;padding:20px">{data["error"]}</pre>', 500

    all_emails = data['all_emails']

    # 建立左側列表 HTML
    def make_item(e, idx):
        dot = {'high':'dot-high','medium':'dot-med','low':'dot-low','wl':'dot-wl'}.get(e['level'],'dot-wl')
        score_text = f"{e['risk_score']}/100 · {e['category']}" if e['risk_score'] >= 0 else '白名單 · 略過分析'
        return (f'<div class="email-item" data-idx="{idx}" onclick="showDetail({idx}, this)">'
                f'<div class="risk-dot {dot}"></div>'
                f'<div class="item-body">'
                f'<div class="item-subj">{e["subject"]}</div>'
                f'<div class="item-from">{e["sender"]}</div>'
                f'<div class="item-score">{score_text}</div>'
                f'</div></div>')

    high_items  = [make_item(e,i) for i,e in enumerate(all_emails) if e['level']=='high']
    med_items   = [make_item(e,i) for i,e in enumerate(all_emails) if e['level']=='medium']
    low_items   = [make_item(e,i) for i,e in enumerate(all_emails) if e['level']=='low']
    wl_items    = [make_item(e,i) for i,e in enumerate(all_emails) if e['level']=='wl']

    list_html = ''
    if high_items:  list_html += '<div class="list-sec">高風險</div>' + ''.join(high_items)
    if med_items:   list_html += '<div class="list-sec">中風險</div>' + ''.join(med_items)
    if low_items:   list_html += '<div class="list-sec">安全</div>' + ''.join(low_items)
    if wl_items:    list_html += '<div class="list-sec">白名單</div>' + ''.join(wl_items)

    # 把資料注入 JS
    import html as html_lib
    emails_json = json.dumps(all_emails, ensure_ascii=False).replace(
        '<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')

    page = RESULT_HTML.replace('LIST_PLACEHOLDER', list_html)
    page = page.replace('PLACEHOLDER_DATA', emails_json)
    page = page.replace('TOTAL_COUNT', str(data['total']))
    page = page.replace('HIGH_COUNT',  str(data['high']))
    page = page.replace('MED_COUNT',   str(data['med']))
    page = page.replace('LOW_COUNT',   str(data['low']))
    page = page.replace('WL_COUNT',    str(data['wl']))
    page = page.replace('SK_COUNT',    str(data['skipped']))
    return page

@app.route('/report/<scan_id>/<int:index>/pdf')
def report_pdf(scan_id, index):
    data = _scans.get(scan_id)
    if not data or not data.get('done'):
        return redirect('/')
    emails = data.get('all_emails', [])
    if index < 0 or index >= len(emails):
        return '找不到指定郵件', 404
    entry = emails[index]
    email_data = {'sender': entry.get('sender',''), 'subject': entry.get('subject','')}
    pdf = create_pdf_report(email_data, scan_id, index, entry)
    filename = f"phishing_report_{scan_id}_{index+1}.pdf"
    return send_file(pdf, mimetype='application/pdf', as_attachment=True, download_name=filename)

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
    domain = request.get_json().get('domain','').strip().lower()
    if not domain: return jsonify({'success':False,'error':'請輸入網域'})
    try:
        conn = sqlite3.connect('phishing.db')
        c = conn.cursor()
        c.execute('INSERT INTO whitelist (domain, added_time) VALUES (?,?)',
                 (domain, datetime.now().isoformat()))
        conn.commit(); conn.close()
        return jsonify({'success':True})
    except Exception as e:
        return jsonify({'success':False,'error':str(e)})

@app.route('/whitelist/delete', methods=['POST'])
def whitelist_delete():
    domain = request.get_json().get('domain','')
    conn = sqlite3.connect('phishing.db')
    c = conn.cursor()
    c.execute('DELETE FROM whitelist WHERE domain=?', (domain,))
    conn.commit(); conn.close()
    return jsonify({'success':True})

@app.route('/health')
def health():
    return jsonify({'status':'ok','time':datetime.now().isoformat()})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
