# ============================================================
# AI 釣魚信件偵測系統 - Flask 網頁版 v3（暗色優雅風格）
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
:root {
  --gold: #C9A84C; --gold-light: #E8C97A; --gold-dim: #8A6E2F;
  --bg-deep: #141414; --bg-card: #1C1C1C; --bg-hover: #242424;
  --border-subtle: #2A2A2A; --border-gold: #3A3020;
  --text-main: #F0EDE8; --text-muted: #888070; --text-dim: #555045;
  --red: #C0392B; --red-bg: #1E1010; --red-border: #3A1010;
  --orange: #D4874A; --orange-bg: #1E1508; --orange-border: #3A2008;
  --green: #4A9B6F; --green-bg: #0E1A12; --green-border: #0E2A1A;
  --blue: #4A7EC0; --blue-bg: #0E1520;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
       background: var(--bg-deep); color: var(--text-main); min-height: 100vh; }
.hdr { border-bottom: 0.5px solid var(--border-gold); padding: 14px 28px;
       display: flex; align-items: center; justify-content: space-between; }
.hdr-left { display: flex; align-items: center; gap: 10px; }
.shield { width: 30px; height: 30px; background: linear-gradient(135deg, var(--gold-dim), var(--gold));
          border-radius: 6px; display: flex; align-items: center; justify-content: center; font-size: 15px; }
.hdr h1 { font-size: 14px; font-weight: 500; color: var(--text-main); letter-spacing: 0.02em; }
.hdr-nav { display: flex; gap: 6px; }
.hdr-nav a { font-size: 11px; color: var(--text-muted); text-decoration: none;
             padding: 5px 12px; border-radius: 4px; border: 0.5px solid var(--border-subtle);
             transition: all 0.15s; }
.hdr-nav a:hover { color: var(--text-main); border-color: var(--gold-dim); }
.gold-tag { font-size: 10px; color: var(--gold); background: var(--border-gold);
            padding: 3px 8px; border-radius: 20px; border: 0.5px solid var(--gold-dim);
            letter-spacing: 0.05em; }
.back { display: inline-flex; align-items: center; gap: 6px; font-size: 12px;
        color: var(--text-muted); text-decoration: none; padding: 6px 14px;
        border-radius: 4px; border: 0.5px solid var(--border-subtle);
        margin-bottom: 20px; transition: all 0.15s; }
.back:hover { color: var(--text-main); border-color: var(--gold-dim); }
</style>
"""

# ── 首頁 HTML ────────────────────────────────────────────────
HOME_HTML = COMMON_CSS + """
<style>
.hero { max-width: 560px; margin: 0 auto; padding: 80px 20px; text-align: center; }
.hero-icon { width: 64px; height: 64px; background: linear-gradient(135deg, var(--gold-dim), var(--gold));
             border-radius: 16px; display: flex; align-items: center; justify-content: center;
             font-size: 30px; margin: 0 auto 28px; }
.hero h2 { font-size: 32px; font-weight: 500; color: var(--text-main); margin-bottom: 12px;
           letter-spacing: -0.02em; }
.hero-sub { font-size: 15px; color: var(--text-muted); line-height: 1.7; margin-bottom: 36px; }
.google-btn { display: inline-flex; align-items: center; gap: 10px; background: var(--bg-card);
              color: var(--text-main); font-size: 14px; font-weight: 500; padding: 13px 28px;
              border-radius: 8px; text-decoration: none; border: 0.5px solid var(--border-gold);
              transition: all 0.2s; letter-spacing: 0.01em; }
.google-btn:hover { background: var(--bg-hover); border-color: var(--gold); transform: translateY(-1px); }
.divider { width: 1px; height: 14px; background: var(--border-subtle); }
.features { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-top: 56px; }
.feat { background: var(--bg-card); border: 0.5px solid var(--border-subtle);
        border-radius: 10px; padding: 20px; text-align: left; }
.feat-icon { font-size: 20px; margin-bottom: 10px; }
.feat h3 { font-size: 12px; font-weight: 500; color: var(--text-main); margin-bottom: 4px;
           letter-spacing: 0.02em; text-transform: uppercase; }
.feat p { font-size: 12px; color: var(--text-muted); line-height: 1.5; }
.wl-note { background: var(--bg-card); border: 0.5px solid var(--border-gold);
           border-left: 2px solid var(--gold-dim); border-radius: 8px; padding: 12px 16px;
           margin-top: 24px; font-size: 12px; color: var(--text-muted); text-align: left; }
.wl-note strong { color: var(--gold); }
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
  <span class="gold-tag">CAPSTONE</span>
</div>

<div class="hero">
  <div class="hero-icon">🛡️</div>
  <h2>一鍵掃描你的 Gmail</h2>
  <p class="hero-sub">授權後系統自動掃描最新 15 封信件，<br>用三層 AI 引擎識別釣魚攻擊並產生事件通報報告。</p>
  <a href="/login" class="google-btn">
    <svg width="18" height="18" viewBox="0 0 48 48">
      <path fill="#4285F4" d="M45.12 24.5c0-1.56-.14-3.06-.4-4.5H24v8.51h11.84c-.51 2.75-2.06 5.08-4.39 6.64l7.08 5.51C42.45 36.27 45.12 30.87 45.12 24.5z"/>
      <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/>
      <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.08-5.51c-2.13 1.45-4.84 2.3-8.81 2.3-6.72 0-12.43-4.54-14.47-10.64l-7.98 6.19C5.22 42.79 14.04 48 24 48z"/>
      <path fill="#EA4335" d="M24 4.8L6.4 19.2V43.2h10.4V28.8h14.4v14.4H41.6V19.2z"/>
    </svg>
    <div class="divider"></div>
    使用 Google 帳號授權掃描
  </a>

  <div class="features">
    <div class="feat"><div class="feat-icon">🔍</div><h3>三層 AI 分析</h3><p>規則引擎 + ML 分類器 + LLaMA 3.3 深度語意分析</p></div>
    <div class="feat"><div class="feat-icon">🌐</div><h3>HTML 多模態</h3><p>偵測像素追蹤、偽裝連結、隱藏元素等進階手法</p></div>
    <div class="feat"><div class="feat-icon">📄</div><h3>IR 事件報告</h3><p>高風險信件自動產生標準格式資安事件通報</p></div>
  </div>

  <div class="wl-note">
    <strong>白名單已啟用 —</strong>
    SKIMS、lululemon、Alo Yoga、玉山銀行、Google 等已知安全寄件者直接標記為安全，可在「白名單設定」自訂。
  </div>
</div>
"""

# ── Loading HTML ─────────────────────────────────────────────
LOADING_HTML = COMMON_CSS + """
<style>
.loading-wrap { display: flex; flex-direction: column; align-items: center;
                justify-content: center; min-height: calc(100vh - 57px); gap: 24px; }
.spinner { width: 48px; height: 48px; border: 2px solid var(--border-subtle);
           border-top: 2px solid var(--gold); border-radius: 50%;
           animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.loading-title { font-size: 18px; font-weight: 500; color: var(--text-main); }
.steps { display: flex; flex-direction: column; gap: 8px; }
.step { font-size: 13px; color: var(--text-dim); display: flex; align-items: center; gap: 8px; }
.step.active { color: var(--gold); }
.step-dot { width: 5px; height: 5px; border-radius: 50%; background: var(--border-subtle); flex-shrink: 0; }
.step.active .step-dot { background: var(--gold); }
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
    <div class="shield">🛡️</div>
    <h1>AI 釣魚信件偵測系統</h1>
  </div>
  <span class="gold-tag">SCANNING</span>
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

# ── 結果頁 HTML ──────────────────────────────────────────────
RESULT_HTML = COMMON_CSS + """
<style>
.summary { display: flex; border-bottom: 0.5px solid var(--border-subtle); }
.stat { flex: 1; padding: 16px 24px; border-right: 0.5px solid var(--border-subtle); }
.stat:last-child { border-right: none; }
.stat-num { font-size: 24px; font-weight: 500; margin-bottom: 2px; }
.stat-lbl { font-size: 10px; color: var(--text-muted); letter-spacing: 0.08em; text-transform: uppercase; }
.s-total .stat-num { color: var(--gold); }
.s-high  .stat-num { color: var(--red); }
.s-med   .stat-num { color: var(--orange); }
.s-low   .stat-num { color: var(--green); }
.s-wl    .stat-num { color: var(--text-dim); }
.s-sk    .stat-num { color: var(--text-dim); }
.main { display: flex; height: calc(100vh - 115px); }
.left { width: 310px; border-right: 0.5px solid var(--border-subtle); overflow-y: auto; flex-shrink: 0; }
.list-sec { padding: 10px 18px 6px; font-size: 9px; color: var(--gold-dim);
            letter-spacing: 0.1em; text-transform: uppercase;
            border-bottom: 0.5px solid var(--border-subtle); }
.email-item { padding: 13px 18px; border-bottom: 0.5px solid var(--border-subtle);
              cursor: pointer; transition: background 0.1s;
              display: flex; align-items: flex-start; gap: 10px; }
.email-item:hover { background: var(--bg-hover); }
.email-item.active { background: var(--bg-hover); border-left: 2px solid var(--gold); padding-left: 16px; }
.risk-dot { width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; margin-top: 5px; }
.dot-high { background: var(--red); box-shadow: 0 0 5px var(--red); }
.dot-med  { background: var(--orange); }
.dot-low  { background: var(--green); }
.dot-wl   { background: var(--text-dim); }
.item-body { flex: 1; min-width: 0; }
.item-subj { font-size: 12px; color: var(--text-main); white-space: nowrap;
             overflow: hidden; text-overflow: ellipsis; margin-bottom: 2px; font-weight: 500; }
.item-from { font-size: 11px; color: var(--text-muted); white-space: nowrap;
             overflow: hidden; text-overflow: ellipsis; }
.item-score { font-size: 10px; color: var(--text-dim); margin-top: 2px; }
.right { flex: 1; overflow-y: auto; padding: 28px 32px; }
.detail-badge { display: inline-flex; align-items: center; gap: 6px;
                padding: 4px 12px; border-radius: 20px; font-size: 11px;
                font-weight: 500; margin-bottom: 14px; }
.badge-high { background: var(--red-bg); color: var(--red); border: 0.5px solid var(--red-border); }
.badge-med  { background: var(--orange-bg); color: var(--orange); border: 0.5px solid var(--orange-border); }
.badge-low  { background: var(--green-bg); color: var(--green); border: 0.5px solid var(--green-border); }
.badge-wl   { background: var(--bg-card); color: var(--text-dim); border: 0.5px solid var(--border-subtle); }
.detail-subj { font-size: 20px; font-weight: 500; color: var(--text-main);
               margin-bottom: 5px; letter-spacing: -0.01em; line-height: 1.3; }
.detail-from { font-size: 12px; color: var(--text-muted); margin-bottom: 22px; }
.gold-line { width: 28px; height: 1px; background: var(--gold); opacity: 0.35; margin: 18px 0 14px; }
.sec-label { font-size: 9px; color: var(--gold-dim); letter-spacing: 0.1em;
             text-transform: uppercase; margin-bottom: 8px; }
.detail-text { font-size: 13px; color: var(--text-main); line-height: 1.7; }
.tag-row { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 10px; }
.htag { font-size: 11px; color: var(--orange); background: var(--orange-bg);
        padding: 3px 8px; border-radius: 4px; border: 0.5px solid var(--orange-border); }
.score-row { display: flex; gap: 20px; margin-top: 10px; }
.score-item { font-size: 11px; color: var(--text-muted); }
.score-item span { color: var(--text-main); font-weight: 500; }
.divider { height: 0.5px; background: var(--border-subtle); margin: 18px 0; }
.recommend { font-size: 13px; color: var(--text-main); background: var(--bg-card);
             border: 0.5px solid var(--border-subtle); border-radius: 6px;
             padding: 12px 16px; line-height: 1.6; }
.ir-box { background: #0A160A; border: 0.5px solid #1A3A1A;
          border-left: 2px solid var(--green); border-radius: 8px;
          padding: 14px 18px; margin-top: 18px; }
.ir-label { font-size: 9px; color: var(--green); letter-spacing: 0.1em;
            text-transform: uppercase; margin-bottom: 6px; }
.ir-id { font-size: 11px; color: var(--text-dim); font-family: monospace; margin-bottom: 6px; }
.ir-impact { font-size: 12px; color: #7EC87E; line-height: 1.6; }
.ir-actions { margin-top: 10px; display: flex; flex-direction: column; gap: 4px; }
.ir-action { font-size: 12px; color: #64A8E8; }
.empty-detail { display: flex; align-items: center; justify-content: center;
                height: 100%; color: var(--text-dim); font-size: 13px;
                flex-direction: column; gap: 10px; }
.empty-icon { font-size: 32px; opacity: 0.3; }
</style>
<script>
const emailData = PLACEHOLDER_DATA;

function showDetail(idx) {
  const d = emailData[idx];
  if (!d) return;
  const panel = document.getElementById('right-panel');
  let badgeClass = d.level === 'high' ? 'badge-high' : d.level === 'medium' ? 'badge-med' : d.level === 'low' ? 'badge-low' : 'badge-wl';
  let badgeText = d.level === 'high' ? '🚨 高風險' : d.level === 'medium' ? '⚠️ 中風險' : d.level === 'low' ? '✅ 安全' : '🔒 白名單';
  let scoreStr = d.risk_score >= 0 ? ` &nbsp;·&nbsp; ${d.risk_score} / 100` : '';

  let tagsHtml = d.tags && d.tags.length ? `<div class="tag-row">${d.tags.map(t=>`<span class="htag">${t}</span>`).join('')}</div>` : '';
  let scoresHtml = d.scores ? `<div class="score-row">${d.scores.map(s=>`<div class="score-item">${s[0]} <span>${s[1]}</span></div>`).join('')}</div>` : '';
  let irHtml = d.ir ? `
    <div class="ir-box">
      <div class="ir-label">IR 事件通報報告已自動產生</div>
      <div class="ir-id">${d.ir.id} &nbsp;|&nbsp; 嚴重等級：${d.ir.severity}</div>
      <div class="ir-impact">${d.ir.impact}</div>
      ${d.ir.actions && d.ir.actions.length ? `<div class="ir-actions">${d.ir.actions.map(a=>`<div class="ir-action">• ${a}</div>`).join('')}</div>` : ''}
    </div>` : '';

  panel.innerHTML = `
    <span class="detail-badge ${badgeClass}">${badgeText}${scoreStr}</span>
    <div class="detail-subj">${d.subject}</div>
    <div class="detail-from">來自：${d.sender}</div>
    <div class="gold-line"></div>
    <div class="sec-label">AI 分析說明</div>
    <div class="detail-text">${d.explanation || '—'}</div>
    ${tagsHtml}
    ${scoresHtml}
    <div class="divider"></div>
    <div class="sec-label">建議行動</div>
    <div class="recommend">${d.action || '—'}</div>
    ${irHtml}
  `;

  document.querySelectorAll('.email-item').forEach((el, i) => {
    el.classList.toggle('active', i === idx);
  });
}

window.addEventListener('DOMContentLoaded', () => {
  if (emailData.length > 0) showDetail(0);
});
</script>

<div class="hdr">
  <div class="hdr-left">
    <div class="shield">🛡️</div>
    <h1>AI 釣魚信件偵測系統 — 掃描結果</h1>
  </div>
  <div class="hdr-nav">
    <a href="/history">掃描記錄</a>
    <a href="/whitelist">白名單設定</a>
    <a href="/">重新掃描</a>
  </div>
  <span class="gold-tag">CAPSTONE</span>
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
.container { max-width: 860px; margin: 0 auto; padding: 32px 20px; }
.page-title { font-size: 16px; font-weight: 500; color: var(--text-main); margin-bottom: 20px; }
table { width: 100%; border-collapse: collapse; }
thead tr { border-bottom: 0.5px solid var(--border-gold); }
th { padding: 10px 16px; font-size: 10px; color: var(--gold-dim); letter-spacing: 0.08em;
     text-transform: uppercase; text-align: left; font-weight: 400; }
td { padding: 12px 16px; font-size: 13px; color: var(--text-main);
     border-bottom: 0.5px solid var(--border-subtle); }
tr:hover td { background: var(--bg-hover); }
.cell-high { color: var(--red); font-weight: 500; }
.cell-med { color: var(--orange); }
.cell-low { color: var(--green); }
.empty { padding: 60px; text-align: center; color: var(--text-dim); font-size: 13px; }
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
  <span class="gold-tag">CAPSTONE</span>
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
  <div class="empty">還沒有掃描記錄，<a href="/" style="color:var(--gold)">開始掃描</a>！</div>
  {% endif %}
</div>
"""

# ── 白名單 HTML ──────────────────────────────────────────────
WHITELIST_HTML = COMMON_CSS + """
<style>
.container { max-width: 680px; margin: 0 auto; padding: 32px 20px; }
.page-title { font-size: 16px; font-weight: 500; color: var(--text-main); margin-bottom: 6px; }
.page-sub { font-size: 12px; color: var(--text-muted); margin-bottom: 24px; }
.add-row { display: flex; gap: 8px; margin-bottom: 28px; }
.add-row input { flex: 1; background: var(--bg-card); border: 0.5px solid var(--border-subtle);
                 border-radius: 6px; padding: 10px 14px; color: var(--text-main);
                 font-size: 13px; outline: none; transition: border-color 0.15s; }
.add-row input::placeholder { color: var(--text-dim); }
.add-row input:focus { border-color: var(--gold-dim); }
.add-btn { background: var(--border-gold); color: var(--gold); border: 0.5px solid var(--gold-dim);
           border-radius: 6px; padding: 10px 20px; font-size: 13px; cursor: pointer;
           transition: all 0.15s; white-space: nowrap; }
.add-btn:hover { background: #4A3A18; }
.sec-label { font-size: 9px; color: var(--gold-dim); letter-spacing: 0.1em;
             text-transform: uppercase; margin-bottom: 12px; }
.domain-item { display: flex; justify-content: space-between; align-items: center;
               background: var(--bg-card); border: 0.5px solid var(--border-subtle);
               border-radius: 8px; padding: 12px 16px; margin-bottom: 8px;
               transition: border-color 0.15s; }
.domain-item:hover { border-color: var(--border-gold); }
.domain-name { font-size: 13px; color: var(--text-main); font-family: monospace; }
.domain-time { font-size: 11px; color: var(--text-dim); margin-top: 2px; }
.del-btn { background: var(--red-bg); color: var(--red); border: 0.5px solid var(--red-border);
           border-radius: 4px; padding: 4px 12px; font-size: 11px; cursor: pointer;
           transition: all 0.15s; }
.del-btn:hover { background: #2D1515; }
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
    <div class="shield">🛡️</div>
    <h1>AI 釣魚信件偵測系統</h1>
  </div>
  <div class="hdr-nav">
    <a href="/">首頁</a>
    <a href="/history">掃描記錄</a>
  </div>
  <span class="gold-tag">CAPSTONE</span>
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

    # 建立左側列表 HTML
    def make_item(e, idx):
        dot = {'high':'dot-high','medium':'dot-med','low':'dot-low','wl':'dot-wl'}.get(e['level'],'dot-wl')
        score_text = f"{e['risk_score']}/100 · {e['category']}" if e['risk_score'] >= 0 else '白名單 · 略過分析'
        return (f'<div class="email-item" onclick="showDetail({idx})">'
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
    emails_json = json.dumps(all_emails, ensure_ascii=False)

    page = RESULT_HTML.replace('LIST_PLACEHOLDER', list_html)
    page = page.replace('PLACEHOLDER_DATA', emails_json)
    page = page.replace('TOTAL_COUNT', str(data['total']))
    page = page.replace('HIGH_COUNT',  str(data['high']))
    page = page.replace('MED_COUNT',   str(data['med']))
    page = page.replace('LOW_COUNT',   str(data['low']))
    page = page.replace('WL_COUNT',    str(data['wl']))
    page = page.replace('SK_COUNT',    str(data['skipped']))
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
