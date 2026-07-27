# ============================================================
# AI 釣魚信件偵測系統 - Flask 網頁版 v3.1 (UI/UX 全面優化版)
# ============================================================

import json, os, uuid, threading, base64, re, sqlite3, smtplib
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
GROQ_API_KEY = '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'
MY_EMAIL     = 'sherry940501@gmail.com'
BASE_URL     = 'https://phishing-detector-n8rv.onrender.com'
SCOPES       = ['https://www.googleapis.com/auth/gmail.readonly']

DEFAULT_WHITELIST = [
    'skims.com', 'emails.skims.com', 'links.skims.com',
    'lululemon.com', 'email.lululemon.com', 'e.lululemon.com',
    'aloyoga.com', 'email.aloyoga.com',
    'esunbank.com.tw', 'esun.com.tw', 'esunsec.com.tw',
    'google.com', 'accounts.google.com', 'googlemail.com',
]

SKIP_SUBJECTS = ['[警告]', '[正常]', 'AI 釣魚偵測報告', 'AI 釣魚信件偵測報告']

CRED_DATA = {"web":{"client_id":"727861534469-72ihfsri6r9kpnu56n7541qb2e4ngomk.apps.googleusercontent.com","project_id":"phishing-detector-494720","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_secret":"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","redirect_uris":["https://phishing-detector-n8rv.onrender.com/callback"]}}

with open('credentials.json', 'w') as f:
    json.dump(CRED_DATA, f)

# ── CSS 共用樣式 ─────────────────────────────────────────────
COMMON_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Noto+Sans+TC:wght@400;500;700&display=swap');

:root {
  --gold: #D4AF37;
  --gold-light: #F3E5AB;
  --gold-dim: #7A621E;
  --bg-deep: #0F0F12;
  --bg-card: #18181C;
  --bg-hover: #222228;
  --border-subtle: #26262E;
  --border-gold: #3D351D;
  --text-main: #F4F4F6;
  --text-muted: #8F8F9E;
  --text-dim: #5A5A66;
  --red: #EF4444;
  --red-bg: rgba(239, 68, 68, 0.1);
  --red-border: rgba(239, 68, 68, 0.25);
  --orange: #F97316;
  --orange-bg: rgba(249, 115, 22, 0.1);
  --orange-border: rgba(249, 115, 22, 0.25);
  --green: #10B981;
  --green-bg: rgba(16, 185, 129, 0.1);
  --green-border: rgba(16, 185, 129, 0.25);
  --blue: #3B82F6;
  --blue-bg: rgba(59, 130, 246, 0.1);
  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 16px;
}

* { box-sizing: border-box; margin: 0; padding: 0; }
body { 
  font-family: 'Inter', 'Noto Sans TC', -apple-system, sans-serif;
  background: var(--bg-deep); 
  color: var(--text-main); 
  min-height: 100vh;
  line-height: 1.5;
  -webkit-font-smoothing: antialiased;
}

/* Header */
.hdr {
  border-bottom: 1px solid var(--border-subtle);
  padding: 16px 32px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: rgba(15, 15, 18, 0.8);
  backdrop-filter: blur(12px);
  position: sticky;
  top: 0;
  z-index: 100;
}
.hdr-left { display: flex; align-items: center; gap: 12px; }
.shield {
  width: 34px; height: 34px;
  background: linear-gradient(135deg, var(--gold-dim), var(--gold));
  border-radius: var(--radius-sm);
  display: flex; align-items: center; justify-content: center;
  font-size: 16px;
  box-shadow: 0 2px 10px rgba(212, 175, 55, 0.2);
}
.hdr h1 { font-size: 15px; font-weight: 600; color: var(--text-main); letter-spacing: -0.01em; }
.hdr-nav { display: flex; gap: 8px; align-items: center; }
.hdr-nav a {
  font-size: 12px; color: var(--text-muted); text-decoration: none;
  padding: 6px 14px; border-radius: var(--radius-sm);
  border: 1px solid var(--border-subtle);
  transition: all 0.2s ease;
  font-weight: 500;
}
.hdr-nav a:hover { color: var(--text-main); border-color: var(--gold); background: var(--bg-hover); }
.gold-tag {
  font-size: 10px; color: var(--gold); background: var(--border-gold);
  padding: 4px 10px; border-radius: 20px; border: 1px solid var(--gold-dim);
  font-weight: 600; letter-spacing: 0.05em;
}
.back {
  display: inline-flex; align-items: center; gap: 8px; font-size: 13px;
  color: var(--text-muted); text-decoration: none; padding: 8px 16px;
  border-radius: var(--radius-sm); border: 1px solid var(--border-subtle);
  margin-bottom: 24px; transition: all 0.2s; font-weight: 500;
}
.back:hover { color: var(--text-main); border-color: var(--gold); background: var(--bg-hover); }

/* Buttons */
.btn {
  display: inline-flex; align-items: center; justify-content: center; gap: 8px;
  padding: 10px 20px; border-radius: var(--radius-sm); font-size: 13px; font-weight: 500;
  cursor: pointer; transition: all 0.2s; border: none; text-decoration: none;
}
.btn-primary {
  background: linear-gradient(135deg, var(--gold), #B89628);
  color: #000; font-weight: 600;
}
.btn-primary:hover { opacity: 0.9; transform: translateY(-1px); }
</style>
"""

# ── 首頁 HTML ────────────────────────────────────────────────
HOME_HTML = COMMON_CSS + """
<style>
.hero { max-width: 640px; margin: 0 auto; padding: 90px 24px; text-align: center; }
.hero-icon {
  width: 72px; height: 72px; background: linear-gradient(135deg, var(--gold-dim), var(--gold));
  border-radius: var(--radius-lg); display: flex; align-items: center; justify-content: center;
  font-size: 36px; margin: 0 auto 32px; box-shadow: 0 0 30px rgba(212, 175, 55, 0.25);
}
.hero h2 { font-size: 36px; font-weight: 700; color: var(--text-main); margin-bottom: 16px; letter-spacing: -0.02em; }
.hero-sub { font-size: 16px; color: var(--text-muted); line-height: 1.6; margin-bottom: 40px; }
.google-btn {
  display: inline-flex; align-items: center; gap: 12px; background: var(--bg-card);
  color: var(--text-main); font-size: 15px; font-weight: 500; padding: 14px 32px;
  border-radius: var(--radius-md); text-decoration: none; border: 1px solid var(--border-gold);
  transition: all 0.25s ease; box-shadow: 0 4px 20px rgba(0,0,0,0.3);
}
.google-btn:hover { background: var(--bg-hover); border-color: var(--gold); transform: translateY(-2px); box-shadow: 0 6px 24px rgba(212, 175, 55, 0.15); }
.divider-v { width: 1px; height: 16px; background: var(--border-subtle); }
.features { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-top: 64px; }
.feat {
  background: var(--bg-card); border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md); padding: 24px; text-align: left; transition: border-color 0.2s;
}
.feat:hover { border-color: var(--border-gold); }
.feat-icon { font-size: 24px; margin-bottom: 12px; }
.feat h3 { font-size: 13px; font-weight: 600; color: var(--text-main); margin-bottom: 6px; letter-spacing: 0.02em; }
.feat p { font-size: 12px; color: var(--text-muted); line-height: 1.6; }
.wl-note {
  background: var(--bg-card); border: 1px solid var(--border-gold);
  border-left: 3px solid var(--gold); border-radius: var(--radius-md); padding: 16px 20px;
  margin-top: 28px; font-size: 13px; color: var(--text-muted); text-align: left; line-height: 1.6;
}
.wl-note strong { color: var(--gold); }
@media (max-width: 768px) {
  .features { grid-template-columns: 1fr; }
  .hero h2 { font-size: 28px; }
}
</style>

<div class="hdr">
  <div class="hdr-left">
    <div class="shield">🛡️</div>
    <h1>AI 釣魚信件偵測系統</h1>
  </div>
  <div class="hdr-nav">
    <a href="/history">掃描記錄</a>
    <a href="/whitelist">白名單設定</a>
  </div>
</div>

<div class="hero">
  <div class="hero-icon">🛡️</div>
  <h2>一鍵掃描你的 Gmail</h2>
  <p class="hero-sub">授權後系統自動讀取最新 15 封信件，<br>運用三層 AI 引擎多維度偵測潛在釣魚威脅並自動通報。</p>
  <a href="/login" class="google-btn">
    <svg width="20" height="20" viewBox="0 0 48 48">
      <path fill="#4285F4" d="M45.12 24.5c0-1.56-.14-3.06-.4-4.5H24v8.51h11.84c-.51 2.75-2.06 5.08-4.39 6.64l7.08 5.51C42.45 36.27 45.12 30.87 45.12 24.5z"/>
      <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/>
      <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.08-5.51c-2.13 1.45-4.84 2.3-8.81 2.3-6.72 0-12.43-4.54-14.47-10.64l-7.98 6.19C5.22 42.79 14.04 48 24 48z"/>
      <path fill="#EA4335" d="M24 4.8L6.4 19.2V43.2h10.4V28.8h14.4v14.4H41.6V19.2z"/>
    </svg>
    <div class="divider-v"></div>
    使用 Google 帳號授權掃描
  </a>

  <div class="features">
    <div class="feat"><div class="feat-icon">🔍</div><h3>三層 AI 分析引擎</h3><p>結合精準規則庫 + ML 機率模型 + LLaMA 3.3 深度語意推理。</p></div>
    <div class="feat"><div class="feat-icon">🌐</div><h3>HTML 多模態解析</h3><p>深度剖析像素追蹤、隱藏釣魚連結與偽裝品牌元素。</p></div>
    <div class="feat"><div class="feat-icon">📄</div><h3>IR 事件報告通報</h3><p>自動生成標準化資安事件通報，即時評估影響層面與應對策略。</p></div>
  </div>

  <div class="wl-note">
    <strong>💡 白名單防護機制 —</strong>
    知名品牌（如 SKIMS、lululemon、玉山銀行、Google 等）與自訂信任網域將自動標記為安全，可至「白名單設定」彈性管理。
  </div>
</div>
"""

# ── Loading HTML ─────────────────────────────────────────────
LOADING_HTML = COMMON_CSS + """
<style>
.loading-wrap { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: calc(100vh - 70px); gap: 28px; }
.spinner {
  width: 54px; height: 54px; border: 3px solid var(--border-subtle);
  border-top: 3px solid var(--gold); border-radius: 50%;
  animation: spin 0.8s cubic-bezier(0.6, 0.2, 0.1, 1) infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
.loading-title { font-size: 20px; font-weight: 600; color: var(--text-main); }
.steps { display: flex; flex-direction: column; gap: 12px; width: 280px; }
.step { font-size: 13px; color: var(--text-dim); display: flex; align-items: center; gap: 10px; transition: color 0.3s; }
.step.active { color: var(--gold); font-weight: 500; }
.step-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--border-subtle); flex-shrink: 0; transition: background 0.3s; }
.step.active .step-dot { background: var(--gold); box-shadow: 0 0 8px var(--gold); }
.progress-bar-bg { width: 280px; height: 4px; background: var(--border-subtle); border-radius: 2px; overflow: hidden; }
.progress-bar { width: 0%; height: 100%; background: var(--gold); transition: width 0.4s ease; }
</style>

<div class="hdr">
  <div class="hdr-left">
    <div class="shield">🛡️</div>
    <h1>AI 釣魚信件偵測系統</h1>
  </div>
  <span class="gold-tag">SCANNING</span>
</div>
<div class="loading-wrap">
  <div class="spinner"></div>
  <div class="loading-title">正在安全掃描你的 Gmail...</div>
  <div class="progress-bar-bg"><div class="progress-bar" id="pbar"></div></div>
  <div class="steps">
    <div class="step active" id="step-0"><div class="step-dot"></div>連線 Gmail API 安全授權...</div>
    <div class="step" id="step-1"><div class="step-dot"></div>讀取收件匣最新信件...</div>
    <div class="step" id="step-2"><div class="step-dot"></div>規則與 HTML 多模態分析...</div>
    <div class="step" id="step-3"><div class="step-dot"></div>LLaMA 3.3 AI 語意推理...</div>
    <div class="step" id="step-4"><div class="step-dot"></div>彙整風險等級並生成報告...</div>
  </div>
</div>

<script>
let stepIdx = 0;
const pbar = document.getElementById('pbar');
const interval = setInterval(() => {
  if (stepIdx < 4) {
    stepIdx++;
    document.getElementById(`step-${stepIdx}`).classList.add('active');
    pbar.style.width = `${(stepIdx + 1) * 20}%`;
  }
}, 2200);

setInterval(() => {
  fetch('/scan_status')
    .then(r => r.json())
    .then(d => {
      if (d.done) {
        pbar.style.width = '100%';
        window.location.href = '/result/' + d.scan_id;
      }
    });
}, 1000);
</script>
"""

# ── 結果頁 HTML ──────────────────────────────────────────────
RESULT_HTML = COMMON_CSS + """
<style>
.summary { display: flex; border-bottom: 1px solid var(--border-subtle); background: var(--bg-card); }
.stat { flex: 1; padding: 20px 24px; border-right: 1px solid var(--border-subtle); text-align: center; }
.stat:last-child { border-right: none; }
.stat-num { font-size: 28px; font-weight: 700; margin-bottom: 2px; }
.stat-lbl { font-size: 11px; color: var(--text-muted); letter-spacing: 0.05em; font-weight: 500; }
.s-total .stat-num { color: var(--gold); }
.s-high  .stat-num { color: var(--red); }
.s-med   .stat-num { color: var(--orange); }
.s-low   .stat-num { color: var(--green); }
.s-wl    .stat-num { color: var(--text-dim); }

.main { display: flex; height: calc(100vh - 145px); }
.left { width: 360px; border-right: 1px solid var(--border-subtle); overflow-y: auto; flex-shrink: 0; background: var(--bg-deep); }
.list-sec {
  padding: 12px 20px 8px; font-size: 10px; color: var(--gold-dim);
  letter-spacing: 0.1em; text-transform: uppercase; font-weight: 700;
  border-bottom: 1px solid var(--border-subtle); background: rgba(0,0,0,0.2);
}
.email-item {
  padding: 16px 20px; border-bottom: 1px solid var(--border-subtle);
  cursor: pointer; transition: background 0.15s;
  display: flex; align-items: flex-start; gap: 12px;
}
.email-item:hover { background: var(--bg-hover); }
.email-item.active { background: var(--bg-hover); border-left: 3px solid var(--gold); padding-left: 17px; }
.risk-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; margin-top: 6px; }
.dot-high { background: var(--red); box-shadow: 0 0 8px var(--red); }
.dot-med  { background: var(--orange); }
.dot-low  { background: var(--green); }
.dot-wl   { background: var(--text-dim); }
.item-body { flex: 1; min-width: 0; }
.item-subj { font-size: 13px; color: var(--text-main); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-bottom: 4px; font-weight: 500; }
.item-from { font-size: 11px; color: var(--text-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.item-score { font-size: 11px; color: var(--text-dim); margin-top: 4px; }

.right { flex: 1; overflow-y: auto; padding: 36px 40px; background: var(--bg-card); }
.detail-badge {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 4px 12px; border-radius: 20px; font-size: 12px;
  font-weight: 600; margin-bottom: 16px;
}
.badge-high { background: var(--red-bg); color: var(--red); border: 1px solid var(--red-border); }
.badge-med  { background: var(--orange-bg); color: var(--orange); border: 1px solid var(--orange-border); }
.badge-low  { background: var(--green-bg); color: var(--green); border: 1px solid var(--green-border); }
.badge-wl   { background: var(--bg-deep); color: var(--text-dim); border: 1px solid var(--border-subtle); }

.detail-subj { font-size: 22px; font-weight: 600; color: var(--text-main); margin-bottom: 8px; line-height: 1.4; }
.detail-from { font-size: 13px; color: var(--text-muted); margin-bottom: 24px; }
.sec-label { font-size: 11px; color: var(--gold); letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 10px; font-weight: 600; }
.detail-text { font-size: 14px; color: var(--text-main); line-height: 1.7; background: var(--bg-deep); padding: 16px; border-radius: var(--radius-md); border: 1px solid var(--border-subtle); }

.tag-row { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 14px; }
.htag { font-size: 11px; color: var(--orange); background: var(--orange-bg); padding: 4px 10px; border-radius: 4px; border: 1px solid var(--orange-border); }

.score-row { display: flex; gap: 16px; margin-top: 16px; }
.score-item { font-size: 12px; color: var(--text-muted); background: var(--bg-deep); padding: 8px 14px; border-radius: var(--radius-sm); border: 1px solid var(--border-subtle); }
.score-item span { color: var(--text-main); font-weight: 600; margin-left: 4px; }

.divider { height: 1px; background: var(--border-subtle); margin: 24px 0; }
.recommend { font-size: 14px; color: var(--text-main); background: var(--bg-deep); border: 1px solid var(--border-subtle); border-radius: var(--radius-md); padding: 16px; line-height: 1.6; }

.ir-box {
  background: rgba(16, 185, 129, 0.05); border: 1px solid var(--green-border);
  border-left: 4px solid var(--green); border-radius: var(--radius-md);
  padding: 20px; margin-top: 24px; position: relative;
}
.ir-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.ir-label { font-size: 11px; color: var(--green); letter-spacing: 0.08em; font-weight: 700; text-transform: uppercase; }
.ir-id { font-size: 12px; color: var(--text-muted); font-family: monospace; }
.ir-impact { font-size: 13px; color: var(--text-main); line-height: 1.6; margin-bottom: 12px; }
.ir-actions { display: flex; flex-direction: column; gap: 6px; }
.ir-action { font-size: 12px; color: #60A5FA; display: flex; align-items: center; gap: 6px; }

.btn-copy { position: absolute; right: 16px; top: 16px; font-size: 11px; padding: 4px 10px; background: var(--bg-card); color: var(--text-muted); border: 1px solid var(--border-subtle); border-radius: var(--radius-sm); cursor: pointer; }
.btn-copy:hover { color: var(--text-main); border-color: var(--gold); }

.empty-detail { display: flex; align-items: center; justify-content: center; height: 100%; color: var(--text-dim); font-size: 14px; flex-direction: column; gap: 12px; }
.empty-icon { font-size: 48px; opacity: 0.3; }

@media (max-width: 900px) {
  .main { flex-direction: column; height: auto; }
  .left { width: 100%; height: 300px; }
  .right { padding: 24px; }
}
</style>

<div class="hdr">
  <div class="hdr-left">
    <div class="shield">🛡️</div>
    <h1>AI 釣魚信件偵測系統 — 分析報告</h1>
  </div>
  <div class="hdr-nav">
    <a href="/history">歷史紀錄</a>
    <a href="/whitelist">白名單</a>
    <a href="/">重新掃描</a>
  </div>
</div>

<div class="summary">
  <div class="stat s-total"><div class="stat-num" id="cnt-total">0</div><div class="stat-lbl">掃描總數</div></div>
  <div class="stat s-high"><div class="stat-num" id="cnt-high">0</div><div class="stat-lbl">高風險</div></div>
  <div class="stat s-med"><div class="stat-num" id="cnt-med">0</div><div class="stat-lbl">中風險</div></div>
  <div class="stat s-low"><div class="stat-num" id="cnt-low">0</div><div class="stat-lbl">安全</div></div>
  <div class="stat s-wl"><div class="stat-num" id="cnt-wl">0</div><div class="stat-lbl">白名單</div></div>
</div>

<div class="main">
  <div class="left" id="left-panel"></div>
  <div class="right" id="right-panel">
    <div class="empty-detail">
      <div class="empty-icon">🛡️</div>
      <div>請點擊左側信件檢視詳細 AI 分析與報告</div>
    </div>
  </div>
</div>

<script>
const rawData = PLACEHOLDER_DATA;
const counts = PLACEHOLDER_COUNTS;

document.getElementById('cnt-total').textContent = counts.total;
document.getElementById('cnt-high').textContent  = counts.high;
document.getElementById('cnt-med').textContent   = counts.med;
document.getElementById('cnt-low').textContent   = counts.low;
document.getElementById('cnt-wl').textContent    = counts.wl;

function renderLeftList() {
  const left = document.getElementById('left-panel');
  left.innerHTML = '';

  const groups = [
    { key: 'high', label: '高風險信件' },
    { key: 'medium', label: '中風險信件' },
    { key: 'low', label: '安全信件' },
    { key: 'wl', label: '白名單信件' }
  ];

  groups.forEach(g => {
    const items = rawData.filter(e => e.level === g.key);
    if (items.length === 0) return;

    const secHeader = document.createElement('div');
    secHeader.className = 'list-sec';
    secHeader.textContent = g.label;
    left.appendChild(secHeader);

    items.forEach(item => {
      const globalIdx = rawData.indexOf(item);
      const div = document.createElement('div');
      div.className = 'email-item';
      div.dataset.index = globalIdx;

      const dotClass = { high:'dot-high', medium:'dot-med', low:'dot-low', wl:'dot-wl' }[item.level] || 'dot-wl';
      const scoreTxt = item.risk_score >= 0 ? `${item.risk_score}/100 · ${item.category}` : '白名單 · 免掃描';

      div.innerHTML = `
        <div class="risk-dot ${dotClass}"></div>
        <div class="item-body">
          <div class="item-subj"></div>
          <div class="item-from"></div>
          <div class="item-score"></div>
        </div>
      `;

      div.querySelector('.item-subj').textContent = item.subject;
      div.querySelector('.item-from').textContent = item.sender;
      div.querySelector('.item-score').textContent = scoreTxt;

      div.onclick = () => showDetail(globalIdx);
      left.appendChild(div);
    });
  });
}

function showDetail(idx) {
  const d = rawData[idx];
  if (!d) return;

  document.querySelectorAll('.email-item').forEach(el => {
    el.classList.toggle('active', parseInt(el.dataset.index) === idx);
  });

  const panel = document.getElementById('right-panel');
  panel.innerHTML = '';

  // Badge
  const badge = document.createElement('span');
  const badgeMap = {
    high: ['badge-high', '🚨 高風險'],
    medium: ['badge-med', '⚠️ 中風險'],
    low: ['badge-low', '✅ 安全'],
    wl: ['badge-wl', '🔒 白名單']
  };
  const [bClass, bTxt] = badgeMap[d.level] || badgeMap.wl;
  badge.className = `detail-badge ${bClass}`;
  badge.textContent = d.risk_score >= 0 ? `${bTxt} · 風險分數 ${d.risk_score}/100` : bTxt;
  panel.appendChild(badge);

  // Subject & From
  const subj = document.createElement('div');
  subj.className = 'detail-subj';
  subj.textContent = d.subject;
  panel.appendChild(subj);

  const from = document.createElement('div');
  from.className = 'detail-from';
  from.textContent = `寄件者：${d.sender}`;
  panel.appendChild(from);

  // Explanation
  const expLabel = document.createElement('div');
  expLabel.className = 'sec-label';
  expLabel.textContent = 'AI 語意分析說明';
  panel.appendChild(expLabel);

  const expText = document.createElement('div');
  expText.className = 'detail-text';
  expText.textContent = d.explanation || '（無說明）';
  panel.appendChild(expText);

  // Tags
  if (d.tags && d.tags.length > 0) {
    const tagRow = document.createElement('div');
    tagRow.className = 'tag-row';
    d.tags.forEach(t => {
      const span = document.createElement('span');
      span.className = 'htag';
      span.textContent = t;
      tagRow.appendChild(span);
    });
    panel.appendChild(tagRow);
  }

  // Scores
  if (d.scores && d.scores.length > 0) {
    const scoreRow = document.createElement('div');
    scoreRow.className = 'score-row';
    d.scores.forEach(s => {
      const item = document.createElement('div');
      item.className = 'score-item';
      item.textContent = `${s[0]}: `;
      const val = document.createElement('span');
      val.textContent = s[1];
      item.appendChild(val);
      scoreRow.appendChild(item);
    });
    panel.appendChild(scoreRow);
  }

  // Divider
  const div1 = document.createElement('div');
  div1.className = 'divider';
  panel.appendChild(div1);

  // Recommendation
  const recLabel = document.createElement('div');
  recLabel.className = 'sec-label';
  recLabel.textContent = '處置建議';
  panel.appendChild(recLabel);

  const recText = document.createElement('div');
  recText.className = 'recommend';
  recText.textContent = d.action || '（無建議）';
  panel.appendChild(recText);

  // IR Report
  if (d.ir) {
    const irBox = document.createElement('div');
    irBox.className = 'ir-box';
    
    const irHeader = document.createElement('div');
    irHeader.className = 'ir-header';
    irHeader.innerHTML = `
      <div class="ir-label">🛡️ IR 通報報告已生成</div>
      <div class="ir-id">${d.ir.id} | 嚴重程度：${d.ir.severity}</div>
    `;

    const copyBtn = document.createElement('button');
    copyBtn.className = 'btn-copy';
    copyBtn.textContent = '複製 IR 摘要';
    copyBtn.onclick = () => {
      const textToCopy = `[${d.ir.id}] 風險: ${d.ir.severity}\n寄件者: ${d.sender}\n影響評估: ${d.ir.impact}`;
      navigator.clipboard.writeText(textToCopy);
      copyBtn.textContent = '已複製！';
      setTimeout(() => copyBtn.textContent = '複製 IR 摘要', 2000);
    };
    irBox.appendChild(copyBtn);
    irBox.appendChild(irHeader);

    const impact = document.createElement('div');
    impact.className = 'ir-impact';
    impact.textContent = d.ir.impact;
    irBox.appendChild(impact);

    if (d.ir.actions && d.ir.actions.length > 0) {
      const actionsDiv = document.createElement('div');
      actionsDiv.className = 'ir-actions';
      d.ir.actions.forEach(act => {
        const aItem = document.createElement('div');
        aItem.className = 'ir-action';
        aItem.textContent = `• ${act}`;
        actionsDiv.appendChild(aItem);
      });
      irBox.appendChild(actionsDiv);
    }
    panel.appendChild(irBox);
  }
}

window.addEventListener('DOMContentLoaded', () => {
  renderLeftList();
  if (rawData.length > 0) showDetail(0);
});
</script>
"""

# ── 歷史記錄 HTML ────────────────────────────────────────────
HISTORY_HTML = COMMON_CSS + """
<style>
.container { max-width: 900px; margin: 0 auto; padding: 40px 24px; }
.page-title { font-size: 20px; font-weight: 600; color: var(--text-main); margin-bottom: 24px; }
.table-card { background: var(--bg-card); border: 1px solid var(--border-subtle); border-radius: var(--radius-md); overflow: hidden; }
table { width: 100%; border-collapse: collapse; text-align: left; }
thead tr { background: var(--bg-deep); border-bottom: 1px solid var(--border-subtle); }
th { padding: 14px 20px; font-size: 11px; color: var(--gold); letter-spacing: 0.08em; text-transform: uppercase; font-weight: 600; }
td { padding: 16px 20px; font-size: 13px; color: var(--text-main); border-bottom: 1px solid var(--border-subtle); }
tr:last-child td { border-bottom: none; }
tr:hover td { background: var(--bg-hover); }
.cell-high { color: var(--red); font-weight: 600; }
.cell-med { color: var(--orange); }
.cell-low { color: var(--green); }
.empty { padding: 60px; text-align: center; color: var(--text-dim); font-size: 14px; }
</style>

<div class="hdr">
  <div class="hdr-left">
    <div class="shield">🛡️</div>
    <h1>AI 釣魚信件偵測系統</h1>
  </div>
  <div class="hdr-nav">
    <a href="/">首頁</a>
    <a href="/whitelist">白名單設定</a>
  </div>
</div>

<div class="container">
  <a href="/" class="back">← 返回首頁</a>
  <div class="page-title">掃描歷史紀錄</div>
  
  <div class="table-card">
    {% if history %}
    <table>
      <thead>
        <tr>
          <th>掃描時間</th>
          <th>總計</th>
          <th>高風險</th>
          <th>中風險</th>
          <th>安全</th>
          <th>白名單</th>
        </tr>
      </thead>
      <tbody>
      {% for h in history %}
      <tr>
        <td style="font-family: monospace;">{{h[1]}}</td>
        <td><strong>{{h[2]}}</strong></td>
        <td class="cell-high">{{h[3]}}</td>
        <td class="cell-med">{{h[4]}}</td>
        <td class="cell-low">{{h[5]}}</td>
        <td style="color:var(--text-dim)">{{h[6]}}</td>
      </tr>
      {% endfor %}
      </tbody>
    </table>
    {% else %}
    <div class="empty">尚無掃描紀錄，<a href="/" style="color:var(--gold); text-decoration: none;">立即進行首次掃描</a>。</div>
    {% endif %}
  </div>
</div>
"""

# ── 白名單 HTML ──────────────────────────────────────────────
WHITELIST_HTML = COMMON_CSS + """
<style>
.container { max-width: 680px; margin: 0 auto; padding: 40px 24px; }
.page-title { font-size: 20px; font-weight: 600; color: var(--text-main); margin-bottom: 8px; }
.page-sub { font-size: 13px; color: var(--text-muted); margin-bottom: 28px; }
.add-row { display: flex; gap: 12px; margin-bottom: 32px; }
.add-row input {
  flex: 1; background: var(--bg-card); border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm); padding: 12px 16px; color: var(--text-main);
  font-size: 14px; outline: none; transition: border-color 0.2s;
}
.add-row input:focus { border-color: var(--gold); }
.sec-label { font-size: 11px; color: var(--gold); letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 14px; font-weight: 600; }
.domain-item {
  display: flex; justify-content: space-between; align-items: center;
  background: var(--bg-card); border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md); padding: 14px 20px; margin-bottom: 10px;
  transition: border-color 0.2s;
}
.domain-item:hover { border-color: var(--border-gold); }
.domain-name { font-size: 14px; color: var(--text-main); font-family: monospace; font-weight: 500; }
.domain-time { font-size: 11px; color: var(--text-dim); margin-top: 2px; }
.del-btn {
  background: var(--red-bg); color: var(--red); border: 1px solid var(--red-border);
  border-radius: var(--radius-sm); padding: 6px 14px; font-size: 12px; cursor: pointer;
  transition: all 0.2s; font-weight: 500;
}
.del-btn:hover { background: rgba(239, 68, 68, 0.2); }
</style>

<div class="hdr">
  <div class="hdr-left">
    <div class="shield">🛡️</div>
    <h1>AI 釣魚信件偵測系統</h1>
  </div>
  <div class="hdr-nav">
    <a href="/">首頁</a>
    <a href="/history">掃描記錄</a>
  </div>
</div>

<div class="container">
  <a href="/" class="back">← 返回首頁</a>
  <div class="page-title">信任網域白名單</div>
  <p class="page-sub">列於白名單中的網域將被視為安全來源，系統將自動跳過 AI 深度分析。</p>

  <div class="add-row">
    <input type="text" id="domain-input" placeholder="輸入網域，例如: example.com">
    <button class="btn btn-primary" onclick="addDomain()">新增網域</button>
  </div>

  <div class="sec-label">目前啟用白名單（{{count}} 個）</div>
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

<script>
function addDomain() {
  const domain = document.getElementById('domain-input').value.trim();
  if (!domain) return alert('請輸入網域');
  fetch('/whitelist/add', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ domain })
  }).then(r => r.json()).then(d => {
    if (d.success) location.reload();
    else alert(d.error || '新增失敗');
  });
}

function deleteDomain(domain) {
  if (!confirm(`確定要將 ${domain} 從白名單移除嗎？`)) return;
  fetch('/whitelist/delete', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ domain })
  }).then(r => r.json()).then(d => {
    if (d.success) location.reload();
  });
}

document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('domain-input').addEventListener('keydown', e => {
    if (e.key === 'Enter') addDomain();
  });
});
</script>
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

def is_whitelisted(sender):
    return any(d in sender.lower() for d in get_whitelist())

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

# ── ML 模型 ──────────────────────────────────────────────────
print('訓練 ML 模型...')
_url = 'https://raw.githubusercontent.com/justmarkham/pycon-2016-tutorial/master/data/sms.tsv'
df = pd.read_csv(_url, sep='\t', header=None, names=['label', 'text'])
X_train, X_test, y_train, y_test = train_test_split(
    df['text'], df['label'], test_size=0.2, random_state=42, stratify=df['label'])
vectorizer = TfidfVectorizer(max_features=3000, stop_words='english')
X_train_vec = vectorizer.fit_transform(X_train)
model = LogisticRegression(max_iter=1000, random_state=42)
model.fit(X_train_vec, y_train)
groq_client = Groq(api_key=GROQ_API_KEY)
print('OK - 模型就緒')

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
            messages=[{'role': 'user', 'content': prompt}], temperature=0.2)
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
            if d in href.lower(): score += 3; findings.append(('可疑連結',[href[:50]])); break
    trackers = [img.get('src','')[:50] for img in soup.find_all('img')
                if str(img.get('width','')) in ['1','0']]
    if trackers: findings.append(('像素追蹤', trackers[:2])); score += len(trackers)*2
    hidden = soup.find_all(style=re.compile(r'display\s*:\s*none', re.I))
    if hidden: findings.append(('隱藏元素',[f'{len(hidden)} 個'])); score += 3
    found_brands = [b for b in ['paypal','microsoft','apple','amazon','facebook','netflix']
                    if b in soup.get_text().lower()]
    if found_brands: findings.append(('品牌偵測',[', '.join(found_brands)])); score += 4
    return score, findings

def full_pipeline(text, html=''):
    score, rules = rule_based_score(text)
    vec = vectorizer.transform([text])
    spam_prob = model.predict_proba(vec)[0][list(model.classes_).index('spam')]
    html_score, html_findings = (0, [])
    if html: html_score, html_findings = analyze_html(html)
    total = score + (html_score // 2)
    if total >= 4 or spam_prob >= 0.3:
        report = ai_agent_analyze(text, total, rules)
    else:
        report = {'risk_level':'low','risk_score':int(spam_prob*100),
                  'category':'正常信件','explanation':'安全信件',
                  'recommended_action':'可安全閱讀','suspicious_points':[]}
    for cat, items in html_findings:
        for item in items:
            report['suspicious_points'].append(f'[HTML] {cat}: {item}')
    return report, html_score, html_findings, score, spam_prob

def gen_ir(email_data, report):
    incident_id = f"IR-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"
    prompt = (
        "You are a cybersecurity analyst. Reply ONLY with JSON.\n"
        f"Email from: {email_data['sender']}\nSubject: {email_data['subject']}\n"
        f"Risk: {report['risk_score']}/100\n"
        'JSON: {"severity":"Critical/High/Medium","impact_assessment":"繁體中文",'
        '"immediate_actions":["行動1","行動2","行動3"]}'
    )
    try:
        resp = groq_client.chat.completions.create(
            model='llama-3.3-70b-versatile',
            messages=[{'role':'user','content':prompt}], temperature=0.2)
        raw = resp.choices[0].message.content.strip().replace('```json','').replace('```','').strip()
        ir = json.loads(raw)
    except:
        ir = {'severity':'High','impact_assessment':'可能導致個資外洩或財務損失',
              'immediate_actions':['不要點擊連結','不要提供個資','向資安人員通報']}
    return incident_id, ir

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
app.secret_key = 'phishing2024elegant'
_state = {}
_creds = {}
_scans = {}

@app.route('/')
def index():
    return HOME_HTML

@app.route('/login')
def login():
    import secrets, hashlib, base64 as _b64
    cv = secrets.token_urlsafe(64)
    cc = _b64.urlsafe_b64encode(hashlib.sha256(cv.encode()).digest()).rstrip(b'=').decode()
    _state['code_verifier'] = cv
    flow = Flow.from_client_secrets_file('credentials.json', scopes=SCOPES,
                                          redirect_uri=f'{BASE_URL}/callback')
    auth_url, state = flow.authorization_url(prompt='consent', access_type='offline',
                                              code_challenge=cc, code_challenge_method='S256')
    _state['current'] = state
    return redirect(auth_url)

@app.route('/callback')
def callback():
    try:
        flow = Flow.from_client_secrets_file('credentials.json', scopes=SCOPES,
            redirect_uri=f'{BASE_URL}/callback', state=_state.get('current',''))
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
                'category': report.get('category',''),
                'ir': None
            }

            if report['risk_level'] == 'high':
                ir_id, ir_detail = gen_ir({'sender':sender,'subject':subject}, report)
                entry['ir'] = {
                    'id': ir_id,
                    'severity': ir_detail.get('severity','High'),
                    'impact': ir_detail.get('impact_assessment','')[:150],
                    'actions': ir_detail.get('immediate_actions',[])[:3]
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

@app.route('/result/<scan_id>')
def result(scan_id):
    data = _scans.get(scan_id)
    if not data or not data.get('done'): return redirect('/')
    if 'error' in data:
        return f'<pre style="background:#1c1c1c;color:#f0ede8;padding:20px">{data["error"]}</pre>', 500

    all_emails = data['all_emails']
    counts = {
        'total': data['total'],
        'high': data['high'],
        'med': data['med'],
        'low': data['low'],
        'wl': data['wl'],
        'skipped': data['skipped']
    }

    emails_json = json.dumps(all_emails, ensure_ascii=False)
    counts_json = json.dumps(counts, ensure_ascii=False)

    page = RESULT_HTML.replace('PLACEHOLDER_DATA', emails_json)
    page = page.replace('PLACEHOLDER_COUNTS', counts_json)
    return page

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
