# ============================================================
# AI 釣魚信件偵測系統 - Flask 網頁版 v25（加入測試範例）
# ============================================================

import json, os, uuid, threading, base64, re, sqlite3, smtplib, secrets
import joblib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
try:
    from groq import Groq
except ImportError:
    Groq = None
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

# ── CSS 共用樣式 (全站統一風格：極簡工程風／終端機質感，黑白為主) ───────────────────
COMMON_CSS = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700;800&family=Noto+Sans+TC:wght@400;500;700&family=Noto+Serif+TC:wght@700;900&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root {
  --sans: 'Noto Sans TC', system-ui, sans-serif;
  --serif: 'Noto Serif TC', 'Songti TC', serif;
  --accent: #141414;
  --mono: 'IBM Plex Mono', 'Noto Sans TC', ui-monospace, Menlo, monospace;
  --hl: #ffb6d5;
  --paper: #faf8f3;
  --bg-main: #faf8f3;
  --bg-card: #f2efe7;
  --bg-hover: #ebe7dc;
  --border-subtle: #dcd7ca;
  --border-accent: #a8a291;
  --text-main: #141414;
  --text-muted: #55524a;
  --text-dim: #8a8678;
  --red: #c8321e; --red-bg: rgba(200,50,30,0.07); --red-border: rgba(200,50,30,0.35);
  --orange: #a8650f; --orange-bg: rgba(178,106,0,0.08); --orange-border: rgba(178,106,0,0.35);
  --green: #2e6a4d; --green-bg: rgba(30,122,79,0.08); --green-border: rgba(30,122,79,0.35);
  --blue: #2b4c8c; --blue-bg: rgba(43,76,140,0.07);
}
* { 
  box-sizing: border-box; 
  margin: 0; 
  padding: 0; 
  scrollbar-width: thin;
  scrollbar-color: #333 transparent;
}
body { 
  font-family: var(--mono);
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
  background: #333;
  border-radius:0;
  transition: background 0.2s ease;
}
::-webkit-scrollbar-thumb:hover {
  background: #cfcfcf;
}

/* 全站統一導航列 */
.hdr { 
  border-bottom: 1px solid var(--border-subtle); 
  padding: 16px 32px;
  display: flex; 
  align-items: center; 
  justify-content: space-between; 
}
.hdr-left { display: flex; align-items: center; gap: 10px; font-weight: 600; font-size: 14px; letter-spacing: 0; font-family: var(--mono); }
.hdr-left::before { content: "$"; color: var(--green); margin-right: -2px; }
.shield-icon { display: none; }
.hdr h1 { font-size: 14px; font-weight: 600; color: var(--text-main); letter-spacing: 0; }
.hdr-nav { display: flex; gap: 8px; align-items: center; }
.hdr-nav a { 
  font-size: 12px; 
  color: var(--text-muted); 
  text-decoration: none;
  padding: 6px 12px; 
  border-radius:0; 
  border: 1px solid var(--border-subtle);
  transition: all 0.15s ease; 
}
.hdr-nav a:hover { color: #fff; border-color: #0a0a0a; background: #0a0a0a; }
.proj-tag { 
  background: transparent; 
  border: 1px solid var(--border-subtle);
  color: var(--text-dim); 
  font-size: 11px; 
  padding: 4px 10px; 
  border-radius:0; 
  font-family: var(--mono); 
}
.back { 
  display: inline-flex; align-items: center; gap: 6px; font-size: 12px;
  color: var(--text-muted); text-decoration: none; padding: 6px 14px;
  border-radius:0; border: 1px solid var(--border-subtle);
  margin-bottom: 20px; transition: all 0.15s ease; font-family: var(--mono);
}
.back:hover { color: #fff; border-color: #0a0a0a; background: #0a0a0a; }

.score-breakdown{margin-top:14px;padding:16px 18px;border:1px solid var(--border-subtle);border-radius:0;background:var(--bg-card);color:var(--text-main)}
.score-breakdown h4{margin:0 0 12px;color:var(--text-main);font-size:13px;font-weight:600;letter-spacing:0}.score-breakdown h4::before{content:"# ";color:var(--text-dim)}.score-row{display:flex;justify-content:space-between;align-items:center;gap:16px;padding:9px 0;border-bottom:1px solid var(--border-subtle);font-size:12.5px;color:var(--text-muted);font-family:var(--mono)}.score-row span:first-child{color:var(--text-main)!important;font-weight:500}.score-row span:last-child{color:var(--text-muted)!important;text-align:right;font-family:var(--mono)}.score-total{margin-top:12px;padding-top:2px;font-weight:600;color:var(--text-main);font-family:var(--mono)}

/* STEP 12：分析結果頁 UI（單一色階、直角為主） */
.result-hero{
    background:var(--bg-card);
    border:1px solid var(--border-subtle);
    border-radius:0;
    padding:28px;
    margin-bottom:22px;
}
.result-hero-grid{
    display:grid;
    grid-template-columns:180px 1fr;
    gap:28px;
    align-items:center;
}
.risk-score-box{
    min-height:150px;
    border:1px solid var(--border-subtle);
    border-radius:0;
    display:flex;
    flex-direction:column;
    align-items:center;
    justify-content:center;
    background:var(--bg-main);
}
.risk-score-number{
    font-size:48px;
    line-height:1;
    font-weight:800;
    letter-spacing:-1px;
    font-family:var(--mono);
}
.risk-score-label{
    margin-top:9px;
    color:var(--text-muted);
    font-size:12px;
    font-family:var(--mono);
}
.result-title{
    margin:0 0 10px;
    font-size:22px;
    line-height:1.4;
    word-break:break-word;
}
.result-meta{
    color:var(--text-muted);
    font-size:13px;
    line-height:1.8;
    font-family:var(--mono);
}
.result-focus{
    margin-top:18px;
    padding:14px 16px;
    border-radius:0;
    background:var(--bg-card);
    border-left:2px solid var(--text-dim);
}
.result-focus strong{
    display:block;
    margin-bottom:7px;
    color:var(--text-main);
}
.result-focus ul{
    margin:0;
    padding-left:20px;
    color:var(--text-muted);
}
.result-section{
    margin-top:22px;
}
.result-section-title{
    display:flex;
    align-items:center;
    gap:9px;
    margin:0 0 13px;
    font-size:16px;
    font-family:var(--mono);
}
.layer-grid{
    display:grid;
    grid-template-columns:repeat(2,minmax(0,1fr));
    gap:12px;
}
.layer-card{
    min-width:0;
    border:1px solid var(--border-subtle);
    background:var(--bg-card);
    border-radius:0;
    padding:16px;
    transition:border-color .15s ease;
}
.layer-card:hover{
    border-color:var(--border-accent);
}
.layer-card-top{
    display:flex;
    justify-content:space-between;
    gap:12px;
    align-items:flex-start;
}
.layer-card-name{
    font-weight:700;
    color:var(--text-main);
    font-family:var(--mono);
}
.layer-card-score{
    font-weight:800;
    white-space:nowrap;
    font-family:var(--mono);
}
.layer-card-desc{
    margin:8px 0 13px;
    color:var(--text-muted);
    font-size:12.5px;
    line-height:1.6;
}
.layer-bar{
    height:4px;
    background:var(--border-subtle);
    border-radius:0;
    overflow:hidden;
}
.layer-bar-fill{
    height:100%;
    border-radius:0;
    background:currentColor;
}
.result-panel{
    border:1px solid var(--border-subtle);
    background:var(--bg-card);
    border-radius:0;
    padding:20px;
}
.result-panel + .result-panel{
    margin-top:15px;
}
.finding-list{
    display:grid;
    gap:8px;
}
.finding-item{
    padding:11px 14px;
    border-radius:0;
    background:var(--bg-hover);
    color:var(--text-muted);
    line-height:1.65;
    font-size:13px;
}
.finding-item::before{
    content:"›";
    margin-right:8px;
    color:var(--text-dim);
}
@media(max-width:760px){
    .result-hero{padding:20px;}
    .result-hero-grid{grid-template-columns:1fr;gap:18px;}
    .risk-score-box{min-height:125px;}
    .risk-score-number{font-size:42px;}
    .layer-grid{grid-template-columns:1fr;}
    .result-title{font-size:19px;}
}


/* STEP 13：歷史紀錄頁 UI */
.history-header{display:flex;justify-content:space-between;align-items:flex-end;gap:18px;margin-bottom:20px}
.history-header h1{margin:0 0 6px;font-size:22px;font-family:var(--mono)}
.history-header p{margin:0;color:var(--text-muted);font-size:13px}
.history-toolbar{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:18px}
.history-filter{min-width:180px;padding:10px 13px;border-radius:0;border:1px solid var(--border-subtle);background:var(--bg-card);color:var(--text-main);font-family:var(--mono)}
.history-list{display:grid;gap:10px}
.history-item{display:grid;grid-template-columns:72px 1fr auto;gap:16px;align-items:center;padding:16px 18px;border:1px solid var(--border-subtle);border-radius:0;background:var(--bg-card);transition:border-color .15s ease}
.history-item:hover{border-color:var(--border-accent)}
.history-score{width:54px;height:54px;border-radius:0;display:flex;align-items:center;justify-content:center;background:var(--bg-main);border:1px solid var(--border-subtle);font-weight:800;font-size:16px;font-family:var(--mono)}
.history-subject{font-weight:700;color:var(--text-main);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.history-meta{margin-top:5px;color:var(--text-muted);font-size:12.5px;font-family:var(--mono)}
.history-actions{display:flex;gap:8px;align-items:center}
.history-empty{text-align:center;padding:45px 20px;border:1px dashed var(--border-subtle);border-radius:0;color:var(--text-muted)}
@media(max-width:700px){.history-header{align-items:flex-start;flex-direction:column}.history-item{grid-template-columns:58px 1fr}.history-actions{grid-column:2}}


/* STEP 14：全站導覽列與 Gmail Dashboard UI */
.app-nav{
    display:flex;align-items:center;justify-content:space-between;
    gap:18px;padding:12px 18px;margin-bottom:22px;
    border:1px solid var(--border-subtle);border-radius:0;
    background:var(--bg-card);
}
.app-brand{display:flex;align-items:center;gap:10px;font-weight:800;color:var(--text-main);text-decoration:none;font-family:var(--mono)}
.app-brand-icon{width:30px;height:30px;border-radius:0;display:flex;align-items:center;justify-content:center;background:var(--bg-main);border:1px solid var(--border-subtle)}
.app-nav-links{display:flex;align-items:center;gap:5px;flex-wrap:wrap}
.app-nav-link{
    padding:7px 11px;border-radius:0;color:var(--text-muted);
    text-decoration:none;font-size:12.5px;transition:.15s ease;font-family:var(--mono);
}
.app-nav-link:hover,.app-nav-link.active{color:#fff;background:#0a0a0a}
.dashboard-summary{
    display:grid;grid-template-columns:repeat(5,minmax(0,1fr));
    gap:10px;margin-bottom:18px;
}
.dashboard-stat{
    padding:14px;border:1px solid var(--border-subtle);
    border-radius:0;background:var(--bg-card);
}
.dashboard-stat-label{font-size:11px;color:var(--text-muted);font-family:var(--mono)}
.dashboard-stat-value{margin-top:5px;font-size:22px;font-weight:800;color:var(--text-main);font-family:var(--mono)}
.dashboard-stat-sub{margin-top:3px;font-size:10.5px;color:var(--text-dim)}
.scan-list-header{
    display:flex;justify-content:space-between;align-items:center;
    gap:12px;margin:18px 0 10px;
}
.scan-list-header h2{margin:0;font-size:16px;font-family:var(--mono)}
.scan-list-header span{font-size:11px;color:var(--text-dim)}
.scan-email-card{
    display:grid;grid-template-columns:52px 1fr auto;
    gap:14px;align-items:center;padding:13px 16px;margin-bottom:8px;
    border:1px solid var(--border-subtle);border-radius:0;
    background:var(--bg-card);transition:.15s ease;
}
.scan-email-card:hover{border-color:var(--border-accent)}
.scan-risk{
    width:42px;height:42px;border-radius:0;
    display:flex;align-items:center;justify-content:center;
    background:var(--bg-main);border:1px solid var(--border-subtle);
    font-weight:800;font-size:13px;font-family:var(--mono);
}
.scan-email-subject{font-weight:700;color:var(--text-main);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.scan-email-meta{margin-top:4px;color:var(--text-dim);font-size:11.5px;font-family:var(--mono)}
@media(max-width:900px){.dashboard-summary{grid-template-columns:repeat(3,1fr)}}
@media(max-width:650px){
    .app-nav{align-items:flex-start;flex-direction:column}
    .app-nav-links{width:100%}
    .dashboard-summary{grid-template-columns:repeat(2,1fr)}
    .scan-email-card{grid-template-columns:44px 1fr}
}


/* ── 統一視覺：「被批註的可疑郵件」——螢光筆、色條遮蔽、印章、檔案標籤 ── */
body { font-family: var(--sans); background: var(--paper); color: var(--text-main); }
::selection { background: var(--hl); color: #141414; }
body :focus-visible { outline: 2px solid #141414; outline-offset: 3px; }
body .hdr { display: flex; align-items: center; justify-content: space-between; height: 3rem; padding: 0 2rem; background: var(--paper); border-bottom: 1px solid #141414; }
body .hdr-left { font-family: var(--mono); font-weight: 500; font-size: 12.5px; color: #141414; }
body .hdr-left::before { content: none; }
body .hdr-nav { display: flex; align-items: center; gap: 2rem; }
body .hdr-nav a { display: inline-flex; align-items: center; gap: .55rem; border: 0; border-radius: 0; padding: 0; background: transparent; font-family: var(--mono); font-size: 12.5px; color: #141414; }
body .hdr-nav a:hover { background: transparent; color: #141414; text-decoration: underline; text-decoration-color: #ff6fae; text-decoration-thickness: 3px; text-underline-offset: 4px; }
kbd.k { display: inline-flex; align-items: center; justify-content: center; min-width: 1.25rem; height: 1.25rem; padding: 0 3px; background: #141414; color: var(--paper); border: 0; border-radius: 0; font-family: var(--mono); font-size: 10.5px; font-weight: 600; line-height: 1; text-transform: uppercase; }
body .container, body .paste-wrap { margin-left: 0; margin-right: 0; padding-left: 2rem; padding-right: 2rem; }
body .back { display: flex; width: fit-content; border: 0; padding: 0; background: transparent; color: #141414; font-family: var(--mono); font-size: 12.5px; margin-bottom: 2.25rem; }
body .back:hover { background: transparent; text-decoration: underline; text-decoration-color: #ff6fae; text-decoration-thickness: 3px; text-underline-offset: 4px; }
.ftab { display: inline-flex; align-items: center; gap: .6rem; font-family: var(--mono); font-size: 11.5px; letter-spacing: .08em; text-transform: uppercase; margin-bottom: 1.1rem; }
.ftab mark { background: var(--hl); color: #141414; padding: 1px 7px; font-weight: 600; }
.hl { background: linear-gradient(transparent 58%, var(--hl) 58%); -webkit-box-decoration-break: clone; box-decoration-break: clone; padding: 0 .08em; }
body .page-title, body .paste-title { font-family: var(--serif); font-weight: 900; font-size: clamp(2rem, 4.6vw, 3.9rem); line-height: 1.22; letter-spacing: -.01em; color: #141414; margin-bottom: 1.4rem; text-wrap: balance; }
body .page-title::before, body .page-title::after, body .paste-title::after { content: none; }
body .page-sub, body .paste-sub { font-family: var(--sans); font-size: 14.5px; line-height: 1.85; max-width: 62ch; color: var(--text-muted); }
body .submit-btn, body .add-btn { background: #141414; color: var(--paper); border: 1px solid #141414; border-radius: 0; font-family: var(--mono); font-size: 12.5px; font-weight: 500; padding: .55rem .9rem; }
body .submit-btn:hover, body .add-btn:hover { background: var(--hl); color: #141414; border-color: #141414; }
body .sample-btn, body .ir-dl-btn { background: transparent; color: #141414; border: 1px solid #141414; border-radius: 0; font-family: var(--mono); font-size: 12px; }
body .sample-btn:hover, body .ir-dl-btn:hover { background: var(--hl); color: #141414; border-color: #141414; }
body input, body textarea, body select { border-radius: 0; font-family: var(--mono); background: #fff; }
body input:focus, body textarea:focus, body select:focus { border-color: #141414; outline: none; box-shadow: 0 0 0 3px var(--hl); }
body .field-label::before, body .sample-title::before, body .why-title::before, body .safety-title::before,
body .sec-h::before, body .sec-label::before, body .demo-title::before, body .loading-title::before, body .score-breakdown h4::before { content: none; }
body .sample-title, body .demo-title, body .sec-h, body .sec-label, body .why-title, body .safety-title, body .field-label {
  font-family: var(--mono); font-size: 11.5px; font-weight: 600; text-transform: uppercase; letter-spacing: .08em; color: #141414; }
body table.rt th, body thead tr { background: #141414; color: var(--paper); }
body table.rt th { border-bottom: 0; font-family: var(--mono); font-weight: 500; }
body .kw, body .tag, body .chip { border-radius: 0; background: var(--hl); border: 0; color: #141414; font-family: var(--mono); }
body .stat, body .stat-box { background: transparent; border: 1px solid #141414; border-radius: 0; }
footer.f { background: #141414; color: var(--paper); padding: 3rem 2rem 2.25rem; margin-top: 6rem; font-family: var(--mono); font-size: 12.5px; }
footer.f .big { font-family: var(--serif); font-weight: 900; font-size: clamp(2rem, 6vw, 4.5rem); line-height: 1.1; margin-bottom: 2.5rem; }
footer.f .big span { background: var(--hl); color: #141414; padding: 0 .12em; }
footer.f nav { display: flex; flex-wrap: wrap; gap: .75rem 2rem; }
footer.f a { color: var(--paper); text-decoration: none; }
footer.f a:hover { text-decoration: underline; text-decoration-color: var(--hl); text-decoration-thickness: 3px; text-underline-offset: 4px; }
footer.f .cp { margin-top: 2.25rem; color: #8a8678; }

/* ── 檔案版面：左側固定欄 + 右側主內容（規則／白名單／記錄共用） ── */
.dz { display: grid; grid-template-columns: minmax(0,1fr); }
@media (min-width: 1000px) { .dz { grid-template-columns: 23rem minmax(0,1fr); } }
.dz-side { padding: 1.75rem 2rem 2rem; border-bottom: 1px solid #141414; }
@media (min-width: 1000px) { .dz-side { position: sticky; top: 0; align-self: start; height: calc(100svh - 3rem); overflow-y: auto; border-bottom: 0; border-right: 1px solid #141414; } }
.dz-main { padding: 2rem clamp(1.25rem,4vw,3.5rem) 4rem; min-width: 0; }
.dz + footer.f { margin-top: 0; }
.pg-title { font-family: var(--serif); font-weight: 900; font-size: clamp(2rem,3.2vw,3rem); line-height: 1.22; margin: .1rem 0 1rem; text-wrap: balance; }
.pg-sub { font-size: 13.5px; line-height: 1.85; color: var(--text-muted); }
.nums { display: grid; grid-template-columns: 1fr 1fr; gap: 1px; background: #141414; border: 1px solid #141414; margin-top: 1.5rem; }
.nums div { background: var(--paper); padding: .8rem .9rem; }
.nums b { display: block; font-family: var(--serif); font-weight: 900; font-size: 2.1rem; line-height: 1.05; }
.nums span { font-family: var(--mono); font-size: 11px; color: var(--text-muted); }
.idx { list-style: none; margin: 1.5rem 0 0; padding: 0; font-family: var(--mono); font-size: 12px; }
.idx a { display: flex; gap: .7rem; padding: .4rem 0; border-top: 1px solid #dcd7ca; color: #141414; text-decoration: none; }
.idx a em { font-style: normal; color: var(--text-dim); }
.idx a.on span, .idx a:hover span { background: var(--hl); }
.sh { display: flex; flex-wrap: wrap; align-items: baseline; gap: .4rem 1rem; margin: 3.2rem 0 1.1rem; padding-top: 1rem; border-top: 1px solid #141414; }
.sh:first-child { margin-top: 0; }
.sh .n { font-family: var(--mono); font-size: 12px; font-weight: 600; background: var(--hl); padding: 0 .45rem; }
.sh h2 { font-family: var(--serif); font-weight: 900; font-size: 1.55rem; line-height: 1.3; }
.sh p { flex-basis: 100%; font-family: var(--mono); font-size: 12px; color: var(--text-muted); line-height: 1.7; max-width: 70ch; }
.cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(17rem, 1fr)); gap: 1rem; }
.card { position: relative; display: flex; flex-direction: column; gap: .55rem; background: #fff; border: 1px solid #141414; padding: 1rem 1.1rem 1.15rem; }
.card .rid { font-family: var(--serif); font-weight: 900; font-size: 2.3rem; line-height: 1; }
.card h3 { font-size: 1.05rem; font-weight: 700; }
.card p { font-size: 13px; line-height: 1.7; color: var(--text-muted); }
.card .kws { display: flex; flex-wrap: wrap; gap: .3rem; margin-top: .2rem; }
.card .kws span { background: var(--hl); font-family: var(--mono); font-size: 11.5px; padding: 0 .38rem; }
.st { display: inline-block; border: 2px solid currentColor; padding: .02rem .5rem; font-family: var(--serif); font-weight: 900; font-size: .85rem; line-height: 1.4; transform: rotate(-4deg); mix-blend-mode: multiply; }
.st.red { color: #c8321e; } .st.grn { color: #2e6a4d; } .st.org { color: #a8650f; } .st.ink { color: #141414; }
.card .st { position: absolute; right: .85rem; top: .95rem; font-size: .75rem; max-width: 11rem; text-align: center; }
.note2 { margin-top: .9rem; font-family: var(--mono); font-size: 12px; color: var(--text-muted); line-height: 1.8; }
.note2 b { background: var(--hl); font-weight: 500; padding: 0 .25rem; }

body .hdr-left a { color: inherit; text-decoration: none; font-weight: 600; }
body .hdr-nav a.cur { background: var(--hl); padding: 2px .45rem; }
@media (max-width: 700px) {
  body .hdr { height: auto; min-height: 3rem; flex-wrap: wrap; gap: .3rem 1rem; padding: .6rem 1rem; }
  body .hdr-nav { gap: .9rem; flex-wrap: wrap; }
  body .hdr-nav a kbd.k { display: none; }
  .dz-side { padding: 1.25rem 1rem 1.5rem; }
}
</style>
<script>
document.addEventListener('DOMContentLoaded',function(){
  var path=location.pathname,map={'/rules':'R','/whitelist':'W','/':'H','/history':'L','/paste':'P','/login':'S'};
  var keys={'h':'/'};
  document.querySelectorAll('.hdr-nav a').forEach(function(a){
    var pn=new URL(a.href,location.href).pathname;
    if(pn===path)a.classList.add('cur');
    var k=map[pn];
    if(!k||keys[k.toLowerCase()])return;
    var e=document.createElement('kbd');e.className='k';e.textContent=k;a.appendChild(e);keys[k.toLowerCase()]=a.href;
  });
  document.querySelectorAll('[data-key]').forEach(function(el){keys[el.getAttribute('data-key')]=el.href;});
  var names={'/rules':'rules','/whitelist':'whitelist','/history':'history','/paste':'paste'};
  var t=document.querySelector('.page-title, .paste-title');
  if(names[path]&&t&&!t.querySelector('.hl')){
    var tab=document.createElement('div');tab.className='ftab';tab.innerHTML='<mark>FILE</mark><span>'+names[path]+'</span>';
    t.parentNode.insertBefore(tab,t);
    t.innerHTML='<span class="hl">'+t.innerHTML+'</span>';
  }
  if(path!=='/'&&!document.querySelector('footer.f')&&!document.querySelector('.main')){
    var f=document.createElement('footer');f.className='f';
    f.innerHTML='<div class="big"><span>phishing</span>-detector</div><nav><a href="/rules">偵測規則</a><a href="/whitelist">白名單</a><a href="/paste">貼上分析</a><a href="/login">Google 登入</a></nav>';
    document.body.appendChild(f);
  }
  document.addEventListener('keydown',function(ev){
    if(ev.metaKey||ev.ctrlKey||ev.altKey)return;
    var t2=ev.target,tn=t2&&t2.tagName;
    if(tn==='INPUT'||tn==='TEXTAREA'||tn==='SELECT'||(t2&&t2.isContentEditable))return;
    var h=keys[(ev.key||'').toLowerCase()];
    if(h)location.href=h;
  });
});
</script>

"""

# ── 首頁 HTML (極簡工程風／終端機質感，單頁固定 100vh 滿版，無滾輪) ─────
HOME_HTML = COMMON_CSS + """
<style>
html,body{background:var(--paper);color:#141414;font-family:var(--sans);-webkit-font-smoothing:antialiased;scroll-behavior:smooth}
.wrap{max-width:1560px;margin:0 auto;padding:0 2rem}
.mono{font-family:var(--mono)}
.hero{padding:clamp(2.5rem,7vh,5rem) 0 clamp(3rem,8vh,6rem)}
.hero .wrap{display:grid;gap:3rem;align-items:center}
@media(min-width:1000px){.hero .wrap{grid-template-columns:1fr 1.02fr;gap:4.5rem;min-height:calc(100svh - 3rem - 8rem)}}
h1{font-family:var(--serif);font-weight:900;font-size:clamp(2.3rem,4.7vw,4.4rem);line-height:1.2;letter-spacing:-.01em;text-wrap:balance}
h1 .hl{background:linear-gradient(transparent 56%,var(--hl) 56%)}
.sub{margin-top:1.5rem;max-width:44ch;color:#55524a;font-size:16px;line-height:1.85}
.cta{margin-top:2.25rem;display:flex;flex-direction:column;gap:.6rem;max-width:25rem}
.btn{display:flex;align-items:center;justify-content:space-between;gap:1rem;padding:.7rem .8rem;border:1px solid #141414;background:#141414;color:var(--paper);font-family:var(--mono);font-size:12.5px;text-decoration:none;transition:background .15s,color .15s}
.btn.o{background:transparent;color:#141414}
.btn .key{display:flex;align-items:center;justify-content:center;min-width:1.35rem;height:1.35rem;background:var(--paper);color:#141414;font-weight:600;font-size:11px;text-transform:uppercase}
.btn.o .key{background:#141414;color:var(--paper)}
.btn:hover{background:var(--hl);color:#141414}.btn:hover .key{background:#141414;color:var(--paper)}
/* 被批註的示意郵件 */
.docwrap{position:relative}
.doc{position:relative;background:#fff;border:1px solid #141414;padding:1.75rem 1.9rem 1.5rem;font-family:var(--mono);font-size:13.5px;line-height:2;transform:rotate(-1deg);box-shadow:0 22px 34px -26px rgba(20,20,20,.55)}
.doc dl{margin:0 0 1rem;padding-bottom:1rem;border-bottom:1px solid #dcd7ca}
.doc dl div{display:grid;grid-template-columns:4.2em 1fr;gap:.5rem}
.doc dt{color:#8a8678;font-size:11.5px;letter-spacing:.06em}
.doc dd{margin:0;word-break:break-all}
.doc p{margin:0 0 .6rem;font-family:var(--sans);font-size:15px;line-height:2.1}
mark.m{position:relative;color:#141414;background:linear-gradient(var(--hl),var(--hl)) no-repeat;background-size:100% 100%;padding:.05em .12em;cursor:default;animation:draw .55s cubic-bezier(.3,.7,.3,1) both;animation-delay:calc(var(--i) * .38s + .3s)}
mark.m::after{content:attr(data-n);position:relative;top:-.7em;margin-left:.15em;display:inline-grid;place-items:center;width:1.25em;height:1.25em;border-radius:50%;background:#141414;color:var(--paper);font:600 10px/1 var(--mono)}
@keyframes draw{from{background-size:0% 100%}to{background-size:100% 100%}}
.bar{display:inline-block;background:#141414;color:#141414;padding:0 .2em;transition:background .2s,color .2s;user-select:none;cursor:help}
.bar:hover{background:transparent;color:#141414}
.notes{margin:1.1rem 0 0;padding:1rem 0 0;border-top:1px dashed #a8a291;list-style:none;font-family:var(--sans);font-size:13px;line-height:1.7;color:#55524a}
.notes li{display:flex;gap:.65rem;padding:.12rem 0;transition:color .15s}
.notes li b{flex:none;display:grid;place-items:center;width:1.25rem;height:1.25rem;margin-top:.2rem;border-radius:50%;background:#141414;color:var(--paper);font:600 10px/1 var(--mono)}
.notes li.on{color:#141414}.notes li.on span{background:var(--hl)}
.stamp{position:absolute;right:-1.1rem;top:-1.6rem;z-index:2;padding:.2rem .75rem .25rem;border:3px solid #c8321e;color:#c8321e;text-align:center;font-family:var(--serif);font-weight:900;font-size:1.7rem;line-height:1.15;transform:rotate(9deg);mix-blend-mode:multiply;background:rgba(250,248,243,.35);animation:stamp .45s cubic-bezier(.2,1.7,.4,1) 2.1s both}
.stamp small{display:block;font-family:var(--mono);font-size:.62rem;letter-spacing:.2em;font-weight:600}
@keyframes stamp{from{opacity:0;transform:rotate(22deg) scale(2.4)}to{opacity:.92;transform:rotate(9deg) scale(1)}}
.cap{margin-top:1.1rem;font-family:var(--mono);font-size:11px;color:#8a8678}
@media(prefers-reduced-motion:reduce){mark.m,.stamp{animation:none}.stamp{opacity:.92}}
/* sections */
.sec{border-top:1px solid #141414;padding:clamp(3rem,8vh,5.5rem) 0}
h2{font-family:var(--serif);font-weight:900;font-size:clamp(1.8rem,3.4vw,3rem);line-height:1.25;margin-top:.4rem;max-width:26ch;text-wrap:balance}
h2 .hl{white-space:nowrap}
.rows{margin-top:2.5rem}
.row{display:grid;grid-template-columns:3.2rem 1fr;gap:.2rem 1rem;padding:1.4rem 0;border-top:1px solid #dcd7ca}
.row:last-child{border-bottom:1px solid #dcd7ca}
@media(min-width:800px){.row{grid-template-columns:3.2rem 15rem 1fr 1fr;align-items:baseline}}
.row p,.row .eg{grid-column:2}
@media(min-width:800px){.row p,.row .eg{grid-column:auto}}
.row .n{display:grid;place-items:center;width:1.9rem;height:1.9rem;border-radius:50%;background:#141414;color:var(--paper);font:600 12px/1 var(--mono)}
.row h3{font-family:var(--serif);font-weight:700;font-size:1.3rem}
.row p{color:#55524a;font-size:14.5px}
.row .eg{font-family:var(--mono);font-size:12px;color:#8a8678}
.row .eg mark{background:var(--hl);color:#141414;padding:0 .3em}
table.m{width:100%;border-collapse:collapse;margin-top:2.25rem;font-family:var(--mono);font-size:12.5px}
table.m th{background:#141414;color:var(--paper);text-align:left;font-weight:500;padding:.65rem .9rem}
table.m td{padding:.65rem .9rem;border-bottom:1px solid #dcd7ca;vertical-align:top}
.tw{overflow-x:auto}
.note{margin-top:.8rem;font-family:var(--mono);font-size:11.5px;color:#8a8678;max-width:64ch;line-height:1.7}
.clear{display:grid}
@media(min-width:900px){.clear{grid-template-columns:1fr 1fr}}
.clear>div{padding:clamp(2rem,6vw,4rem) 2rem;position:relative}
.clear .l{background:#ebe7dc}
.clear .r{background:#141414;color:var(--paper);display:flex;flex-direction:column;justify-content:space-between;gap:2.5rem}
.clear .stamp2{position:absolute;right:2rem;top:2rem;border:3px solid #2e6a4d;color:#2e6a4d;padding:.15rem .7rem;font-family:var(--serif);font-weight:900;font-size:1.3rem;transform:rotate(-6deg);mix-blend-mode:multiply}
.clear .stamp2 small{display:block;font-family:var(--mono);font-size:.55rem;letter-spacing:.2em;font-weight:600;text-align:center}
.clear .acts{display:flex;flex-direction:column;gap:.6rem;max-width:20rem}
.clear .btn{background:transparent;color:var(--paper);border-color:var(--paper)}.clear .btn .key{background:var(--paper);color:#141414}
.clear .btn:hover{background:var(--hl);color:#141414;border-color:var(--hl)}
footer.f{margin-top:0;padding:3rem 2rem 2.25rem}
</style>
<div class="hdr"><div class="hdr-left"><a href="/">phishing-detector</a></div><div class="hdr-nav"><a href="/rules">偵測規則</a><a href="/whitelist">白名單</a><a href="/history">掃描記錄</a><a href="/paste">貼上分析</a></div></div>
<main>
<section class="hero"><div class="wrap">
  <div>
    <div class="ftab"><mark>FILE</mark><span>四層分析 / 案件檢視</span></div>
    <h1>安全掃描 Gmail，快速找出<span class="hl">可疑</span>郵件</h1>
    <p class="sub">授權 Google 後掃描最新 15 封郵件，結合規則引擎、機器學習、URL / HTML 解析與 AI 語意判讀，快速找出可疑信件。</p>
    <div class="cta">
      <a class="btn" href="/login" data-key="s"><span>使用 Google 帳號開始掃描</span><span class="key">S</span></a>
      <a class="btn o" href="/paste" data-key="p"><span>不想連接 Gmail？直接貼上郵件內容分析</span><span class="key">P</span></a>
    </div>
  </div>
  <div class="docwrap">
    <div class="stamp" aria-hidden="true">可疑<small>SUSPICIOUS</small></div>
    <article class="doc" aria-label="示意郵件">
      <dl>
        <div><dt>寄件者</dt><dd><span class="bar" title="掃描時會一併檢查寄件網域">service</span>@secure-account.example</dd></div>
        <div><dt>主　旨</dt><dd>您的帳戶已被暫停</dd></div>
      </dl>
      <p>親愛的客戶：<br><mark class="m" data-n="2" style="--i:1">我們偵測到您的帳戶有異常登入行為。</mark><br>
      請<mark class="m" data-n="1" style="--i:0">立即</mark>點擊 <mark class="m" data-n="3" style="--i:2">驗證帳戶</mark>，並<mark class="m" data-n="4" style="--i:3">回覆您的帳號密碼與<span class="bar" title="敏感資訊">信用卡號</span></mark>，否則帳戶將於 <mark class="m" data-n="1" style="--i:0">24 小時內</mark>永久停用。</p>
      <ul class="notes">
        <li data-n="1"><b>1</b><span>規則引擎：命中急迫語氣</span></li>
        <li data-n="2"><b>2</b><span>ML 模型：整體用詞接近釣魚樣本</span></li>
        <li data-n="3"><b>3</b><span>URL / HTML 解析：顯示文字與實際連結需還原比對</span></li>
        <li data-n="4"><b>4</b><span>AI 語意判讀：索取敏感資訊</span></li>
      </ul>
    </article>
    <p class="cap">示意郵件，非真實案例。滑過標記可對照批註。</p>
  </div>
</div></section>

<section class="sec" id="pipeline"><div class="wrap">
  <div class="ftab"><mark>FILE 02</mark><span>pipeline</span></div>
  <h2>四層分析，<span class="hl">逐層</span>交叉比對</h2>
  <div class="rows">
    <div class="row"><span class="n">1</span><h3>規則引擎</h3><p>已知釣魚樣式與關鍵字比對</p><span class="eg">例：<mark>立即</mark> <mark>24 小時內</mark></span></div>
    <div class="row"><span class="n">2</span><h3>ML 模型</h3><p>TF-IDF + Logistic Regression</p><span class="eg">例：整體用詞特徵</span></div>
    <div class="row"><span class="n">3</span><h3>URL / HTML 解析</h3><p>連結還原、追蹤像素、隱藏元素偵測</p><span class="eg">例：<mark>顯示文字</mark> ≠ 實際連結</span></div>
    <div class="row"><span class="n">4</span><h3>AI 語意判讀</h3><p>交叉比對郵件意圖與敏感資訊索取</p><span class="eg">例：<mark>索取密碼</mark></span></div>
  </div>
</div></section>

<section class="sec" id="metrics"><div class="wrap">
  <div class="ftab"><mark>FILE 03</mark><span>model report</span></div>
  <h2>ML 模型<span class="hl">測試結果</span></h2>
  <div class="tw"><table class="m">
    <thead><tr><th>項目</th><th>數值</th></tr></thead>
    <tbody>
    <tr><td>資料集</td><td>Phishing Email Dataset，清理後 82,077 筆（訓練 65,661 / 測試 16,416）</td></tr>
    <tr><td>Accuracy</td><td>98.41%</td></tr>
    <tr><td>Precision</td><td>98.28%</td></tr>
    <tr><td>Recall</td><td>98.68%</td></tr>
    <tr><td>F1</td><td>98.48%</td></tr>
    </tbody></table></div>
  <p class="note">以上僅為第 2 層 ML 模型在測試資料上的表現，不代表整體四層系統在真實信箱中的準確率。</p>
</div></section>

<section class="clear">
  <div class="l"><div class="stamp2" aria-hidden="true">已放行<small>CLEARED</small></div>
    <div class="ftab"><mark>FILE 04</mark><span>whitelist</span></div>
    <h2>白名單機制<span class="hl">已啟用</span></h2></div>
  <div class="r"><p class="mono" style="max-width:34ch;font-size:13px;line-height:1.8">已知安全網域自動略過重複分析。</p>
    <div class="acts">
      <a class="btn" href="/whitelist" data-key="w"><span>查看白名單</span><span class="key">W</span></a>
      <a class="btn" href="/rules" data-key="r"><span>偵測規則</span><span class="key">R</span></a>
    </div></div>
</section>
</main>
<footer class="f">
  <div class="big"><span>phishing</span>-detector</div>
  <nav><a href="/rules">偵測規則</a><a href="/whitelist">白名單</a><a href="/paste">貼上分析</a><a href="/login">Google 登入</a></nav>
</footer>
<script>
(function(){
  var marks=document.querySelectorAll('mark.m'),notes=document.querySelectorAll('.notes li');
  function set(n,on){notes.forEach(function(li){if(li.getAttribute('data-n')===n)li.classList.toggle('on',on);});}
  marks.forEach(function(m){var n=m.getAttribute('data-n');
    m.addEventListener('mouseenter',function(){set(n,true)});m.addEventListener('mouseleave',function(){set(n,false)});});
  notes.forEach(function(li){var n=li.getAttribute('data-n');
    li.addEventListener('mouseenter',function(){marks.forEach(function(m){if(m.getAttribute('data-n')===n)m.style.outline='2px solid #141414'});});
    li.addEventListener('mouseleave',function(){marks.forEach(function(m){m.style.outline='';});});});
})();
</script>
"""

# ── Loading HTML ─────────────────────────────────────────────
LOADING_HTML = COMMON_CSS + """
<style>
.big3 { font-family: var(--serif); font-weight: 900; font-size: 4.2rem; line-height: 1; margin-top: 1.5rem; }
.big3 small { font-family: var(--mono); font-size: 14px; font-weight: 400; color: #55524a; margin-left: .4rem; }
.el { margin-top: .5rem; font-family: var(--mono); font-size: 12px; color: #8a8678; }
.phase { list-style: none; margin: 1.6rem 0 0; padding: 0; font-family: var(--mono); font-size: 12.5px; }
.phase li { display: flex; gap: .7rem; padding: .5rem 0; border-top: 1px solid #dcd7ca; color: #8a8678; }
.phase li b { flex: none; display: grid; place-items: center; width: 1.3rem; height: 1.3rem; border-radius: 50%; border: 1px solid currentColor; font-size: 10px; }
.phase li.on { color: #141414; } .phase li.on span { background: var(--hl); }
.phase li.on b { background: #141414; color: #faf8f3; border-color: #141414; }
.phase li.dn { color: #141414; } .phase li.dn b { background: #2e6a4d; color: #fff; border-color: #2e6a4d; }
.tally { grid-template-columns: repeat(2, 1fr); }
.wall { display: grid; grid-template-columns: repeat(auto-fill, minmax(10rem, 1fr)); gap: 1rem; }
.slip { position: relative; min-height: 8.5rem; padding: .8rem .9rem; background: #fff; border: 1px dashed #a8a291; overflow: hidden; transition: border-color .2s; }
.slip .no { font-family: var(--mono); font-size: 11px; color: #8a8678; }
.slip .ln { display: block; height: .5rem; margin-top: .6rem; background: #ebe7dc; }
.slip .ln:nth-of-type(2) { width: 82%; } .slip .ln:nth-of-type(3) { width: 64%; }
.slip.now { border: 1px solid #141414; }
.slip.now::after { content: ""; position: absolute; left: -40%; top: 0; bottom: 0; width: 40%; background: linear-gradient(90deg, transparent, rgba(255,182,213,.85), transparent); animation: sweep 1.1s linear infinite; }
@keyframes sweep { to { left: 100%; } }
.slip.dn { border: 1px solid #141414; }
.slip .stp { position: absolute; right: .6rem; bottom: .7rem; padding: .02rem .55rem; border: 2px solid currentColor; font-family: var(--serif); font-weight: 900; font-size: 1rem; line-height: 1.4; transform: rotate(-6deg); mix-blend-mode: multiply; animation: stampin .4s cubic-bezier(.2,1.7,.4,1) both; }
.slip .stp.red { color: #c8321e; } .slip .stp.org { color: #a8650f; } .slip .stp.grn { color: #2e6a4d; } .slip .stp.ink { color: #55524a; }
@keyframes stampin { from { opacity: 0; transform: rotate(14deg) scale(2.2); } to { opacity: .95; transform: rotate(-6deg) scale(1); } }
.slip.empty { border-style: dotted; color: #8a8678; }
.note3 { margin-top: 1.4rem; font-family: var(--mono); font-size: 11.5px; line-height: 1.8; color: #8a8678; }
@media (prefers-reduced-motion: reduce) { .slip.now::after, .slip .stp { animation: none; } }
</style>
<div class="hdr"><div class="hdr-left"><a href="/">phishing-detector</a></div><div class="hdr-nav"><a href="/rules">偵測規則</a><a href="/whitelist">白名單</a><a href="/history">掃描記錄</a><a href="/paste">貼上分析</a></div></div>
<div class="dz">
  <aside class="dz-side">
    <div class="ftab"><mark>FILE</mark><span>scanning</span></div>
    <h1 class="pg-title"><span class="hl">正在掃描你的 Gmail</span></h1>
    <p class="pg-sub">唯讀授權，只讀取收件匣最新 15 封信。每檢驗完一封，右邊就蓋上一枚印章。</p>
    <div class="big3"><span id="cnt">0</span><small>/ <span id="tot">—</span> 封</small></div>
    <div class="el" id="el">已等待 0 秒</div>
    <ul class="phase" id="phase">
      <li data-p="1"><b>1</b><span>連線 Gmail，讀取最新信件</span></li>
      <li data-p="2"><b>2</b><span>逐封檢驗</span></li>
      <li data-p="3"><b>3</b><span>整理分析結果</span></li>
    </ul>
    <div class="nums tally">
      <div><b id="t-high" style="color:#c8321e">0</b><span>可疑</span></div>
      <div><b id="t-med" style="color:#a8650f">0</b><span>注意</span></div>
      <div><b id="t-low" style="color:#2e6a4d">0</b><span>安全</span></div>
      <div><b id="t-wl">0</b><span>白名單／略過</span></div>
    </div>
  </aside>
  <main class="dz-main">
    <div class="sh"><span class="n">01</span><h2>案件牆</h2><p>每一格是一封信。印章顏色是該封信的風險等級，進度來自後端實際完成的封數。</p></div>
    <div class="wall" id="wall"></div>
    <p class="note3" id="note3"></p>
  </main>
</div>
<script>
const LV = { high: ['可疑', 'red'], medium: ['注意', 'org'], low: ['安全', 'grn'], wl: ['放行', 'ink'], sk: ['略過', 'ink'] };
const started = Date.now();
let total = null, drawn = 0, fails = 0, finished = false;

function slipHtml(i) {
  return '<div class="slip empty" id="slip-' + i + '"><div class="no">' + String(i + 1).padStart(2, '0') + '</div><i class="ln"></i><i class="ln"></i><i class="ln"></i></div>';
}
function buildWall(n) {
  const wall = document.getElementById('wall');
  let h = ''; for (let i = 0; i < n; i++) h += slipHtml(i);
  wall.innerHTML = h; drawn = n;
}
function setPhase(p) {
  document.querySelectorAll('#phase li').forEach(function (li) {
    const n = Number(li.getAttribute('data-p'));
    li.className = n < p ? 'dn' : (n === p ? 'on' : '');
    li.querySelector('b').textContent = n < p ? '✓' : String(n);
  });
}
function paint(progress) {
  const t = { high: 0, medium: 0, low: 0, other: 0 };
  progress.forEach(function (lv, i) {
    const el = document.getElementById('slip-' + i); if (!el) return;
    if (!el.classList.contains('dn')) {
      const v = LV[lv] || ['—', 'ink'];
      el.className = 'slip dn';
      el.insertAdjacentHTML('beforeend', '<span class="stp ' + v[1] + '">' + v[0] + '</span>');
    }
    if (lv === 'high') t.high++; else if (lv === 'medium') t.medium++; else if (lv === 'low') t.low++; else t.other++;
  });
  const cur = document.getElementById('slip-' + progress.length);
  if (cur && !finished) cur.className = 'slip now';
  document.getElementById('cnt').textContent = progress.length;
  document.getElementById('t-high').textContent = t.high;
  document.getElementById('t-med').textContent = t.medium;
  document.getElementById('t-low').textContent = t.low;
  document.getElementById('t-wl').textContent = t.other;
}
function tick() {
  document.getElementById('el').textContent = '已等待 ' + Math.floor((Date.now() - started) / 1000) + ' 秒';
}
function poll() {
  fetch('/scan_status').then(function (r) { return r.json(); }).then(function (d) {
    fails = 0;
    if (d.total !== null && d.total !== undefined && total === null) {
      total = d.total; document.getElementById('tot').textContent = total;
      document.getElementById('note3').textContent = '全部檢驗完成後，會自動跳到分析結果。';
      if (total === 0) { document.getElementById('wall').innerHTML = '<p class="note3">收件匣沒有信件。</p>'; } else buildWall(total);
    }
    const prog = d.progress || [];
    if (total === null) setPhase(1);
    else if (prog.length < total) setPhase(2);
    else setPhase(3);
    if (total) paint(prog);
    if (d.done) {
      finished = true; setPhase(4);
      if (total) { document.querySelectorAll('.slip.now').forEach(function (e) { e.className = 'slip dn'; }); }
      setTimeout(function () { window.location.href = '/result/' + d.scan_id; }, 900);
      return;
    }
    setTimeout(poll, 700);
  }).catch(function () {
    fails++;
    if (fails > 15) { document.getElementById('note3').textContent = '與伺服器的連線中斷，請重新整理頁面。'; return; }
    setTimeout(poll, 1500);
  });
}
buildWall(15);
document.getElementById('note3').textContent = '正在連線 Gmail 並讀取信件，信件數量確定後，這裡會依實際封數更新。';
setInterval(tick, 1000);
poll();
</script>
"""

# ── 錯誤頁（授權失敗／分析失敗）──────────────────────────────
ERROR_HTML = COMMON_CSS + """
<style>
.ew { max-width: 56rem; padding: 3rem 2rem 2rem; }
.ew .stamp-lg { display: inline-block; border: 4px solid #c8321e; color: #c8321e; padding: .15rem 1rem .25rem; font-family: var(--serif); font-weight: 900; font-size: 2rem; line-height: 1.15; text-align: center; transform: rotate(-5deg); mix-blend-mode: multiply; }
.ew .stamp-lg small { display: block; font-family: var(--mono); font-size: .65rem; letter-spacing: .2em; }
.ew h1 { font-family: var(--serif); font-weight: 900; font-size: clamp(1.8rem, 3.4vw, 2.8rem); line-height: 1.3; margin: 1.6rem 0 .8rem; }
.ew p { font-size: 14.5px; line-height: 1.9; color: #55524a; max-width: 60ch; }
.ew details { margin-top: 1.6rem; border: 1px solid #141414; background: #fff; }
.ew summary { cursor: pointer; padding: .75rem 1rem; font-family: var(--mono); font-size: 12px; font-weight: 600; }
.ew pre { margin: 0; padding: .9rem 1rem 1.1rem; border-top: 1px dashed #a8a291; font-family: var(--mono); font-size: 12px; line-height: 1.7; white-space: pre-wrap; word-break: break-word; max-height: 22rem; overflow: auto; }
.ew .acts { margin-top: 1.8rem; display: flex; flex-wrap: wrap; gap: .6rem; }
.ew .acts a { display: inline-flex; padding: .65rem 1.1rem; border: 1px solid #141414; background: #141414; color: #faf8f3; font-family: var(--mono); font-size: 12.5px; text-decoration: none; }
.ew .acts a.o { background: transparent; color: #141414; }
.ew .acts a:hover { background: var(--hl); color: #141414; }
</style>
<div class="hdr"><div class="hdr-left"><a href="/">phishing-detector</a></div><div class="hdr-nav"><a href="/rules">偵測規則</a><a href="/whitelist">白名單</a><a href="/history">掃描記錄</a><a href="/paste">貼上分析</a></div></div>
<main class="ew">
  <div class="stamp-lg">失敗<small>FAILED</small></div>
  <h1>ERR_TITLE</h1>
  <p>ERR_MSG</p>
  ERR_DETAIL
  <div class="acts"><a href="/">返回首頁</a><a class="o" href="/paste">改用貼上分析</a></div>
</main>
"""

def render_error(title, message, detail=''):
    """統一風格的錯誤頁；title / message / detail 皆會做 HTML 跳脫。"""
    import html as html_lib
    box = ''
    if detail:
        box = ('<details><summary>技術細節</summary><pre>' + html_lib.escape(str(detail)) + '</pre></details>')
    out = ERROR_HTML.replace('ERR_TITLE', html_lib.escape(title)).replace('ERR_MSG', html_lib.escape(message))
    out = out.replace('ERR_DETAIL', box)
    return out


# ── 貼上郵件內容分析 HTML（免登入）───────────────────────────
PASTE_HTML = COMMON_CSS + """
<style>
.err-box { border: 1px solid #c8321e; background: #fff3f0; padding: .8rem 1rem; margin-bottom: 1.2rem; font-size: 13px; line-height: 1.7; }
.err-box pre { white-space: pre-wrap; font-size: 12px; }
.sample-form .sr { display: flex; gap: .5rem; margin-top: 1.4rem; }
.sample-select { flex: 1; min-width: 0; border: 1px solid #141414; background: #fff; padding: .55rem .6rem; font: 12.5px var(--mono); }
.sample-hint { margin-top: .6rem; font-family: var(--mono); font-size: 11px; color: #8a8678; line-height: 1.7; }
.mail { background: #fff; border: 1px solid #141414; }
.mrow { display: grid; grid-template-columns: 5.5rem minmax(0,1fr); align-items: center; border-bottom: 1px solid #dcd7ca; padding: 0 1.1rem; }
.mrow label { margin: 0; font-family: var(--mono); font-size: 11.5px; letter-spacing: .06em; color: #8a8678; }
.mrow input { width: 100%; border: 0; background: transparent; font: 500 14px var(--mono); padding: .85rem 0; box-shadow: none; }
.mrow input:focus { border: 0; box-shadow: none; }
.mrow:focus-within { background: #fffbe8; }
.ruled { display: block; width: 100%; min-height: 15rem; border: 0; padding: .25rem 1.1rem 1rem; font: 15px/2rem var(--sans); resize: vertical;
  background: repeating-linear-gradient(transparent 0 calc(2rem - 1px), #e8e3d6 calc(2rem - 1px) 2rem) local; background-position: 0 .25rem; box-shadow: none; }
.ruled:focus { border: 0; box-shadow: none; }
.att { margin-top: 1rem; border: 1px solid #141414; background: #fff; }
.att summary { cursor: pointer; padding: .75rem 1.1rem; font-family: var(--mono); font-size: 12px; font-weight: 600; }
.att .ab { padding: 0 1.1rem 1rem; }
.att textarea { width: 100%; min-height: 8rem; border: 1px solid #dcd7ca; background: #faf8f3; padding: .6rem .75rem; font: 12.5px/1.7 var(--mono); }
.att .fh { margin-top: .5rem; font-size: 12px; color: #8a8678; line-height: 1.7; }
.act { display: flex; flex-wrap: wrap; align-items: center; gap: .8rem 1.4rem; margin-top: 1.2rem; }
.act .submit-btn { padding: .8rem 1.6rem; font-size: 14px; }
.act span { font-family: var(--mono); font-size: 11.5px; color: #8a8678; }
.pv { margin-top: 2.2rem; border: 1px dashed #a8a291; background: #fff; padding: 1rem 1.2rem 1.1rem; }
.pv .lb { font-family: var(--mono); font-size: 11px; font-weight: 600; letter-spacing: .08em; text-transform: uppercase; display: flex; justify-content: space-between; gap: 1rem; }
.pv .lb em { font-style: normal; color: #8a8678; font-weight: 400; letter-spacing: 0; }
#pv { margin-top: .6rem; min-height: 3.5rem; font: 15px/2 var(--sans); white-space: pre-wrap; word-break: break-word; max-height: 16rem; overflow: auto; color: #8a8678; }
#pv.has { color: #141414; }
mark.m { position: relative; color: #141414; background: var(--hl); padding: .05em .12em; }
mark.m:not(.f)::after { display: none; }
mark.m::after { content: attr(data-n); position: relative; top: -.7em; margin-left: .15em; display: inline-grid; place-items: center; width: 1.25em; height: 1.25em; border-radius: 50%; background: #141414; color: #faf8f3; font: 600 10px/1 var(--mono); }
.pv .nt { margin-top: .6rem; font-family: var(--mono); font-size: 11px; color: #8a8678; line-height: 1.7; }
</style>
<script>
const RULE_KW = KEYWORDS_PLACEHOLDER;
const WORDS = (function () {
  const w = [];
  RULE_KW.forEach(function (g) { g[3].forEach(function (x) { w.push(String(x).toLowerCase()); }); });
  w.sort(function (a, b) { return b.length - a.length; });
  return w;
})();
function isSp(c) { const n = c.charCodeAt(0); return n <= 32 || n === 12288; }
function preview() {
  const t = document.getElementById('body-input').value, low = t.toLowerCase(), out = document.getElementById('pv'), st = document.getElementById('pv-stat');
  out.textContent = '';
  if (!t.trim()) { out.className = ''; out.textContent = '貼上內文後，這裡會即時標出命中的關鍵字與連結。'; st.textContent = ''; return; }
  out.className = 'has';
  let buf = '', i = 0, k, end, found, el, kw = 0, urls = 0;
  function flush() { if (buf) { out.appendChild(document.createTextNode(buf)); buf = ''; } }
  while (i < t.length) {
    if (low.startsWith('http://', i) || low.startsWith('https://', i)) {
      end = i; while (end < t.length && !isSp(t[end])) end++;
      flush(); el = document.createElement('mark'); el.className = urls ? 'm' : 'm f'; el.setAttribute('data-n', '3'); el.textContent = t.slice(i, end); out.appendChild(el); urls++; i = end; continue;
    }
    found = null;
    for (k = 0; k < WORDS.length; k++) { if (low.startsWith(WORDS[k], i)) { found = WORDS[k]; break; } }
    if (found) { flush(); el = document.createElement('mark'); el.className = kw ? 'm' : 'm f'; el.setAttribute('data-n', '1'); el.textContent = t.slice(i, i + found.length); out.appendChild(el); kw++; i += found.length; }
    else { buf += t[i]; i++; }
  }
  flush();
  st.textContent = '關鍵字 ' + kw + '・連結 ' + urls;
}
document.addEventListener('DOMContentLoaded', function () {
  const b = document.getElementById('body-input'), h = document.getElementById('html-input');
  b.addEventListener('input', preview); preview();
  if (h.value.trim()) document.getElementById('att').open = true;
});
</script>
<div class="hdr"><div class="hdr-left"><a href="/">phishing-detector</a></div><div class="hdr-nav"><a href="/rules">偵測規則</a><a href="/whitelist">白名單</a><a href="/history">掃描記錄</a><a href="/paste">貼上分析</a></div></div>
<div class="dz">
  <aside class="dz-side">
    <div class="ftab"><mark>FILE</mark><span>paste</span></div>
    <h1 class="pg-title"><span class="hl">貼上郵件內容進行分析</span></h1>
    <p class="pg-sub">不需要 Google 帳號授權，將郵件的寄件者、主旨與內文貼上即可，系統會以相同的三層式（規則引擎 + ML + HTML / URL + AI）架構進行分析。</p>
    <form method="GET" action="/paste" class="sample-form">
      <div class="lb" style="font-family:var(--mono);font-size:11px;font-weight:600;letter-spacing:.08em;margin-top:1.8rem">快速載入測試信件</div>
      <div class="sr">
        <select name="sample" class="sample-select">
          <option value="">請選擇測試範例</option>
          <option value="account" SELECT_ACCOUNT>帳戶停用釣魚信</option>
          <option value="prize" SELECT_PRIZE>中獎詐騙信</option>
          <option value="delivery" SELECT_DELIVERY>假物流通知</option>
          <option value="normal" SELECT_NORMAL>正常商業信件</option>
          <option value="wl_real" SELECT_WL_REAL>白名單演示 ①：google.com 官方寄件者（會被略過）</option>
          <option value="wl_fake" SELECT_WL_FAKE>白名單演示 ②：偽冒網域 google.com.verify-login.xyz（不會被略過）</option>
        </select>
        <button type="submit" class="sample-btn">載入範例</button>
      </div>
      <div class="sample-hint">選擇範例後按「載入範例」，系統會直接填入郵件欄位，不依賴 JavaScript。</div>
    </form>
  </aside>
  <main class="dz-main">
    ERROR_PLACEHOLDER
    <form method="POST" action="/paste_analyze">
      <div class="sh"><span class="n">01</span><h2>待檢驗郵件</h2></div>
      <div class="mail">
        <div class="mrow"><label for="sender-input">寄件者</label><input id="sender-input" type="text" name="sender" value="SAMPLE_SENDER" placeholder="選填，用於白名單比對，例如 service@example.com"></div>
        <div class="mrow"><label for="subject-input">主　旨</label><input id="subject-input" type="text" name="subject" value="SAMPLE_SUBJECT" placeholder="郵件主旨"></div>
        <textarea id="body-input" class="ruled" name="body" placeholder="貼上郵件的純文字內容（必填）..." required>SAMPLE_BODY</textarea>
      </div>
      <details class="att" id="att">
        <summary>附件：HTML 原始碼（選填，用於偵測像素追蹤／偽裝連結等）</summary>
        <div class="ab"><textarea id="html-input" name="html" placeholder="若有郵件的 HTML 原始碼，可貼於此處以啟用多模態偵測...">SAMPLE_HTML</textarea>
        <div class="fh">在大部分信箱可透過「顯示原始郵件 / 檢視原始碼」取得 HTML 內容。</div></div>
      </details>
      <div class="act"><button class="submit-btn" type="submit">開始分析</button><span>送出後會進行完整的四層分析</span></div>
    </form>
    <div class="pv">
      <div class="lb"><span>預檢標記（即時）</span><em id="pv-stat"></em></div>
      <div id="pv"></div>
      <div class="nt">這只是規則引擎關鍵字與連結的前端預覽，送出後才會進行完整的四層分析。</div>
    </div>
  </main>
</div>
"""

# ── 貼上分析測試範例（伺服器端載入，不依賴 JavaScript） ────────
SAMPLE_EMAILS = {
    'account': {'sender':'security@example-security.com','subject':'【緊急】您的帳戶即將被停用，請立即驗證','body':'親愛的使用者：\n\n我們偵測到您的帳戶有異常登入活動。若未在 24 小時內完成驗證，您的帳戶將被暫停。\n\n請立即登入以下連結：\nhttps://secure-account-verify.example.xyz/login\n\n請輸入您的帳號、密碼、信用卡資訊及簡訊驗證碼，以完成身分驗證。\n\n若未完成驗證，系統將自動限制您的帳戶。','html':'<a href="https://secure-account-verify.example.xyz/login">立即驗證帳戶</a><form><input type="password"></form>'},
    'prize': {'sender':'winner@reward-notice.example.xyz','subject':'🎉 恭喜您獲得限時獎金，請立即領取！','body':'恭喜您！您的電子郵件已被抽中獲得新台幣 50,000 元獎金。\n\n請於今日 23:59 前點擊下方連結完成領取，逾期資格將自動失效：\nhttps://claim-reward.example.xyz/prize\n\n為了確認身分，請提供姓名、身分資料及銀行帳戶資訊。','html':'<a href="https://claim-reward.example.xyz/prize">立即領取獎金</a>'},
    'delivery': {'sender':'delivery@shipping-update.example.xyz','subject':'【物流通知】您的包裹配送地址需要確認','body':'您好，您的包裹目前無法完成配送。\n\n請在 12 小時內確認配送地址，否則包裹將退回寄件地：\nhttps://delivery-check.example.xyz/verify\n\n請輸入收件資訊與信用卡資料以支付重新配送費用。','html':'<a href="https://delivery-check.example.xyz/verify">確認配送資訊</a><img src="https://delivery-check.example.xyz/p.gif" width="1" height="1">'},
    'wl_real': {'sender':'Google <no-reply@accounts.google.com>','subject':'【緊急】請立即驗證您的帳戶密碼','body':'您好：\n\n我們偵測到新的登入活動，請立即確認是否為本人操作。\n\n如非本人，請前往 https://accounts.google.com/security 重設密碼並檢查帳戶。','html':''},
    'wl_fake': {'sender':'Google <no-reply@accounts.google.com.verify-login.xyz>','subject':'【緊急】請立即驗證您的帳戶密碼','body':'您好：\n\n我們偵測到新的登入活動，請立即確認是否為本人操作。\n\n如非本人，請前往 https://accounts.google.com.verify-login.xyz/security 重設密碼並檢查帳戶。','html':'<a href="https://accounts.google.com.verify-login.xyz/security">立即驗證</a><form><input type="password"></form>'},
    'normal': {'sender':'service@company.example.com','subject':'本月電子帳單與服務通知','body':'您好，您的本月服務帳單已產生。\n\n您可以登入官方網站查看帳單與使用明細。若您近期沒有使用相關服務，請透過官方客服管道聯繫我們。\n\n謝謝您的使用。','html':'<p>您好，您的本月服務帳單已產生。</p>'}
}

def _kw_json():
    """規則關鍵字清單（供前端預檢／原信批註比對用，已做 script 安全跳脫）。"""
    return json.dumps(RULE_KEYWORD_GROUPS, ensure_ascii=False).replace(
        '<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')

def render_paste_page(sample_key='', error=''):
    import html as html_lib
    sample = SAMPLE_EMAILS.get(sample_key, {'sender':'','subject':'','body':'','html':''})
    out = PASTE_HTML.replace('KEYWORDS_PLACEHOLDER', _kw_json())
    out = out.replace('ERROR_PLACEHOLDER', error)
    out = out.replace('SAMPLE_SENDER', html_lib.escape(sample['sender'], quote=True))
    out = out.replace('SAMPLE_SUBJECT', html_lib.escape(sample['subject'], quote=True))
    out = out.replace('SAMPLE_BODY', html_lib.escape(sample['body']))
    out = out.replace('SAMPLE_HTML', html_lib.escape(sample['html']))
    for key in SAMPLE_EMAILS:
        out = out.replace(f'SELECT_{key.upper()}', 'selected' if key == sample_key else '')
    return out

# ── 結果頁 HTML (修正點擊與高亮同步邏輯) ─────────────────────
RESULT_HTML = COMMON_CSS + """
<style>
.dz-side .nums { grid-template-columns: repeat(3, 1fr); }
.dz-side .nums b { font-size: 1.6rem; }
.dz-side .nums span { font-size: 10.5px; }
.ov { margin-top: 1.1rem; }
.lb { font-family: var(--mono); font-size: 11px; font-weight: 600; letter-spacing: .08em; text-transform: uppercase; margin-bottom: .45rem; }
.risk-track { display: flex; height: .9rem; border: 1px solid #141414; background: #fff; }
.risk-track div { height: 100%; }
.risk-seg-high { background: #c8321e; } .risk-seg-med { background: #e39a2d; } .risk-seg-low { background: #2e6a4d; } .risk-seg-wl { background: #b8b3a4; }
.overview-meta { display: flex; justify-content: space-between; font-family: var(--mono); font-size: 11px; color: #8a8678; margin-top: .35rem; }
.lst { margin-top: 1.4rem; }
.list-sec { display: inline-block; margin: 1rem 0 .4rem; padding: 0 .45rem; background: var(--hl); font-family: var(--mono); font-size: 11px; font-weight: 600; letter-spacing: .08em; }
.email-item { display: flex; gap: .65rem; padding: .7rem; border-top: 1px solid #dcd7ca; border-left: 4px solid transparent; cursor: pointer; }
.email-item:hover { background: #ebe7dc; }
.email-item.active { background: #fff; border-left-color: #141414; box-shadow: inset 0 0 0 1px #141414; }
.risk-dot { flex: none; width: .7rem; height: .7rem; margin-top: .4rem; border: 1px solid #141414; }
.dot-high { background: #c8321e; } .dot-med { background: #e39a2d; } .dot-low { background: #2e6a4d; } .dot-wl { background: #b8b3a4; }
.item-body { min-width: 0; }
.item-subj { font-weight: 700; font-size: 13.5px; line-height: 1.45; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.item-from { font-family: var(--mono); font-size: 11px; color: #8a8678; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.item-score { font-family: var(--mono); font-size: 11.5px; margin-top: .15rem; }
.item-reason { font-size: 12px; color: #55524a; margin-top: .2rem; line-height: 1.5; }
.solo #listwrap { display: none; }
/* 結論 */
.vd { display: grid; gap: 1.4rem; align-items: start; }
@media (min-width: 900px) { .vd { grid-template-columns: minmax(0,1fr) auto; } }
.vd-subj { font-family: var(--serif); font-weight: 900; font-size: clamp(1.6rem,2.6vw,2.4rem); line-height: 1.3; margin: .2rem 0 .5rem; word-break: break-word; }
.vd-from { font-family: var(--mono); font-size: 12.5px; color: #55524a; word-break: break-all; }
.tg { display: flex; flex-wrap: wrap; gap: .35rem; margin-top: .9rem; }
.tg span { background: var(--hl); font-family: var(--mono); font-size: 11.5px; padding: 0 .4rem; }
.vd-r { display: flex; flex-direction: column; align-items: flex-end; gap: 1rem; padding-right: .6rem; }
.stamp-lg { border: 4px solid currentColor; padding: .15rem 1rem .25rem; font-family: var(--serif); font-weight: 900; font-size: 2.4rem; line-height: 1.15; text-align: center; transform: rotate(-6deg); mix-blend-mode: multiply; animation: stampin .45s cubic-bezier(.2,1.7,.4,1) both; }
.stamp-lg small { display: block; font-family: var(--mono); font-size: .7rem; letter-spacing: .2em; font-weight: 600; }
.stamp-lg.red { color: #c8321e; } .stamp-lg.org { color: #a8650f; } .stamp-lg.grn { color: #2e6a4d; } .stamp-lg.ink { color: #141414; }
@keyframes stampin { from { opacity: 0; transform: rotate(14deg) scale(2.2); } to { opacity: .95; transform: rotate(-6deg) scale(1); } }
.vscore { font-family: var(--serif); font-weight: 900; font-size: 3.4rem; line-height: 1; }
.vscore small { font-family: var(--mono); font-size: 13px; font-weight: 400; color: #55524a; margin-left: .3rem; }
.gauge { position: relative; margin: 1.8rem 0 .3rem; padding-top: 1.7rem; }
.gscale { display: flex; height: .9rem; border: 1px solid #141414; }
.gscale i { display: block; } .gscale .lo { flex: 40; background: #2e6a4d; } .gscale .md { flex: 30; background: #e39a2d; } .gscale .hi { flex: 30; background: #c8321e; }
.pin { position: absolute; top: 0; transform: translateX(-50%); font-family: var(--mono); font-weight: 600; font-size: 12px; background: #141414; color: #faf8f3; padding: 0 .4rem; }
.pin::after { content: ""; position: absolute; left: 50%; bottom: -7px; transform: translateX(-50%); border: 4px solid transparent; border-top-color: #141414; }
.gt { position: relative; height: 1rem; font-family: var(--mono); font-size: 11px; color: #8a8678; margin-top: .25rem; }
.gt span { position: absolute; transform: translateX(-50%); }
/* 原信批註 */
.mdoc { background: #fff; border: 1px solid #141414; padding: 1.2rem 1.4rem; }
.mdoc dl { margin: 0 0 .9rem; padding-bottom: .8rem; border-bottom: 1px solid #dcd7ca; font-family: var(--mono); font-size: 12.5px; line-height: 1.9; }
.mdoc dl div { display: grid; grid-template-columns: 4.2em 1fr; gap: .5rem; }
.mdoc dt { color: #8a8678; font-size: 11.5px; letter-spacing: .06em; }
.mdoc dd { margin: 0; word-break: break-all; }
.mbody { font-size: 15px; line-height: 2.05; white-space: pre-wrap; word-break: break-word; max-height: 24rem; overflow: auto; }
mark.m { position: relative; color: #141414; background: linear-gradient(var(--hl), var(--hl)) no-repeat; background-size: 100% 100%; padding: .05em .12em; animation: draw .5s cubic-bezier(.3,.7,.3,1) both; animation-delay: calc(var(--i, 0) * .07s + .2s); }
mark.m:not(.f)::after { display: none; }
mark.m::after { content: attr(data-n); position: relative; top: -.7em; margin-left: .15em; display: inline-grid; place-items: center; width: 1.25em; height: 1.25em; border-radius: 50%; background: #141414; color: #faf8f3; font: 600 10px/1 var(--mono); }
@keyframes draw { from { background-size: 0% 100%; } to { background-size: 100% 100%; } }
.notes { margin: 1rem 0 0; padding: .9rem 0 0; border-top: 1px dashed #a8a291; list-style: none; font-size: 13px; line-height: 1.7; color: #55524a; }
.notes li { display: flex; gap: .65rem; padding: .15rem 0; }
.notes li b { flex: none; display: grid; place-items: center; width: 1.25rem; height: 1.25rem; margin-top: .22rem; border-radius: 50%; background: #141414; color: #faf8f3; font: 600 10px/1 var(--mono); }
.notes li.on { color: #141414; } .notes li.on span { background: var(--hl); }
.cap2 { margin-top: .7rem; font-family: var(--mono); font-size: 11.5px; color: #8a8678; line-height: 1.7; }
/* 四層 */
.lgrid { display: grid; grid-template-columns: repeat(auto-fit, minmax(13rem, 1fr)); gap: 1rem; }
.lc { background: #fff; border: 1px solid #141414; padding: .9rem 1rem 1rem; display: flex; flex-direction: column; gap: .5rem; }
.ln { display: flex; align-items: center; gap: .55rem; font-family: var(--mono); font-size: 12px; font-weight: 600; }
.ln b { display: grid; place-items: center; width: 1.3rem; height: 1.3rem; border-radius: 50%; background: #141414; color: #faf8f3; font-size: 10px; }
.lsc { font-family: var(--serif); font-weight: 900; font-size: 2.2rem; line-height: 1; }
.lsc small { font-family: var(--mono); font-size: 12px; font-weight: 400; color: #55524a; margin-left: .25rem; }
.ls { font-size: 13px; line-height: 1.7; color: #55524a; }
.bar { height: .6rem; border: 1px solid #141414; background: #faf8f3; }
.bar-fill { height: 100%; background: #141414; }
.lm { display: flex; justify-content: space-between; gap: .6rem; font-family: var(--mono); font-size: 11px; color: #8a8678; }
.fnote { margin-top: .9rem; font-family: var(--mono); font-size: 12px; line-height: 1.8; color: #55524a; }
.bk { display: flex; border: 1px solid #141414; height: 2.3rem; font-family: var(--mono); font-size: 11.5px; margin-top: 1.1rem; background: #fff; }
.bk i { font-style: normal; display: flex; align-items: center; padding: 0 .55rem; overflow: hidden; white-space: nowrap; border-right: 1px solid #141414; }
.bk i:last-child { border-right: 0; }
.bk .c0 { background: #141414; color: #faf8f3; } .bk .c1 { background: #55524a; color: #faf8f3; } .bk .c2 { background: var(--hl); } .bk .c3 { background: #ffe0ee; }
.brow { display: flex; justify-content: space-between; gap: 1rem; padding: .45rem 0; border-bottom: 1px dashed #a8a291; font-family: var(--mono); font-size: 12.5px; }
.btot { margin-top: .8rem; font-family: var(--mono); font-size: 13px; font-weight: 600; }
/* 為什麼／證據／處置 */
.why { list-style: none; margin: 0; padding: 0; }
.why li { display: grid; grid-template-columns: 5.2rem minmax(0,1fr); gap: 1rem; padding: 1rem 0; border-top: 1px solid #dcd7ca; }
.why li:last-child { border-bottom: 1px solid #dcd7ca; }
.why .src { font-family: var(--mono); font-size: 11px; color: #8a8678; }
.why .hd { font-weight: 700; margin: .1rem 0 .2rem; }
.why .dt { font-size: 13.5px; line-height: 1.8; color: #55524a; }
.ev { border: 1px solid #141414; background: #fff; margin-top: .7rem; }
.ev summary { cursor: pointer; padding: .7rem 1rem; font-family: var(--mono); font-size: 12px; font-weight: 600; }
.ev div.it { padding: .5rem 1rem; border-top: 1px dashed #a8a291; font-size: 13px; line-height: 1.7; color: #55524a; word-break: break-word; }
.rec { border-left: 6px solid #141414; background: #fff; padding: 1rem 1.2rem; font-family: var(--serif); font-weight: 700; font-size: 1.15rem; line-height: 1.75; }
.chk { margin-top: 1.2rem; }
.chk label { display: flex; gap: .75rem; padding: .6rem 0; border-top: 1px dashed #a8a291; cursor: pointer; font-size: 14px; line-height: 1.7; }
.chk input { flex: none; width: 1.1rem; height: 1.1rem; margin-top: .25rem; accent-color: #141414; }
.chk input:checked + span { text-decoration: line-through; color: #8a8678; }
/* IR 報告單 */
.ir { background: #fff; border: 1px solid #141414; }
.irh { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: .6rem 1rem; padding: .8rem 1.1rem; background: #141414; color: #faf8f3; font-family: var(--mono); font-size: 12px; }
.irh .st { color: #faf8f3; border-color: #faf8f3; mix-blend-mode: normal; transform: rotate(-3deg); }
.irc { padding: 1.1rem 1.1rem 1.2rem; }
.irc p { font-size: 14px; line-height: 1.8; color: #333; }
.irc ul { margin: .6rem 0 0 1.2rem; font-size: 13.5px; line-height: 1.8; }
.irmeta { display: flex; flex-wrap: wrap; gap: .4rem 2rem; margin-top: 1rem; font-family: var(--mono); font-size: 11.5px; color: #55524a; }
.ir3 { display: grid; gap: 1px; background: #141414; border-top: 1px solid #141414; }
@media (min-width: 900px) { .ir3 { grid-template-columns: repeat(3, 1fr); } }
.ir3 div { background: #fff; padding: .9rem 1.1rem 1.1rem; }
.ir3 b { display: block; font-family: var(--mono); font-size: 11px; letter-spacing: .08em; text-transform: uppercase; margin-bottom: .4rem; }
.ir3 p { font-size: 13px; line-height: 1.75; color: #333; }
.irn { padding: .9rem 1.1rem; border-top: 1px solid #141414; font-size: 12.5px; line-height: 1.8; color: #55524a; background: #faf8f3; }
.irdl { display: flex; flex-wrap: wrap; gap: .6rem; padding: .9rem 1.1rem 1.1rem; border-top: 1px solid #141414; }
@media (prefers-reduced-motion: reduce) { mark.m, .stamp-lg { animation: none; } }
</style>
<script>
const emailData = PLACEHOLDER_DATA;
const RULE_KW = KEYWORDS_PLACEHOLDER;

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, c => ({
    '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'
  }[c]));
}


function downloadIR(idx, fmt) {
  const d = emailData[idx];
  if (!d || !d.ir) return;
  const ir = d.ir;
  const actions = (ir.actions_full && ir.actions_full.length ? ir.actions_full : ir.actions) || [];
  const findings = (d.explainable_findings || []).map(x => `- [${x.source || ''}] ${x.title || ''}：${x.detail || ''}`);
  let content, mime;
  if (fmt === 'json') {
    content = JSON.stringify({
      incident_id: ir.id, status: ir.status, severity: ir.severity, risk_score: ir.risk_score,
      created_at: ir.created_at, email_sender: ir.email_sender || d.sender, email_subject: ir.email_subject || d.subject,
      impact_assessment: ir.impact_full || ir.impact, immediate_actions: actions,
      containment: ir.containment, verification: ir.verification, recovery: ir.recovery,
      explainable_findings: d.explainable_findings || []
    }, null, 2);
    mime = 'application/json;charset=utf-8';
  } else {
    content = [
      '資安事件回應報告 (Incident Response Report)',
      '==========================================',
      `事件編號：${ir.id}`,
      `事件狀態：${ir.status || 'Open'}（Open = 已建立、尚待處理）`,
      `嚴重等級：${ir.severity}`,
      `風險分數：${ir.risk_score} / 100`,
      `建立時間：${ir.created_at}`,
      `寄件者：${ir.email_sender || d.sender}`,
      `主旨：${ir.email_subject || d.subject}`,
      '',
      '【影響評估】', ir.impact_full || ir.impact || '—',
      '',
      '【立即行動】', ...(actions.length ? actions.map((a, i) => `${i + 1}. ${a}`) : ['—']),
      '',
      '【隔離 Containment】', ir.containment || '—',
      '',
      '【驗證 Verification】', ir.verification || '—',
      '',
      '【復原 Recovery】', ir.recovery || '—',
      '',
      '【偵測依據】', ...(findings.length ? findings : ['—']),
      '',
      '※ 本報告由 phishing-detector 自動產生，僅供輔助參考，實際處置請依組織資安流程。'
    ].join('\\r\\n');
    mime = 'text/plain;charset=utf-8';
  }
  const blob = new Blob(['\\ufeff' + content], {type: mime});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `${ir.id}.${fmt}`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 1000);
}


const WORDS = (function () {
  const w = [];
  RULE_KW.forEach(function (g) { g[3].forEach(function (x) { w.push(String(x).toLowerCase()); }); });
  w.sort(function (a, b) { return b.length - a.length; });
  return w;
})();
function isSp(c) { const n = c.charCodeAt(0); return n <= 32 || n === 12288; }
let seenN = {};
function markup(text) {
  const low = text.toLowerCase();
  let out = '', buf = '', i = 0, k, end, found, cnt = { kw: 0, url: 0 }, seq = 0;
  function flush() { if (buf) { out += escapeHtml(buf); buf = ''; } }
  while (i < text.length) {
    if (low.startsWith('http://', i) || low.startsWith('https://', i)) {
      end = i; while (end < text.length && !isSp(text[end])) end++;
      flush(); out += '<mark class="m' + (seenN[3] ? '' : ' f') + '" data-n="3" style="--i:' + Math.min(seq++, 14) + '">' + escapeHtml(text.slice(i, end)) + '</mark>';
      seenN[3] = 1; cnt.url++; i = end; continue;
    }
    found = null;
    for (k = 0; k < WORDS.length; k++) { if (low.startsWith(WORDS[k], i)) { found = WORDS[k]; break; } }
    if (found) {
      flush(); out += '<mark class="m' + (seenN[1] ? '' : ' f') + '" data-n="1" style="--i:' + Math.min(seq++, 14) + '">' + escapeHtml(text.slice(i, i + found.length)) + '</mark>';
      seenN[1] = 1; cnt.kw++; i += found.length;
    } else { buf += text[i]; i++; }
  }
  flush();
  return { html: out, cnt: cnt };
}

function showDetail(idx, element) {
  const d = emailData[idx];
  if (!d) return;
  document.querySelectorAll('.email-item').forEach(function (el) { el.classList.remove('active'); });
  if (element) element.classList.add('active');
  else { const t = document.querySelector('.email-item[data-idx="' + idx + '"]'); if (t) t.classList.add('active'); }

  const panel = document.getElementById('right-panel');
  seenN = {};
  const lv = d.level;
  const V = { high: ['可疑', 'SUSPICIOUS', 'red'], medium: ['注意', 'CAUTION', 'org'], low: ['安全', 'SAFE', 'grn'], wl: ['白名單', 'CLEARED', 'grn'] }[lv] || ['—', '', 'ink'];
  const score = d.risk_score >= 0 ? Number(d.risk_score) : null;
  const layers = d.layers || {};
  const order = ['rule', 'ml', 'html', 'llm'];
  let sec = 0;
  const H = function (t, p) { sec++; return '<div class="sh"><span class="n">' + String(sec).padStart(2, '0') + '</span><h2>' + t + '</h2>' + (p ? '<p>' + p + '</p>' : '') + '</div>'; };

  let html = '';
  /* 1 結論 */
  html += '<div class="vd"><div><div class="ftab"><mark>CASE</mark><span>' + (idx + 1) + ' / ' + emailData.length + '</span></div>' +
    '<h1 class="vd-subj">' + escapeHtml(d.subject) + '</h1><div class="vd-from">來自：' + escapeHtml(d.sender) + '</div>' +
    (d.tags && d.tags.length ? '<div class="tg">' + d.tags.map(function (t) { return '<span>' + escapeHtml(t) + '</span>'; }).join('') + '</div>' : '') +
    '</div><div class="vd-r"><div class="stamp-lg ' + V[2] + '">' + V[0] + '<small>' + V[1] + '</small></div>' +
    (score !== null ? '<div class="vscore">' + score + '<small>/ 100</small></div>' : '') + '</div></div>';
  if (score !== null) {
    const pos = Math.max(3, Math.min(97, score));
    html += '<div class="gauge"><div class="gscale"><i class="lo"></i><i class="md"></i><i class="hi"></i></div>' +
      '<div class="pin" style="left:' + pos + '%">' + score + '</div></div>' +
      '<div class="gt"><span style="left:0">0</span><span style="left:40%">40</span><span style="left:70%">70</span><span style="left:100%">100</span></div>';
  }
  html += '<div class="sh" style="margin-top:2.2rem;display:none"></div>';

  /* 2 原信批註 */
  let hasDoc = false;
  if (d.body) {
    hasDoc = true;
    const sub = markup(d.subject || ''), bd = markup(d.body);
    const kwN = sub.cnt.kw + bd.cnt.kw, urlN = sub.cnt.url + bd.cnt.url;
    let notes = '';
    order.forEach(function (key, n) {
      const x = layers[key]; if (!x) return;
      const where = (key === 'rule' && kwN) ? '（信中標出 ' + kwN + ' 處）' : (key === 'html' && urlN) ? '（信中標出 ' + urlN + ' 個連結）' : '';
      const line = x.status || ((x.findings && x.findings[0]) || '—');
      notes += '<li data-n="' + (n + 1) + '"><b>' + (n + 1) + '</b><span>' + escapeHtml(x.name) + '：' + escapeHtml(String(line)) + where + '</span></li>';
    });
    html += H('原信批註', '標記為規則引擎關鍵字與連結的比對結果；ML 與 AI 針對整封信判斷，無法標示在單一詞上。') +
      '<article class="mdoc"><dl><div><dt>寄件者</dt><dd>' + escapeHtml(d.sender) + '</dd></div><div><dt>主　旨</dt><dd>' + sub.html + '</dd></div></dl>' +
      '<div class="mbody">' + bd.html + '</div>' + (notes ? '<ul class="notes">' + notes + '</ul>' : '') + '</article>';
  }

  /* 3 四層分析 */
  let layerHtml = '';
  order.forEach(function (key, n) {
    const x = layers[key]; if (!x) return;
    const sc = x.score == null ? 0 : Math.max(0, Math.min(100, Number(x.score)));
    const scT = x.score == null ? '—' : Number(x.score).toFixed(0);
    const meta = key === 'ml' && x.probability != null ? '釣魚機率 ' + Number(x.probability).toFixed(1) + '%' : '融合權重 ' + Number(x.weight || 0).toFixed(1) + '%';
    layerHtml += '<div class="lc"><div class="ln"><b>' + (n + 1) + '</b>' + escapeHtml(x.name) + '</div>' +
      '<div class="lsc">' + scT + '<small>/ 100</small></div><div class="bar"><div class="bar-fill" style="width:' + sc + '%"></div></div>' +
      '<div class="ls">' + escapeHtml(x.status || '—') + '</div>' +
      '<div class="lm"><span>' + escapeHtml(meta) + '</span><span>' + (key === 'llm' && x.score == null ? '未提供分數' : '分析完成') + '</span></div></div>';
  });
  if (layerHtml) {
    html += H('四層檢驗', '四層各自獨立打分，再依固定權重融合成最終分數。') + '<div class="lgrid">' + layerHtml + '</div>';
    if (d.fusion_formula) html += '<div class="fnote">風險融合公式：' + escapeHtml(d.fusion_formula) + '。最終分數由系統固定公式計算，不直接採用單一模型結果。</div>';
    if (d.risk_breakdown && d.risk_breakdown.components) {
      const comps = d.risk_breakdown.components, tot = comps.reduce(function (a, c) { return a + Math.max(0, c.contribution); }, 0) || 1;
      html += '<div class="bk">' + comps.map(function (c, i) {
        return '<i class="c' + (i % 4) + '" style="flex:' + Math.max(0.0001, c.contribution) + '" title="' + escapeHtml(c.name) + '">' + (c.contribution / tot > 0.12 ? escapeHtml(c.name) : '') + '</i>';
      }).join('') + '</div>' +
        comps.map(function (c) { return '<div class="brow"><span>' + escapeHtml(c.name) + '</span><span>' + c.score.toFixed(1) + ' × ' + c.weight + '% = ' + c.contribution.toFixed(1) + '</span></div>'; }).join('') +
        '<div class="btot">公式計算值：' + d.risk_breakdown.raw_total.toFixed(1) + ' → 最終 ' + d.risk_breakdown.rounded_final + ' / 100</div>';
    }
  }

  /* 4 AI 說明與依據 */
  const ex = d.explainable_findings || [];
  html += H('AI 分析說明') + '<p style="font-size:14.5px;line-height:1.9;color:#333;max-width:70ch">' + escapeHtml(d.explanation || '—') + '</p>';
  if (ex.length) {
    html += H('為什麼會被判定為可疑？') + '<ul class="why">' + ex.map(function (x) {
      const cls = x.severity === 'high' ? 'red' : x.severity === 'low' ? 'grn' : 'org';
      const lab = x.severity === 'high' ? '高風險' : x.severity === 'low' ? '低風險' : '注意';
      return '<li><div><span class="st ' + cls + '">' + lab + '</span></div><div><div class="src">' + escapeHtml(x.source || '') + '</div><div class="hd">' + escapeHtml(x.title || '') + '</div><div class="dt">' + escapeHtml(x.detail || '') + '</div></div></li>';
    }).join('') + '</ul>';
  }
  let evHtml = '';
  order.forEach(function (key) {
    const x = layers[key]; if (!x || !x.findings || !x.findings.length) return;
    evHtml += '<details class="ev"><summary>' + escapeHtml(x.name) + ' — 偵測證據（' + x.findings.length + '）</summary>' +
      x.findings.slice(0, 6).map(function (v) { return '<div class="it">' + escapeHtml(v) + '</div>'; }).join('') + '</details>';
  });
  if (evHtml) html += H('各層偵測證據') + evHtml;

  /* 5 處置 */
  html += H('建議行動') + '<div class="rec">' + escapeHtml(d.action || '—') + '</div>';
  const sa = d.safety_actions || [];
  if (sa.length) html += '<div class="chk">' + sa.map(function (x) { return '<label><input type="checkbox"><span>' + escapeHtml(x) + '</span></label>'; }).join('') + '</div>';

  /* 6 IR 報告單 */
  if (d.ir) {
    const ir = d.ir;
    html += H('IR 事件報告單', '系統已自動產生事件報告。') + '<div class="ir"><div class="irh"><span>' + escapeHtml(ir.id) + '　|　嚴重等級：' + escapeHtml(ir.severity) +
      '</span><span class="st ink">' + escapeHtml(ir.status || 'Open') + '</span></div><div class="irc"><p>' + escapeHtml(ir.impact) + '</p>' +
      (ir.actions && ir.actions.length ? '<ul>' + ir.actions.map(function (a) { return '<li>' + escapeHtml(a) + '</li>'; }).join('') + '</ul>' : '') +
      '<div class="irmeta"><span>Risk ' + escapeHtml(String(ir.risk_score == null ? '—' : ir.risk_score)) + '/100</span><span>Created ' + escapeHtml(ir.created_at || '—') + '</span></div></div>' +
      '<div class="ir3"><div><b>隔離 Containment</b><p>' + escapeHtml(ir.containment || '—') + '</p></div><div><b>驗證 Verification</b><p>' + escapeHtml(ir.verification || '—') + '</p></div><div><b>復原 Recovery</b><p>' + escapeHtml(ir.recovery || '—') + '</p></div></div>' +
      '<div class="irn">Status = Open 代表此事件<b>已建立、尚待人員處理</b>；本系統只負責產生處置建議，不會自動通知他人或關閉事件，處理完成後由資安人員自行結案（Closed）。</div>' +
      '<div class="irdl"><button class="ir-dl-btn" onclick="downloadIR(' + idx + ',&quot;txt&quot;)">下載 IR 報告 (.txt)</button><button class="ir-dl-btn" onclick="downloadIR(' + idx + ',&quot;json&quot;)">下載 (.json)</button></div></div>';
  }

  panel.innerHTML = html.replace('<div class="sh" style="margin-top:2.2rem;display:none"></div>', '');
  /* 標記與批註互相連動 */
  const marks = panel.querySelectorAll('mark.m'), notes = panel.querySelectorAll('.notes li');
  function tog(n, on) { notes.forEach(function (li) { if (li.getAttribute('data-n') === n) li.classList.toggle('on', on); }); }
  marks.forEach(function (m) { const n = m.getAttribute('data-n'); m.addEventListener('mouseenter', function () { tog(n, true); }); m.addEventListener('mouseleave', function () { tog(n, false); }); });
  notes.forEach(function (li) { const n = li.getAttribute('data-n');
    li.addEventListener('mouseenter', function () { marks.forEach(function (m) { if (m.getAttribute('data-n') === n) m.style.outline = '2px solid #141414'; }); });
    li.addEventListener('mouseleave', function () { marks.forEach(function (m) { m.style.outline = ''; }); }); });
  window.scrollTo(0, 0);
}

window.addEventListener('DOMContentLoaded', function () {
  if (Array.isArray(emailData) && emailData.length > 0) {
    if (emailData.length === 1) document.querySelector('.dz').classList.add('solo');
    showDetail(0);
  }
});
</script>
<div class="hdr"><div class="hdr-left"><a href="/">phishing-detector</a></div><div class="hdr-nav"><a href="/rules">偵測規則</a><a href="/whitelist">白名單</a><a href="/history">掃描記錄</a><a href="/paste">貼上分析</a></div></div>
<div class="dz">
  <aside class="dz-side">
    <div class="ftab"><mark>FILE</mark><span>result</span></div>
    <h1 class="pg-title"><span class="hl">分析結果</span></h1>
    <div class="nums">
      <div><b>TOTAL_COUNT</b><span>掃描封數</span></div>
      <div><b style="color:#c8321e">HIGH_COUNT</b><span>高風險</span></div>
      <div><b style="color:#a8650f">MED_COUNT</b><span>中風險</span></div>
      <div><b style="color:#2e6a4d">LOW_COUNT</b><span>安全</span></div>
      <div><b>WL_COUNT</b><span>白名單</span></div>
      <div><b>SK_COUNT</b><span>略過</span></div>
    </div>
    <div class="ov">
      <div class="lb">風險分布</div>
      <div class="risk-track" title="高風險 / 中風險 / 安全 / 白名單">
        <div class="risk-seg-high" style="width:HIGH_PCT%"></div>
        <div class="risk-seg-med" style="width:MED_PCT%"></div>
        <div class="risk-seg-low" style="width:LOW_PCT%"></div>
        <div class="risk-seg-wl" style="width:WL_PCT%"></div>
      </div>
      <div class="overview-meta"><span>已分析：ANALYZED_COUNT 封</span><span>高風險優先顯示</span></div>
    </div>
    <div class="lst" id="listwrap">
      <div class="lb">案件清單</div>
      <div id="left-panel">LIST_PLACEHOLDER</div>
    </div>
  </aside>
  <main class="dz-main"><div id="right-panel"></div></main>
</div>
"""

# ── 歷史記錄 HTML ────────────────────────────────────────────
HISTORY_HTML = COMMON_CSS + """
<style>
.leg { display: flex; flex-wrap: wrap; gap: .5rem 1.4rem; font-family: var(--mono); font-size: 12px; margin-bottom: 1rem; }
.dot { display: inline-block; width: .8rem; height: .8rem; margin-right: .4rem; border: 1px solid #141414; vertical-align: -1px; }
.dot.h, .bar3 .h { background: #c8321e; } .dot.m, .bar3 .m { background: #e39a2d; } .dot.l, .bar3 .l { background: #2e6a4d; } .dot.w, .bar3 .w { background: #b8b3a4; }
.led { border-top: 1px solid #141414; }
.lr { display: grid; grid-template-columns: 1fr; gap: .7rem; padding: 1.1rem 0; border-bottom: 1px solid #dcd7ca; align-items: center; }
@media (min-width: 900px) { .lr { grid-template-columns: 9.5rem minmax(0,1fr) 14rem; gap: 1.5rem; padding-right: .6rem; } }
.lr .tm b { display: block; font-family: var(--serif); font-weight: 900; font-size: 1.35rem; line-height: 1.2; }
.lr .tm span { font-family: var(--mono); font-size: 11.5px; color: #8a8678; }
.bar3 { display: flex; height: 1.7rem; border: 1px solid #141414; background: repeating-linear-gradient(135deg, #faf8f3 0 6px, #ebe7dc 6px 12px); }
.bar3 i { display: block; min-width: 3px; border-right: 1px solid #141414; } .bar3 i:last-child { border-right: 0; }
.lr .nm { display: flex; align-items: center; justify-content: space-between; gap: .8rem; font-family: var(--mono); font-size: 12px; }
.lr .nm span { white-space: nowrap; }
.lr .nm .st { font-size: .8rem; }
.empty2 { border: 1px dashed #a8a291; padding: 4rem 1.5rem; text-align: center; background: #fff; }
.empty2 .st { font-size: 1.6rem; padding: .2rem 1.1rem; }
.empty2 p { margin-top: 1.4rem; font-size: 14px; color: #55524a; }
.empty2 a { color: #141414; text-underline-offset: 4px; }
</style>
<div class="hdr"><div class="hdr-left"><a href="/">phishing-detector</a></div><div class="hdr-nav"><a href="/rules">偵測規則</a><a href="/whitelist">白名單</a><a href="/history">掃描記錄</a><a href="/paste">貼上分析</a></div></div>
<div class="dz">
  <aside class="dz-side">
    <div class="ftab"><mark>FILE</mark><span>history</span></div>
    <h1 class="pg-title"><span class="hl">掃描記錄</span></h1>
    <p class="pg-sub">最近 20 次掃描的風險分布。每一列是一次掃描，色條依比例顯示各風險等級的郵件數量。</p>
    {% if history %}
    <div class="nums">
      <div><b>{{ history|length }}</b><span>掃描次數</span></div>
      <div><b>{{ history|sum(attribute=2) }}</b><span>郵件總數</span></div>
      <div><b style="color:#c8321e">{{ history|sum(attribute=3) }}</b><span>高風險</span></div>
      <div><b style="color:#a8650f">{{ history|sum(attribute=4) }}</b><span>中風險</span></div>
    </div>
    {% endif %}
  </aside>
  <main class="dz-main">
    {% if history %}
    <div class="sh"><span class="n">01</span><h2>案件簿</h2></div>
    <div class="leg"><span><i class="dot h"></i>高風險</span><span><i class="dot m"></i>中風險</span><span><i class="dot l"></i>安全</span><span><i class="dot w"></i>白名單</span></div>
    <div class="led">
    {% for h in history %}
      <div class="lr">
        <div class="tm"><b>{{ h[1][:10] }}</b><span>{{ h[1][11:16] }}　共 {{ h[2] }} 封</span></div>
        <div class="bar3" title="高 {{ h[3] }}／中 {{ h[4] }}／安全 {{ h[5] }}／白名單 {{ h[6] }}">
          {% if h[3] %}<i class="h" style="flex:{{ h[3] }}"></i>{% endif %}
          {% if h[4] %}<i class="m" style="flex:{{ h[4] }}"></i>{% endif %}
          {% if h[5] %}<i class="l" style="flex:{{ h[5] }}"></i>{% endif %}
          {% if h[6] %}<i class="w" style="flex:{{ h[6] }}"></i>{% endif %}
        </div>
        <div class="nm">
          <span>高 {{ h[3] }}　中 {{ h[4] }}　安 {{ h[5] }}　白 {{ h[6] }}</span>
          {% if h[3] %}<span class="st red">高風險</span>{% elif h[4] %}<span class="st org">中風險</span>{% else %}<span class="st grn">安全</span>{% endif %}
        </div>
      </div>
    {% endfor %}
    </div>
    {% else %}
    <div class="sh"><span class="n">01</span><h2>案件簿</h2></div>
    <div class="empty2"><span class="st ink">尚無案件</span><p>還沒有掃描記錄，<a href="/">開始掃描</a>！</p></div>
    {% endif %}
  </main>
</div>
"""

# ── 偵測規則展示頁 ────────────────────────────────────────────
RULES_HTML = COMMON_CSS + """
<style>
.play { display: grid; border: 1px solid #141414; background: #fff; }
@media (min-width: 900px) { .play { grid-template-columns: 1.35fr 1fr; } }
.play .in { padding: 1rem 1.15rem 1.2rem; }
@media (min-width: 900px) { .play .in { border-right: 1px solid #141414; } }
.play .pn { padding: 1rem 1.15rem 1.2rem; border-top: 1px solid #141414; background: #faf8f3; }
@media (min-width: 900px) { .play .pn { border-top: 0; } }
.lb { font-family: var(--mono); font-size: 11px; font-weight: 600; letter-spacing: .08em; text-transform: uppercase; color: #141414; margin-bottom: .45rem; }
#pt { width: 100%; min-height: 6.5rem; border: 1px solid #dcd7ca; background: #faf8f3; padding: .6rem .75rem; font: 15px/1.9 var(--sans); resize: vertical; }
#mirror { min-height: 4.5rem; padding: .5rem 0; font: 15px/2 var(--sans); white-space: pre-wrap; word-break: break-word; }
#mirror mark { background: var(--hl); color: #141414; padding: .05em .12em; }
#mirror u { text-decoration: underline wavy #c8321e; text-underline-offset: 4px; }
.hits { list-style: none; margin: .6rem 0 0; padding: 0; font-size: 13px; }
.hits li { display: flex; justify-content: space-between; gap: 1rem; padding: .35rem 0; border-top: 1px dashed #a8a291; }
.hits li small { font-family: var(--mono); color: #55524a; }
.score { font-family: var(--serif); font-weight: 900; font-size: 3rem; line-height: 1; }
.score small { font-family: var(--mono); font-size: 12px; font-weight: 400; color: #55524a; margin-left: .4rem; }
.meter { height: .8rem; border: 1px solid #141414; background: #fff; margin: .7rem 0 .3rem; }
.meter i { display: block; height: 100%; width: 0; background: #141414; transition: width .3s; }
.seg { display: flex; border: 1px solid #141414; font-family: var(--mono); font-size: 11.5px; margin: .6rem 0 .2rem; }
.seg i { font-style: normal; padding: .45rem .55rem; white-space: nowrap; overflow: hidden; border-right: 1px solid #141414; }
.seg i:last-child { border-right: 0; }
.seg .a { background: #141414; color: #faf8f3; } .seg .b { background: #55524a; color: #faf8f3; } .seg .c { background: var(--hl); } .seg .d { background: #ffe0ee; }
.scale { display: flex; border: 1px solid #141414; font-family: var(--mono); font-size: 11.5px; }
.scale i { font-style: normal; padding: .5rem .6rem; color: #fff; }
.scale .lo { flex: 40; background: #2e6a4d; } .scale .md { flex: 30; background: #a8650f; } .scale .hi { flex: 30; background: #c8321e; }
.ticks { display: flex; font-family: var(--mono); font-size: 11px; color: #8a8678; margin-top: .25rem; }
.ticks span:nth-child(1) { flex: 40; } .ticks span:nth-child(2) { flex: 30; } .ticks span:nth-child(3) { flex: 30; }
.fz { display: grid; gap: 1.4rem; }
@media (min-width: 900px) { .fz { grid-template-columns: 1fr 1fr; } }
.fz .box { border: 1px solid #141414; background: #fff; padding: 1rem 1.1rem 1.15rem; }
.fz .box h3 { font-size: 1rem; font-weight: 700; }
.fz .box p { font-size: 12.5px; color: #55524a; line-height: 1.75; margin-top: .5rem; }
</style>
<div class="hdr"><div class="hdr-left"><a href="/">phishing-detector</a></div><div class="hdr-nav"><a href="/rules">偵測規則</a><a href="/whitelist">白名單</a><a href="/history">掃描記錄</a><a href="/paste">貼上分析</a></div></div>
<div class="dz">
  <aside class="dz-side">
    <div class="ftab"><mark>FILE</mark><span>rules</span></div>
    <h1 class="pg-title"><span class="hl">偵測規則一覽</span></h1>
    <p class="pg-sub">以下為系統實際使用中的規則（關鍵字清單直接讀取自偵測程式，與實際判斷同源）。規則引擎僅是四層分析中的第一層，其分數會再與 ML、HTML/URL、AI 判讀依固定權重融合。</p>
    <div class="nums">
      <div><b>{{ kw_total }}</b><span>關鍵字（4 類）</span></div>
      <div><b>{{ url_items|length }}</b><span>URL 結構規則</span></div>
      <div><b>{{ html_items|length }}</b><span>HTML 結構規則</span></div>
      <div><b>{{ whitelist_count }}</b><span>白名單網域</span></div>
    </div>
    <ul class="idx" id="idx">
      <li><a href="#try"><em>00</em><span>試試看</span></a></li>
      <li><a href="#kw"><em>01</em><span>關鍵字規則 R1–R6</span></a></li>
      <li><a href="#url"><em>02</em><span>URL 結構 U1–U8</span></a></li>
      <li><a href="#html"><em>03</em><span>HTML 結構 H1–H7</span></a></li>
      <li><a href="#fuse"><em>04</em><span>融合與分級</span></a></li>
    </ul>
  </aside>
  <main class="dz-main">
    <div class="sh" id="try"><span class="n">00</span><h2>試試看</h2>
      <p>貼上一段文字，命中的關鍵字會被螢光筆標出，並依下方 R1–R5 的計分方式估算。僅為前端示意，不含 URL / HTML 結構規則、ML 與 AI 判讀，實際結果以後端為準。</p></div>
    <div class="play">
      <div class="in">
        <div class="lb">輸入文字</div>
        <textarea id="pt">親愛的客戶，您的帳戶將於 24 小時內停用，請立即點擊 https://example.com/verify 驗證密碼。</textarea>
        <div class="lb" style="margin-top:.9rem">命中標記</div>
        <div id="mirror"></div>
      </div>
      <div class="pn">
        <div class="lb">規則引擎原始分數</div>
        <div class="score"><span id="raw">0</span><small>→ 正規化 <b id="norm">0</b> / 100</small></div>
        <div class="meter"><i id="mt"></i></div>
        <ul class="hits" id="hits"></ul>
      </div>
    </div>

    <div class="sh" id="kw"><span class="n">01</span><h2>第一層：規則引擎（郵件文字）</h2>
      <p>命中即累加原始規則分數，並將觸發的規則與命中詞記錄於結果頁。關鍵字比對皆不分大小寫，同時涵蓋英文與繁體中文。</p></div>
    <div class="cards">
    {% for rid, name, meaning, words, pts in groups %}
      <article class="card"><span class="st red">{{ pts }}</span><div class="rid">{{ rid }}</div><h3>{{ name }}</h3><p>{{ meaning }}</p>
        <div class="kws">{% for w in words %}<span>{{ w }}</span>{% endfor %}</div></article>
    {% endfor %}
      <article class="card"><span class="st red">+min(3 + 連結數, 8)</span><div class="rid">R5</div><h3>含有連結</h3><p>郵件內文出現 http(s) 網址</p><div class="kws"><span>https?://…</span></div></article>
      <article class="card"><span class="st red">每個網址 +min(2×命中數, 8)</span><div class="rid">R6</div><h3>URL 風險</h3><p>對內文每個網址（最多 10 個）套用 U1–U8</p><div class="kws"><span>U1 – U8</span></div></article>
    </div>
    <p class="note2">規則分數會正規化為 <b>min(原始分數 × 5, 100)</b> 後再進入融合。</p>

    <div class="sh" id="url"><span class="n">02</span><h2>URL 結構規則 U1–U8</h2><p>只解析網址字串，不連線、不開啟目標網站。</p></div>
    <div class="cards">
    {% for rid, name, cond in url_items %}
      <article class="card"><div class="rid">{{ rid }}</div><h3>{{ name }}</h3><p>{{ cond }}</p></article>
    {% endfor %}
    </div>

    <div class="sh" id="html"><span class="n">03</span><h2>第三層：HTML 結構規則 H1–H7</h2><p>僅在郵件含 HTML 時執行。</p></div>
    <div class="cards">
    {% for rid, name, cond, pts in html_items %}
      <article class="card"><span class="st red">{{ pts }}</span><div class="rid">{{ rid }}</div><h3>{{ name }}</h3><p>{{ cond }}</p></article>
    {% endfor %}
    </div>
    <p class="note2">HTML 分數會正規化為 <b>min(HTML 分數 × 8, 100)</b> 後再進入融合。</p>

    <div class="sh" id="fuse"><span class="n">04</span><h2>融合與分級</h2><p>各層分數依固定權重融合；寄件網域命中<a href="/whitelist" style="color:#141414;text-decoration:underline">白名單</a>者直接略過全部分析。</p></div>
    <div class="fz">
      <div class="box"><h3>有 AI 判讀</h3>
        <div class="seg"><i class="a" style="flex:35">規則 35%</i><i class="b" style="flex:35">ML 35%</i><i class="c" style="flex:15">HTML/URL 15%</i><i class="d" style="flex:15">AI 15%</i></div>
        <p>rule_score ≥ 4、ML 機率 ≥ 0.30、html_score ≥ 4 任一成立才呼叫 AI。</p></div>
      <div class="box"><h3>無 AI 判讀</h3>
        <div class="seg"><i class="a" style="flex:42.5">規則 42.5%</i><i class="b" style="flex:42.5">ML 42.5%</i><i class="c" style="flex:15">HTML/URL 15%</i></div>
        <p>AI 未觸發或失敗時自動改用。</p></div>
    </div>
    <div class="box" style="margin-top:1.4rem;border:1px solid #141414;background:#fff;padding:1rem 1.1rem 1.15rem">
      <h3 style="font-size:1rem;font-weight:700">風險等級</h3>
      <div class="scale" style="margin-top:.7rem"><i class="lo">Low &lt; 40</i><i class="md">Medium 40–69</i><i class="hi">High ≥ 70</i></div>
      <div class="ticks"><span>0</span><span>40</span><span>70 → 100</span></div>
    </div>
  </main>
</div>
<script>
var G = {{ groups|tojson }};
function per(p){p=String(p);var k=p.lastIndexOf('+');return k<0?0:(parseInt(p.slice(k+1),10)||0);}
var WORDS=[];G.forEach(function(g,gi){g[3].forEach(function(w){WORDS.push([String(w).toLowerCase(),gi]);});});
WORDS.sort(function(a,b){return b[0].length-a[0].length;});
function isSpace(c){var n=c.charCodeAt(0);return n<=32||n===12288;}
function run(){
  var t=document.getElementById('pt').value,low=t.toLowerCase(),out=document.getElementById('mirror');out.textContent='';
  var hit={},links=0,buf='',i=0,k,el,end;
  function flush(){if(buf){out.appendChild(document.createTextNode(buf));buf='';}}
  while(i<t.length){
    if(low.startsWith('http://',i)||low.startsWith('https://',i)){
      end=i;while(end<t.length&&!isSpace(t[end]))end++;
      flush();el=document.createElement('u');el.textContent=t.slice(i,end);out.appendChild(el);links++;i=end;continue;
    }
    var found=null;
    for(k=0;k<WORDS.length;k++){if(low.startsWith(WORDS[k][0],i)){found=WORDS[k];break;}}
    if(found){flush();el=document.createElement('mark');el.textContent=t.slice(i,i+found[0].length);out.appendChild(el);
      (hit[found[1]]=hit[found[1]]||{})[found[0]]=1;i+=found[0].length;}
    else{buf+=t[i];i++;}
  }
  flush();
  var raw=0,ul=document.getElementById('hits');ul.textContent='';
  Object.keys(hit).forEach(function(g){var grp=G[g],n=Object.keys(hit[g]).length,pts=n*per(grp[4]);raw+=pts;
    var li=document.createElement('li'),a=document.createElement('span'),b=document.createElement('small');
    a.textContent=grp[0]+' '+grp[1];b.textContent=Object.keys(hit[g]).join('、')+'　+'+pts;li.appendChild(a);li.appendChild(b);ul.appendChild(li);});
  if(links){var p=Math.min(3+links,8);raw+=p;var li2=document.createElement('li'),a2=document.createElement('span'),b2=document.createElement('small');
    a2.textContent='R5 含有連結';b2.textContent=links+' 個連結　+'+p;li2.appendChild(a2);li2.appendChild(b2);ul.appendChild(li2);}
  if(!ul.children.length){var e=document.createElement('li');e.textContent='沒有命中任何規則';ul.appendChild(e);}
  var norm=Math.min(raw*5,100);
  document.getElementById('raw').textContent=raw;document.getElementById('norm').textContent=norm;document.getElementById('mt').style.width=norm+'%';
}
document.addEventListener('DOMContentLoaded',function(){
  document.getElementById('pt').addEventListener('input',run);run();
  var links=document.querySelectorAll('#idx a'),secs=[];
  links.forEach(function(a){var s=document.querySelector(a.getAttribute('href'));if(s)secs.push([a,s]);});
  function spy(){var y=window.scrollY+120,cur=secs[0];secs.forEach(function(p){if(p[1].getBoundingClientRect().top+window.scrollY<=y)cur=p;});
    links.forEach(function(a){a.classList.toggle('on',cur&&a===cur[0]);});}
  window.addEventListener('scroll',spy,{passive:true});spy();
});
</script>
"""


# ── 白名單 HTML ──────────────────────────────────────────────
WHITELIST_HTML = COMMON_CSS + """
<style>
.ck { border: 1px solid #141414; background: #fff; }
.ck .row { display: flex; gap: .6rem; padding: 1rem 1.15rem; border-bottom: 1px solid #141414; }
.ck input { flex: 1; min-width: 0; border: 0; border-bottom: 2px solid #141414; background: transparent; font: 500 1.05rem var(--mono); padding: .45rem 0; }
.ck input:focus { box-shadow: none; }
.out { padding: 1.4rem 1.15rem 1.5rem; min-height: 11rem; display: grid; gap: 1rem; align-content: start; }
.dom { font-family: var(--mono); font-weight: 600; font-size: clamp(1.1rem,2.6vw,1.9rem); line-height: 1.5; word-break: break-all; }
.dom .hl { background: linear-gradient(transparent 55%, #9fe0c2 55%); }
.dom u { text-decoration: underline wavy #c8321e; text-underline-offset: 6px; }
.dom s { color: #8a8678; }
.verdict { display: flex; flex-wrap: wrap; align-items: center; gap: .9rem 1.2rem; }
.verdict .st { font-size: 1.15rem; padding: .1rem .8rem; }
.verdict p { font-size: 13.5px; line-height: 1.8; color: #55524a; flex: 1; min-width: 14rem; }
.chips { display: flex; flex-wrap: wrap; gap: .5rem; padding: 0 1.15rem 1.1rem; }
.chips button { font-family: var(--mono); font-size: 11.5px; padding: .3rem .6rem; border: 1px solid #141414; background: transparent; cursor: pointer; }
.chips button:hover { background: var(--hl); }
.chips a { font-family: var(--mono); font-size: 11.5px; color: #141414; align-self: center; text-underline-offset: 3px; }
.pass { position: relative; background: #fff; border: 1px solid #141414; padding: .95rem 1rem 1rem; display: flex; flex-direction: column; gap: .35rem; }
.pass .dn { font-family: var(--mono); font-weight: 600; font-size: 13.5px; word-break: break-all; padding-right: 1.6rem; }
.pass .dt { font-family: var(--mono); font-size: 11px; color: #8a8678; }
.pass .st { align-self: flex-start; margin-top: .5rem; font-size: .7rem; }
.pass .x { position: absolute; right: .55rem; top: .5rem; width: 1.5rem; height: 1.5rem; border: 0; background: transparent; font: 400 1.2rem/1 var(--mono); color: #8a8678; cursor: pointer; }
.pass .x:hover { background: #c8321e; color: #fff; }
.side-form { margin-top: 1.5rem; }
.side-form .lb, .lb { font-family: var(--mono); font-size: 11px; font-weight: 600; letter-spacing: .08em; text-transform: uppercase; margin-bottom: .45rem; }
.side-form .r { display: flex; gap: .5rem; }
.side-form input { flex: 1; min-width: 0; border: 1px solid #141414; padding: .55rem .7rem; font: 13px var(--mono); }
.rst { margin-top: 1rem; font-family: var(--mono); font-size: 11.5px; padding: .3rem .6rem; border: 1px solid #141414; background: transparent; cursor: pointer; }
.rst:hover { background: var(--hl); }
</style>
<script>
var WL = {{ domains|map(attribute=0)|list|tojson }};
function addDomain() {
  const domain = document.getElementById('domain-input').value.trim();
  if (!domain) return alert('請輸入網域');
  fetch('/whitelist/add', {method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({domain})}).then(r => r.json()).then(d => {
    if (d.success) location.reload();
    else alert(d.error || '新增失敗');
  });
}
function escH(x) { return String(x).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
function checkSender(value) {
  const input = document.getElementById('check-input');
  if (value !== undefined) input.value = value;
  const sender = input.value.trim();
  const out = document.getElementById('check-out');
  if (!sender) { out.innerHTML = '<p class="pg-sub">請輸入寄件者信箱，例如 name@example.com</p>'; return; }
  fetch('/whitelist/check', {method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({sender})}).then(r => r.json()).then(d => {
    if (!d.success) { out.innerHTML = '<p class="pg-sub">' + escH(d.error || '檢查失敗') + '</p>'; return; }
    const dom = d.domain;
    if (d.matched) {
      const wl = d.whitelist_domain, pre = dom.slice(0, dom.length - wl.length);
      out.innerHTML = '<div class="dom">' + escH(pre) + '<span class="hl">' + escH(wl) + '</span></div>' +
        '<div class="verdict"><span class="st grn">放行</span><p>' + escH(d.mode) + '：寄件網域命中白名單「' + escH(wl) + '」，系統將略過分析，直接判定為安全。</p></div>';
    } else {
      const fake = WL.find(w => dom.indexOf(w) >= 0);
      let shown = escH(dom), why = '未命中任何白名單網域，將進入完整四層分析。';
      if (fake) {
        const k = dom.indexOf(fake);
        shown = escH(dom.slice(0, k)) + '<u>' + escH(fake) + '</u>' + escH(dom.slice(k + fake.length));
        why = '網域中雖然出現「' + escH(fake) + '」，但它不是網域結尾，所以不命中，將進入完整四層分析。';
      }
      out.innerHTML = '<div class="dom">' + shown + '</div><div class="verdict"><span class="st red">不命中</span><p>' + why + '</p></div>';
    }
  }).catch(() => { out.innerHTML = '<p class="pg-sub">檢查失敗，請稍後再試</p>'; });
}
function deleteDomain(domain) {
  if (!confirm('確定要刪除 ' + domain + '？')) return;
  fetch('/whitelist/delete', {method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({domain})}).then(r => r.json()).then(d => {
    if (d.success) location.reload();
    else alert(d.error || '刪除失敗');
  }).catch(() => alert('刪除失敗，請稍後再試'));
}
function resetWhitelist() {
  if (!confirm('要還原預設白名單嗎？（只會補回被刪除的預設網域，不會刪除你新增的網域）')) return;
  fetch('/whitelist/reset', {method:'POST'}).then(r => r.json()).then(d => {
    if (d.success) location.reload();
  });
}
document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('domain-input').addEventListener('keydown', e => { if (e.key === 'Enter') addDomain(); });
  document.getElementById('check-input').addEventListener('keydown', e => { if (e.key === 'Enter') checkSender(); });
  checkSender('no-reply@accounts.google.com');
});
</script>
<div class="hdr"><div class="hdr-left"><a href="/">phishing-detector</a></div><div class="hdr-nav"><a href="/rules">偵測規則</a><a href="/whitelist">白名單</a><a href="/history">掃描記錄</a><a href="/paste">貼上分析</a></div></div>
<div class="dz">
  <aside class="dz-side">
    <div class="ftab"><mark>FILE</mark><span>whitelist</span></div>
    <h1 class="pg-title"><span class="hl">白名單設定</span></h1>
    <p class="pg-sub">加入白名單後，來自該網域及其子網域的信件將直接標記為安全，不進行 AI 分析。請只加入確定可信任的網域。</p>
    <div class="nums"><div><b>{{ count }}</b><span>目前白名單網域</span></div><div><b>2</b><span>比對方式：完全相同／子網域</span></div></div>
    <div class="side-form">
      <div class="lb">新增網域</div>
      <div class="r"><input type="text" id="domain-input" placeholder="例如：example.com"><button class="add-btn" onclick="addDomain()">新增</button></div>
      <button class="rst" onclick="resetWhitelist()">還原預設白名單</button>
    </div>
  </aside>
  <main class="dz-main">
    <div class="sh"><span class="n">01</span><h2>比對檢測</h2>
      <p>輸入任一寄件者信箱，即時顯示是否命中白名單。寄件網域「完全相同」或為白名單網域的「子網域」才算命中；開頭相似、後面接其他網域的偽冒網域不會命中。</p></div>
    <div class="ck">
      <div class="row"><input type="text" id="check-input" placeholder="例如：no-reply@accounts.google.com"><button class="add-btn" onclick="checkSender()">檢測</button></div>
      <div class="out" id="check-out"></div>
      <div class="chips">
        <button onclick="checkSender('no-reply@accounts.google.com')">範例①：官方網域（命中）</button>
        <button onclick="checkSender('alert@mail.google.com')">範例②：子網域（命中）</button>
        <button onclick="checkSender('no-reply@accounts.google.com.verify-login.xyz')">範例③：偽冒網域（不命中）</button>
        <a href="/paste?sample=wl_real">完整演示①：白名單信件</a>
        <a href="/paste?sample=wl_fake">完整演示②：偽冒信件</a>
      </div>
    </div>

    <div class="sh"><span class="n">02</span><h2>目前白名單（{{ count }} 個）</h2><p>每個網域及其子網域都會被放行。</p></div>
    <div class="cards">
    {% for d in domains %}
      <div class="pass">
        <button class="x" title="刪除" onclick="deleteDomain('{{ d[0] }}')">×</button>
        <div class="dn">{{ d[0] }}</div>
        <div class="dt">新增時間：{{ d[1][:10] if d[1] else '—' }}</div>
        <span class="st grn">已放行 CLEARED</span>
      </div>
    {% endfor %}
    </div>
  </main>
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
    c.execute('CREATE TABLE IF NOT EXISTS app_meta (key TEXT PRIMARY KEY, value TEXT)')
    c.execute("SELECT value FROM app_meta WHERE key='whitelist_seeded'")
    if not c.fetchone():
        # 預設白名單只在首次建立時寫入，之後使用者刪除的網域不會在重啟後復原
        for domain in DEFAULT_WHITELIST:
            c.execute('INSERT OR IGNORE INTO whitelist (domain, added_time) VALUES (?, ?)',
                     (domain, datetime.now().isoformat()))
        c.execute("INSERT OR REPLACE INTO app_meta (key, value) VALUES ('whitelist_seeded', '1')")
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

def normalize_whitelist_domain(value):
    """正規化白名單網域，只接受純網域名稱。"""
    value = (value or '').strip().lower()
    value = re.sub(r'^https?://', '', value)
    value = value.split('/', 1)[0].split('?', 1)[0].split('#', 1)[0]
    value = value.rstrip('.')
    if ':' in value:
        return ''
    if not re.fullmatch(r'[a-z0-9](?:[a-z0-9.-]{0,251}[a-z0-9])?', value):
        return ''
    if '.' not in value or '..' in value or value.startswith('.'):
        return ''
    labels = value.split('.')
    if any(not x or len(x) > 63 or x.startswith('-') or x.endswith('-') for x in labels):
        return ''
    return value

def whitelist_match(sender):
    """回傳 (寄件網域, 命中的白名單網域, 比對方式)；未命中時命中網域為空字串。"""
    domain = extract_sender_domain(sender)
    if not domain:
        return '', '', ''
    for d in get_whitelist():
        if domain == d:
            return domain, d, '精確網域比對'
        if domain.endswith('.' + d):
            return domain, d, '子網域比對'
    return domain, '', ''

def is_whitelisted(sender):
    return bool(whitelist_match(sender)[1])

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

groq_client = Groq(api_key=GROQ_API_KEY) if (GROQ_API_KEY and Groq is not None) else None
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


URGENT_WORDS = [
    'urgent', 'immediately', 'expire', 'suspended', 'verify now', 'act now',
    '立即', '緊急', '即將停用', '馬上', '限時', '暫停', '停用'
]
BAIT_WORDS = [
    'free', 'winner', 'won', 'prize', 'claim', 'lucky', 'reward', 'gift',
    '中獎', '免費', '領取', '恭喜', '退款', '補助'
]
PERSONAL_WORDS = [
    'password', 'credit card', 'bank account', 'pin',
    '密碼', '帳號', '信用卡', '身分證', '帳戶'
]
MONEY_WORDS = [
    '$', 'cash', 'money', 'transfer', 'wire', 'payment', 'invoice',
    '匯款', '轉帳', '付款', 'NT$', '退款'
]


def rule_based_score(text):
    score = 0
    triggered = []
    t = (text or '').lower()

    hits = [w for w in URGENT_WORDS if w in t]
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

    hits2 = [w for w in BAIT_WORDS if w in t]
    if hits2:
        score += len(hits2) * 2
        triggered.append(f'誘騙話術: {hits2}')

    hits3 = [w for w in PERSONAL_WORDS if w in t]
    if hits3:
        score += len(hits3) * 3
        triggered.append(f'索取個資: {hits3}')

    hits4 = [w for w in MONEY_WORDS if w in t]
    if hits4:
        score += len(hits4) * 2
        triggered.append(f'金錢相關: {hits4}')

    return score, triggered


# 規則展示頁使用的規則目錄（關鍵字直接引用上方常數，與實際偵測邏輯同源）
RULE_KEYWORD_GROUPS = [
    ('R1', '緊急語句', '製造時間壓力，逼迫收件者倉促行動', URGENT_WORDS, '每命中 1 個詞 +2'),
    ('R2', '誘騙話術', '以獎金、免費、退款等利益誘使點擊', BAIT_WORDS, '每命中 1 個詞 +2'),
    ('R3', '索取個資', '要求提供密碼、卡號、帳戶等敏感資料', PERSONAL_WORDS, '每命中 1 個詞 +3'),
    ('R4', '金錢相關', '涉及匯款、付款、轉帳等金流指示', MONEY_WORDS, '每命中 1 個詞 +2'),
]
RULE_URL_ITEMS = [
    ('U1', 'URL 使用 IP 位址', '主機名稱為 IP 而非網域'),
    ('U2', 'URL 含有 @', '以 @ 隱藏真正目的地'),
    ('U3', '網域含 Punycode', '網域以 xn-- 開頭，可能為仿冒字元網域'),
    ('U4', '高風險網域後綴', '.xyz / .top / .click / .zip / .mov / .work / .biz'),
    ('U5', 'URL 過長', '網址長度超過 100 字元'),
    ('U6', '子網域層級過深', '主機名稱中的「.」達 4 個以上'),
    ('U7', '短網址服務', 'bit.ly、tinyurl.com、t.co 等 9 種短網址'),
    ('U8', '登入／驗證誘導字樣', 'login、verify、secure、update、account、password、signin、confirm、wallet'),
]
RULE_HTML_ITEMS = [
    ('H1', '網址結構風險', '連結 href 觸發 U1–U8 任一項', '每個連結 +3×命中數（上限 10）'),
    ('H2', '偽裝連結', '連結顯示文字的網域與實際 href 網域不同', '+6'),
    ('H3', '像素追蹤', '寬或高為 0 / 1 的圖片', '每個 +2（上限 8）'),
    ('H4', '隱藏元素', 'style 含 display:none 或 visibility:hidden', '+3'),
    ('H5', '表單元素', '含 <form>', '+3'),
    ('H6', '密碼輸入欄位', '含 type="password" 的 <input>', '+5'),
    ('H7', '品牌偵測', '內文出現 paypal / microsoft / apple / amazon / facebook / netflix / google', '+2'),
]


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


def ir_download_fields(ir_detail, sender, subject):
    """供前端「下載 IR 報告」使用的完整欄位（畫面上的摘要有截斷，下載檔不截斷）。"""
    return {
        'impact_full': ir_detail.get('impact_assessment', ''),
        'actions_full': ir_detail.get('immediate_actions', []),
        'email_sender': sender,
        'email_subject': subject,
    }


def get_header(msg, name):
    for h in msg['payload']['headers']:
        if h['name'].lower() == name.lower(): return h['value']
    return ''

def _walk_parts(payload):
    yield payload
    for part in payload.get('parts', []) or []:
        yield from _walk_parts(part)

def _decode_part(part):
    data = part.get('body', {}).get('data', '')
    if not data:
        return ''
    try:
        return base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
    except Exception:
        return ''

def get_body(msg):
    # 優先取得 text/plain；若信件只有 HTML，退回 HTML 去除標籤後的文字。
    payload = msg.get('payload', {})
    for part in _walk_parts(payload):
        if part.get('mimeType') == 'text/plain':
            text = _decode_part(part)
            if text:
                return text[:5000]
    for part in _walk_parts(payload):
        if part.get('mimeType') == 'text/html':
            html = _decode_part(part)
            if html:
                return BeautifulSoup(html, 'html.parser').get_text(' ', strip=True)[:5000]
    return ''

def get_html(msg):
    payload = msg.get('payload', {})
    for part in _walk_parts(payload):
        if part.get('mimeType') == 'text/html':
            html = _decode_part(part)
            if html:
                return html[:20000]
    return ''

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
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2 MB
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = os.getenv('COOKIE_SECURE', '1' if BASE_URL.startswith('https://') else '0') == '1'


@app.errorhandler(413)
def handle_payload_too_large(e):
    if request.path.startswith('/api') or request.is_json:
        return jsonify({"ok": False, "error": "內容過大，請縮短郵件內容後再試。"}), 413
    return "內容過大，請縮短郵件內容後再試。", 413

@app.errorhandler(404)
def handle_not_found(e):
    if request.path.startswith('/api') or request.is_json:
        return jsonify({"ok": False, "error": "找不到要求的頁面。"}), 404
    return "找不到要求的頁面。", 404

@app.errorhandler(500)
def handle_internal_error(e):
    app.logger.exception("Unhandled application error")
    if request.path.startswith('/api') or request.is_json:
        return jsonify({"ok": False, "error": "系統暫時發生錯誤，請稍後再試。"}), 500
    return "系統暫時發生錯誤，請稍後再試。", 500

app.secret_key = os.environ.get('FLASK_SECRET_KEY') or secrets.token_hex(32)
if not os.environ.get('FLASK_SECRET_KEY') and BASE_URL.startswith('https://'):
    print('WARNING: FLASK_SECRET_KEY 未設定，已使用隨機暫時金鑰；正式部署請設定環境變數。')
_state = {}
_creds = {}
_scans = {}


@app.after_request
def add_security_headers(response):
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault(
        "Permissions-Policy",
        "camera=(), microphone=(), geolocation=()"
    )
    return response

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
        auth_resp = request.url
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
        detail = traceback.format_exc()
        return render_error('Google Gmail 授權失敗', '請確認 Google OAuth 的重新導向 URI、Client ID / Secret 與 Gmail API 設定。', detail), 500

def _scan_progress(scan_id, level):
    """記錄每封信完成後的風險等級，供掃描中頁面顯示真實進度（不含信件內容）。"""
    st = _scans.get(scan_id)
    if st is not None and not st.get('done'):
        st.setdefault('progress', []).append(level)

def do_scan(token_data, scan_id):
    try:
        creds = Credentials(**token_data)
        service = build('gmail','v1',credentials=creds)
        results_api = service.users().messages().list(
            userId='me', maxResults=15, labelIds=['INBOX']).execute()
        messages = results_api.get('messages', [])
        inbox_count = len(messages)
        _scans[scan_id]['inbox_total'] = inbox_count
        _scans[scan_id]['progress'] = []
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
                _scan_progress(scan_id, 'sk')
                continue

            if is_whitelisted(sender):
                entry = {'level':'wl','risk_score':-1,'subject':subject[:55],
                         'sender':sender[:60],'explanation':'來自白名單寄件者，系統判定為安全。',
                         'action':'可安全閱讀','tags':[],'scores':[],
                         'category':'白名單安全信件','ir':None}
                wl_list.append(entry)
                all_emails.append(entry)
                _scan_progress(scan_id, 'wl')
                continue

            report, html_score, html_findings, rule_score, spam_prob = full_pipeline(text, html)
            html_tags = [cat for cat,_ in html_findings[:3]]
            tags = report.get('suspicious_points',[])[:5]

            entry = {
                'level': report['risk_level'],
                'risk_score': report['risk_score'],
                'subject': subject[:55],
                'sender': sender[:60],
                'body': body[:4000],
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
                    **ir_download_fields(ir_detail, sender, subject),
                }
                high_list.append(entry)
            elif report['risk_level'] == 'medium':
                med_list.append(entry)
            else:
                low_list.append(entry)
            all_emails.append(entry)
            _scan_progress(scan_id, report['risk_level'])

        scan_time = datetime.now().strftime('%Y-%m-%d %H:%M')
        save_scan(scan_id, scan_time,
                  len(high_list)+len(med_list)+len(low_list)+len(wl_list),
                  high_list, med_list, low_list, len(wl_list), skipped)

        _scans[scan_id] = {
            'done': True,
            'all_emails': all_emails,
            'high': len(high_list), 'med': len(med_list),
            'low': len(low_list), 'wl': len(wl_list), 'skipped': skipped,
            'total': len(all_emails),
            'inbox_messages_fetched': inbox_count
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
        st = _scans[scan_id]
        return jsonify({'done': st.get('done',False), 'scan_id': scan_id,
                        'total': st.get('inbox_total'), 'progress': st.get('progress', [])})
    return jsonify({'done': False, 'scan_id': ''})

@app.route('/paste')
def paste_page():
    return render_paste_page(request.args.get('sample', '').strip())

@app.route('/paste_analyze', methods=['POST'])
def paste_analyze():
    sender  = request.form.get('sender', '').strip() or '(未提供寄件者)'
    subject = request.form.get('subject', '').strip() or '(無主旨)'
    body    = request.form.get('body', '').strip()
    html    = request.form.get('html', '').strip()

    if not body:
        err = '<div class="err-box">請貼上郵件內文再送出。</div>'
        return render_paste_page(error=err)

    text = f"From: {sender}\nSubject: {subject}\nBody: {body}"

    try:
        wl_domain, wl_hit, wl_mode = whitelist_match(sender)
        if wl_hit:
            entry = {'level': 'wl', 'risk_score': -1, 'subject': subject[:55],
                     'sender': sender[:60],
                     'explanation': f'寄件網域 {wl_domain} 命中白名單「{wl_hit}」（{wl_mode}），系統略過規則、ML、HTML 與 AI 分析，直接判定為安全。',
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
                'body': body[:4000],
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
                    **ir_download_fields(ir_detail, sender, subject),
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
        return render_paste_page(error=err)

@app.route('/result/<scan_id>')
def result(scan_id):
    data = _scans.get(scan_id)
    if not data or not data.get('done'): return redirect('/')
    if 'error' in data:
        return render_error('掃描失敗', '分析過程發生錯誤，詳細資訊如下。', data['error']), 500

    all_emails = data['all_emails']

    # 建立左側列表 HTML
    import html as html_lib

    def make_item(e, idx):
        level = e.get('level', 'wl')
        dot = {'high':'dot-high','medium':'dot-med','low':'dot-low','wl':'dot-wl'}.get(level,'dot-wl')
        score_text = f"{e.get('risk_score', -1)}/100 · {e.get('category','')}" if e.get('risk_score', -1) >= 0 else '白名單 · 略過分析'
        reason = ''
        findings = e.get('explainable_findings') or []
        if findings:
            reason = str(findings[0].get('title') or findings[0].get('detail') or '')
        elif e.get('explanation'):
            reason = str(e.get('explanation'))
        reason = html_lib.escape(reason[:70])
        subject = html_lib.escape(str(e.get('subject','')))
        sender = html_lib.escape(str(e.get('sender','')))
        category = html_lib.escape(str(e.get('category','')))
        return (f'<div class="email-item" data-idx="{idx}" onclick="showDetail({idx}, this)">'
                f'<div class="risk-dot {dot}"></div>'
                f'<div class="item-body">'
                f'<div class="item-subj">{subject}</div>'
                f'<div class="item-from">{sender}</div>'
                f'<div class="item-score">{html_lib.escape(score_text)}</div>'
                f'{f"<div class=\"item-reason {level}\">› {reason}</div>" if reason else ""}'
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

    page = RESULT_HTML.replace('KEYWORDS_PLACEHOLDER', _kw_json())
    page = page.replace('TOTAL_COUNT', str(data['total']))
    page = page.replace('HIGH_COUNT',  str(data['high']))
    page = page.replace('MED_COUNT',   str(data['med']))
    page = page.replace('LOW_COUNT',   str(data['low']))
    page = page.replace('WL_COUNT',    str(data['wl']))
    page = page.replace('SK_COUNT',    str(data['skipped']))
    total_for_pct = max(int(data.get('total', 0)), 1)
    analyzed_count = int(data.get('high', 0)) + int(data.get('med', 0)) + int(data.get('low', 0))
    page = page.replace('HIGH_PCT', f"{data['high'] / total_for_pct * 100:.2f}")
    page = page.replace('MED_PCT', f"{data['med'] / total_for_pct * 100:.2f}")
    page = page.replace('LOW_PCT', f"{data['low'] / total_for_pct * 100:.2f}")
    page = page.replace('WL_PCT', f"{data['wl'] / total_for_pct * 100:.2f}")
    page = page.replace('ANALYZED_COUNT', str(analyzed_count))
    # 使用者內容（信件列表、信件資料）最後才注入，避免內容中的字串被誤替換
    page = page.replace('LIST_PLACEHOLDER', list_html)
    page = page.replace('PLACEHOLDER_DATA', emails_json)
    return page


@app.route('/history')
def history():
    rows = get_history()
    return render_template_string(HISTORY_HTML, history=rows)

@app.route('/rules')
def rules_page():
    kw_total = sum(len(g[3]) for g in RULE_KEYWORD_GROUPS)
    return render_template_string(
        RULES_HTML, groups=RULE_KEYWORD_GROUPS, url_items=RULE_URL_ITEMS,
        html_items=RULE_HTML_ITEMS, kw_total=kw_total,
        whitelist_count=len(get_whitelist()))

@app.route('/whitelist/check', methods=['POST'])
def whitelist_check():
    """白名單檢測：輸入寄件者，回傳是否命中及命中的規則（供展示用，不寫入資料庫）。"""
    data = request.get_json(silent=True) or {}
    sender = str(data.get('sender', ''))[:200]
    domain, hit, mode = whitelist_match(sender)
    if not domain:
        return jsonify({'success': False, 'error': '無法從輸入中解析出寄件網域，請輸入如 name@example.com'}), 400
    return jsonify({'success': True, 'domain': domain, 'matched': bool(hit),
                    'whitelist_domain': hit, 'mode': mode})

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
    data = request.get_json(silent=True) or {}
    raw_domain = data.get('domain', '')
    domain = normalize_whitelist_domain(raw_domain)
    if not domain:
        return jsonify({'success':False,'error':'網域格式不正確，請輸入例如 example.com'}), 400
    try:
        conn = sqlite3.connect('phishing.db')
        c = conn.cursor()
        c.execute('INSERT INTO whitelist (domain, added_time) VALUES (?,?)',
                 (domain, datetime.now().isoformat()))
        conn.commit(); conn.close()
        return jsonify({'success':True,'domain':domain})
    except sqlite3.IntegrityError:
        return jsonify({'success':False,'error':'這個網域已經在白名單中'})
    except Exception as e:
        return jsonify({'success':False,'error':'新增白名單失敗'})

@app.route('/whitelist/reset', methods=['POST'])
def whitelist_reset():
    """還原預設白名單（補回被刪除的預設網域，不影響使用者自行新增的網域）。"""
    conn = sqlite3.connect('phishing.db')
    c = conn.cursor()
    for domain in DEFAULT_WHITELIST:
        c.execute('INSERT OR IGNORE INTO whitelist (domain, added_time) VALUES (?, ?)',
                 (domain, datetime.now().isoformat()))
    conn.commit(); conn.close()
    return jsonify({'success': True})

@app.route('/whitelist/delete', methods=['POST'])
def whitelist_delete():
    data = request.get_json(silent=True) or {}
    domain = normalize_whitelist_domain(data.get('domain', ''))
    if not domain:
        return jsonify({'success':False,'error':'網域格式不正確'}), 400
    conn = sqlite3.connect('phishing.db')
    c = conn.cursor()
    c.execute('DELETE FROM whitelist WHERE domain=?', (domain,))
    deleted = c.rowcount
    conn.commit(); conn.close()
    return jsonify({'success':True,'deleted':bool(deleted)})

def run_system_self_test():
    """執行不依賴 Gmail / Groq 的本機系統自我檢測。"""
    tests = []

    def add(name, passed, detail=''):
        tests.append({'name': name, 'passed': bool(passed), 'detail': detail})

    # 1. 模型與向量器
    add('ML 模型已載入', model is not None and hasattr(model, 'predict_proba'),
        'predict_proba 可用' if model is not None else '模型未載入')
    add('TF-IDF 已載入', vectorizer is not None and hasattr(vectorizer, 'transform'),
        'transform 可用' if vectorizer is not None else '向量器未載入')

    # 2. 風險公式與門檻
    for item in run_risk_score_self_test():
        add('風險公式：' + item['name'], item['passed'],
            f"actual={item['actual']}, expected={item['expected']}")

    # 3. URL 分析
    url_findings = analyze_url('https://example.xyz/login/verify')
    add('URL 風險分析', len(url_findings) >= 2, str(url_findings))

    # 4. HTML 分析
    sample_html = '''<html><body>
        <a href="https://evil.xyz/login">https://google.com/login</a>
        <img src="https://evil.xyz/p.gif" width="1" height="1">
        <form><input type="password"></form>
        <div style="display:none">hidden</div>
    </body></html>'''
    html_score, html_findings = analyze_html(sample_html)
    add('HTML 風險分析', html_score > 0 and len(html_findings) >= 3,
        f'score={html_score}, findings={len(html_findings)}')

    # 5. 白名單
    normalized = normalize_whitelist_domain('https://Example.COM/path')
    add('白名單網域正規化', normalized == 'example.com', normalized)
    add('白名單子網域比對', is_whitelisted('User <a@accounts.google.com>'),
        'google.com 子網域應通過' if is_whitelisted('User <a@accounts.google.com>') else '比對失敗')

    # 6. Flask 路由
    route_paths = {str(rule.rule) for rule in app.url_map.iter_rules()}
    required_routes = {'/', '/health', '/self_test', '/paste', '/history', '/whitelist'}
    missing = sorted(required_routes - route_paths)
    add('核心路由存在', not missing, 'missing=' + ','.join(missing))

    passed = sum(1 for x in tests if x['passed'])
    total = len(tests)
    return {
        'status': 'ok' if passed == total else 'warning',
        'passed': passed,
        'total': total,
        'tests': tests,
        'external_services_tested': False,
        'note': '自我檢測不會連線 Gmail 或 Groq。'
    }


@app.route('/self_test')
def self_test():
    return jsonify(run_system_self_test())


@app.route('/health')
def health():
    ml_ready = model is not None and vectorizer is not None
    self_test = run_system_self_test()
    return jsonify({
        'status': 'ok' if self_test['status'] == 'ok' else 'warning',
        'time': datetime.now().isoformat(),
        'ml_model_loaded': model is not None,
        'tfidf_loaded': vectorizer is not None,
        'gmail_oauth_configured': bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET),
        'ai_configured': bool(GROQ_API_KEY and Groq is not None),
        'ml_ready': ml_ready,
        'self_test': {
            'status': self_test['status'],
            'passed': self_test['passed'],
            'total': self_test['total']
        }
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
