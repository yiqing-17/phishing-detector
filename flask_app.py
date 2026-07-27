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

# ── CSS 共用樣式 (全站統一風格：極簡深藍黑主題) ───────────────────
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
* { box-sizing: border-box; margin: 0; padding: 0; }
body { 
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: var(--bg-main); 
  color: var(--text-main); 
  min-height: 100vh; 
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

    <div class="features-grid">
      <div class="feature-card">
        <div class="feature-icon">🔍</div>
        <h3>三層 AI 分析</h3>
        <p>規則引擎 + ML + LLaMA 3.3 深度分析</p>
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

# ── 結果頁 HTML ──────────────────────────────────────────────
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
              cursor: pointer; transition: background 0.15s ease;
              display: flex; align-items: flex-start; gap: 10px; }
.email-item:hover { background: var(--bg-hover); }
.email-item.active { background: var(--bg-hover); border-left: 3px solid var(--blue); padding-left: 15px; }
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
.score-row { display: flex; gap: 20px; margin-top: 12px; }
.score-item { font-size: 12px; color: var(--text-muted); }
.score-item span { color: var(--text-main); font-weight: 600; }
.divider { height: 1px; background: var(--border-subtle); margin: 20px 0; }
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
.empty-detail { display: flex; align-items: center; justify-content: center;
                height: 100%; color: var(--text-dim); font-size: 13px;
                flex-direction: column; gap: 10px; }
.empty-icon { font-size: 32px; opacity: 0.4; }
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
