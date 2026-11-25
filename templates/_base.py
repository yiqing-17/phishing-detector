"""共用 CSS / JS 與頁面後處理工具（各頁面模組共用）。"""
import json

# ── CSS 共用樣式 (全站統一風格：極簡工程風／終端機質感，黑白為主) ───────────────────
COMMON_CSS = """<!DOCTYPE html>
<html lang="zh-Hant">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#141414">
<meta name="description" content="結合規則、機器學習、URL／HTML 解析與 AI 語意判讀，找出可疑信件。">
<script>try{var _t=+sessionStorage.getItem('pdSx');sessionStorage.removeItem('pdSx');if(_t&&Date.now()-_t<5000){var _d=document.documentElement;_d.classList.add('sxin');setTimeout(function(){_d.classList.remove('sxin');},1400);}}catch(e){}</script>
<style>
html.sxin::after{content:"";position:fixed;inset:0;z-index:9999;background:#141414;pointer-events:none;animation:sxaOutRes .5s cubic-bezier(.7,0,.2,1) .06s forwards}
@keyframes sxaOutRes{from{clip-path:inset(0)}to{clip-path:inset(0 0 0 100%)}}
@media (prefers-reduced-motion: reduce){html.sxin::after{display:none}}
.irflow{margin-top:14px;padding:12px;border:1px dashed var(--line,#999)}.irfl-h{display:flex;gap:14px;flex-wrap:wrap;align-items:center}.irfl-h span{opacity:.7;font-size:.85em}.irfl-note{width:100%;box-sizing:border-box;margin:10px 0 6px;padding:8px}.irfl-b{display:flex;gap:8px;flex-wrap:wrap}.irfl-msg{color:#b3261e;min-height:1.2em;margin-top:6px}.irfl-ev{margin:8px 0 0;padding-left:1.2em;font-size:.85em;opacity:.85}</style>
<meta property="og:type" content="website">
<meta property="og:title" content="phishing-detector">
<meta property="og:description" content="授權 Gmail 或直接貼信，四層分析逐層比對，找出可疑信件。">
<link rel="manifest" href="/manifest.webmanifest">
<meta name="theme-color" content="#141414">
<link rel="icon" type="image/png" href="/static/icon-192.png">
<link rel="apple-touch-icon" href="/static/icon-192.png">
<meta property="og:site_name" content="phishing-detector">
<meta property="og:locale" content="zh_TW">
<meta property="og:image" content="https://phishing-detector-n8rv.onrender.com/static/og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="phishing-detector：四層分析，找出可疑信件">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' fill='%23ffb6d5'/%3E%3Ctext x='16' y='25' font-size='25' font-family='Georgia,serif' font-weight='900' text-anchor='middle' fill='%23141414'%3Ep%3C/text%3E%3C/svg%3E">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="preload" as="style" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=Noto+Sans+TC:wght@400;500;700&family=Noto+Serif+TC:wght@700;900&family=Klee+One&display=swap" onload="this.onload=null;this.rel='stylesheet'">
<noscript><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=Noto+Sans+TC:wght@400;500;700&family=Noto+Serif+TC:wght@700;900&family=Klee+One&display=swap"></noscript>
<style>
:root {
  --sans: 'Noto Sans TC', system-ui, sans-serif;
  --serif: 'Noto Serif TC', 'Songti TC', serif;
  --accent: #141414;
  --mono: 'IBM Plex Mono', 'Noto Sans TC', ui-monospace, Menlo, monospace;
  --hl: #ffb6d5;
  --paper: #f1f1f1;
  --bg-main: #f1f1f1;
  --bg-card: #e9e9e9;
  --bg-hover: #e2e2e2;
  --border-subtle: #d4d4d4;
  --border-accent: #9a9a9a;
  --text-main: #141414;
  --text-muted: #4a4a4a;
  --text-dim: #6b6b6b;
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
.ftab { display: flex; width: fit-content; align-items: center; gap: .6rem; font-family: var(--mono); font-size: 11.5px; letter-spacing: .08em; text-transform: uppercase; padding-bottom: 1.1rem; }
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
body textarea { vertical-align: top; }
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
footer.f .cp { margin-top: 2.25rem; color: #6b6b6b; }

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
.nums span { display: block; font-family: var(--mono); font-size: 11px; color: var(--text-muted); }
.idx { list-style: none; margin: 1.5rem 0 0; padding: 0; font-family: var(--mono); font-size: 12px; }
.idx a { display: flex; gap: .7rem; padding: .4rem 0; border-top: 1px solid #d4d4d4; color: #141414; text-decoration: none; }
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
.st.red { color: #c8321e; } .st.grn { color: #2e6a4d; } .st.org { color: #925709; } .st.ink { color: #141414; }
.card .st { position: absolute; right: .85rem; top: .95rem; font-size: .75rem; max-width: 11rem; text-align: center; }
.note2 { margin-top: .9rem; font-family: var(--mono); font-size: 12px; color: var(--text-muted); line-height: 1.8; }
.note2 b { background: var(--hl); font-weight: 500; padding: 0 .25rem; }

body .hdr-left a { color: inherit; text-decoration: none; font-weight: 600; }
body .hdr-nav a.cur { background: var(--hl); padding: 2px .45rem; }
@media (max-width: 700px) {
  body .hdr { height: auto; min-height: 3rem; flex-wrap: wrap; gap: .3rem 1rem; padding: .6rem 1rem; }
  body .hdr-nav { width: 100%; display: grid; grid-template-columns: repeat(4, 1fr); gap: 0; }
  body .hdr-nav a, body .hdr-nav a.cur { justify-content: center; min-height: 44px; padding: 0 .2rem; }
  body .hdr-nav a kbd.k { display: none; }
  .dz-side { padding: 1.25rem 1rem 1.5rem; }
}
footer.f .fi { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: flex-end; gap: 1.5rem 3rem; }
footer.f .fi .big { margin-bottom: 0; }
footer.f .fi nav { padding-bottom: .6rem; }
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
    f.innerHTML='<div class="fi"><div class="big"><span>phishing</span>-detector</div><nav><a href="/rules">偵測規則</a><a href="/whitelist">白名單</a><a href="/paste">貼信送檢</a><a href="/login">Google 登入</a></nav></div>';
    document.body.appendChild(f);
  }
  document.addEventListener('keydown',function(ev){
    if(ev.metaKey||ev.ctrlKey||ev.altKey)return;
    var t2=ev.target,tn=t2&&t2.tagName;
    if(tn==='INPUT'||tn==='TEXTAREA'||tn==='SELECT'||(t2&&t2.isContentEditable))return;
    var h=keys[(ev.key||'').toLowerCase()];
    if(h){if(window.PDX)PDX.key(ev.key,h);else location.href=h;}
  });
});
</script>

"""

# ── 首頁 HTML (極簡工程風／終端機質感，單頁固定 100vh 滿版，無滾輪) ─────
DESIGN2_CSS = """
<style>
/* ===== 設計系統 v3：減卡・信紙。信是主角，其餘是平面排版 ===== */
:root{--paper:#f1f1f1;--bg-main:#f1f1f1;--bg-card:#e9e9e9;--bg-hover:#e2e2e2;--sheet:#fdfdfe}
html,body{background:#f1f1f1}
.sh{border-top:0;margin-top:3.6rem}
.sh::before{content:"";display:block;flex-basis:100%;height:5px;background:#141414;margin-bottom:.9rem}
.sh .n{background:#141414;color:var(--hl);padding:.05rem .55rem;font-size:13px}
.sh h2{font-size:1.9rem}
::selection{background:var(--hl);color:#141414}
.sh .n{color:#f1f1f1}
.pg-title .hl{background:none}
.dz-side{background:transparent}
footer.f{background:#141414;color:#f1f1f1;border-top:0}
footer.f .big{color:#f1f1f1}
footer.f .big span{background:var(--hl);color:#141414}
footer.f a{color:#f1f1f1}
.dz ~ footer.f{margin-top:0}
.btn:not(.o),.submit-btn,.add-btn{clip-path:polygon(0 0,calc(100% - 10px) 0,100% 10px,100% 100%,0 100%)}

/* 信紙：全站唯一的軟陰影與紙張質感 */
.doc,.mini,.qmail,.mail,.mdoc{
 position:relative;isolation:isolate;background:var(--sheet)!important;border:0!important;
 box-shadow:0 1px 1px rgba(0,0,0,.10),0 10px 18px -6px rgba(0,0,0,.28),0 26px 40px -16px rgba(0,0,0,.22)!important}
.doc::before,.mini::before,.qmail::before,.mail::before,.mdoc::before{
 content:"";position:absolute;inset:0;z-index:-1;pointer-events:none;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='220' height='220'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='2' stitchTiles='stitch'/%3E%3CfeColorMatrix values='0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 .055 0'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E")}
.doc::after,.mini::after,.qmail::after,.mail::after,.mdoc::after{
 content:"";position:absolute;inset:0;z-index:-1;pointer-events:none;
 background:
  linear-gradient(to bottom,transparent calc(33.33% - 5px),rgba(0,0,0,.028) calc(33.33% - 1px),rgba(255,255,255,.5) 33.33%,transparent calc(33.33% + 5px)),
  linear-gradient(to bottom,transparent calc(66.66% - 5px),rgba(0,0,0,.028) calc(66.66% - 1px),rgba(255,255,255,.5) 66.66%,transparent calc(66.66% + 5px))}
.lh{font:600 11px var(--mono);letter-spacing:.24em;text-align:center;color:#141414;text-transform:uppercase;padding-bottom:.55rem;margin-bottom:.85rem;border-bottom:3px double #141414}

/* 平面框：只給「獨一無二的物件」 */
.play,.ck,.att,.ir,main.ew{border:1.5px solid #141414!important;background:#fff!important;box-shadow:none!important}
main.ew{margin:3.5rem auto;padding:3rem 2.4rem 2.4rem;width:calc(100% - 2.5rem)}

/* 黑色切角卡：每頁一到兩張的重點 */
.qsum,.pv,.rec,.vd,.led .lr:first-of-type{
 background:#141414!important;color:#f1f1f1;border:0!important;box-shadow:none!important;
 clip-path:polygon(0 0,calc(100% - 22px) 0,100% 22px,100% 100%,22px 100%,0 calc(100% - 22px))}

/* 側欄數字：細線格 */
.nums{gap:1px;background:#141414;border:1px solid #141414;border-top-width:5px}
.nums div{background:var(--paper);padding:.8rem .9rem;border:0;box-shadow:none}

/* ── 首頁 ── */
.doc{padding-top:1.4rem}
#pipeline{background:#141414;color:#f1f1f1}
#pipeline .ftab{color:#f1f1f1}
#pipeline h2{color:#f1f1f1}
#pipeline h2 .hl,.js #pipeline h2 .hl{color:var(--hl);background:none}
#pipeline .step{border-top-color:#3a3a3a;color:#f1f1f1}
#pipeline .step p{color:#b5b5b5}
#pipeline .step .eg{color:#9a9a9a}
#pipeline .step .n{background:var(--hl);color:#141414}
#pipeline .mini{color:#141414}
#pipeline .meter{background:#141414;border:1.5px solid #5a5a5a;color:#f1f1f1}
#pipeline .meter .lbl,#pipeline .meter .hint{color:#9a9a9a}
#pipeline .meter b{color:var(--hl)}
#pipeline .meter .track{background:#3a3a3a}
#pipeline .meter .track s{background:#f1f1f1}
#pipeline .meter .lv{color:#b5b5b5;border-color:#9a9a9a}
#pipeline .meter.lo .lv{color:#7fd6a0;border-color:#7fd6a0}
#pipeline .meter.mid .lv{color:#ffb25c;border-color:#ffb25c}
#pipeline .meter.hi .lv{color:#ff8a78;border-color:#ff8a78}
#pipeline .meter.lo .track i{background:#7fd6a0}
#pipeline .meter.mid .track i{background:#ffb25c}
#pipeline .meter.hi .track i{background:#ff8a78}
@media(min-width:1000px){
 .scrolly{align-items:stretch}
 .stage{position:sticky;top:var(--stick);height:calc(100svh - var(--stick));display:flex;flex-direction:column;justify-content:center;align-self:start;transition:top .28s ease,height .28s ease}
 .stage .meter{margin-top:1.8rem}
}
@media(max-width:999px){.stage{background:#141414}}
.qmail{margin:1.4rem 0 1.2rem}
.qres.on{margin-top:.8rem}
.qsum{padding:1.5rem 1.6rem}
.qsum b{color:var(--hl)}
.qsum p{color:#b5b5b5}
.qsum .btn{background:#f1f1f1;color:#141414;border-color:#f1f1f1}
.qsum .btn .key{background:#141414;color:#f1f1f1}
.qsum .btn.o{background:transparent;color:#f1f1f1}
.qsum .btn.o .key{background:#f1f1f1;color:#141414}
.qsum .btn:hover{background:var(--hl);color:#141414}
.mt-ds{display:inline-block;margin-top:1.8rem;background:#141414;color:#f1f1f1;padding:.4rem 1rem .4rem .8rem;font:12px var(--mono);clip-path:polygon(0 0,calc(100% - 12px) 0,100% 12px,100% 100%,0 100%)}
.bigstats{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));border-top:5px solid #141414;margin-top:1.4rem}
@media(min-width:900px){.bigstats{grid-template-columns:repeat(4,minmax(0,1fr))}}
.bs{padding:1.1rem 1.2rem 1.4rem;border-bottom:1.5px solid #141414;border-right:1px solid #141414}
.bs:last-child{border-right:0}
@media(max-width:899px){.bs:nth-child(2n){border-right:0}}
.bs .k{display:block;font:600 11.5px var(--mono);letter-spacing:.08em;text-transform:uppercase;color:#4a4a4a}
.bs b{display:block;font-family:var(--serif);font-weight:900;font-size:clamp(2.6rem,6vw,4.8rem);line-height:1.05;margin-top:.5rem}
.bs b .cu{background:linear-gradient(transparent 62%,var(--hl) 62%)}
.bs b i{font-style:normal;font-size:.4em;margin-left:.1em}
.bs .bb{margin-top:1rem;max-width:none;background:#e2e2e2;height:5px}
.bs .bb::after{background:#141414}
.js .mt4.in .bb::after{transform:scaleX(1)}
.mt4 + .note{margin-top:1.6rem}
.clear{background:#fff;border-top:1.5px solid #141414;border-bottom:1.5px solid #141414}
@media(min-width:900px){.clear .wrap>div:last-child{border-left:2px solid #141414;padding-left:2.5rem}}

/* ── 規則頁：色帶索引卡 ── */
:is(#kwcards,#url + .cards,#html + .cards){display:grid;grid-template-columns:repeat(auto-fill,minmax(min(19rem,100%),1fr));gap:1.2rem;border-top:0}
:is(#kwcards,#url + .cards,#html + .cards) .card{
 --cc:#e2e2e2;display:grid;grid-template-columns:auto minmax(0,1fr) auto;grid-template-rows:auto auto 1fr;
 column-gap:.7rem;row-gap:0;align-items:center;padding:0;
 background:#fff!important;border:1.5px solid #141414!important;box-shadow:none!important}
:is(#kwcards,#url + .cards,#html + .cards) .card[data-gi="0"]{--cc:#ffb6d5}
:is(#kwcards,#url + .cards,#html + .cards) .card[data-gi="1"]{--cc:#ffe58a}
:is(#kwcards,#url + .cards,#html + .cards) .card[data-gi="2"]{--cc:#bfe0ff}
:is(#kwcards,#url + .cards,#html + .cards) .card[data-gi="3"]{--cc:#c5ecd2}
:is(#kwcards,#url + .cards,#html + .cards) .card::before{content:"";grid-row:1;grid-column:1 / -1;align-self:stretch;background:var(--cc);border-bottom:1.5px solid #141414}
:is(#kwcards,#url + .cards,#html + .cards) .card .rid{grid-row:1;grid-column:1;padding:.6rem 0 .6rem .85rem;font-size:1.7rem;line-height:1}
:is(#kwcards,#url + .cards,#html + .cards) .card h3{grid-row:1;grid-column:2;padding:.6rem 0;margin:0}
:is(#kwcards,#url + .cards,#html + .cards) .card .st{grid-row:1;grid-column:3;position:static!important;margin:0 .8rem 0 0;align-self:center;transform:rotate(-2deg);background:rgba(255,255,255,.6);max-width:none;font-size:.66rem}
:is(#kwcards,#url + .cards,#html + .cards) .card p{grid-row:2;grid-column:1 / -1;padding:.8rem .85rem 0;margin:0}
:is(#kwcards,#url + .cards,#html + .cards) .card .kws{grid-row:3;grid-column:1 / -1;align-self:start;padding:.6rem .85rem .95rem;margin:0}
:is(#kwcards,#url + .cards,#html + .cards) .card .ex{grid-row:4;grid-column:1 / -1;margin:0 .85rem .9rem}
.card.xp:hover{background:#fafafa!important}
.card.open{outline:2px solid #141414;outline-offset:2px;background:#fff!important}
.fz .box{border:0!important;background:transparent!important;box-shadow:none!important;border-top:5px solid #141414!important;padding:.9rem 0 0!important}
.dz-main>.box{border:0!important;border-top:5px solid #141414!important;background:transparent!important;box-shadow:none!important;padding-left:0!important;padding-right:0!important}

/* ── 貼上頁 ── */
.mail{margin-top:1.2rem}
.pv{padding:1.1rem 1.2rem}
.pv .lb,.pv .nt,#pv{color:#9a9a9a}
#pv.has{color:#f1f1f1}
.pm{color:#b5b5b5}
.pm .tk{background:#3a3a3a;border-color:#5a5a5a}
.pm .tk i{background:var(--hl)}

/* ── 掃描中 ── */
.slip.dn{background:#fff!important;border:1.5px solid #141414!important;border-top:7px solid var(--flap,#9a9a9a)!important;box-shadow:none!important}
.slip.now{background:#fff;border:1.5px solid #141414;box-shadow:none}
.slip.dn .ln{background:#e2e2e2}
.slip.lv-h{--flap:#c8321e}.slip.lv-m{--flap:#e39a2d}.slip.lv-l{--flap:#2e6a4d}.slip.lv-w{--flap:#9a9a9a}

/* ── 掃描記錄：列表 ── */
.heat{margin:0 0 1.8rem}
.heat .hl2{font:11.5px var(--mono);color:#4a4a4a;margin-bottom:.6rem}
.heat .hg{display:flex;flex-wrap:wrap;gap:.35rem}
.heat .hc{width:2rem;height:2rem;border:1.5px solid #141414;background:rgba(200,50,30,var(--a));cursor:pointer;padding:0;border-radius:0;animation:pdIn .35s ease both;animation-delay:calc(var(--i) * .03s)}
.heat .hc:hover{outline:2px solid #141414;outline-offset:2px}
.led{border-top:5px solid #141414}
.lr{position:relative;background:transparent!important;border:0!important;border-bottom:1px solid #141414!important;border-left:6px solid #2e6a4d!important;box-shadow:none!important;padding:1rem 1.4rem 1rem 1rem;margin:0}
.lr.lv-h{border-left-color:#c8321e!important}
.lr.lv-m{border-left-color:#e39a2d!important}
.lr:hover{background:#ececec!important}
.lr .tg{position:absolute;right:1rem;bottom:.5rem;font:600 14px var(--mono);color:#6b6b6b}
.led .lr:first-of-type{margin:1.1rem 0 1.5rem;padding:1.2rem 1.5rem 1.2rem 1.3rem;border-left:0!important}
.led .lr:first-of-type:hover{background:#141414!important}
.led .lr:first-of-type .tg{color:#9a9a9a}
.led .lr:first-of-type .st{mix-blend-mode:normal;background:#f1f1f1}
.led .lr:first-of-type .bar3{border-color:#f1f1f1}
.led .lr:first-of-type .mrow .tx,.led .lr:first-of-type .sk{color:#b5b5b5}
.led .lr:first-of-type .mrow .tk{background:#3a3a3a}
.lr.flash{animation:lrflash 1.1s ease}
@keyframes lrflash{0%,60%{outline:3px solid var(--hl);outline-offset:5px}100%{outline:3px solid transparent;outline-offset:5px}}

/* ── 白名單：預設白、自訂黑 ── */
.pass{display:grid!important;grid-template-columns:minmax(0,1fr) auto auto;grid-template-rows:auto auto;column-gap:.7rem;row-gap:.1rem;align-items:center;
 background:#fff!important;border:1.5px solid #141414!important;box-shadow:none!important;padding:.7rem .9rem .75rem!important;color:#141414}
.pass .dn{grid-column:1;grid-row:1;font-weight:700}
.pass .dt{grid-column:1;grid-row:2;font-size:.72rem;color:#6b6b6b}
.pass::after{content:"預設";grid-column:2;grid-row:1 / 3;font:600 10px var(--mono);color:#6b6b6b;border:1px solid #6b6b6b;padding:0 .4rem;line-height:1.7}
.pass .x{grid-column:3;grid-row:1 / 3;position:static!important;margin:0}
.pass .st{display:none}
.pass .dn::before{content:"";display:inline-block;width:.55rem;height:.55rem;background:#2e6a4d;margin-right:.55rem}
.pass.custom{background:#141414!important;border:0!important;color:#f1f1f1;clip-path:polygon(0 0,calc(100% - 12px) 0,100% 12px,100% 100%,12px 100%,0 calc(100% - 12px))}
.pass.custom .dt{color:#9a9a9a}
.pass.custom::after{content:"自訂";background:var(--hl);color:#141414;border:0}
.pass.custom .dn::before{background:var(--hl)}
.pass.custom .x{color:#f1f1f1}
.ck{margin-top:1.2rem}

/* ── 結果頁 ── */
.email-item{background:transparent!important;border:0!important;border-bottom:1px solid #d4d4d4!important;border-left:6px solid #9a9a9a!important;box-shadow:none!important;padding:.75rem .8rem;margin:0}
.email-item:has(.dot-high){border-left-color:#c8321e!important}
.email-item:has(.dot-med){border-left-color:#e39a2d!important}
.email-item:has(.dot-low){border-left-color:#2e6a4d!important}
.email-item:hover{background:#e2e2e2!important}
.email-item.active{background:#141414!important;color:#f1f1f1}
.email-item.active:hover{background:#141414!important}
.email-item.active .item-from{color:#9a9a9a}
.email-item.active .item-reason{color:#b5b5b5}
.email-item .risk-dot{display:none}
.vd{padding:1.6rem 1.8rem 1.5rem;margin-top:.8rem}
.vd .ftab{color:#f1f1f1}
.vd .tg span{color:#141414}
.vd-subj{color:#fff}
.vd-from{color:#9a9a9a}
.vscore{color:var(--hl)}
.vscore small{color:#9a9a9a}
.vd .stamp-lg{mix-blend-mode:normal;background:#f1f1f1;animation-name:stampvd}
@keyframes stampvd{from{opacity:0;transform:rotate(14deg) scale(2.2)}to{opacity:1;transform:rotate(-6deg) scale(1)}}
@media(prefers-reduced-motion:reduce){.vd .stamp-lg{animation:none}}
.vd .cn{border-color:#f1f1f1;color:#f1f1f1}
.vd .cn:hover{background:var(--hl);color:#141414}
.lgrid{grid-template-columns:repeat(4,minmax(0,1fr));gap:0;border-top:5px solid #141414;border-bottom:1.5px solid #141414}
.lc{background:transparent!important;border:0!important;border-right:1px solid #141414!important;box-shadow:none!important;padding:.9rem 1rem 1.1rem}
.lc:last-child{border-right:0!important}
.lc.lv-hi .bar-fill{background:#c8321e}
.lc.lv-mid .bar-fill{background:#e39a2d}
.lc.lv-lo .bar-fill{background:#2e6a4d}
.lc.hot{background:#ececec!important}
@media(max-width:900px){.lgrid{grid-template-columns:repeat(2,minmax(0,1fr))}.lc:nth-child(2n){border-right:0!important}.lc{border-bottom:1px solid #141414!important}}
.rec{padding:1.2rem 1.5rem}

/* ===== 骨架 v2：記錄、規則改全寬；白名單左右分割；短頁不放大標題 ===== */
.dz-short .sh{margin-top:0;display:block}
.dz-short .sh::before,.dz-short .sh .n,.dz-short .sh h2{display:none}
.dz-short .sh:not(:has(p)){display:none}
.dz-short .sh p{margin:0 0 .8rem}
@media(min-width:1000px){
 .dz-wide{grid-template-columns:minmax(0,1fr)}
 .dz-wide>.dz-side{position:static;height:auto;overflow:visible;border-right:0;border-bottom:1.5px solid #141414;
  padding:2.2rem clamp(1.25rem,4vw,3.5rem) 1.9rem;display:grid;grid-template-columns:minmax(0,1.15fr) minmax(0,1fr);column-gap:3.5rem;align-items:center}
 .dz-wide>.dz-side .pg-title{margin-bottom:.8rem}
 .dz-wide>.dz-side .nums{margin-top:0}
 .dz-wide>.dz-side .br>*:first-child{margin-top:0}
 .dz-wide>.idx{position:sticky;top:var(--stick);z-index:20;display:flex;gap:2rem;margin:0;padding:0 clamp(1.25rem,4vw,3.5rem);overflow-x:auto;background:#f1f1f1;border-bottom:1.5px solid #141414;transition:top .28s ease}
  .dz-wide>.idx a{flex:none;border-top:0;padding:.85rem 0;white-space:nowrap}
 .dz-wide>.dz-main{padding-top:2.2rem}
 .dz-split .dz-main{display:grid;grid-template-columns:minmax(0,1.1fr) minmax(0,1fr);column-gap:3.5rem;align-items:start}
 .dz-split .dz-main>.sh:first-child{grid-column:1;grid-row:1;margin-top:0}
 .dz-split .dz-main>.ck{grid-column:1;grid-row:2}
 .dz-split .dz-main>.ck ~ .sh{grid-column:2;grid-row:1;margin-top:0}
 .dz-split .dz-main>.cards{grid-column:2;grid-row:2;grid-template-columns:repeat(auto-fill,minmax(14rem,1fr))}
}
@media(max-width:999px){.dz-wide>.idx{margin:1rem 1.25rem 0;display:block}}
/* 三頁標題帶（規則／白名單／案件簿）：墨黑底 */
.dz-wide>.dz-side{background:#141414;color:#f1f1f1}
.dz-wide>.dz-side .ftab{color:#f1f1f1}
.dz-wide>.dz-side .pg-title{color:#f1f1f1}
.dz-wide>.dz-side .pg-title .hl{background:var(--hl);color:#141414;padding:.02em .18em}
.dz-wide>.dz-side .pg-sub{color:#d0d0d0}
.dz-wide>.dz-side .nums{display:block;background:none;border:0}
.dz-wide>.dz-side .nums>div{position:relative;display:grid;grid-template-columns:3.6rem minmax(0,1fr) 38%;align-items:center;column-gap:.9rem;padding:.55rem 0;border-top:1px solid #5f5f5f;background:none}
.dz-wide>.dz-side .nums b{color:var(--hl);font-size:1.75rem;line-height:1}
.dz-wide>.dz-side .nums span{color:#d0d0d0;grid-column:2}
.dz-wide>.dz-side .nums>div:not([data-bar]) span{grid-column:2 / -1}
.dz-wide>.dz-side .nums>div.hb::before,.dz-wide>.dz-side .nums>div.hb::after{content:"";position:absolute;right:0;top:50%;width:38%;height:6px;margin-top:-3px}
.dz-wide>.dz-side .nums>div.hb::before{background:#3a3a3a}
.dz-wide>.dz-side .nums>div.hb::after{background:var(--bc,#ffb6d5);transform:scaleX(var(--p,0));transform-origin:left}
.dz-wide>.dz-side .nums>div:has(b[style*="c8321e"]){--bc:#ff8a78}
.dz-wide>.dz-side .nums>div:has(b[style*="a8650f"]){--bc:#ffb25c}
/* 統計列入場（播放型）：預設可見，列先逐列登錄，條再粗線描出 */
.dz-wide>.dz-side .nums>div.in{animation:rowIn .42s ease backwards;animation-delay:calc(var(--ni,0) * .09s)}
.dz-wide>.dz-side .nums>div.in::after{animation:barDraw .6s cubic-bezier(.3,.7,.3,1) backwards;animation-delay:calc(var(--ni,0) * .09s + .35s)}
@media (prefers-reduced-motion: reduce){.dz-wide>.dz-side .nums>div.in,.dz-wide>.dz-side .nums>div.in::after{animation:none}}
.dz-wide>.dz-side .lb{color:#f1f1f1}
.dz-wide>.dz-side .side-form input{border-color:#f1f1f1}
body .dz-wide>.dz-side .add-btn{background:var(--hl);color:#141414;border-color:var(--hl)}
body .dz-wide>.dz-side .add-btn:hover{background:#f1f1f1;border-color:#f1f1f1}
.dz-wide>.dz-side .rst{color:#f1f1f1;border-color:#f1f1f1}
.dz-wide>.dz-side .rst:hover{background:var(--hl);color:#141414;border-color:var(--hl)}
.dz-wide>.dz-side .nums b[style*="c8321e"]{color:#ff8a78!important}
.dz-wide>.dz-side .nums b[style*="a8650f"]{color:#ffb25c!important}
.dz-wide>.dz-side .spark{color:#d0d0d0}
.dz-wide>.dz-side .spark .ax{stroke:#d0d0d0}
.dz-wide>.dz-side .spark .area{fill:rgba(255,138,120,.18)}
.dz-wide>.dz-side .spark .ln{stroke:#ff8a78}
/* 記錄頁：熱度格是主視覺 */
.heat .hg{display:grid;grid-template-columns:repeat(auto-fill,minmax(3.2rem,4.6rem));gap:.45rem}
.heat .hc{width:auto;height:3.6rem}
.heat .hl2{font-size:12px;margin-bottom:.8rem}

/* ===== 首頁節奏：斜貼的標籤膠帶、猜猜看靠右 ===== */
.tick{position:relative;z-index:6;width:calc(100% + 6rem);margin:-1.1rem -3rem -1.1rem;transform:rotate(-1.2deg);background:var(--hl);border-top:1.5px solid #141414;border-bottom:1.5px solid #141414;padding:.5rem 0;overflow:hidden;white-space:nowrap;font:600 12px var(--mono);letter-spacing:.32em;color:#141414}
@media(max-width:700px){.tick{transform:rotate(-.8deg);margin-top:-.6rem;margin-bottom:-.6rem}}
@media(min-width:1100px){.quiz{margin-left:auto}}

/* ===== 證據剪報（規則頁）：撕邊的信紙碎片，上面是真的釣魚句子 ===== */
:is(#kwcards,#url + .cards,#html + .cards){filter:drop-shadow(0 7px 9px rgba(0,0,0,.17));gap:1.7rem 1.5rem}
:is(#kwcards,#url + .cards,#html + .cards) .card{
 --rot:-1deg;grid-template-rows:auto auto auto 1fr;background:#fdfdfe!important;border:0!important;
 transform:rotate(var(--rot));transition:transform .2s ease;
 clip-path:polygon(0 0,100% 0,100% calc(100% - 8px),95% 100%,90% calc(100% - 6px),84% 100%,78% calc(100% - 7px),72% 100%,66% calc(100% - 5px),60% 100%,54% calc(100% - 7px),47% 100%,41% calc(100% - 5px),35% 100%,29% calc(100% - 7px),22% 100%,16% calc(100% - 5px),9% 100%,4% calc(100% - 7px),0 calc(100% - 3px))}
:is(#kwcards,#url + .cards,#html + .cards) .card:nth-child(3n+2){--rot:.8deg;
 clip-path:polygon(0 0,100% 0,100% calc(100% - 4px),93% calc(100% - 1px),88% 100%,81% calc(100% - 6px),75% calc(100% - 2px),69% 100%,62% calc(100% - 7px),56% calc(100% - 3px),50% 100%,43% calc(100% - 6px),37% calc(100% - 2px),31% 100%,24% calc(100% - 7px),17% calc(100% - 3px),11% 100%,5% calc(100% - 6px),0 calc(100% - 2px))}
:is(#kwcards,#url + .cards,#html + .cards) .card:nth-child(3n){--rot:-.5deg;
 clip-path:polygon(0 0,100% 0,100% calc(100% - 6px),96% 100%,91% calc(100% - 3px),85% calc(100% - 8px),79% 100%,73% calc(100% - 4px),67% calc(100% - 7px),60% 100%,54% calc(100% - 3px),48% calc(100% - 8px),42% 100%,36% calc(100% - 4px),30% calc(100% - 7px),23% 100%,17% calc(100% - 3px),10% calc(100% - 8px),5% 100%,0 calc(100% - 5px))}
:is(#kwcards,#url + .cards,#html + .cards) .card:hover{transform:rotate(0) translateY(-3px)}
:is(#kwcards,#url + .cards,#html + .cards) .card .clip{grid-row:2;grid-column:1 / -1;padding:.95rem 1rem .35rem;font:13.5px/1.95 var(--sans);color:#141414}
:is(#kwcards,#url + .cards,#html + .cards) .card .clip.code{font:12px/1.8 var(--mono);word-break:break-all}
.clip[role="button"]{cursor:pointer}
.clip mark{background:#ffb6d5;color:#141414;padding:.02em .12em}
.clip mark[data-g="0"]{background:#ffc3dc}.clip mark[data-g="1"]{background:#ffe58a}.clip mark[data-g="2"]{background:#bfe0ff}.clip mark[data-g="3"]{background:#c5ecd2}
:is(#kwcards,#url + .cards,#html + .cards) .card p{grid-row:3;padding:.1rem 1rem 1.25rem;font-size:11.5px;color:#4a4a4a}
:is(#kwcards,#url + .cards,#html + .cards) .card .kws{grid-row:4;align-self:end;border-top:1px dashed #b5b5b5;margin:.8rem 1rem 0;padding:.55rem 0 1.3rem}
.card .kws span{font-size:10px;padding:0 .3em}
:is(#kwcards,#url + .cards,#html + .cards) .card:has(.kws) p{padding-bottom:0}
@media (prefers-reduced-motion: reduce){:is(#kwcards,#url + .cards,#html + .cards) .card{transition:none}}

/* ===== 簽證章頁（白名單）：每個網域是一枚蓋在通行頁上的章 ===== */
.dz-split .dz-main>.cards{display:flex;flex-wrap:wrap;align-items:center;gap:.4rem 1.1rem;background:#fafafa repeating-linear-gradient(135deg,rgba(0,0,0,.028) 0 1px,transparent 1px 8px);border:1px dashed #b5b5b5;padding:1.5rem 1.3rem 1.7rem;position:relative}
.dz-split .dz-main>.cards::before{content:"PASSPORT　通行頁";position:absolute;left:1rem;top:.55rem;font:600 9.5px var(--mono);letter-spacing:.22em;color:#9a9a9a}
.cards .pass{display:block!important;position:relative;background:transparent!important;border:0!important;box-shadow:none!important;padding:0!important;clip-path:none!important;color:#2e6a4d;transform:rotate(var(--r,0deg));margin-top:calc(var(--j,0) * 1px);animation:none}
.cards .pass.custom{color:#2b3a67;background:transparent!important}
.cards .pass::after,.cards .pass .dn::before{content:none!important}
.cards .pass .dn,.cards .pass .dt,.cards .pass .st{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
.stamp-svg{display:block}
.stamp-svg svg{display:block;width:9.6rem;height:auto;overflow:visible}
.stamp-svg svg[data-shape="circle"]{width:7rem}
.stamp-svg g{mix-blend-mode:multiply}
.cards .pass .x{position:absolute!important;top:-6px;right:-4px;width:22px;height:22px;border:0;border-radius:50%;background:#141414;color:#fff;font-size:13px;line-height:22px;padding:0;margin:0;opacity:0;transition:opacity .15s;z-index:3;cursor:pointer}
.cards .pass:hover .x,.cards .pass:focus-within .x{opacity:1}
@media(hover:none){.cards .pass .x{opacity:.85}}
.cards .pass.new .stamp-svg svg{animation:stampDown .55s cubic-bezier(.2,1.6,.4,1) backwards}
@keyframes stampDown{from{opacity:0;transform:scale(2.6) rotate(18deg)}}
.cards .pass.gone{animation:passOut .28s ease-in forwards}
@media (prefers-reduced-motion: reduce){.cards .pass.new .stamp-svg svg{animation:none}.cards .pass .x{transition:none}}

/* ===== 手寫批註：只出現在信紙上 ===== */
.hw{font-family:"Klee One","Kaiti TC","BiauKai","DFKai-SB","KaiTi",cursive;color:#2b3a67;font-size:1.02rem;line-height:1.5;transform:rotate(-3deg);pointer-events:none;position:absolute;z-index:2;text-align:left}
.doc .hw{right:1.7rem;top:5.2rem;max-width:9.5rem;animation:hwIn .9s ease-out 3.3s backwards}
.qmail .hw{right:1.5rem;top:3.4rem;max-width:15rem;animation:hwIn .8s ease-out .85s backwards}
@keyframes hwIn{from{clip-path:inset(0 100% 0 0);opacity:.2}to{clip-path:inset(0 0 0 0);opacity:1}}
@media(max-width:760px){.doc .hw,.qmail .hw{display:none}}
@media (prefers-reduced-motion: reduce){.doc .hw,.qmail .hw{animation:none}}

/* ===== 動效 v2：每個動作都在說一件事（描線、塗銷、滑入、蓋章、登錄） ===== */
/* 小節標題：粗線描出後，編號與標題才出現 */
.js .sh.pre::before{transform:scaleX(0)}
.js .sh.pre>*{opacity:0}
.sh.in::before{transform-origin:left;animation:barDraw .5s cubic-bezier(.3,.7,.3,1) backwards}
.sh.in>.n,.sh.in>h2,.sh.in>p{animation:shIn .3s ease-out .32s backwards}
@keyframes barDraw{from{transform:scaleX(0)}}
@keyframes shIn{from{opacity:0}}
/* 規則卡：色帶像被塗上去 */
.js .card.pre::before{transform:scaleX(0)}
.card.in::before{transform-origin:left;animation:barDraw .55s cubic-bezier(.3,.7,.3,1) backwards;animation-delay:calc(var(--ri,0) * .07s)}
/* 記錄列：逐列登錄（墨水由左掃過） */
.js .lr.pre{opacity:0}
.lr.in{animation:rowIn .42s ease backwards;animation-delay:calc(var(--ri,0) * .07s)}
@keyframes rowIn{from{opacity:0;clip-path:inset(0 100% 0 0)}}
.led .lr:first-of-type.in{animation-name:shIn}
.lr.in.flash{animation:lrflash 1.1s ease}
.email-item.reg{animation:regIn .4s cubic-bezier(.3,.7,.3,1) backwards;animation-delay:calc(var(--ri,0) * .06s)}
@keyframes regIn{from{opacity:0;clip-path:inset(0 100% 0 0)}}
/* 信紙：滑進桌面（首頁、猜猜看、結果頁原信） */
@keyframes paperIn{from{opacity:0;transform:translateX(70px) rotate(4deg)}}
@keyframes paperR{from{opacity:0;transform:translateX(70px) rotate(4deg)}}
@keyframes paperL{from{opacity:0;transform:translateX(-70px) rotate(-4deg)}}
@keyframes shk{25%{transform:translate(-2px,1px) rotate(-1deg)}50%{transform:translate(2px,-1px) rotate(-1deg)}75%{transform:translate(-1px,0) rotate(-1deg)}}
@keyframes shk2{25%{transform:translate(-2px,1px)}50%{transform:translate(2px,-1px)}75%{transform:translate(-1px,0)}}
@keyframes qIn{from{opacity:0;transform:translateX(70px) rotate(4deg)}to{opacity:1;transform:none}}
.qmail.in{animation:qIn .55s cubic-bezier(.2,.8,.2,1) both}
.qmail.shake{animation:shk2 .32s .4s}
.mdoc.pin-r{animation:paperR .55s cubic-bezier(.2,.8,.2,1) backwards}
.mdoc.pin-l{animation:paperL .55s cubic-bezier(.2,.8,.2,1) backwards}
/* 首頁示意郵件：信紙滑入 → 塗銷 → 標記 → 蓋章 → 輕震 */
.doc{animation:paperIn .55s cubic-bezier(.2,.8,.2,1) backwards,shk .3s 2.95s}
.doc .bar{background:linear-gradient(#141414,#141414) no-repeat left center/100% 100%;transition:background-size .25s ease}
.doc .bar:hover{background:linear-gradient(#141414,#141414) no-repeat left center/0 100%;color:#141414}
.js .doc .bar{animation:redact .55s cubic-bezier(.7,0,.3,1) var(--rd,.7s) backwards}
.doc dd .bar{--rd:.7s}
.doc mark .bar{--rd:1.05s}
@keyframes redact{from{background-size:0 100%}}
mark.m{animation-delay:calc(var(--i) * .3s + .8s)}
.stamp{animation-delay:2.5s}
@media (prefers-reduced-motion: reduce){
 .doc,.qmail.in,.qmail.shake,.mdoc.pin-l,.mdoc.pin-r,.sh.in::before,.sh.in>.n,.sh.in>h2,.sh.in>p,.card.in::before,.lr.in,.email-item.reg,.js .doc .bar{animation:none}
 .js .sh.pre::before{transform:none}.js .sh.pre>*{opacity:1}.js .card.pre::before{transform:none}.js .lr.pre{opacity:1}
}
@media (prefers-reduced-motion: reduce){.heat .hc,.lr.flash{animation:none}.stage{transition:none}}
</style>
"""

COMMON_JS = """
<style>
:root{--stick:var(--hh,3rem)}
html.hdr-hide{--stick:0px}
#pgbar{position:fixed;left:0;top:0;height:3px;width:100%;background:#ff6fae;transform:scaleX(0);transform-origin:left;z-index:200;pointer-events:none}
body .hdr{position:sticky;top:0;z-index:100;transition:transform .28s ease}
html.hdr-hide body .hdr{transform:translateY(-100%)}
html.hdr-hide body .hdr:focus-within{transform:none}
@media(min-width:1000px){.dz-side{top:var(--stick);height:calc(100svh - var(--stick));transition:top .28s ease,height .28s ease}}
html{scroll-padding-top:4rem}
html,body{overflow-x:clip}
@keyframes pdPop{from{transform:scale(.4) rotate(-12deg);opacity:0}to{transform:none;opacity:1}}
.js footer.f .big span{background:linear-gradient(var(--hl),var(--hl)) no-repeat;background-size:0 100%;transition:background-size .8s cubic-bezier(.3,.7,.3,1) .1s}
.js footer.f.in .big span{background-size:100% 100%}
[data-parallax]{translate:0 var(--py,0px)}
.pd-toasts{position:fixed;right:1.2rem;bottom:1.2rem;z-index:300;display:flex;flex-direction:column;gap:.5rem;max-width:min(24rem,calc(100vw - 2.4rem))}
.pd-toast{background:#141414;color:var(--paper);font:12.5px/1.6 var(--mono);padding:.65rem .9rem;border-left:5px solid var(--hl);display:flex;gap:.8rem;align-items:center;animation:pdIn .28s cubic-bezier(.2,1.2,.4,1) both;transition:opacity .25s,transform .25s}
.pd-toast.err{border-left-color:#c8321e}.pd-toast.ok{border-left-color:#2e6a4d}
.pd-toast.out{opacity:0;transform:translateY(8px)}
.pd-toast button{margin-left:auto;background:transparent;border:1px solid var(--paper);color:var(--paper);font:inherit;padding:.1rem .5rem;cursor:pointer;border-radius:0}
.pd-toast button:hover{background:var(--hl);color:#141414}
@keyframes pdIn{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:none}}
.pd-help{position:fixed;inset:0;z-index:400;background:rgba(20,20,20,.55);display:none;align-items:center;justify-content:center;padding:1rem}
.pd-help.on{display:flex}
.pd-help .box{background:var(--paper);border:1px solid #141414;max-width:30rem;width:100%;padding:1.4rem 1.6rem;box-shadow:8px 8px 0 #141414;font-family:var(--mono)}
.pd-help h3{font-family:var(--serif);font-weight:900;font-size:1.5rem;margin-bottom:.8rem}
.pd-help ul{list-style:none;margin:0;padding:0}
.pd-help li{display:flex;align-items:center;gap:1rem;padding:.45rem 0;border-top:1px solid #d4d4d4;font-size:12.5px}
.pd-help li kbd.k{flex:none;min-width:2.2rem}
.pd-help .ft{margin-top:.8rem;color:#6b6b6b;font-size:11px}
@media(prefers-reduced-motion:reduce){body .hdr,.dz-side,.js footer.f .big span{transition:none}.pd-toast{animation:none}}
#sender-input:focus-visible,#subject-input:focus-visible,#body-input:focus-visible{outline:2px solid #141414;outline-offset:-2px;background-color:rgba(255,182,213,.22)}
@media print{ #pgbar,.pd-toasts,.pd-help{display:none}}
</style>
<script>
(function(){
var html=document.documentElement;html.classList.add('js');
var RM=!!(window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches);
var HAS_IO='IntersectionObserver' in window;
function all(s,c){return Array.prototype.slice.call((c||document).querySelectorAll(s));}
function esc(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
function onView(els,cb,th){
  if(RM||!HAS_IO){els.forEach(function(e,i){cb(e,i);});return;}
  var io=new IntersectionObserver(function(es){es.forEach(function(en){if(en.isIntersecting){io.unobserve(en.target);cb(en.target,els.indexOf(en.target));}});},{threshold:th||.25});
  els.forEach(function(e){io.observe(e);});
}
function tween(a,b,ms,fn){
  if(RM){fn(b);return;}
  var t0=null;
  function step(t){if(t0===null)t0=t;var p=Math.min((t-t0)/ms,1),e=1-Math.pow(1-p,3);fn(a+(b-a)*e);if(p<1)requestAnimationFrame(step);}
  requestAnimationFrame(step);
}
/* 關鍵字比對：與後端 analysis._kw_hit 規則一致（lowStr 已轉小寫、w 已轉小寫） */
function isL(c){return !!c&&c>='a'&&c<='z';}
function kwAt(low,i,w){
  if(!w||low.substr(i,w.length)!==w)return false;
  if(/^[a-z ]+$/.test(w)){
    if(isL(low.charAt(i-1)))return false;
    if(w.length<=4&&isL(low.charAt(i+w.length)))return false;
  }
  return true;
}
var toastBox=null;
function toast(msg,o){
  o=o||{};
  if(!toastBox){toastBox=document.createElement('div');toastBox.className='pd-toasts';toastBox.setAttribute('role','status');toastBox.setAttribute('aria-live','polite');document.body.appendChild(toastBox);}
  var t=document.createElement('div');t.className='pd-toast '+(o.type||'');
  var sp=document.createElement('span');sp.textContent=msg;t.appendChild(sp);
  function close(){t.classList.add('out');setTimeout(function(){if(t.parentNode)t.parentNode.removeChild(t);},260);}
  var act=o.action||(o.undo?{label:'復原',fn:o.undo}:null);
  if(act){var b=document.createElement('button');b.type='button';b.textContent=act.label;b.addEventListener('click',function(){act.fn();close();});t.appendChild(b);}
  toastBox.appendChild(t);
  setTimeout(close,o.ms||(o.undo?6000:3200));
  return close;
}
/* 快捷鍵說明 */
var keyRows=[['H','首頁'],['S','授權 Google 送檢'],['P','貼信送檢'],['W','白名單'],['R','偵測規則'],['L','案件簿'],['?','開啟 / 關閉這份說明'],['Esc','關閉']];
var help=null;
function buildHelp(){
  help=document.createElement('div');help.className='pd-help';help.setAttribute('role','dialog');help.setAttribute('aria-modal','true');help.setAttribute('aria-label','鍵盤快捷鍵');
  help.innerHTML='<div class="box"><h3>鍵盤快捷鍵</h3><ul>'+keyRows.map(function(r){return '<li><kbd class="k">'+esc(r[0])+'</kbd><span>'+esc(r[1])+'</span></li>';}).join('')+'</ul><p class="ft">在輸入框內打字時，快捷鍵不會觸發。</p></div>';
  help.addEventListener('click',function(e){if(e.target===help)help.classList.remove('on');});
  document.body.appendChild(help);
}
function toggleHelp(){if(!help)buildHelp();help.classList.toggle('on');}
document.addEventListener('keydown',function(e){
  if(e.key==='Escape'&&help)help.classList.remove('on');
  if(e.key!=='?'||e.metaKey||e.ctrlKey||e.altKey)return;
  var t=e.target,tn=t&&t.tagName;
  if(tn==='INPUT'||tn==='TEXTAREA'||tn==='SELECT'||(t&&t.isContentEditable))return;
  e.preventDefault();toggleHelp();
});
window.PD={RM:RM,all:all,esc:esc,onView:onView,tween:tween,kwAt:kwAt,toast:toast,
  addKeys:function(rows){keyRows=keyRows.slice(0,6).concat(rows,keyRows.slice(6));if(help){help.parentNode.removeChild(help);help=null;}}};
/* 捲動：進度線、標題列收合、視差 */
document.addEventListener('DOMContentLoaded',function(){
  var bar=document.createElement('div');bar.id='pgbar';bar.setAttribute('aria-hidden','true');document.body.appendChild(bar);
  var hdr=document.querySelector('.hdr');
  function setHH(){if(hdr)html.style.setProperty('--hh',hdr.offsetHeight+'px');}
  setHH();window.addEventListener('resize',setHH);
  var px=all('[data-parallax]'),last=window.scrollY,tick=false,spyFn=null;
  function par(){px.forEach(function(el){var r=el.getBoundingClientRect();if(r.bottom<-200||r.top>innerHeight+200)return;el.style.setProperty('--py',((r.top+r.height/2-innerHeight/2)*-parseFloat(el.getAttribute('data-parallax'))).toFixed(1)+'px');});}
  function frame(){
    var y=window.scrollY,h=html.scrollHeight-innerHeight;
    bar.style.transform='scaleX('+(h>0?Math.min(y/h,1):0)+')';
    if(!RM){if(y>last+6&&y>120)html.classList.add('hdr-hide');else if(y<last-6||y<60)html.classList.remove('hdr-hide');}
    last=y;if(!RM)par();if(spyFn)spyFn();tick=false;
  }
  window.addEventListener('scroll',function(){if(!tick){tick=true;requestAnimationFrame(frame);}},{passive:true});
  frame();
  /* 入場動作（取代淡入上浮）：標題粗線描出、規則卡色帶、記錄列逐列登錄。
     只有「首屏之外」的元素會先收起，其餘立即播放；動態產生而沒被登記的元素維持可見，不會消失。 */
  var batch=0,bt=null;
  function arm(sel){
    all(sel).forEach(function(el){
      if(el.classList.contains('armed'))return;
      el.classList.add('armed');
      var play=function(){el.style.setProperty('--ri',Math.min(batch,7));batch++;clearTimeout(bt);bt=setTimeout(function(){batch=0;},120);el.classList.remove('pre');el.classList.add('in');};
      if(RM||!HAS_IO){el.classList.add('in');return;}
      if(el.getBoundingClientRect().top>innerHeight*0.92){el.classList.add('pre');onView([el],play,.2);}else{play();}
    });
  }
  PD.arm=arm;
  /* 標題帶統計列的比例條：max＝同組最大值為滿；share＝占「郵件總數」的比例（須在數字滾動歸零之前讀值） */
  all('.dz-wide>.dz-side .nums').forEach(function(box){
    var val=function(d){var b=d.querySelector('b');return b?(parseInt(b.textContent,10)||0):0;};
    var rows=all('div[data-bar]',box),tot=box.querySelector('div[data-role="total"]'),mx=1,tv=tot?val(tot):0;
    rows.forEach(function(r){if(r.getAttribute('data-bar')==='max')mx=Math.max(mx,val(r));});
    rows.forEach(function(r){
      var v=val(r),den=r.getAttribute('data-bar')==='share'?tv:mx;
      if(!den)return;
      r.style.setProperty('--p',Math.min(1,Math.max(v?0.04:0,v/den)).toFixed(3));
      r.classList.add('hb');
    });
  });
  all('.dz-wide>.dz-side .nums>div').forEach(function(r,i){r.style.setProperty('--ni',i);r.classList.add('in');});
  arm('.dz-main .sh');arm('.dz-main .cards .card');arm('.dz-main .led .lr');
  /* 側欄數字滾動 */
  all('.nums b').forEach(function(b){
    if(b.id||!/^[0-9]+$/.test(b.textContent.trim()))return;
    var to=parseInt(b.textContent,10);if(!to)return;
    b.textContent='0';
    onView([b],function(){PD.tween(0,to,900,function(x){b.textContent=Math.round(x);});},.5);
  });
  /* 目錄高亮（scrollspy，依捲動位置計算，點錨點跳轉也會亮） */
  var links=all('.idx a[href^="#"]');
  if(links.length){
    var secs=links.map(function(a){return[a,document.getElementById(a.getAttribute('href').slice(1))];}).filter(function(p){return p[1];});
    spyFn=function(){
      var y=innerHeight*0.3,cur=secs[0];
      secs.forEach(function(p){if(p[1].getBoundingClientRect().top<=y)cur=p;});
      if(window.innerHeight+window.scrollY>=html.scrollHeight-4)cur=secs[secs.length-1];
      links.forEach(function(a){a.classList.toggle('on',!!cur&&a===cur[0]);});
    };
    spyFn();
  }
  /* 頁尾大字螢光掃過 */
  var ft=document.querySelector('footer.f');
  if(ft)onView([ft],function(){ft.classList.add('in');},.3);
});
})();
</script>
<style>
/* ── 全站質感層（方案 C）：換頁黑幕、游標環、按壓蓋章、焦點外框 ── */
.pdx{position:fixed;inset:0;z-index:9500}
.pdx-w{position:absolute;inset:0;background:#141414;clip-path:inset(0 100% 0 0);animation:pdxWipe .25s cubic-bezier(.7,0,.2,1) forwards}
.pdx-e{position:absolute;top:0;bottom:0;left:0;width:6px;background:var(--hl,#ffb6d5);animation:pdxEdge .25s cubic-bezier(.7,0,.2,1) forwards}
@keyframes pdxWipe{to{clip-path:inset(0)}}
@keyframes pdxEdge{to{transform:translateX(100vw)}}
.pdc{position:fixed;left:0;top:0;width:18px;height:18px;margin:-9px 0 0 -9px;border:2px solid #141414;border-radius:50%;box-shadow:0 0 0 1px #fff;pointer-events:none;z-index:9600;opacity:0;transition:width .18s ease,height .18s ease,margin .18s ease,background-color .18s ease,opacity .15s ease;will-change:transform}
.pdc.on{opacity:1}
.pdc.hov{width:34px;height:34px;margin:-17px 0 0 -17px;background:rgba(255,182,213,.55)}
.pdc.dn{width:12px;height:12px;margin:-6px 0 0 -6px;background:#141414}
.pdc.txt{opacity:0}
.btn,.submit-btn,.add-btn,.rst,.acr,.ivb{position:relative;overflow:hidden;isolation:isolate}
.pdp{transform:translateY(2px);transition:transform .08s ease}
.pdr{position:absolute;width:12px;height:12px;margin:-6px 0 0 -6px;background:#141414;opacity:.3;z-index:-1;pointer-events:none;animation:pdrOut .4s cubic-bezier(.2,.7,.2,1) forwards}
.pdr.dk{background:#ffb6d5;opacity:.9}
@keyframes pdrOut{to{transform:scale(18);opacity:0}}
kbd.k.hit,.key.hit{background:var(--hl,#ffb6d5)!important;color:#141414!important}
a:focus-visible,button:focus-visible,summary:focus-visible,select:focus-visible,[tabindex]:not([tabindex="-1"]):focus-visible{outline:2px solid #141414;outline-offset:3px;box-shadow:0 0 0 5px #fff}
.btn:focus-visible,.submit-btn:focus-visible,.add-btn:focus-visible{background:var(--hl,#ffb6d5);color:#141414;outline-offset:-5px;box-shadow:none}
@media (prefers-reduced-motion: reduce){.pdr{display:none}.pdp{transform:none;transition:none}.pdc{transition:none}}
</style>
<script>
(function () {
  if (!window.PD) return;
  const RM = PD.RM, root = document.documentElement;
  let cover = null;
  function stamp() { try { sessionStorage.setItem('pdSx', String(Date.now())); } catch (e) {} }
  function drop() { if (cover && cover.parentNode) cover.parentNode.removeChild(cover); cover = null; }
  function leave(href, delay) {
    if (cover) return;
    stamp();
    cover = document.createElement('div'); cover.className = 'pdx'; cover.setAttribute('aria-hidden', 'true');
    cover.innerHTML = '<i class="pdx-w"></i><i class="pdx-e"></i>';
    document.body.appendChild(cover);
    setTimeout(function () { location.href = href; }, delay || 250);
    setTimeout(function () { drop(); try { sessionStorage.removeItem('pdSx'); } catch (e) {} }, 3000);
  }
  function go(href) { if (RM) { location.href = href; return; } leave(href, 250); }
  function flash(k) {
    const L = String(k || '').toUpperCase();
    let el = null;
    document.querySelectorAll('.hdr-nav kbd.k').forEach(function (e) { if (e.textContent === L) el = e; });
    if (!el && /^[a-z]$/i.test(String(k))) el = document.querySelector('[data-key="' + String(k).toLowerCase() + '"] .key');
    if (el) el.classList.add('hit');
  }
  function key(k, href) {
    let same = false;
    try { same = new URL(href, location.href).pathname === location.pathname; } catch (e) {}
    if (RM || same) { location.href = href; return; }
    flash(k); leave(href, 300);
  }
  window.PDX = { stamp: stamp, go: go, key: key };
  document.addEventListener('click', function (e) {
    if (RM || e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    const a = e.target.closest && e.target.closest('a[href]');
    if (!a || (a.target && a.target !== '_self') || a.hasAttribute('download')) return;
    let u; try { u = new URL(a.href, location.href); } catch (err) { return; }
    if (u.origin !== location.origin || (u.pathname === location.pathname && u.search === location.search)) return;
    e.preventDefault(); leave(u.href, 250);
  });
  window.addEventListener('pageshow', function (e) { if (e.persisted) { drop(); root.classList.remove('sxin'); } });
  const PRESS = '.btn,.submit-btn,.add-btn,.rst,.acr,.ivb';
  document.addEventListener('pointerdown', function (e) {
    if (e.button !== 0) return;
    const b = e.target.closest && e.target.closest(PRESS);
    if (!b || b.disabled || b.classList.contains('busy')) return;
    b.classList.add('pdp');
    if (!RM) {
      const r = b.getBoundingClientRect(), i = document.createElement('i');
      const bg = (getComputedStyle(b).backgroundColor.match(/[0-9.]+/g) || []).map(Number);
      const dark = bg.length >= 3 && (bg.length < 4 || bg[3] > 0.5) && (bg[0] * 0.299 + bg[1] * 0.587 + bg[2] * 0.114) < 110;
      i.className = dark ? 'pdr dk' : 'pdr'; i.setAttribute('aria-hidden', 'true');
      i.style.left = (e.clientX - r.left) + 'px'; i.style.top = (e.clientY - r.top) + 'px';
      b.appendChild(i); setTimeout(function () { if (i.parentNode) i.parentNode.removeChild(i); }, 450);
    }
    const up = function () { b.classList.remove('pdp'); document.removeEventListener('pointerup', up, true); document.removeEventListener('pointercancel', up, true); };
    document.addEventListener('pointerup', up, true); document.addEventListener('pointercancel', up, true);
  }, true);
  document.addEventListener('DOMContentLoaded', function () {
    if (RM || !window.matchMedia || !window.matchMedia('(hover: hover) and (pointer: fine)').matches) return;
    const ring = document.createElement('div'); ring.className = 'pdc'; ring.setAttribute('aria-hidden', 'true'); document.body.appendChild(ring);
    const CLICK = 'a[href],button,[role="button"],summary,label[for],select,input[type="submit"],input[type="button"],input[type="checkbox"],input[type="radio"]';
    const TEXT = 'input:not([type="submit"]):not([type="button"]):not([type="checkbox"]):not([type="radio"]):not([type="range"]),textarea,[contenteditable="true"]';
    let x = -100, y = -100, rx = -100, ry = -100, vis = false, raf = 0;
    function loop() {
      rx += (x - rx) * 0.28; ry += (y - ry) * 0.28;
      ring.style.transform = 'translate3d(' + rx.toFixed(1) + 'px,' + ry.toFixed(1) + 'px,0)';
      raf = (Math.abs(x - rx) > 0.1 || Math.abs(y - ry) > 0.1) ? requestAnimationFrame(loop) : 0;
    }
    document.addEventListener('pointermove', function (e) {
      if (e.pointerType !== 'mouse') return;
      x = e.clientX; y = e.clientY;
      if (!vis) { rx = x; ry = y; vis = true; ring.classList.add('on'); }
      if (!raf) raf = requestAnimationFrame(loop);
      const t = e.target;
      ring.classList.toggle('txt', !!(t.closest && t.closest(TEXT)));
      ring.classList.toggle('hov', !!(t.closest && t.closest(CLICK)));
    }, { passive: true });
    root.addEventListener('mouseleave', function () { vis = false; ring.classList.remove('on'); });
    document.addEventListener('pointerdown', function (e) { if (e.pointerType === 'mouse') ring.classList.add('dn'); }, true);
    document.addEventListener('pointerup', function () { ring.classList.remove('dn'); }, true);
    document.addEventListener('pointercancel', function () { ring.classList.remove('dn'); }, true);
  });
})();
</script>
"""
COMMON_CSS += COMMON_JS
DESIGN_CSS = ""
COMMON_CSS += DESIGN_CSS

def kw_json(rule_keyword_groups):
    """規則關鍵字清單（供前端預檢／原信批註比對用，已做 script 安全跳脫）。"""
    return json.dumps(rule_keyword_groups, ensure_ascii=False).replace(
        '<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')


def finish(html, title):
    """為頁面插入 DESIGN2_CSS（置於最後一個 </style> 後）並補上 <title>。
    與舊版 templates.py 檔尾的後處理邏輯完全相同。"""
    i = html.rfind("</style>") + len("</style>")
    html = html[:i] + DESIGN2_CSS + html[i:]
    return html.replace('<meta name="viewport" content="width=device-width, initial-scale=1">',
                        '<meta name="viewport" content="width=device-width, initial-scale=1">\n<title>' + title + '</title>', 1)
