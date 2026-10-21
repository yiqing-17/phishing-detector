"""HTML page templates and rendering helpers."""
import json

# ── CSS 共用樣式 (全站統一風格：極簡工程風／終端機質感，黑白為主) ───────────────────
COMMON_CSS = """
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#141414">
<meta name="description" content="結合規則、機器學習、URL／HTML 解析與 AI 語意判讀，找出可疑信件。">
<meta property="og:type" content="website">
<meta property="og:title" content="phishing-detector">
<meta property="og:description" content="授權 Gmail 或直接貼信，四層分析逐層比對，找出可疑信件。">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' fill='%23ffb6d5'/%3E%3Ctext x='16' y='25' font-size='25' font-family='Georgia,serif' font-weight='900' text-anchor='middle' fill='%23141414'%3Ep%3C/text%3E%3C/svg%3E">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700;800&family=Noto+Sans+TC:wght@400;500;700&family=Noto+Serif+TC:wght@700;900&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Klee+One:wght@400;600&display=swap">
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
.nums span { font-family: var(--mono); font-size: 11px; color: var(--text-muted); }
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
    if(h)location.href=h;
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
:is(#kwcards,#url + .cards,#html + .cards){display:grid;grid-template-columns:repeat(auto-fill,minmax(19rem,1fr));gap:1.2rem;border-top:0}
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
.vd .stamp-lg{mix-blend-mode:normal;background:#f1f1f1}
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
 .dz-wide>.idx li{list-style:none;flex:none}
 .dz-wide>.idx a{border-top:0;padding:.85rem 0;white-space:nowrap}
 .dz-wide>.dz-main{padding-top:2.2rem}
 .dz-split .dz-main{display:grid;grid-template-columns:minmax(0,1.1fr) minmax(0,1fr);column-gap:3.5rem;align-items:start}
 .dz-split .dz-main>.sh:first-child{grid-column:1;grid-row:1;margin-top:0}
 .dz-split .dz-main>.ck{grid-column:1;grid-row:2}
 .dz-split .dz-main>.ck ~ .sh{grid-column:2;grid-row:1;margin-top:0}
 .dz-split .dz-main>.cards{grid-column:2;grid-row:2;grid-template-columns:repeat(auto-fill,minmax(14rem,1fr))}
}
@media(max-width:999px){.dz-wide>.idx{margin:1rem 1.25rem 0;display:block}}
/* 記錄頁：熱度格是主視覺 */
.heat .hg{display:grid;grid-template-columns:repeat(auto-fill,minmax(3.2rem,4.6rem));gap:.45rem}
.heat .hc{width:auto;height:3.6rem}
.heat .hl2{font-size:12px;margin-bottom:.8rem}

/* ===== 首頁節奏：斜貼的標籤膠帶、猜猜看靠右 ===== */
.tick{position:relative;z-index:6;width:calc(100% + 6rem);margin:-1.1rem -3rem -1.1rem;transform:rotate(-1.2deg);background:var(--hl);border-top:1.5px solid #141414;border-bottom:1.5px solid #141414;padding:.5rem 0;overflow:hidden;white-space:nowrap;font:600 12px var(--mono);letter-spacing:.32em;color:#141414}
@media(max-width:700px){.tick{transform:rotate(-.8deg);margin-top:-.6rem;margin-bottom:-.6rem}}
@media(min-width:1100px){.quiz{margin-left:auto}}

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
"""
COMMON_CSS += COMMON_JS
DESIGN_CSS = ""
COMMON_CSS += DESIGN_CSS

HOME_HTML = COMMON_CSS + """
<style>
html,body{background:var(--paper);color:#141414;font-family:var(--sans);-webkit-font-smoothing:antialiased;scroll-behavior:smooth}
.wrap{max-width:1360px;margin:0 auto;padding:0 2rem}
.mono{font-family:var(--mono)}
.hero{padding:clamp(2.5rem,7vh,5rem) 0 clamp(3rem,8vh,6rem)}
.hero .wrap{display:grid;gap:3rem;align-items:center}
@media(min-width:1000px){.hero .wrap{grid-template-columns:1fr 1.02fr;gap:3rem;min-height:calc(100svh - 3rem - 8rem)}}
h1{font-family:var(--serif);font-weight:900;font-size:clamp(2.3rem,4.7vw,4.4rem);line-height:1.2;letter-spacing:-.01em;text-wrap:balance}
h1 .hl{background:linear-gradient(transparent 56%,var(--hl) 56%)}
.sub{margin-top:1.5rem;max-width:36rem;color:#4a4a4a;font-size:16px;line-height:1.85}
.cta{margin-top:2.25rem;display:flex;flex-direction:column;gap:.6rem;max-width:30rem}
.btn{display:flex;align-items:center;justify-content:space-between;gap:1rem;padding:.7rem .8rem;border:1px solid #141414;background:#141414;color:var(--paper);font-family:var(--mono);font-size:12.5px;text-decoration:none;transition:background .15s,color .15s}
.btn.o{background:transparent;color:#141414}
.btn .key{display:flex;align-items:center;justify-content:center;min-width:1.35rem;height:1.35rem;background:var(--paper);color:#141414;font-weight:600;font-size:11px;text-transform:uppercase}
.btn.o .key{background:#141414;color:var(--paper)}
.btn:hover{background:var(--hl);color:#141414}.btn:hover .key{background:#141414;color:var(--paper)}
/* 被批註的示意郵件 */
.docwrap{position:relative}
.doc{position:relative;background:#fff;border:1px solid #141414;padding:1.75rem 1.9rem 1.5rem;font-family:var(--mono);font-size:13.5px;line-height:2;transform:rotate(-1deg);box-shadow:0 22px 34px -26px rgba(20,20,20,.55)}
.doc dl{margin:0 0 1rem;padding-bottom:1rem;border-bottom:1px solid #d4d4d4}
.doc dl div{display:grid;grid-template-columns:4.2em 1fr;gap:.5rem}
.doc dt{color:#6b6b6b;font-size:11.5px;letter-spacing:.06em}
.doc dd{margin:0;word-break:break-all}
.doc p{margin:0 0 .6rem;font-family:var(--sans);font-size:15px;line-height:2.1}
mark.m{position:relative;color:#141414;background:linear-gradient(var(--hl),var(--hl)) no-repeat;background-size:100% 100%;padding:.05em .12em;cursor:default;animation:draw .55s cubic-bezier(.3,.7,.3,1) both;animation-delay:calc(var(--i) * .38s + .3s)}
mark.m::after{content:attr(data-n);position:relative;top:-.7em;margin-left:.15em;display:inline-grid;place-items:center;width:1.25em;height:1.25em;border-radius:50%;background:#141414;color:var(--paper);font:600 10px/1 var(--mono)}
@keyframes draw{from{background-size:0% 100%}to{background-size:100% 100%}}
.bar{display:inline-block;background:#141414;color:#141414;padding:0 .2em;transition:background .2s,color .2s;user-select:none;cursor:help}
.bar:hover{background:transparent;color:#141414}
.notes{margin:1.1rem 0 0;padding:1rem 0 0;border-top:1px dashed #9a9a9a;list-style:none;font-family:var(--sans);font-size:13px;line-height:1.7;color:#4a4a4a}
.notes li{display:flex;gap:.65rem;padding:.12rem 0;transition:color .15s}
.notes li b{flex:none;display:grid;place-items:center;width:1.25rem;height:1.25rem;margin-top:.2rem;border-radius:50%;background:#141414;color:var(--paper);font:600 10px/1 var(--mono)}
.notes li.on{color:#141414}.notes li.on span{background:var(--hl)}
.stamp{position:absolute;right:-1.1rem;top:-1.6rem;z-index:2;padding:.2rem .75rem .25rem;border:3px solid #c8321e;color:#c8321e;text-align:center;font-family:var(--serif);font-weight:900;font-size:1.7rem;line-height:1.15;transform:rotate(9deg);mix-blend-mode:multiply;background:rgba(250,248,243,.35);animation:stamp .45s cubic-bezier(.2,1.7,.4,1) 2.1s both}
.stamp small{display:block;font-family:var(--mono);font-size:.62rem;letter-spacing:.2em;font-weight:600}
@keyframes stamp{from{opacity:0;transform:rotate(22deg) scale(2.4)}to{opacity:.92;transform:rotate(9deg) scale(1)}}
.cap{margin-top:1.1rem;font-family:var(--mono);font-size:11px;color:#6b6b6b}
@media(prefers-reduced-motion:reduce){mark.m,.stamp{animation:none}.stamp{opacity:.92}}
/* sections */
.sec{border-top:1px solid #141414;padding:clamp(3rem,8vh,5.5rem) 0}
h2{font-family:var(--serif);font-weight:900;font-size:clamp(1.8rem,3.4vw,3rem);line-height:1.25;margin-top:.4rem;max-width:26ch;text-wrap:balance}
h2 .hl{white-space:nowrap}
.rows{margin-top:2.5rem}
.row{display:grid;grid-template-columns:3.2rem 1fr;gap:.2rem 1rem;padding:1.4rem 0;border-top:1px solid #d4d4d4}
.row:last-child{border-bottom:1px solid #d4d4d4}
@media(min-width:800px){.row{grid-template-columns:3.2rem 15rem 1fr 1fr;align-items:baseline}}
.row p,.row .eg{grid-column:2}
@media(min-width:800px){.row p,.row .eg{grid-column:auto}}
.row .n{display:grid;place-items:center;width:1.9rem;height:1.9rem;border-radius:50%;background:#141414;color:var(--paper);font:600 12px/1 var(--mono)}
.row h3{font-family:var(--serif);font-weight:700;font-size:1.3rem}
.row p{color:#4a4a4a;font-size:14.5px}
.row .eg{font-family:var(--mono);font-size:12px;color:#6b6b6b}
.row .eg mark{background:var(--hl);color:#141414;padding:0 .3em}
table.m{width:100%;border-collapse:collapse;margin-top:2.25rem;font-family:var(--mono);font-size:12.5px}
table.m th{background:#141414;color:var(--paper);text-align:left;font-weight:500;padding:.65rem .9rem}
table.m td{padding:.65rem .9rem;border-bottom:1px solid #d4d4d4;vertical-align:top}
.tw{overflow-x:auto}
.note{margin-top:.8rem;font-family:var(--mono);font-size:11.5px;color:#6b6b6b;max-width:64ch;line-height:1.7}
.clear{background:#e2e2e2;border-top:1px solid #141414;border-bottom:1px solid #141414}
.clear .wrap{display:grid;gap:2rem 4rem;align-items:center;padding-top:clamp(3rem,8vh,5rem);padding-bottom:clamp(3rem,8vh,5rem)}
@media(min-width:900px){.clear .wrap{grid-template-columns:1.25fr 1fr}}
.clear h2{margin-top:.4rem;max-width:none}
.clear .stamp2{display:inline-block;margin-left:1rem;vertical-align:middle;border:3px solid #2e6a4d;color:#2e6a4d;padding:.1rem .6rem;font-family:var(--serif);font-weight:900;font-size:1.05rem;line-height:1.3;transform:rotate(-6deg);mix-blend-mode:multiply;white-space:nowrap}
.clear .stamp2 small{display:block;font-family:var(--mono);font-size:.5rem;letter-spacing:.2em;font-weight:600;text-align:center}
.clear p.t{font-size:15px;line-height:1.9;color:#4a4a4a;max-width:34ch}
.clear .acts{display:flex;flex-wrap:wrap;gap:.6rem;margin-top:1.4rem}
.clear .btn{min-width:11.5rem}
footer.f{margin-top:0;padding:3rem 2rem 2.25rem}
/* ── 互動強化 ─────────────────────────────── */
.doc{transition:transform .2s ease-out}
.stamp{cursor:pointer}
.stamp:focus-visible,mark.m:focus-visible,.row:focus-visible{outline:2px solid #141414;outline-offset:2px}
mark.m[data-n="3"]{cursor:pointer;text-decoration:underline dotted;text-underline-offset:3px}
.status{margin-top:.9rem;padding:.35rem .6rem;border:1px solid #d4d4d4;background:#e9e9e9;font-family:var(--mono);font-size:11.5px;line-height:1.7;color:#6b6b6b;min-height:3.6em;transition:background .15s,border-color .15s,color .15s;word-break:break-all}
.status.on{background:rgba(200,50,30,.07);border-color:rgba(200,50,30,.45);color:#141414}
.status .k{color:#6b6b6b}.status .u{color:#c8321e;font-weight:600}
.status .x{display:inline-block;margin-left:.4rem;background:#c8321e;color:#fff;padding:0 .35rem}
/* h2 螢光筆掃過 */
.js h2 .hl{background-image:linear-gradient(transparent 56%,var(--hl) 56%);background-repeat:no-repeat;background-size:0% 100%;transition:background-size .7s cubic-bezier(.3,.7,.3,1) .15s}
.js h2.in .hl{background-size:100% 100%}
/* 捲動敘事：郵件固定、四層逐層帶出 */
.scrolly{margin-top:2.5rem;display:grid;gap:1.5rem}
@media(min-width:1000px){.scrolly{grid-template-columns:minmax(0,1.05fr) minmax(0,.95fr);gap:3rem}}
.stage{position:sticky;top:calc(var(--stick) + 1.2rem);align-self:start;z-index:2;transition:top .28s ease}
.mini{position:relative;background:#fff;border:1px solid #141414;padding:1.3rem 1.5rem 1.2rem;font-family:var(--mono);font-size:13px;line-height:2;box-shadow:0 22px 34px -26px rgba(20,20,20,.55)}
.mini dl{margin:0 0 .8rem;padding-bottom:.8rem;border-bottom:1px solid #d4d4d4}
.mini dl div{display:grid;grid-template-columns:4.2em 1fr;gap:.5rem}
.mini dt{color:#6b6b6b;font-size:11.5px}.mini dd{margin:0;word-break:break-all}
.mini .mb{margin:0;font-family:var(--sans);font-size:15px;line-height:2.1;border-radius:2px;transition:background .5s}
.mini.ml .mb{background:rgba(255,182,213,.2)}
.mini [data-l]{background:linear-gradient(var(--hl),var(--hl)) no-repeat;background-size:0 100%;transition:background-size .6s cubic-bezier(.3,.7,.3,1);padding:.05em .12em}
.mini [data-l].on{background-size:100% 100%}
.mini [data-l].on::after{content:attr(data-l);position:relative;top:-.7em;margin-left:.15em;display:inline-grid;place-items:center;width:1.25em;height:1.25em;border-radius:50%;background:#141414;color:var(--paper);font:600 10px/1 var(--mono)}
.mini [data-l="3"]{text-decoration:underline dotted;text-underline-offset:3px}
.mini .status{margin-top:.9rem;min-height:3.4em}
.vstamp{position:absolute;right:-.8rem;top:-1.3rem;z-index:3;padding:.2rem .75rem .25rem;border:3px solid;text-align:center;font-family:var(--serif);font-weight:900;font-size:1.7rem;line-height:1.15;transform:rotate(9deg);mix-blend-mode:multiply;opacity:0}
.vstamp small{display:block;font-family:var(--mono);font-size:.62rem;letter-spacing:.2em;font-weight:600}
.vstamp.red{color:#c8321e;border-color:#c8321e}.vstamp.grn{color:#2e6a4d;border-color:#2e6a4d}
.vstamp.show{animation:vslam .45s cubic-bezier(.2,1.7,.4,1) both}
@keyframes vslam{from{opacity:0;transform:rotate(22deg) scale(2.4)}to{opacity:.92;transform:rotate(9deg) scale(1)}}
.meter{margin-top:1rem;border:1px solid #141414;background:#fff;padding:.9rem 1.1rem;font-family:var(--mono);font-size:12px}
.meter .mt{display:flex;align-items:baseline;gap:.8rem;flex-wrap:wrap}
.meter .lbl{color:#6b6b6b;letter-spacing:.06em}
.meter b{font-family:var(--serif);font-weight:900;font-size:1.9rem;line-height:1;min-width:2ch}
.meter .lv{margin-left:auto;padding:.1rem .55rem;border:2px solid #9a9a9a;color:#6b6b6b;font-weight:600;transition:color .3s,border-color .3s}
.meter.lo .lv{border-color:var(--green);color:var(--green)}
.meter.mid .lv{border-color:var(--orange);color:var(--orange)}
.meter.hi .lv{border-color:var(--red);color:var(--red)}
.meter .track{position:relative;height:8px;background:#e2e2e2;margin-top:.8rem}
.meter .track i{position:absolute;left:0;top:0;bottom:0;width:0;background:var(--green);transition:width .7s cubic-bezier(.2,.7,.2,1),background .3s}
.meter.mid .track i{background:var(--orange)}.meter.hi .track i{background:var(--red)}
.meter .track s{position:absolute;top:-3px;bottom:-3px;width:1px;background:#141414;opacity:.45}
.meter .hint{margin-top:.6rem;color:#6b6b6b;font-size:11px}
.steps{padding-bottom:12vh}
.step{display:grid;grid-template-columns:2.6rem 1fr;gap:.3rem 1rem;align-content:center;min-height:56vh;padding:1.4rem 0;border-top:1px solid #d4d4d4;opacity:.38;transition:opacity .35s,background .15s}
.step.act{opacity:1}
.step:focus-visible{outline:2px solid #141414;outline-offset:2px}
.step .n{grid-row:span 3;display:grid;place-items:center;width:2rem;height:2rem;border-radius:50%;background:#141414;color:var(--paper);font:600 12px/1 var(--mono)}
.step h3{font-family:var(--serif);font-weight:900;font-size:1.7rem}
.step p{color:#4a4a4a;font-size:14.5px}
.step .eg{font-family:var(--mono);font-size:12px;color:#6b6b6b}
.step .eg mark{background:var(--hl);color:#141414;padding:0 .3em}
@media(max-width:999px){.mini{display:none}.stage{top:var(--stick);background:var(--paper);padding:.5rem 0}.meter{margin-top:0}.step{min-height:auto}.steps{padding-bottom:0}}
/* 猜猜看 */
.quiz{margin-top:1.8rem;display:grid;gap:1rem;max-width:58rem}
.qhead{display:flex;justify-content:space-between;font:12px var(--mono);color:#6b6b6b}
.qmail{position:relative;background:#fff;border:1px solid #141414;padding:1.3rem 1.5rem;font-family:var(--mono);font-size:13.5px;line-height:2;box-shadow:0 18px 30px -24px rgba(20,20,20,.5)}
.qmail.in{animation:qIn .4s cubic-bezier(.2,.9,.3,1) both}
@keyframes qIn{from{opacity:0;transform:translateX(26px) rotate(1.5deg)}to{opacity:1;transform:none}}
.qmail dl{margin:0 0 .8rem;padding-bottom:.8rem;border-bottom:1px solid #d4d4d4}
.qmail dl div{display:grid;grid-template-columns:4.2em 1fr;gap:.5rem}
.qmail dt{color:#6b6b6b;font-size:11.5px;letter-spacing:.06em}.qmail dd{margin:0;word-break:break-all}
.qmail p{margin:0;font-family:var(--sans);font-size:15px;line-height:2.1;white-space:pre-wrap}
.qmail .lnk{text-decoration:underline dotted;text-underline-offset:3px;color:#2b4c8c}
.qmail mark{background:var(--hl);color:#141414;padding:.05em .1em}
.qmail mark::after{content:attr(data-r);position:relative;top:-.7em;margin-left:.15em;font:600 9px/1 var(--mono);background:#141414;color:var(--paper);padding:1px 3px}
.qmail .status{margin-top:.9rem;min-height:2.6em}
.qmail .vstamp{right:-.6rem;top:-1.2rem}
.qact{display:grid;gap:.6rem;grid-template-columns:1fr 1fr}
@media(max-width:560px){.qact{grid-template-columns:1fr}}
.qact.off{display:none}
.qres{display:none}
.qres.on{display:block}
.qfb{font-family:var(--serif);font-weight:900;font-size:1.5rem;margin-bottom:.6rem}
.qfb.ok span{background:linear-gradient(transparent 56%,#a9d8bd 56%)}.qfb.no span{background:linear-gradient(transparent 56%,#f2b5a8 56%)}
.layers{list-style:none;margin:0;padding:0;font-family:var(--mono);font-size:12.5px}
.layers li{display:grid;grid-template-columns:1.9rem 8.5rem 1fr;gap:.2rem .8rem;align-items:baseline;padding:.55rem 0;border-top:1px solid #d4d4d4;opacity:0;transform:translateY(8px);transition:opacity .4s,transform .4s}
.layers li.in{opacity:1;transform:none}
.layers li b{display:grid;place-items:center;width:1.5rem;height:1.5rem;border-radius:50%;background:#141414;color:var(--paper);font:600 11px/1 var(--mono)}
.layers li .nm{font-weight:600}
.layers li .ds{color:#4a4a4a;font-family:var(--sans);font-size:13.5px}
.layers li .ds i{font-style:normal;display:inline-block;margin-right:.5rem;padding:0 .4rem;border:1px solid #141414;font:600 11px/1.6 var(--mono)}
.layers li .ds i.hot{background:var(--hl)}.layers li .ds i.cool{background:#dff0e6}
@media(max-width:560px){.layers li{grid-template-columns:1.9rem 1fr}.layers li .ds{grid-column:2}}
.qnext{margin-top:.9rem;display:flex;flex-wrap:wrap;gap:.6rem}
.qnext .btn{min-width:11.5rem}
.qsum{border:1px solid #141414;background:#fff;padding:1.4rem 1.5rem}
.qsum b{font-family:var(--serif);font-weight:900;font-size:3.2rem;line-height:1}
.qsum p{margin-top:.6rem;color:#4a4a4a;line-height:1.8;font-size:14.5px}
@media(prefers-reduced-motion:reduce){.stage,.step,.layers li,.mini [data-l],.meter .track i{transition:none}.qmail.in,.vstamp.show{animation:none}.vstamp.show{opacity:.92}}
/* 數字 + 進度條 */
.bb{display:block;height:4px;background:#e2e2e2;margin-top:.45rem;position:relative;max-width:22rem}
.bb::after{content:"";position:absolute;left:0;top:0;bottom:0;width:var(--w);background:#141414}
.js .bb::after{transform:scaleX(0);transform-origin:left;transition:transform 1.1s cubic-bezier(.2,.7,.2,1)}
.js table.m.in .bb::after{transform:scaleX(1)}
/* 已放行章 */
.js .clear .stamp2{opacity:0}
.clear.in .stamp2{opacity:.92;animation:slam .45s cubic-bezier(.2,1.7,.4,1) .35s both}
@keyframes slam{from{opacity:0;transform:rotate(-18deg) scale(2.2)}to{opacity:.92;transform:rotate(-6deg) scale(1)}}
@media(prefers-reduced-motion:reduce){.doc,.js .row,.js h2 .hl,.meter .track i,.js .bb::after{transition:none}.clear.in .stamp2{animation:none}}
</style>
<div class="hdr"><div class="hdr-left"><a href="/">phishing-detector</a></div><div class="hdr-nav"><a href="/rules">偵測規則</a><a href="/whitelist">白名單</a><a href="/history">案件簿</a><a href="/paste">貼信送檢</a></div></div>
<main>
<section class="hero"><div class="wrap">
  <div>
    <div class="ftab"><mark>FILE</mark><span>四層分析 / 案件檢視</span></div>
    <h1>安全掃描 Gmail，快速找出<span class="hl">可疑</span>郵件</h1>
    <p class="sub">授權 Google 後掃描最新 15 封郵件，結合規則引擎、機器學習、URL / HTML 解析與 AI 語意判讀，快速找出可疑信件。</p>
    <div class="cta">
      <a class="btn" href="/login" data-key="s"><span>授權 Google 送檢</span><span class="key">S</span></a>
      <a class="btn o" href="/paste" data-key="p"><span>不想連接 Gmail？直接貼信送檢</span><span class="key">P</span></a>
    </div>
  </div>
  <div class="docwrap" data-parallax="0.05">
    <div class="stamp" role="button" tabindex="0" aria-label="重播標記動畫" title="點擊重播">可疑<small>SUSPICIOUS</small></div>
    <article class="doc" aria-label="示意郵件">
    <div class="lh">secure-account.example</div>
      <dl>
        <div><dt>寄件者</dt><dd><span class="bar" title="掃描時會一併檢查寄件網域">service</span>@secure-account.example</dd></div>
        <div><dt>主　旨</dt><dd>您的帳戶已被暫停</dd></div>
      </dl>
      <p>親愛的客戶：<br><mark class="m" data-n="2" style="--i:1">我們偵測到您的帳戶有異常登入行為。</mark><br>
      請<mark class="m" data-n="1" style="--i:0">立即</mark>點擊 <mark class="m" data-n="3" style="--i:2" data-url="http://secure-acc0unt-verify.example/login">驗證帳戶</mark>，並<mark class="m" data-n="4" style="--i:3">回覆您的帳號密碼與<span class="bar" title="敏感資訊">信用卡號</span></mark>，否則帳戶將於 <mark class="m" data-n="1" style="--i:0">24 小時內</mark>永久停用。</p>
      <div class="status" id="st">將游標移到「驗證帳戶」上，看它真正會連到哪裡。</div>
      <ul class="notes">
        <li data-n="1"><b>1</b><span>規則引擎：命中急迫語氣</span></li>
        <li data-n="2"><b>2</b><span>ML 模型：整體用詞接近釣魚樣本</span></li>
        <li data-n="3"><b>3</b><span>URL / HTML 解析：顯示文字與實際連結需還原比對</span></li>
        <li data-n="4"><b>4</b><span>AI 語意判讀：索取敏感資訊</span></li>
      </ul>
      <div class="hw" aria-hidden="true">↙ 四個破綻，<br>滑過看看</div>
  </article>
    <p class="cap">示意郵件，非真實案例。滑過標記可對照批註，點擊印章可重播。</p>
  </div>
</div></section>

<div class="tick" aria-hidden="true">SUSPICIOUS　✕　CLEARED　✕　SUSPICIOUS　✕　CLEARED　✕　SUSPICIOUS　✕　CLEARED　✕　SUSPICIOUS　✕　CLEARED　✕　SUSPICIOUS　✕　CLEARED　✕　SUSPICIOUS　✕　CLEARED　✕　SUSPICIOUS　✕　CLEARED　✕　SUSPICIOUS　✕　CLEARED　✕　SUSPICIOUS　✕　CLEARED　✕　</div>

<section class="sec" id="pipeline"><div class="wrap">
  <div class="ftab"><mark>FILE 02</mark><span>pipeline</span></div>
  <h2>四層分析，<span class="hl">逐層</span>交叉比對</h2>
  <div class="scrolly">
    <div class="stage" id="stage">
      <div class="mini" id="mini" aria-hidden="true">
        <div class="lh">secure-account.example</div>
        <dl><div><dt>寄件者</dt><dd>service@secure-account.example</dd></div><div><dt>主　旨</dt><dd>您的帳戶已被暫停</dd></div></dl>
        <p class="mb">親愛的客戶：<span data-l="2">我們偵測到您的帳戶有異常登入行為。</span>請<span data-l="1">立即</span>點擊 <span data-l="3">驗證帳戶</span>，並<span data-l="4">回覆您的帳號密碼與信用卡號</span>，否則帳戶將於 <span data-l="1">24 小時內</span>永久停用。</p>
        <div class="status" id="mstat">第 3 層會把連結還原：顯示文字與真正網址是否一致。</div>
        <div class="vstamp red" id="mstamp">可疑<small>SUSPICIOUS</small></div>
      </div>
      <div class="meter" id="meter" aria-live="polite">
        <div class="mt"><span class="lbl">風險累積（示意）</span><b id="mv">0</b><span class="lv" id="ml">待分析</span></div>
        <div class="track"><i id="mb"></i><s style="left:28%"></s><s style="left:52%"></s><s style="left:76%"></s><s style="left:94%"></s></div>
        <p class="hint">往下捲動，逐層看這封信是怎麼被拆開的。數值為示意，非實際評分公式。</p>
      </div>
    </div>
    <div class="steps" id="steps">
      <article class="step" data-i="1" data-s="28" tabindex="0"><span class="n">1</span><h3>規則引擎</h3><p>已知釣魚樣式與關鍵字比對</p><span class="eg">例：<mark>立即</mark> <mark>24 小時內</mark></span></article>
      <article class="step" data-i="2" data-s="52" tabindex="0"><span class="n">2</span><h3>ML 模型</h3><p>TF-IDF + Logistic Regression</p><span class="eg">例：整體用詞特徵</span></article>
      <article class="step" data-i="3" data-s="76" tabindex="0"><span class="n">3</span><h3>URL / HTML 解析</h3><p>連結還原、追蹤像素、隱藏元素偵測</p><span class="eg">例：<mark>顯示文字</mark> ≠ 實際連結</span></article>
      <article class="step" data-i="4" data-s="94" tabindex="0"><span class="n">4</span><h3>AI 語意判讀</h3><p>交叉比對郵件意圖與敏感資訊索取</p><span class="eg">例：<mark>索取密碼</mark></span></article>
    </div>
  </div>
</div></section>

<section class="sec" id="quiz"><div class="wrap">
  <div class="ftab"><mark>FILE 03</mark><span>猜猜看</span></div>
  <h2>這封信，<span class="hl">你</span>會信嗎？</h2>
  <p class="note">先憑直覺判斷，再看四層分析怎麼拆這封信。範例皆為虛構郵件；第 1 層的命中詞由實際規則詞庫即時比對，其餘三層為預先寫好的示意，並非即時模型輸出。</p>
  <div class="quiz" id="quizbox">
    <div class="qhead"><span id="qn">1 / 5</span><span id="qs">答對 0</span></div>
    <article class="qmail" id="qmail" aria-live="polite"></article>
    <div class="qact" id="qact">
      <button type="button" class="btn o" data-g="safe"><span>看起來安全</span><span class="key">←</span></button>
      <button type="button" class="btn" data-g="phish"><span>這是釣魚信</span><span class="key">→</span></button>
    </div>
    <div class="qres" id="qres" aria-live="polite"></div>
  </div>
</div></section>

<section class="sec" id="metrics"><div class="wrap">
  <div class="ftab"><mark>FILE 04</mark><span>model report</span></div>
  <h2>ML 模型<span class="hl">測試結果</span></h2>
  <div class="mt-ds">資料集　Phishing Email Dataset，清理後 82,077 筆（訓練 65,661 / 測試 16,416）</div>
  <div class="mt4 bigstats">
    <div class="bs"><span class="k">Accuracy</span><b><span class="cu" data-to="98.41">98.41</span><i>%</i></b><span class="bb" style="--w:98.41%"></span></div>
    <div class="bs"><span class="k">Precision</span><b><span class="cu" data-to="98.28">98.28</span><i>%</i></b><span class="bb" style="--w:98.28%"></span></div>
    <div class="bs"><span class="k">Recall</span><b><span class="cu" data-to="98.68">98.68</span><i>%</i></b><span class="bb" style="--w:98.68%"></span></div>
    <div class="bs"><span class="k">F1</span><b><span class="cu" data-to="98.48">98.48</span><i>%</i></b><span class="bb" style="--w:98.48%"></span></div>
  </div>
  <p class="note">以上僅為第 2 層 ML 模型在測試資料上的表現，不代表整體四層系統在真實信箱中的準確率。</p>
</div></section>

<section class="clear"><div class="wrap">
  <div>
    <div class="ftab"><mark>FILE 05</mark><span>whitelist</span></div>
    <h2>白名單機制<span class="hl">已啟用</span><span class="stamp2" aria-hidden="true">已放行<small>CLEARED</small></span></h2>
  </div>
  <div>
    <p class="t">已知安全網域自動略過重複分析。</p>
    <div class="acts">
      <a class="btn" href="/whitelist" data-key="w"><span>查看白名單</span><span class="key">W</span></a>
      <a class="btn o" href="/rules" data-key="r"><span>偵測規則</span><span class="key">R</span></a>
    </div>
  </div>
</div></section>
</main>
<footer class="f"><div class="fi">
  <div class="big"><span>phishing</span>-detector</div>
  <nav><a href="/rules">偵測規則</a><a href="/whitelist">白名單</a><a href="/paste">貼信送檢</a><a href="/login">Google 登入</a></nav>
</div></footer>
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
<script>
(function(){
var root=document.documentElement;root.classList.add('js');
var RM=!!(window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches);
var HAS_IO=('IntersectionObserver' in window);
function all(s,c){return Array.prototype.slice.call((c||document).querySelectorAll(s));}
function esc(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
function onView(els,cb,th){
  if(RM||!HAS_IO){els.forEach(function(e,i){cb(e,i);});return;}
  var io=new IntersectionObserver(function(es){es.forEach(function(en){if(en.isIntersecting){io.unobserve(en.target);cb(en.target,els.indexOf(en.target));}});},{threshold:th||.3});
  els.forEach(function(e){io.observe(e);});
}
function tween(a,b,ms,fn){
  if(RM){fn(b);return;}
  var t0=null;
  function step(t){if(t0===null)t0=t;var p=Math.min((t-t0)/ms,1),e=1-Math.pow(1-p,3);fn(a+(b-a)*e);if(p<1)requestAnimationFrame(step);}
  requestAnimationFrame(step);
}

/* 1. 標記可用鍵盤聚焦；印章可重播；文件跟著游標微傾 */
var doc=document.querySelector('.doc'),dw=document.querySelector('.docwrap'),stamp=document.querySelector('.stamp');
all('mark.m').forEach(function(m){
  m.setAttribute('tabindex','0');
  m.addEventListener('focus',function(){m.dispatchEvent(new Event('mouseenter'));});
  m.addEventListener('blur',function(){m.dispatchEvent(new Event('mouseleave'));});
});
function replay(){
  var els=all('mark.m').concat(stamp?[stamp]:[]);
  els.forEach(function(e){e.style.animation='none';});
  void doc.offsetWidth;
  els.forEach(function(e){e.style.animation='';});
}
if(stamp&&doc){
  stamp.addEventListener('click',replay);
  stamp.addEventListener('keydown',function(e){if(e.key==='Enter'||e.key===' '){e.preventDefault();replay();}});
}
if(doc&&dw&&!RM&&window.matchMedia('(pointer: fine)').matches){
  dw.addEventListener('mousemove',function(e){
    var r=dw.getBoundingClientRect(),x=(e.clientX-r.left)/r.width-.5,y=(e.clientY-r.top)/r.height-.5;
    doc.style.transform='rotate('+(-1+x*1.6).toFixed(2)+'deg) translate('+(x*6).toFixed(1)+'px,'+(y*6).toFixed(1)+'px)';
  });
  dw.addEventListener('mouseleave',function(){doc.style.transform='';});
}

/* 2. 顯示文字 ≠ 實際連結 */
var st=document.getElementById('st'),m3=document.querySelector('mark.m[data-n="3"]');
if(st&&m3){
  var idle=st.innerHTML;
  var show=function(){st.className='status on';st.innerHTML='<span class="k">顯示文字</span> '+esc(m3.textContent)+' <span class="k">→ 實際連結</span> <span class="u">'+esc(m3.getAttribute('data-url'))+'</span><span class="x">不一致</span>';};
  var hide=function(){st.className='status';st.innerHTML=idle;};
  m3.addEventListener('mouseenter',show);m3.addEventListener('mouseleave',hide);
}

/* 3. 標題螢光筆、已放行章 */
onView(all('.sec h2,.clear h2'),function(h){h.classList.add('in');},.6);
var clr=document.querySelector('.clear');
if(clr)onView([clr],function(){clr.classList.add('in');},.45);

/* 4. 捲動敘事 */
var meter=document.getElementById('meter'),mb=document.getElementById('mb'),mv=document.getElementById('mv'),ml=document.getElementById('ml');
var steps=all('#steps .step'),mini=document.getElementById('mini'),mstat=document.getElementById('mstat'),mstamp=document.getElementById('mstamp');
var curStep=0,scrollStep=0,disp=0,tok=0,statIdle=mstat?mstat.innerHTML:'';
function setMeter(v){
  var my=++tok,from=disp;
  mb.style.width=v+'%';
  meter.className='meter'+(v>=70?' hi':v>=35?' mid':v>0?' lo':'');
  ml.textContent=v>=70?'可疑':v>=35?'留意':v>0?'低':'待分析';
  tween(from,v,700,function(x){if(my===tok){disp=x;mv.textContent=Math.round(x);}});
}
function stepScore(i){return i<1?0:+steps[i-1].getAttribute('data-s');}
function act(i,fromScroll){
  if(fromScroll)scrollStep=i;
  if(i===curStep)return;
  curStep=i;
  steps.forEach(function(s,k){s.classList.toggle('act',k+1===i);});
  all('[data-l]',mini).forEach(function(el){el.classList.toggle('on',+el.getAttribute('data-l')<=i);});
  mini.classList.toggle('ml',i>=2);
  if(i>=3){mstat.className='status on';mstat.innerHTML='<span class="k">顯示文字</span> 驗證帳戶 <span class="k">→ 實際連結</span> <span class="u">http://secure-acc0unt-verify.example/login</span><span class="x">不一致</span>';}
  else{mstat.className='status';mstat.innerHTML=statIdle;}
  mstamp.classList.remove('show');
  if(i>=4){void mstamp.offsetWidth;mstamp.classList.add('show');}
  setMeter(stepScore(i));
}
if(meter&&mini&&steps.length){
  steps.forEach(function(s,k){
    var i=k+1;
    s.addEventListener('mouseenter',function(){act(i,false);});
    s.addEventListener('focus',function(){act(i,false);});
    s.addEventListener('mouseleave',function(){act(scrollStep,false);});
    s.addEventListener('blur',function(){act(scrollStep,false);});
  });
  if(RM||!HAS_IO){steps.forEach(function(s){s.classList.add('act');});act(4,true);}
  else{
    var sc=document.querySelector('.scrolly'),pt=false;
    var pick=function(){
      pt=false;
      var sr=sc.getBoundingClientRect();
      if(sr.bottom<0||sr.top>innerHeight){scrollStep=0;act(0,true);return;}
      var r1=steps[0].getBoundingClientRect();
      if(r1.top+r1.height/2>innerHeight*0.9){scrollStep=0;act(0,true);return;}
      var stg=document.getElementById('stage').getBoundingClientRect(),mid=innerWidth>=1000?stg.top+stg.height/2:innerHeight*0.5,best=1,bd=1e9;
      steps.forEach(function(st,k){var r=st.getBoundingClientRect(),d=Math.abs(r.top+r.height/2-mid);if(d<bd){bd=d;best=k+1;}});
      act(best,true);
    };
    window.addEventListener('scroll',function(){if(!pt){pt=true;requestAnimationFrame(pick);}},{passive:true});
    pick();
  }
}

/* 5. 猜猜看 */
var KW=KEYWORDS_PLACEHOLDER;
var qbox=document.getElementById('quizbox');
if(qbox&&KW&&KW.length){
  var groups=KW.map(function(g){var m=/[+]([0-9]+)/.exec(String(g[4]||''));return{id:g[0],name:g[1],words:(g[3]||[]).filter(Boolean).map(function(w){return String(w).toLowerCase();}),w:m?+m[1]:2};});
  var Q=[
   {phish:true,from:'service@twbank-secure.example',hw:'網址和顯示文字不一樣',subj:'【重要】您的帳戶將於 24 小時內凍結',
    body:['親愛的客戶：偵測到您的帳戶有異常登入。請立即點擊「',{l:'登入驗證',u:'http://twbank-secure.example/verify'},'」，輸入帳號與密碼，否則帳戶將被停用。'],
    ml:['hot','偏高','整體用詞接近釣魚樣本'],url:['hot','不一致','連結顯示為銀行登入，實際網域卻是 twbank-secure.example'],ai:['hot','索取憑證','信件要求輸入帳號與密碼']},
   {phish:false,from:'amy.chen@company.example',hw:'沒有連結，也沒有要資料',subj:'週五專案會議改期',
    body:['各位好，','週五的專案會議改到下午三點，議程請見附件。','有問題再跟我說，謝謝。'],
    ml:['cool','偏低','用詞接近一般工作信件'],url:['cool','無連結','內文沒有網址，也沒有隱藏元素'],ai:['cool','意圖正常','只是通知時間變更，沒有索取資訊']},
   {phish:false,from:'receipts@shop.example',hw:'只通知出貨，沒要任何資料',subj:'您的訂單 #A1024 已出貨',
    body:['您的訂單 #A1024 已出貨，預計 2 日內送達。','可到官網「訂單查詢」頁面查看物流，不需要提供任何個人資料。'],
    ml:['cool','偏低','用詞接近訂單通知'],url:['cool','無連結','沒有可點擊的網址'],ai:['cool','意圖正常','單純通知出貨，沒有要求付款或登入']},
   {phish:true,from:'no-reply@parcel-tw.example',hw:'小額運費是常見誘餌',subj:'包裹無法投遞，請補繳運費',
    body:['您的包裹地址不完整，請立即點擊 ',{l:'補繳運費',u:'http://parcel-tw-pay.example/pay'},' 完成付款 NT$25，逾期將退回寄件人。'],
    ml:['hot','偏高','運費補繳類用詞常見於釣魚樣本'],url:['hot','不一致','連結指向 parcel-tw-pay.example，與寄件網域不同'],ai:['hot','誘導付款','以小額運費誘使輸入付款資料']},
   {phish:true,from:'support@paypa1-help.example',hw:'paypa1：數字 1 假扮字母 l',subj:'Action required: your account is suspended',
    body:['Your account has been suspended. Verify now to avoid permanent closure. Enter your password and credit card number at ',{l:'http://paypal.com/login',u:'http://paypa1-help.example/login'},'.'],
    ml:['hot','偏高','用詞接近釣魚樣本'],url:['hot','仿冒網域','paypa1 把字母 l 換成數字 1，且顯示網址與實際不符'],ai:['hot','索取憑證','要求提供密碼與信用卡號']}
  ];
  var qi=0,qok=0,answered=false,visible=false;
  var elMail=document.getElementById('qmail'),elAct=document.getElementById('qact'),elRes=document.getElementById('qres'),elN=document.getElementById('qn'),elS=document.getElementById('qs');
  function hlText(txt,words){
    var low=txt.toLowerCase(),r=[],i,k;
    for(i=0;i<low.length;i++){
      for(k=0;k<groups.length;k++){
        var g=groups[k],hit=null;
        for(var m=0;m<g.words.length;m++){if(PD.kwAt(low,i,g.words[m])&&(!hit||g.words[m].length>hit.length))hit=g.words[m];}
        if(hit){r.push([i,i+hit.length,g.id]);i+=hit.length-1;break;}
      }
    }
    var out='',pos=0;
    r.forEach(function(x){out+=esc(txt.slice(pos,x[0]))+'<mark data-r="'+x[2]+'">'+esc(txt.slice(x[0],x[1]))+'</mark>';pos=x[1];});
    return out+esc(txt.slice(pos));
  }
  function layer1(q){
    var full=('from: '+q.from+' subject: '+q.subj+' body: '+q.body.map(function(p){return typeof p==='string'?p:p.l;}).join('')).toLowerCase(),raw=0,hits=[];
    groups.forEach(function(g){var h=g.words.filter(function(w){for(var i=0;i<full.length;i++){if(PD.kwAt(full,i,w))return true;}return false;});raw+=h.length*g.w;h.forEach(function(w){hits.push(w);});});
    return{raw:raw,hits:hits};
  }
  function showQ(){
    answered=false;var q=Q[qi];
    elN.textContent=(qi+1)+' / '+Q.length;elS.textContent='答對 '+qok;
    elMail.className='qmail';void elMail.offsetWidth;elMail.className='qmail in';
    elMail.innerHTML='<div class="lh">'+esc(q.from.split('@')[1])+'</div><dl><div><dt>寄件者</dt><dd>'+esc(q.from)+'</dd></div><div><dt>主　旨</dt><dd>'+esc(q.subj)+'</dd></div></dl><p>'+q.body.map(function(p){return typeof p==='string'?esc(p):'<span class="lnk">'+esc(p.l)+'</span>';}).join('')+'</p><div class="status" id="qst">將游標移到藍色連結上，看它真正會連到哪裡。</div>';
    var lk=elMail.querySelector('.lnk'),st=document.getElementById('qst'),lq=q.body.filter(function(p){return typeof p!=='string';})[0];
    if(lk&&lq){
      lk.addEventListener('mouseenter',function(){st.className='status on';st.innerHTML='<span class="k">顯示文字</span> '+esc(lq.l)+' <span class="k">→ 實際連結</span> <span class="u">'+esc(lq.u)+'</span>';});
      lk.addEventListener('mouseleave',function(){st.className='status';st.textContent='將游標移到藍色連結上，看它真正會連到哪裡。';});
    }else{st.style.display='none';}
    elAct.className='qact';elRes.className='qres';elRes.innerHTML='';
  }
  function guess(g){
    if(answered)return;answered=true;
    var q=Q[qi],right=(g==='phish')===q.phish;if(right)qok++;
    elS.textContent='答對 '+qok;elAct.className='qact off';
    var l1=layer1(q);
    var bodyHtml=q.body.map(function(p){return typeof p==='string'?hlText(p):'<span class="lnk">'+esc(p.l)+'</span>';}).join('');
    elMail.querySelector('p').innerHTML=bodyHtml;
    elMail.querySelector('dl div:nth-child(2) dd').innerHTML=hlText(q.subj);
    var vs=document.createElement('div');vs.className='vstamp '+(q.phish?'red':'grn');vs.innerHTML=(q.phish?'可疑':'安全')+'<small>'+(q.phish?'SUSPICIOUS':'CLEARED')+'</small>';
    elMail.appendChild(vs);void vs.offsetWidth;vs.classList.add('show');elMail.classList.add('shake');
    var hwEl=document.createElement('div');hwEl.className='hw';hwEl.setAttribute('aria-hidden','true');hwEl.textContent='↙ '+q.hw;elMail.appendChild(hwEl);
    var rows=[
      ['規則引擎',l1.hits.length?'<i class="hot">+'+l1.raw+'</i>命中 '+l1.hits.map(esc).join('、')+'（正規化 '+Math.min(l1.raw*5,100)+'）':'<i class="cool">0</i>沒有命中關鍵字'],
      ['ML 模型','<i class="'+q.ml[0]+'">'+q.ml[1]+'</i>'+esc(q.ml[2])],
      ['URL / HTML','<i class="'+q.url[0]+'">'+q.url[1]+'</i>'+esc(q.url[2])],
      ['AI 語意','<i class="'+q.ai[0]+'">'+q.ai[1]+'</i>'+esc(q.ai[2])]
    ];
    var last=qi===Q.length-1;
    elRes.innerHTML='<div class="qfb '+(right?'ok':'no')+'"><span>'+(right?'猜對了':'差一點')+'</span>　'+(q.phish?'這是釣魚信':'這封是正常信件')+'</div><ul class="layers">'+rows.map(function(r,i){return '<li><b>'+(i+1)+'</b><span class="nm">'+r[0]+'</span><span class="ds">'+r[1]+'</span></li>';}).join('')+'</ul><div class="qnext"><button type="button" class="btn" id="qnext"><span>'+(last?'看結果':'下一封')+'</span><span class="key">→</span></button></div>';
    elRes.className='qres on';
    all('.layers li',elRes).forEach(function(li,i){setTimeout(function(){li.classList.add('in');},PD.RM?0:260*(i+1));});
    document.getElementById('qnext').addEventListener('click',next);
  }
  function next(){
    if(!answered)return;
    if(qi<Q.length-1){qi++;showQ();return;}
    elMail.className='qmail';elMail.innerHTML='';elMail.style.display='none';elAct.className='qact off';
    elN.textContent='完成';
    var msg=qok>=5?'全對。再細微的偽裝，你都看得出來。':qok>=3?'不錯。真正的信件還會混著更多干擾，交給四層分析逐層比對會更穩。':'沒關係，這正是需要四層分析的原因：人眼容易被急迫語氣帶著走。';
    elRes.className='qres on';
    elRes.innerHTML='<div class="qsum"><b>'+qok+' / '+Q.length+'</b><p>'+msg+'</p><div class="qnext"><a class="btn" href="/paste" data-key="p"><span>貼上你的信試試</span><span class="key">P</span></a><a class="btn o" href="/login"><span>授權 Google 送檢</span><span class="key">S</span></a><button type="button" class="btn o" id="qagain"><span>再玩一次</span><span class="key">R</span></button></div></div>';
    document.getElementById('qagain').addEventListener('click',function(){qi=0;qok=0;elMail.style.display='';showQ();});
  }
  all('#qact [data-g]').forEach(function(b){b.addEventListener('click',function(){guess(b.getAttribute('data-g'));});});
  if(HAS_IO){new IntersectionObserver(function(es){visible=es[0].isIntersecting;},{threshold:.2}).observe(qbox);}else{visible=true;}
  document.addEventListener('keydown',function(e){
    if(!visible||e.metaKey||e.ctrlKey||e.altKey)return;
    var tn=e.target&&e.target.tagName;if(tn==='INPUT'||tn==='TEXTAREA'||tn==='SELECT')return;
    if(e.key==='ArrowLeft'&&!answered){e.preventDefault();guess('safe');}
    else if(e.key==='ArrowRight'){e.preventDefault();if(!answered)guess('phish');else next();}
  });
  showQ();
}

/* 6. 模型指標：數字滾動 + 進度條 */
var tbl=document.querySelector('.mt4');
if(tbl){
  var cus=all('.cu',tbl);
  if(HAS_IO&&!RM)cus.forEach(function(el){el.textContent='0.00';});
  onView([tbl],function(){
    tbl.classList.add('in');
    cus.forEach(function(el){var to=parseFloat(el.getAttribute('data-to'));tween(0,to,1100,function(x){el.textContent=x.toFixed(2);});});
  },.35);
}
})();
</script>
"""


def render_home_page(rule_keyword_groups=()):
    """首頁：把規則關鍵字注入第 1 層試玩區（與後端詞庫保持一致）。"""
    return HOME_HTML.replace('KEYWORDS_PLACEHOLDER', _kw_json(rule_keyword_groups))

# ── Loading HTML ─────────────────────────────────────────────
LOADING_HTML = COMMON_CSS + """
<style>
.big3 { font-family: var(--serif); font-weight: 900; font-size: 4.2rem; line-height: 1; margin-top: 1.5rem; }
.big3 small { font-family: var(--mono); font-size: 14px; font-weight: 400; color: #4a4a4a; margin-left: .4rem; }
.el { margin-top: .5rem; font-family: var(--mono); font-size: 12px; color: #6b6b6b; }
.phase { list-style: none; margin: 1.6rem 0 0; padding: 0; font-family: var(--mono); font-size: 12.5px; }
.phase li { display: flex; gap: .7rem; padding: .5rem 0; border-top: 1px solid #d4d4d4; color: #6b6b6b; }
.phase li b { flex: none; display: grid; place-items: center; width: 1.3rem; height: 1.3rem; border-radius: 50%; border: 1px solid currentColor; font-size: 10px; }
.phase li.on { color: #141414; } .phase li.on span { background: var(--hl); }
.phase li.on b { background: #141414; color: #f1f1f1; border-color: #141414; }
.phase li.dn { color: #141414; } .phase li.dn b { background: #2e6a4d; color: #fff; border-color: #2e6a4d; }
.tally { grid-template-columns: repeat(2, 1fr); }
.wall { display: grid; grid-template-columns: repeat(auto-fill, minmax(10rem, 1fr)); gap: 1rem; }
.slip { position: relative; min-height: 8.5rem; padding: .8rem .9rem; background: #fff; border: 1px dashed #9a9a9a; overflow: hidden; transition: border-color .2s; }
.slip .no { font-family: var(--mono); font-size: 11px; color: #6b6b6b; }
.slip .ln { display: block; height: .5rem; margin-top: .6rem; background: #e2e2e2; }
.slip .ln:nth-of-type(2) { width: 82%; } .slip .ln:nth-of-type(3) { width: 64%; }
.slip.now { border: 1px solid #141414; }
.slip.now::after { content: ""; position: absolute; left: -40%; top: 0; bottom: 0; width: 40%; background: linear-gradient(90deg, transparent, rgba(255,182,213,.85), transparent); animation: sweep 1.1s linear infinite; }
@keyframes sweep { to { left: 100%; } }
.slip.dn { border: 1px solid #141414; }
.slip .stp { position: absolute; right: .6rem; bottom: .7rem; padding: .02rem .55rem; border: 2px solid currentColor; font-family: var(--serif); font-weight: 900; font-size: 1rem; line-height: 1.4; transform: rotate(-6deg); mix-blend-mode: multiply; animation: stampin .4s cubic-bezier(.2,1.7,.4,1) both; }
.slip .stp.red { color: #c8321e; } .slip .stp.org { color: #a8650f; } .slip .stp.grn { color: #2e6a4d; } .slip .stp.ink { color: #4a4a4a; }
@keyframes stampin { from { opacity: 0; transform: rotate(14deg) scale(2.2); } to { opacity: .95; transform: rotate(-6deg) scale(1); } }
.slip.empty { border-style: dotted; color: #6b6b6b; }
.note3 { margin-top: 1.4rem; font-family: var(--mono); font-size: 11.5px; line-height: 1.8; color: #6b6b6b; }
@media (prefers-reduced-motion: reduce) { .slip.now::after, .slip .stp { animation: none; } }
.slip.shake{animation:slipshake .38s ease-out}
@keyframes slipshake{0%{transform:translate(0,0)}20%{transform:translate(-3px,1px) rotate(-.6deg)}40%{transform:translate(3px,-1px) rotate(.6deg)}60%{transform:translate(-2px,1px)}80%{transform:translate(1px,0)}100%{transform:none}}
.phase li.dn b{animation:pdPop .45s cubic-bezier(.2,1.7,.4,1) both}
.wall.gather .slip{transition:transform .85s cubic-bezier(.55,0,.9,.4),opacity .85s ease-in;transition-delay:var(--gd,0s);transform:translate(var(--dx),var(--dy)) rotate(var(--gr)) scale(.3);opacity:0}
.big3.bump{animation:bump .3s ease-out}
@keyframes bump{50%{transform:scale(1.06)}}
@media (prefers-reduced-motion: reduce) { .slip.shake, .phase li.dn b, .big3.bump { animation: none; } .wall.gather .slip { transition: none; } }


</style>
<div class="hdr"><div class="hdr-left"><a href="/">phishing-detector</a></div><div class="hdr-nav"><a href="/rules">偵測規則</a><a href="/whitelist">白名單</a><a href="/history">案件簿</a><a href="/paste">貼信送檢</a></div></div>
<div class="dz dz-short">
  <aside class="dz-side">
    <div class="ftab"><mark>FILE</mark><span>scanning</span></div>
    <h1 class="pg-title"><span class="hl">正在掃描你的 Gmail</span></h1>
    <p class="pg-sub">唯讀授權，只讀取收件匣最新 15 封信。每檢驗完一封，右邊就蓋上一枚印章。</p>
    <div class="big3"><span id="cnt">0</span><small>/ <span id="tot">—</span> 封</small></div>
    <div class="el" id="el">已等待 0 秒</div>
    <ul class="phase" id="phase">
      <li data-p="1"><b>1</b><span>連線 Gmail，讀取最新信件</span></li>
      <li data-p="2"><b>2</b><span>逐封檢驗</span></li>
      <li data-p="3"><b>3</b><span>整理檢驗報告</span></li>
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
      el.className = 'slip dn lv-' + (lv === 'high' ? 'h' : lv === 'medium' ? 'm' : lv === 'low' ? 'l' : 'w') + (lv === 'high' ? ' shake' : '');
    el.insertAdjacentHTML('beforeend', '<span class="stp ' + v[1] + '">' + v[0] + '</span>');
    }
    if (lv === 'high') t.high++; else if (lv === 'medium') t.medium++; else if (lv === 'low') t.low++; else t.other++;
  });
  const cur = document.getElementById('slip-' + progress.length);
  if (cur && !finished) cur.className = 'slip now';
  num('cnt', progress.length);
  num('t-high', t.high);
  num('t-med', t.medium);
  num('t-low', t.low);
  num('t-wl', t.other);
}
function num(id, v) {
  const el = document.getElementById(id); if (!el) return;
  const from = Number(el.textContent) || 0; if (from === v) return;
  const tk = (el._tk = (el._tk || 0) + 1);
  PD.tween(from, v, 450, function (x) { if (el._tk === tk) el.textContent = Math.round(x); });
  if (id === 'cnt') { const b = el.closest('.big3'); if (b) { b.classList.remove('bump'); void b.offsetWidth; b.classList.add('bump'); } }
}
function gather() {
  if (PD.RM) return;
  const wall = document.getElementById('wall'); if (!wall) return;
  const wr = wall.getBoundingClientRect(), cx = wr.left + wr.width / 2, cy = wr.top + wr.height / 2;
  wall.querySelectorAll('.slip').forEach(function (s, i) {
    const r = s.getBoundingClientRect();
    s.style.setProperty('--dx', (cx - (r.left + r.width / 2)).toFixed(0) + 'px');
    s.style.setProperty('--dy', (cy - (r.top + r.height / 2)).toFixed(0) + 'px');
    s.style.setProperty('--gr', (((i * 37) % 31) - 15) + 'deg');
    s.style.setProperty('--gd', (i * 0.025).toFixed(2) + 's');
  });
  void wall.offsetWidth; wall.classList.add('gather');
}
function tick() {
  document.getElementById('el').textContent = '已等待 ' + Math.floor((Date.now() - started) / 1000) + ' 秒';
}
function poll() {
  fetch('/scan_status').then(function (r) { return r.json(); }).then(function (d) {
    fails = 0;
    if (d.total !== null && d.total !== undefined && total === null) {
      total = d.total; document.getElementById('tot').textContent = total;
      document.getElementById('note3').textContent = '全部檢驗完成後，會自動跳到檢驗報告。';
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
      gather();
      setTimeout(function () { window.location.href = '/result/' + d.scan_id; }, PD.RM ? 900 : 1500);
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
.ew p { font-size: 14.5px; line-height: 1.9; color: #4a4a4a; max-width: 60ch; }
.ew details { margin-top: 1.6rem; border: 1px solid #141414; background: #fff; }
.ew summary { cursor: pointer; padding: .75rem 1rem; font-family: var(--mono); font-size: 12px; font-weight: 600; }
.ew pre { margin: 0; padding: .9rem 1rem 1.1rem; border-top: 1px dashed #9a9a9a; font-family: var(--mono); font-size: 12px; line-height: 1.7; white-space: pre-wrap; word-break: break-word; max-height: 22rem; overflow: auto; }
.ew .acts { margin-top: 1.8rem; display: flex; flex-wrap: wrap; gap: .6rem; }
.ew .acts a { display: inline-flex; padding: .65rem 1.1rem; border: 1px solid #141414; background: #141414; color: #f1f1f1; font-family: var(--mono); font-size: 12.5px; text-decoration: none; }
.ew .acts a.o { background: transparent; color: #141414; }
.ew .acts a:hover { background: var(--hl); color: #141414; }

</style>
<div class="hdr"><div class="hdr-left"><a href="/">phishing-detector</a></div><div class="hdr-nav"><a href="/rules">偵測規則</a><a href="/whitelist">白名單</a><a href="/history">案件簿</a><a href="/paste">貼信送檢</a></div></div>
<main class="ew">
  <div class="stamp-lg">退回<small>RETURNED</small></div>
  <h1>ERR_TITLE</h1>
  <p>ERR_MSG</p>
  ERR_DETAIL
  <div class="acts"><a href="/">返回首頁</a><a class="o" href="/paste">改用貼信送檢</a></div>
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
.sample-hint { margin-top: .6rem; font-family: var(--mono); font-size: 11px; color: #6b6b6b; line-height: 1.7; }
.mail { background: #fff; border: 1px solid #141414; }
.mrow { display: grid; grid-template-columns: 5.5rem minmax(0,1fr); align-items: center; border-bottom: 1px solid #d4d4d4; padding: 0 1.1rem; }
.mrow label { margin: 0; font-family: var(--mono); font-size: 11.5px; letter-spacing: .06em; color: #6b6b6b; }
.mrow input { width: 100%; border: 0; background: transparent; font: 500 14px var(--mono); padding: .85rem 0; box-shadow: none; }
.mrow input:focus { border: 0; box-shadow: none; }
.mrow:focus-within { background: #ffffff; }
.ruled { display: block; width: 100%; min-height: 15rem; border: 0; padding: .25rem 1.1rem 1rem; font: 15px/2rem var(--sans); resize: vertical;
  background: repeating-linear-gradient(transparent 0 calc(2rem - 1px), #e2e2e2 calc(2rem - 1px) 2rem) local; background-position: 0 .25rem; box-shadow: none; }
.ruled:focus { border: 0; box-shadow: none; }
.att { margin-top: 1rem; border: 1px solid #141414; background: #fff; }
.att summary { cursor: pointer; padding: .75rem 1.1rem; font-family: var(--mono); font-size: 12px; font-weight: 600; }
.att .ab { padding: 0 1.1rem 1rem; }
.att textarea { width: 100%; min-height: 8rem; border: 1px solid #d4d4d4; background: #f1f1f1; padding: .6rem .75rem; font: 12.5px/1.7 var(--mono); }
.att .fh { margin-top: .5rem; font-size: 12px; color: #6b6b6b; line-height: 1.7; }
.act { display: flex; flex-wrap: wrap; align-items: center; gap: .8rem 1.4rem; margin-top: 1.2rem; }
.act .submit-btn { padding: .8rem 1.6rem; font-size: 14px; }
.act span { font-family: var(--mono); font-size: 11.5px; color: #6b6b6b; }
.pv { margin-top: 2.2rem; border: 1px dashed #9a9a9a; background: #fff; padding: 1rem 1.2rem 1.1rem; }
.pv .lb { font-family: var(--mono); font-size: 11px; font-weight: 600; letter-spacing: .08em; text-transform: uppercase; display: flex; justify-content: space-between; gap: 1rem; }
.pv .lb em { font-style: normal; color: #6b6b6b; font-weight: 400; letter-spacing: 0; }
#pv { margin-top: .6rem; min-height: 3.5rem; font: 15px/2 var(--sans); white-space: pre-wrap; word-break: break-word; max-height: 16rem; overflow: auto; color: #6b6b6b; }
#pv.has { color: #141414; }
mark.m { position: relative; color: #141414; background: var(--hl); padding: .05em .12em; }
mark.m:not(.f)::after { display: none; }
mark.m::after { content: attr(data-n); position: relative; top: -.7em; margin-left: .15em; display: inline-grid; place-items: center; width: 1.25em; height: 1.25em; border-radius: 50%; background: #141414; color: #f1f1f1; font: 600 10px/1 var(--mono); }
.pv .nt { margin-top: .6rem; font-family: var(--mono); font-size: 11px; color: #6b6b6b; line-height: 1.7; }
.lgd{display:flex;flex-wrap:wrap;gap:.4rem;margin-top:.7rem}
.lgd button{font:11.5px var(--mono);border:1px solid #141414;background:#fff;padding:.15rem .55rem;cursor:pointer;color:#141414;display:inline-flex;align-items:center;gap:.35rem;border-radius:0}
.lgd button::before{content:"";width:.7rem;height:.7rem;border:1px solid #141414;background:var(--c)}
.lgd button.off{opacity:.45;text-decoration:line-through}
.pm{display:flex;align-items:center;flex-wrap:wrap;gap:.4rem .8rem;margin-top:.7rem;font:11.5px var(--mono);color:#4a4a4a}
.pm .tk{flex:0 0 9rem;height:.7rem;border:1px solid #141414;background:#fff}
.pm .tk i{display:block;height:100%;width:0;background:#141414;transition:width .3s}
mark.m[data-g="0"]{background:#ffc3dc}mark.m[data-g="1"]{background:#ffe58a}mark.m[data-g="2"]{background:#bfe0ff}mark.m[data-g="3"]{background:#c5ecd2}
.mail{position:relative}
.dropmsg{position:absolute;inset:0;display:none;place-items:center;background:rgba(255,251,232,.94);font:600 14px var(--mono);z-index:2}
.mail.drag{outline:3px dashed #ff6fae;outline-offset:4px}
.mail.drag .dropmsg{display:grid}
.emlbtn{display:inline-flex;align-items:center;cursor:pointer;padding:.8rem 1rem;font-size:13px}
.submit-btn.busy{background:var(--hl);color:#141414;position:relative;overflow:hidden;pointer-events:none}
.submit-btn.busy::after{content:"";position:absolute;left:-40%;top:0;bottom:0;width:40%;background:linear-gradient(90deg,transparent,rgba(255,255,255,.75),transparent);animation:sweep2 .9s linear infinite}
@keyframes sweep2{to{left:100%}}
@media (prefers-reduced-motion: reduce){.submit-btn.busy::after{animation:none}.pm .tk i{transition:none}}


</style>
<script>
const RULE_KW = KEYWORDS_PLACEHOLDER;
const GW = RULE_KW.map(function (g) { const m = /[+]([0-9]+)/.exec(String(g[4] || '')); return +(m ? m[1] : 2); });
const PCOL = ['#ffc3dc', '#ffe58a', '#bfe0ff', '#c5ecd2'];
const WORDS = (function () {
 const w = [];
 RULE_KW.forEach(function (g, gi) { g[3].forEach(function (x) { w.push([String(x).toLowerCase(), gi]); }); });
 w.sort(function (a, b) { return b[0].length - a[0].length; });
 return w;
})();
const off = {};
function isSp(c) { const n = c.charCodeAt(0); return n <= 32 || n === 12288; }
function ruleRaw(low, urls) {
 let raw = 0;
 RULE_KW.forEach(function (g, gi) {
  g[3].forEach(function (x) {
   const w = String(x).toLowerCase();
   if (low.indexOf(w) < 0) return;
   for (let p = low.indexOf(w); p >= 0 && p < low.length; p = low.indexOf(w, p + 1)) { if (PD.kwAt(low, p, w)) { raw += GW[gi]; return; } }
  });
 });
 if (urls) raw += Math.min(3 + urls, 8);
 return raw;
}
function preview() {
 const t = document.getElementById('body-input').value, low = t.toLowerCase(), out = document.getElementById('pv'), st = document.getElementById('pv-stat');
 out.textContent = '';
 if (!t.trim()) { out.className = ''; out.textContent = '貼上內文後，這裡會即時標出命中的關鍵字與連結。'; st.textContent = ''; setPm(0); return; }
 out.className = 'has';
 let buf = '', i = 0, k, end, found, el, kw = 0, urls = 0;
 function flush() { if (buf) { out.appendChild(document.createTextNode(buf)); buf = ''; } }
 while (i < t.length) {
  if (low.startsWith('http://', i) || low.startsWith('https://', i)) {
   end = i; while (end < t.length && !isSp(t[end])) end++;
   flush(); el = document.createElement('mark'); el.className = urls ? 'm' : 'm f'; el.setAttribute('data-n', '3'); el.textContent = t.slice(i, end); out.appendChild(el); urls++; i = end; continue;
  }
  found = null;
  for (k = 0; k < WORDS.length; k++) { if (!off[WORDS[k][1]] && PD.kwAt(low, i, WORDS[k][0])) { found = WORDS[k]; break; } }
  if (found) { flush(); el = document.createElement('mark'); el.className = kw ? 'm' : 'm f'; el.setAttribute('data-n', '1'); el.setAttribute('data-g', found[1]); el.textContent = t.slice(i, i + found[0].length); out.appendChild(el); kw++; i += found[0].length; }
  else { buf += t[i]; i++; }
 }
 flush();
 st.textContent = '關鍵字 ' + kw + '・連結 ' + urls;
 setPm(ruleRaw(low, urls));
}
let pmCur = 0;
function setPm(raw) {
 const norm = Math.min(raw * 5, 100), el = document.getElementById('pmv'), from = pmCur;
 document.getElementById('pm').style.width = norm + '%'; pmCur = raw;
 PD.tween(from, raw, 300, function (x) { if (pmCur === raw) el.textContent = '規則分數 ' + Math.round(x) + ' → 正規化 ' + Math.min(Math.round(x) * 5, 100) + ' / 100（僅 R1–R5）'; });
}
/* ── .eml 解析（純前端，不上傳） ── */
function dec(u8, cs) { try { return new TextDecoder(cs || 'utf-8').decode(u8); } catch (e) { return new TextDecoder('utf-8').decode(u8); } }
function b64(s, cs) { try { const bin = atob(s.replace(/\\s+/g, '')), u = new Uint8Array(bin.length); for (let i = 0; i < bin.length; i++) u[i] = bin.charCodeAt(i); return dec(u, cs); } catch (e) { return s; } }
function qp(s, cs) {
 s = s.replace(/=\\r?\\n/g, '');
 const bytes = [];
 for (let i = 0; i < s.length; i++) {
  if (s[i] === '=' && /^[0-9A-Fa-f]{2}$/.test(s.substr(i + 1, 2))) { bytes.push(parseInt(s.substr(i + 1, 2), 16)); i += 2; }
  else bytes.push(s.charCodeAt(i) & 255);
 }
 return dec(new Uint8Array(bytes), cs);
}
function mw(s) {
 return String(s || '').replace(/\\?=\\s+=\\?/g, '?==?').replace(/=\\?([^?]+)\\?([bBqQ])\\?([^?]*)\\?=/g, function (_, cs, enc, tx) {
  return enc.toLowerCase() === 'b' ? b64(tx, cs) : qp(tx.replace(/_/g, ' '), cs);
 });
}
function parseMsg(raw) {
 const k = raw.search(/\\r?\\n\\r?\\n/), head = k < 0 ? raw : raw.slice(0, k), body = k < 0 ? '' : raw.slice(k).replace(/^\\r?\\n\\r?\\n/, ''), h = {};
 head.replace(/\\r?\\n[ \\t]+/g, ' ').split(/\\r?\\n/).forEach(function (l) { const c = l.indexOf(':'); if (c > 0) { const n = l.slice(0, c).toLowerCase(); if (!(n in h)) h[n] = l.slice(c + 1).trim(); } });
 return { h: h, body: body };
}
function walk(msg, out) {
 const ct = msg.h['content-type'] || 'text/plain', cd = (msg.h['content-disposition'] || '').toLowerCase();
 if (cd.indexOf('attachment') === 0) return;
 const cs = (/charset="?([^";\\s]+)/i.exec(ct) || [])[1];
 if (/^\\s*multipart\\//i.test(ct)) {
  const bm = /boundary="?([^";]+)"?/i.exec(ct); if (!bm) return;
  msg.body.split('--' + bm[1]).slice(1).forEach(function (p) { if (p.slice(0, 2) === '--') return; walk(parseMsg(p.replace(/^\\r?\\n/, '')), out); });
  return;
 }
 const te = (msg.h['content-transfer-encoding'] || '').toLowerCase();
 let text = msg.body;
 if (te === 'base64') text = b64(text, cs); else if (te === 'quoted-printable') text = qp(text, cs);
 if (/^\\s*text\\/html/i.test(ct)) { if (!out.html) out.html = text; }
 else if (/^\\s*text\\/plain/i.test(ct)) { if (!out.text) out.text = text; }
}
function loadEml(file) {
 if (!file) return;
 if (file.size > 2 * 1024 * 1024) { PD.toast('檔案超過 2 MB，請改用貼上內文', { type: 'err' }); return; }
 file.text().then(function (raw) {
  const m = parseMsg(raw), out = {};
  walk(m, out);
  let text = out.text || '';
  if (!text && out.html) text = new DOMParser().parseFromString(out.html, 'text/html').body.textContent || '';
  if (!m.h['from'] && !m.h['subject'] && !text) { PD.toast('看起來不是有效的 .eml 檔', { type: 'err' }); return; }
  document.getElementById('sender-input').value = mw(m.h['from']);
  document.getElementById('subject-input').value = mw(m.h['subject']);
  document.getElementById('body-input').value = text.trim();
  document.getElementById('html-input').value = out.html || '';
  if (out.html) document.getElementById('att').open = true;
  preview();
  PD.toast('已調閱 ' + file.name + '（僅在瀏覽器內處理，尚未送出）', { type: 'ok' });
 }).catch(function () { PD.toast('讀取檔案失敗', { type: 'err' }); });
}
document.addEventListener('DOMContentLoaded', function () {
 const b = document.getElementById('body-input'), h = document.getElementById('html-input');
 b.addEventListener('input', preview); preview();
 if (h.value.trim()) document.getElementById('att').open = true;
 const lg = document.getElementById('lgd');
 RULE_KW.forEach(function (g, gi) {
  const bt = document.createElement('button'); bt.type = 'button'; bt.textContent = g[0] + ' ' + g[1]; bt.style.setProperty('--c', PCOL[gi % 4]); bt.setAttribute('aria-pressed', 'true');
  bt.addEventListener('click', function () { off[gi] = !off[gi]; bt.classList.toggle('off', !!off[gi]); bt.setAttribute('aria-pressed', off[gi] ? 'false' : 'true'); preview(); });
  lg.appendChild(bt);
 });
 const mail = document.getElementById('mail'), ef = document.getElementById('emlf');
 ef.addEventListener('change', function () { loadEml(ef.files[0]); ef.value = ''; });
 ['dragenter', 'dragover'].forEach(function (ev) { document.addEventListener(ev, function (e) { if (e.dataTransfer && Array.prototype.indexOf.call(e.dataTransfer.types || [], 'Files') >= 0) { e.preventDefault(); mail.classList.add('drag'); } }); });
 document.addEventListener('dragleave', function (e) { if (!e.relatedTarget) mail.classList.remove('drag'); });
 document.addEventListener('drop', function (e) { if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length) { e.preventDefault(); mail.classList.remove('drag'); loadEml(e.dataTransfer.files[0]); } });
 const form = document.querySelector('form[action="/paste_analyze"]'), sb = form.querySelector('.submit-btn'), orig = sb.textContent;
 form.addEventListener('submit', function () { sb.classList.add('busy'); sb.textContent = '蓋章中…'; setTimeout(function () { sb.disabled = true; }, 0); });
 window.addEventListener('pageshow', function () { sb.classList.remove('busy'); sb.disabled = false; sb.textContent = orig; });
});
</script>
<div class="hdr"><div class="hdr-left"><a href="/">phishing-detector</a></div><div class="hdr-nav"><a href="/rules">偵測規則</a><a href="/whitelist">白名單</a><a href="/history">案件簿</a><a href="/paste">貼信送檢</a></div></div>
<div class="dz dz-short">
  <aside class="dz-side">
    <div class="ftab"><mark>FILE</mark><span>paste</span></div>
    <h1 class="pg-title"><span class="hl">貼上郵件，直接送檢</span></h1>
    <p class="pg-sub">不需要 Google 帳號授權，將郵件的寄件者、主旨與內文貼上即可，系統會以相同的三層式（規則引擎 + ML + HTML / URL + AI）架構進行分析。</p>
    <form method="GET" action="/paste" class="sample-form">
      <div class="lb" style="font-family:var(--mono);font-size:11px;font-weight:600;letter-spacing:.08em;margin-top:1.8rem">快速調閱測試信件</div>
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
        <button type="submit" class="sample-btn">調閱範例</button>
      </div>
      <div class="sample-hint">選擇範例後按「調閱範例」，系統會直接填入郵件欄位，不依賴 JavaScript。</div>
    </form>
  </aside>
  <main class="dz-main">
    ERROR_PLACEHOLDER
    <form method="POST" action="/paste_analyze">
      <div class="sh"><span class="n">01</span><h2>待檢驗郵件</h2></div>
      <div class="mail" id="mail"><div class="dropmsg">放開以調閱 .eml 檔</div>
        <div class="mrow"><label for="sender-input">寄件者</label><input id="sender-input" type="text" name="sender" value="SAMPLE_SENDER" placeholder="選填，用於白名單比對，例如 service@example.com"></div>
        <div class="mrow"><label for="subject-input">主　旨</label><input id="subject-input" type="text" name="subject" value="SAMPLE_SUBJECT" placeholder="郵件主旨"></div>
        <textarea id="body-input" class="ruled" name="body" placeholder="貼上郵件的純文字內容（必填）..." required>SAMPLE_BODY</textarea>
      </div>
      <details class="att" id="att">
        <summary>附件：HTML 原始碼（選填，用於偵測像素追蹤／偽裝連結等）</summary>
        <div class="ab"><textarea id="html-input" name="html" placeholder="若有郵件的 HTML 原始碼，可貼於此處以啟用多模態偵測...">SAMPLE_HTML</textarea>
        <div class="fh">在大部分信箱可透過「顯示原始郵件 / 檢視原始碼」取得 HTML 內容。</div></div>
      </details>
      <div class="act"><button class="submit-btn" type="submit">送檢</button><label class="sample-btn emlbtn">調閱 .eml 檔<input type="file" id="emlf" accept=".eml,message/rfc822" hidden></label><span>送出後會進行完整的四層分析</span></div>
    </form>
    <div class="pv">
      <div class="lb"><span>預檢標記（即時）</span><em id="pv-stat"></em></div>
      <div class="lgd" id="lgd"></div>
 <div class="pm"><span class="tk"><i id="pm"></i></span><span id="pmv">規則分數 0 → 正規化 0 / 100（僅 R1–R5）</span></div>
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

def _kw_json(rule_keyword_groups):
    """規則關鍵字清單（供前端預檢／原信批註比對用，已做 script 安全跳脫）。"""
    return json.dumps(rule_keyword_groups, ensure_ascii=False).replace(
        '<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')

def render_paste_page(sample_key='', error='', rule_keyword_groups=()):
    import html as html_lib
    sample = SAMPLE_EMAILS.get(sample_key, {'sender':'','subject':'','body':'','html':''})
    out = PASTE_HTML.replace('KEYWORDS_PLACEHOLDER', _kw_json(rule_keyword_groups))
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
.risk-seg-high { background: #c8321e; } .risk-seg-med { background: #e39a2d; } .risk-seg-low { background: #2e6a4d; } .risk-seg-wl { background: #9a9a9a; }
.overview-meta { display: flex; justify-content: space-between; font-family: var(--mono); font-size: 11px; color: #6b6b6b; margin-top: .35rem; }
.lst { margin-top: 1.4rem; }
.list-sec { display: inline-block; margin: 1rem 0 .4rem; padding: 0 .45rem; background: var(--hl); font-family: var(--mono); font-size: 11px; font-weight: 600; letter-spacing: .08em; }
.email-item { display: flex; gap: .65rem; padding: .7rem; border-top: 1px solid #d4d4d4; border-left: 4px solid transparent; cursor: pointer; }
.email-item:hover { background: #e2e2e2; }
.email-item.active { background: #fff; border-left-color: #141414; box-shadow: inset 0 0 0 1px #141414; }
.risk-dot { flex: none; width: .7rem; height: .7rem; margin-top: .4rem; border: 1px solid #141414; }
.dot-high { background: #c8321e; } .dot-med { background: #e39a2d; } .dot-low { background: #2e6a4d; } .dot-wl { background: #9a9a9a; }
.item-body { min-width: 0; }
.item-subj { font-weight: 700; font-size: 13.5px; line-height: 1.45; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.item-from { font-family: var(--mono); font-size: 11px; color: #6b6b6b; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.item-score { font-family: var(--mono); font-size: 11.5px; margin-top: .15rem; }
.item-reason { font-size: 12px; color: #4a4a4a; margin-top: .2rem; line-height: 1.5; }
.solo #listwrap { display: none; }
.flt{display:flex;flex-wrap:wrap;gap:.35rem;margin:.2rem 0 .6rem}
.flt button{font:11.5px var(--mono);border:1px solid #141414;background:transparent;padding:.2rem .55rem;cursor:pointer;color:#141414;border-radius:0}
.flt button.on{background:#141414;color:var(--paper)}
.flt button:hover:not(.on){background:var(--hl)}
.flt select{font:11.5px var(--mono);border:1px solid #141414;background:#fff;padding:.2rem .4rem;border-radius:0;flex-basis:100%;margin-top:.2rem}
.email-item.fh,.list-sec.fh,.list-sec.hh{display:none}
.email-item.fin{animation:pdIn .35s ease both}
.cbar{height:3px;background:#e2e2e2;margin:.25rem 0 .7rem}
.cbar i{display:block;height:100%;width:0;background:#141414;transition:width .3s}
#casepos{font-weight:400;color:#6b6b6b;letter-spacing:0;text-transform:none;margin-left:.5rem}
.ftab .cn{margin-left:.3rem;border:1px solid #141414;background:transparent;font:600 13px/1 var(--mono);width:1.7rem;height:1.7rem;cursor:pointer;color:#141414;border-radius:0;padding:0}
.ftab .cn:hover{background:var(--hl)}
.chk input:checked + span{text-decoration:line-through;color:#6b6b6b}
@media (prefers-reduced-motion: reduce){.email-item.fin{animation:none}.cbar i{transition:none}}

/* 結論 */
.vd { display: grid; gap: 1.4rem; align-items: start; }
@media (min-width: 900px) { .vd { grid-template-columns: minmax(0,1fr) auto; } }
.vd-subj { font-family: var(--serif); font-weight: 900; font-size: clamp(1.6rem,2.6vw,2.4rem); line-height: 1.3; margin: .2rem 0 .5rem; word-break: break-word; }
.vd-from { font-family: var(--mono); font-size: 12.5px; color: #4a4a4a; word-break: break-all; }
.tg { display: flex; flex-wrap: wrap; gap: .35rem; margin-top: .9rem; }
.tg span { background: var(--hl); font-family: var(--mono); font-size: 11.5px; padding: 0 .4rem; }
.vd-r { display: flex; flex-direction: column; align-items: flex-end; gap: 1rem; padding-right: .6rem; }
.stamp-lg { border: 4px solid currentColor; padding: .15rem 1rem .25rem; font-family: var(--serif); font-weight: 900; font-size: 2.4rem; line-height: 1.15; text-align: center; transform: rotate(-6deg); mix-blend-mode: multiply; animation: stampin .45s cubic-bezier(.2,1.7,.4,1) both; }
.stamp-lg small { display: block; font-family: var(--mono); font-size: .7rem; letter-spacing: .2em; font-weight: 600; }
.stamp-lg.red { color: #c8321e; } .stamp-lg.org { color: #a8650f; } .stamp-lg.grn { color: #2e6a4d; } .stamp-lg.ink { color: #141414; }
@keyframes stampin { from { opacity: 0; transform: rotate(14deg) scale(2.2); } to { opacity: .95; transform: rotate(-6deg) scale(1); } }
.vscore { font-family: var(--serif); font-weight: 900; font-size: 3.4rem; line-height: 1; }
.vscore small { font-family: var(--mono); font-size: 13px; font-weight: 400; color: #4a4a4a; margin-left: .3rem; }
.gauge { position: relative; margin: 1.8rem 0 .3rem; padding-top: 1.7rem; }
.gscale { display: flex; height: .9rem; border: 1px solid #141414; }
.gscale i { display: block; } .gscale .lo { flex: 40; background: #2e6a4d; } .gscale .md { flex: 30; background: #e39a2d; } .gscale .hi { flex: 30; background: #c8321e; }
.pin { position: absolute; top: 0; transform: translateX(-50%); font-family: var(--mono); font-weight: 600; font-size: 12px; background: #141414; color: #f1f1f1; padding: 0 .4rem; }
.pin::after { content: ""; position: absolute; left: 50%; bottom: -7px; transform: translateX(-50%); border: 4px solid transparent; border-top-color: #141414; }
.gt { position: relative; height: 1rem; font-family: var(--mono); font-size: 11px; color: #6b6b6b; margin-top: .25rem; }
.gt span { position: absolute; transform: translateX(-50%); }
/* 原信批註 */
.mdoc { background: #fff; border: 1px solid #141414; padding: 1.2rem 1.4rem; }
.mdoc dl { margin: 0 0 .9rem; padding-bottom: .8rem; border-bottom: 1px solid #d4d4d4; font-family: var(--mono); font-size: 12.5px; line-height: 1.9; }
.mdoc dl div { display: grid; grid-template-columns: 4.2em 1fr; gap: .5rem; }
.mdoc dt { color: #6b6b6b; font-size: 11.5px; letter-spacing: .06em; }
.mdoc dd { margin: 0; word-break: break-all; }
.mbody { font-size: 15px; line-height: 2.05; white-space: pre-wrap; word-break: break-word; max-height: 24rem; overflow: auto; }
mark.m { position: relative; color: #141414; background: linear-gradient(var(--hl), var(--hl)) no-repeat; background-size: 100% 100%; padding: .05em .12em; animation: draw .5s cubic-bezier(.3,.7,.3,1) both; animation-delay: calc(var(--i, 0) * .07s + .2s); }
mark.m:not(.f)::after { display: none; }
mark.m::after { content: attr(data-n); position: relative; top: -.7em; margin-left: .15em; display: inline-grid; place-items: center; width: 1.25em; height: 1.25em; border-radius: 50%; background: #141414; color: #f1f1f1; font: 600 10px/1 var(--mono); }
@keyframes draw { from { background-size: 0% 100%; } to { background-size: 100% 100%; } }
.notes { margin: 1rem 0 0; padding: .9rem 0 0; border-top: 1px dashed #9a9a9a; list-style: none; font-size: 13px; line-height: 1.7; color: #4a4a4a; }
.notes li { display: flex; gap: .65rem; padding: .15rem 0; }
.notes li b { flex: none; display: grid; place-items: center; width: 1.25rem; height: 1.25rem; margin-top: .22rem; border-radius: 50%; background: #141414; color: #f1f1f1; font: 600 10px/1 var(--mono); }
.notes li.on { color: #141414; } .notes li.on span { background: var(--hl); }
.cap2 { margin-top: .7rem; font-family: var(--mono); font-size: 11.5px; color: #6b6b6b; line-height: 1.7; }
/* 四層 */
.lgrid { display: grid; grid-template-columns: repeat(auto-fit, minmax(13rem, 1fr)); gap: 1rem; }
.lc { background: #fff; border: 1px solid #141414; padding: .9rem 1rem 1rem; display: flex; flex-direction: column; gap: .5rem; }
.ln { display: flex; align-items: center; gap: .55rem; font-family: var(--mono); font-size: 12px; font-weight: 600; }
.ln b { display: grid; place-items: center; width: 1.3rem; height: 1.3rem; border-radius: 50%; background: #141414; color: #f1f1f1; font-size: 10px; }
.lsc { font-family: var(--serif); font-weight: 900; font-size: 2.2rem; line-height: 1; }
.lsc small { font-family: var(--mono); font-size: 12px; font-weight: 400; color: #4a4a4a; margin-left: .25rem; }
.ls { font-size: 13px; line-height: 1.7; color: #4a4a4a; }
.bar { height: .6rem; border: 1px solid #141414; background: #f1f1f1; }
.bar-fill { height: 100%; background: #141414; }
.lm { display: flex; justify-content: space-between; gap: .6rem; font-family: var(--mono); font-size: 11px; color: #6b6b6b; }
.fnote { margin-top: .9rem; font-family: var(--mono); font-size: 12px; line-height: 1.8; color: #4a4a4a; }
.bk { display: flex; border: 1px solid #141414; height: 2.3rem; font-family: var(--mono); font-size: 11.5px; margin-top: 1.1rem; background: #fff; }
.bk i { font-style: normal; display: flex; align-items: center; padding: 0 .55rem; overflow: hidden; white-space: nowrap; border-right: 1px solid #141414; }
.bk i:last-child { border-right: 0; }
.bk .c0 { background: #141414; color: #f1f1f1; } .bk .c1 { background: #4a4a4a; color: #f1f1f1; } .bk .c2 { background: var(--hl); } .bk .c3 { background: #ffe0ee; }
.brow { display: flex; justify-content: space-between; gap: 1rem; padding: .45rem 0; border-bottom: 1px dashed #9a9a9a; font-family: var(--mono); font-size: 12.5px; }
.btot { margin-top: .8rem; font-family: var(--mono); font-size: 13px; font-weight: 600; }
/* 為什麼／證據／處置 */
.why { list-style: none; margin: 0; padding: 0; }
.why li { display: grid; grid-template-columns: 5.2rem minmax(0,1fr); gap: 1rem; padding: 1rem 0; border-top: 1px solid #d4d4d4; }
.why li:last-child { border-bottom: 1px solid #d4d4d4; }
.why .src { font-family: var(--mono); font-size: 11px; color: #6b6b6b; }
.why .hd { font-weight: 700; margin: .1rem 0 .2rem; }
.why .dt { font-size: 13.5px; line-height: 1.8; color: #4a4a4a; }
.ev { border: 1px solid #141414; background: #fff; margin-top: .7rem; }
.ev summary { cursor: pointer; padding: .7rem 1rem; font-family: var(--mono); font-size: 12px; font-weight: 600; }
.ev div.it { padding: .5rem 1rem; border-top: 1px dashed #9a9a9a; font-size: 13px; line-height: 1.7; color: #4a4a4a; word-break: break-word; }
.rec { border-left: 6px solid #141414; background: #fff; padding: 1rem 1.2rem; font-family: var(--serif); font-weight: 700; font-size: 1.15rem; line-height: 1.75; }
.chk { margin-top: 1.2rem; }
.chk label { display: flex; gap: .75rem; padding: .6rem 0; border-top: 1px dashed #9a9a9a; cursor: pointer; font-size: 14px; line-height: 1.7; }
.chk input { flex: none; width: 1.1rem; height: 1.1rem; margin-top: .25rem; accent-color: #141414; }
.chk input:checked + span { text-decoration: line-through; color: #6b6b6b; }
/* IR 報告單 */
.ir { background: #fff; border: 1px solid #141414; }
.irh { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: .6rem 1rem; padding: .8rem 1.1rem; background: #141414; color: #f1f1f1; font-family: var(--mono); font-size: 12px; }
.irh .st { color: #f1f1f1; border-color: #f1f1f1; mix-blend-mode: normal; transform: rotate(-3deg); }
.irc { padding: 1.1rem 1.1rem 1.2rem; }
.irc p { font-size: 14px; line-height: 1.8; color: #333; }
.irc ul { margin: .6rem 0 0 1.2rem; font-size: 13.5px; line-height: 1.8; }
.irmeta { display: flex; flex-wrap: wrap; gap: .4rem 2rem; margin-top: 1rem; font-family: var(--mono); font-size: 11.5px; color: #4a4a4a; }
.ir3 { display: grid; gap: 1px; background: #141414; border-top: 1px solid #141414; }
@media (min-width: 900px) { .ir3 { grid-template-columns: repeat(3, 1fr); } }
.ir3 div { background: #fff; padding: .9rem 1.1rem 1.1rem; }
.ir3 b { display: block; font-family: var(--mono); font-size: 11px; letter-spacing: .08em; text-transform: uppercase; margin-bottom: .4rem; }
.ir3 p { font-size: 13px; line-height: 1.75; color: #333; }
.irn { padding: .9rem 1.1rem; border-top: 1px solid #141414; font-size: 12.5px; line-height: 1.8; color: #4a4a4a; background: #f1f1f1; }
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
    for (k = 0; k < WORDS.length; k++) { if (PD.kwAt(low, i, WORDS[k])) { found = WORDS[k]; break; } }
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
  html += '<div class="vd"><div><div class="ftab"><mark>CASE</mark><span>' + (idx + 1) + ' / ' + emailData.length + '</span>' + (emailData.length > 1 ? '<button type="button" class="cn" data-d="-1" aria-label="上一封">‹</button><button type="button" class="cn" data-d="1" aria-label="下一封">›</button>' : '') + '</div>' +
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
  const vdEl = panel.querySelector('.vd'); if (vdEl) vdEl.classList.add(d.level === 'high' ? 'lv-hi' : d.level === 'medium' ? 'lv-mid' : d.level === 'low' ? 'lv-lo' : 'lv-wl');
  panel.querySelectorAll('.lc').forEach(function (lc) { const f = lc.querySelector('.bar-fill'), v = f ? parseFloat(f.style.width) || 0 : 0; lc.classList.add(v >= 70 ? 'lv-hi' : v >= 40 ? 'lv-mid' : 'lv-lo'); });
  /* 動畫：儀表指針、分數、四層長條依序出現 */
  if (!PD.RM) {
    const pin = panel.querySelector('.pin');
    if (pin && score !== null) {
      const tgt = pin.style.left;
      pin.style.transition = 'none'; pin.style.left = '0%'; pin.textContent = '0'; pin.getBoundingClientRect();
      pin.style.transition = 'left .9s cubic-bezier(.2,.8,.2,1)'; pin.style.left = tgt;
      PD.tween(0, score, 900, function (x) { pin.textContent = Math.round(x); });
    }
    const vs = panel.querySelector('.vscore');
    if (vs && score !== null && vs.firstChild) PD.tween(0, score, 900, function (x) { vs.firstChild.nodeValue = Math.round(x); });
    panel.querySelectorAll('.lc').forEach(function (lc, n) {
      const f = lc.querySelector('.bar-fill'), sc = lc.querySelector('.lsc'); if (!f) return;
      const w = f.style.width;
      f.style.transition = 'none'; f.style.width = '0%'; f.getBoundingClientRect();
      setTimeout(function () { f.style.transition = 'width .8s cubic-bezier(.2,.7,.2,1)'; f.style.width = w; }, 200 + n * 220);
      if (sc && sc.firstChild && /^[0-9]+$/.test(sc.firstChild.nodeValue)) {
        const to = Number(sc.firstChild.nodeValue); sc.firstChild.nodeValue = '0';
        setTimeout(function () { PD.tween(0, to, 800, function (x) { sc.firstChild.nodeValue = Math.round(x); }); }, 200 + n * 220);
      }
    });
  }
  /* 偵探牆紅線：標記 ↔ 批註 ↔ 分析層卡片 */
  function hotLc(n, on) { panel.querySelectorAll('.lc').forEach(function (lc) { const b = lc.querySelector('.ln b'); if (b && b.textContent === n) lc.classList.toggle('hot', on); }); }
  panel.querySelectorAll('mark.m').forEach(function (m) { const n = m.getAttribute('data-n'); m.addEventListener('mouseenter', function () { hotLc(n, true); }); m.addEventListener('mouseleave', function () { hotLc(n, false); }); });
  panel.querySelectorAll('.notes li').forEach(function (li) { const n = li.getAttribute('data-n'); li.addEventListener('mouseenter', function () { hotLc(n, true); }); li.addEventListener('mouseleave', function () { hotLc(n, false); }); });
  panel.querySelectorAll('.cn').forEach(function (b) { b.addEventListener('click', function () { go(Number(b.getAttribute('data-d'))); }); });
  const md = panel.querySelector('.mdoc'); if (md && !PD.RM) md.classList.add(navDir < 0 ? 'pin-l' : 'pin-r');
  PD.arm('#right-panel .sh');
  navDir = 0;
  if (typeof updatePos === 'function') updatePos();
  window.scrollTo(0, 0);
}

/* 案件導覽：篩選、排序、←/→、手機滑動 */
let navDir = 0, fltMode = 'all', sortMode = 'risk', origNodes = [];
function lvOf(el) { const d = emailData[Number(el.getAttribute('data-idx'))]; return d ? d.level : 'wl'; }
function idxOf(el) { return Number(el.getAttribute('data-idx')); }
function scOf(el) { const d = emailData[idxOf(el)]; return d && d.risk_score >= 0 ? Number(d.risk_score) : -1; }
function visItems() { return Array.prototype.slice.call(document.querySelectorAll('#left-panel .email-item')).filter(function (el) { return !el.classList.contains('fh'); }); }
function updatePos() {
  const v = visItems(), a = document.querySelector('.email-item.active'), k = a ? v.indexOf(a) : -1;
  const cp = document.getElementById('casepos'), cb = document.getElementById('cbar');
  if (cp) cp.textContent = k >= 0 ? (k + 1) + ' / ' + v.length : v.length + ' 封';
  if (cb) cb.style.width = (k >= 0 && v.length ? (k + 1) / v.length * 100 : 0) + '%';
}
function applyList() {
  const lp = document.getElementById('left-panel');
  const items = Array.prototype.slice.call(lp.querySelectorAll('.email-item')), heads = Array.prototype.slice.call(lp.querySelectorAll('.list-sec'));
  if (sortMode === 'risk') { origNodes.forEach(function (n) { lp.appendChild(n); }); heads.forEach(function (h) { h.classList.remove('hh'); }); }
  else {
    heads.forEach(function (h) { h.classList.add('hh'); });
    items.slice().sort(sortMode === 'score' ? function (a, b) { return scOf(b) - scOf(a) || idxOf(a) - idxOf(b); } : function (a, b) { return idxOf(a) - idxOf(b); }).forEach(function (n) { lp.appendChild(n); });
  }
  items.forEach(function (el) { el.classList.toggle('fh', !(fltMode === 'all' || lvOf(el) === fltMode)); });
  if (sortMode === 'risk') {
    heads.forEach(function (h) {
      let n = h.nextElementSibling, any = false;
      while (n && n.classList.contains('email-item')) { if (!n.classList.contains('fh')) any = true; n = n.nextElementSibling; }
      h.classList.toggle('fh', !any);
    });
  } else heads.forEach(function (h) { h.classList.remove('fh'); });
  updatePos();
}
function flipList() {
  const items = Array.prototype.slice.call(document.querySelectorAll('#left-panel .email-item')), first = new Map();
  items.forEach(function (el) { if (el.offsetParent !== null) first.set(el, el.getBoundingClientRect().top); });
  applyList();
  if (PD.RM) return;
  items.forEach(function (el) {
    if (el.offsetParent === null) return;
    if (first.has(el)) {
      const dy = first.get(el) - el.getBoundingClientRect().top;
      if (Math.abs(dy) > 1) {
        el.style.transition = 'none'; el.style.transform = 'translateY(' + dy + 'px)'; el.getBoundingClientRect();
        el.style.transition = 'transform .35s cubic-bezier(.2,.8,.2,1)'; el.style.transform = '';
        setTimeout(function () { el.style.transition = ''; }, 400);
      }
    } else { el.classList.add('fin'); setTimeout(function () { el.classList.remove('fin'); }, 400); }
  });
}
function go(dir) {
  const v = visItems(); if (!v.length) return;
  const a = document.querySelector('.email-item.active');
  let k = a ? v.indexOf(a) : -1;
  k = k < 0 ? (dir > 0 ? 0 : v.length - 1) : (k + dir + v.length) % v.length;
  navDir = dir; v[k].click(); v[k].scrollIntoView({ block: 'nearest', behavior: PD.RM ? 'auto' : 'smooth' });
}
function initList() {
  const lp = document.getElementById('left-panel'); origNodes = Array.prototype.slice.call(lp.children);
  if (!PD.RM) { Array.prototype.slice.call(lp.querySelectorAll('.email-item')).forEach(function (el, i) { el.style.setProperty('--ri', Math.min(i, 12)); el.classList.add('reg'); setTimeout(function () { el.classList.remove('reg'); }, 1400); }); }
  const box = document.getElementById('flt');
  if (emailData.length > 1 && box) {
    const NAME = { all: '全部', high: '可疑', medium: '注意', low: '安全', wl: '白名單' }, cnt = { all: emailData.length };
    emailData.forEach(function (d) { cnt[d.level] = (cnt[d.level] || 0) + 1; });
    Object.keys(NAME).forEach(function (k) {
      if (k !== 'all' && !cnt[k]) return;
      const b = document.createElement('button'); b.type = 'button'; b.textContent = NAME[k] + ' ' + cnt[k]; if (k === 'all') b.className = 'on';
      b.addEventListener('click', function () { fltMode = k; Array.prototype.forEach.call(box.querySelectorAll('button'), function (x) { x.classList.toggle('on', x === b); }); flipList(); });
      box.appendChild(b);
    });
    const sel = document.createElement('select'); sel.setAttribute('aria-label', '排序方式');
    [['risk', '依風險分組'], ['score', '分數高 → 低'], ['time', '收件順序']].forEach(function (o) { const op = document.createElement('option'); op.value = o[0]; op.textContent = o[1]; sel.appendChild(op); });
    sel.addEventListener('change', function () { sortMode = sel.value; flipList(); });
    box.appendChild(sel);
    PD.addKeys([['← →', '上一封 / 下一封案件']]);
    document.addEventListener('keydown', function (e) {
      if (e.metaKey || e.ctrlKey || e.altKey || e.shiftKey) return;
      const tn = e.target && e.target.tagName; if (tn === 'INPUT' || tn === 'TEXTAREA' || tn === 'SELECT' || (e.target && e.target.isContentEditable)) return;
      if (e.key === 'ArrowRight') { e.preventDefault(); go(1); } else if (e.key === 'ArrowLeft') { e.preventDefault(); go(-1); }
    });
    const rp = document.getElementById('right-panel'); let sx = 0, sy = 0;
    rp.addEventListener('touchstart', function (e) { const t = e.changedTouches[0]; sx = t.clientX; sy = t.clientY; }, { passive: true });
    rp.addEventListener('touchend', function (e) { const t = e.changedTouches[0], dx = t.clientX - sx, dy = t.clientY - sy; if (Math.abs(dx) > 70 && Math.abs(dx) > Math.abs(dy) * 1.6) go(dx < 0 ? 1 : -1); }, { passive: true });
  }
  updatePos();
}

window.addEventListener('DOMContentLoaded', function () {
  if (Array.isArray(emailData) && emailData.length > 0) {
    if (emailData.length === 1) document.querySelector('.dz').classList.add('solo');
    showDetail(0);
    initList();
  }
});
</script>
<div class="hdr"><div class="hdr-left"><a href="/">phishing-detector</a></div><div class="hdr-nav"><a href="/rules">偵測規則</a><a href="/whitelist">白名單</a><a href="/history">案件簿</a><a href="/paste">貼信送檢</a></div></div>
<div class="dz">
  <aside class="dz-side">
    <div class="ftab"><mark>FILE</mark><span>result</span></div>
    <h1 class="pg-title"><span class="hl">檢驗報告</span></h1>
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
      <div class="lb">案件清單<span id="casepos"></span></div>
 <div class="cbar"><i id="cbar"></i></div>
 <div class="flt" id="flt"></div>
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
.dot.h, .bar3 .h { background: #c8321e; } .dot.m, .bar3 .m { background: #e39a2d; } .dot.l, .bar3 .l { background: #2e6a4d; } .dot.w, .bar3 .w { background: #9a9a9a; }
.led { border-top: 1px solid #141414; }
.lr { display: grid; grid-template-columns: 1fr; gap: .7rem; padding: 1.1rem 0; border-bottom: 1px solid #d4d4d4; align-items: center; }
@media (min-width: 900px) { .lr { grid-template-columns: 9.5rem minmax(0,1fr) 14rem; gap: 1.5rem; padding-right: .6rem; } }
.lr .tm b { display: block; font-family: var(--serif); font-weight: 900; font-size: 1.35rem; line-height: 1.2; }
.lr .tm span { font-family: var(--mono); font-size: 11.5px; color: #6b6b6b; }
.bar3 { display: flex; height: 1.7rem; border: 1px solid #141414; background: repeating-linear-gradient(135deg, #f1f1f1 0 6px, #e2e2e2 6px 12px); }
.bar3 i { display: block; min-width: 3px; border-right: 1px solid #141414; } .bar3 i:last-child { border-right: 0; }
.lr .nm { display: flex; align-items: center; justify-content: space-between; gap: .8rem; font-family: var(--mono); font-size: 12px; }
.lr .nm span { white-space: nowrap; }
.lr .nm .st { font-size: .8rem; }
.empty2 { border: 1px dashed #9a9a9a; padding: 4rem 1.5rem; text-align: center; background: #fff; }
.empty2 .st { font-size: 1.6rem; padding: .2rem 1.1rem; }
.empty2 p { margin-top: 1.4rem; font-size: 14px; color: #4a4a4a; }
.empty2 a { color: #141414; text-underline-offset: 4px; }
.lr{cursor:pointer;transition:background .15s}
.lr:hover{background:rgba(255,182,213,.12)}
.lr:focus-visible{outline:2px solid #141414;outline-offset:-2px}
.bar3 i{transform-origin:left;transition:transform .7s cubic-bezier(.2,.7,.2,1);transition-delay:calc(var(--k,0) * .12s)}
.js .lr:not(.in) .bar3 i{transform:scaleX(0)}
.lr .more{grid-column:1 / -1;display:none;padding:.5rem 0 .3rem}
.lr.open .more{display:block;animation:pdIn .3s ease both}
.mrow{display:grid;grid-template-columns:5rem 1fr 8rem;gap:.8rem;align-items:center;font:12px var(--mono);padding:.3rem 0}
.mrow .tk{height:.55rem;background:#e2e2e2;position:relative}
.mrow .tk i{position:absolute;left:0;top:0;bottom:0;width:var(--w)}
.mrow .tx{text-align:right;color:#4a4a4a}
.lr .sk{font:11.5px var(--mono);color:#6b6b6b;margin-top:.3rem}
.lr .hint2{font:11px var(--mono);color:#6b6b6b}
.tip{position:fixed;z-index:250;pointer-events:none;background:#141414;color:var(--paper);font:11.5px/1.5 var(--mono);padding:.3rem .6rem;opacity:0;transition:opacity .12s;transform:translate(12px,-135%);white-space:nowrap}
.tip.on{opacity:1}
.spark{margin-top:1.4rem;font:11px var(--mono);color:#4a4a4a}
.spark svg{display:block;width:100%;height:4.5rem;margin-top:.5rem;overflow:visible}
.spark .ax{stroke:#141414;stroke-width:1;vector-effect:non-scaling-stroke}
.spark .area{fill:rgba(200,50,30,.1);stroke:none}
.spark .ln{fill:none;stroke:#c8321e;stroke-width:2;stroke-linejoin:round;vector-effect:non-scaling-stroke;stroke-dasharray:1;stroke-dashoffset:1;transition:stroke-dashoffset 1.1s ease-out}
.spark.in .ln{stroke-dashoffset:0}
@media (prefers-reduced-motion: reduce) { .bar3 i, .spark .ln { transition: none; } .lr.open .more { animation: none; } }


</style>
<div class="hdr"><div class="hdr-left"><a href="/">phishing-detector</a></div><div class="hdr-nav"><a href="/rules">偵測規則</a><a href="/whitelist">白名單</a><a href="/history">案件簿</a><a href="/paste">貼信送檢</a></div></div>
<div class="dz dz-wide dz-short">
  <aside class="dz-side">
<div class="bl">
    <div class="ftab"><mark>FILE</mark><span>history</span></div>
    <h1 class="pg-title"><span class="hl">案件簿</span></h1>
    <p class="pg-sub">最近 20 次掃描的風險分布。每一列是一次掃描，色條依比例顯示各風險等級的郵件數量。</p>
</div>
<div class="br">
    {% if history %}
    <div class="nums">
      <div><b>{{ history|length }}</b><span>掃描次數</span></div>
      <div><b>{{ history|sum(attribute=2) }}</b><span>郵件總數</span></div>
      <div><b style="color:#c8321e">{{ history|sum(attribute=3) }}</b><span>高風險</span></div>
      <div><b style="color:#a8650f">{{ history|sum(attribute=4) }}</b><span>中風險</span></div>
    </div>
    <div class="spark" id="spark"></div>
 {% endif %}
  
</div>
</aside>
  <main class="dz-main">
    {% if history %}
    <div class="sh"><span class="n">01</span><h2>近期案件</h2></div>
    <div class="leg"><span><i class="dot h"></i>高風險</span><span><i class="dot m"></i>中風險</span><span><i class="dot l"></i>安全</span><span><i class="dot w"></i>白名單</span></div>
    <div class="heat" id="heat"></div>
<div class="led">
    {% for h in history %}
      <div class="lr {{ 'lv-h' if h[3] else ('lv-m' if h[4] else 'lv-l') }}" data-h="{{ h[3] }}" data-m="{{ h[4] }}" data-l="{{ h[5] }}" data-w="{{ h[6] }}" data-sk="{{ h[7] }}" data-n="{{ h[2] }}">
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
    <div class="sh"><span class="n">01</span><h2>近期案件</h2></div>
    <div class="empty2"><span class="st ink">尚無案件</span><p>案件簿還是空的，<a href="/">送出第一批信件</a>！</p></div>
    {% endif %}
  </main>
</div>
<script>
(function(){
var rows=PD.all('.lr'),NAMES={h:'高風險',m:'中風險',l:'安全',w:'白名單'},COL={h:'#c8321e',m:'#e39a2d',l:'#2e6a4d',w:'#9a9a9a'};
var tip=document.createElement('div');tip.className='tip';document.body.appendChild(tip);
rows.forEach(function(r){
  var n=+r.getAttribute('data-n')||0,bar=r.querySelector('.bar3');
  r.setAttribute('tabindex','0');r.setAttribute('role','button');r.setAttribute('aria-expanded','false');
  if(bar){bar.setAttribute('aria-label',bar.getAttribute('title')||'');bar.removeAttribute('title');}
  PD.all('.bar3 i',r).forEach(function(s,k){s.style.setProperty('--k',k);});
  var more=document.createElement('div');more.className='more';r.appendChild(more);
  var hint=document.createElement('span');hint.className='tg';hint.textContent='＋';r.appendChild(hint);
  function build(){
    var h='';
    ['h','m','l','w'].forEach(function(k){
      var v=+r.getAttribute('data-'+k)||0,pct=n?Math.round(v/n*100):0;
      h+='<div class="mrow"><span>'+NAMES[k]+'</span><span class="tk"><i style="--w:'+pct+'%;background:'+COL[k]+'"></i></span><span class="tx">'+v+' 封 · '+pct+'%</span></div>';
    });
    var sk=+r.getAttribute('data-sk')||0;
    if(sk)h+='<div class="sk">另有 '+sk+' 封被略過，不計入色條。</div>';
    more.innerHTML=h;
  }
  function toggle(){var o=r.classList.toggle('open');r.setAttribute('aria-expanded',o?'true':'false');if(o&&!more.innerHTML)build();hint.textContent=o?'－':'＋';}
  r.addEventListener('click',toggle);
  r.addEventListener('keydown',function(e){if(e.key==='Enter'||e.key===' '){e.preventDefault();toggle();}});
});
document.addEventListener('mousemove',function(e){
  var s=e.target.closest&&e.target.closest('.bar3 i');
  if(!s){tip.classList.remove('on');return;}
  var r=s.closest('.lr'),k=s.className.trim(),v=+r.getAttribute('data-'+k)||0,n=+r.getAttribute('data-n')||0;
  tip.textContent=NAMES[k]+' '+v+' 封（'+(n?Math.round(v/n*100):0)+'%）';
  tip.style.left=e.clientX+'px';tip.style.top=e.clientY+'px';tip.classList.add('on');
});
PD.onView(rows,function(r){r.classList.add('in');},.2);
var heat=document.getElementById('heat');
if(heat&&rows.length){
  var chron=rows.slice().reverse();
  heat.innerHTML='<div class="hl2">近 '+chron.length+' 次掃描（左舊右新，顏色越深＝高風險占比越高）</div><div class="hg"></div>';
  var hg=heat.querySelector('.hg');
  chron.forEach(function(r,i){
    var n=+r.getAttribute('data-n')||0,h=+r.getAttribute('data-h')||0,c=document.createElement('button');
    c.type='button';c.className='hc';c.style.setProperty('--i',i);
    c.style.setProperty('--a',(0.12+Math.min((n?h/n:0)*2.2,1)*0.88).toFixed(2));
    var when=r.firstElementChild?Array.prototype.map.call(r.firstElementChild.children,function(x){return x.textContent.trim();}).join(' '):'';
    c.setAttribute('data-tip',when+'　高風險 '+h+' / '+n+' 封');c.setAttribute('aria-label',c.getAttribute('data-tip'));
    c.addEventListener('click',function(){r.scrollIntoView({behavior:PD.RM?'auto':'smooth',block:'center'});r.classList.remove('flash');void r.offsetWidth;r.classList.add('flash');});
    hg.appendChild(c);
  });
}
document.addEventListener('mousemove',function(e){
  var c=e.target.closest&&e.target.closest('.hc');
  if(!c)return;
  tip.textContent=c.getAttribute('data-tip');tip.style.left=e.clientX+'px';tip.style.top=e.clientY+'px';tip.classList.add('on');
});
document.addEventListener('mouseout',function(e){if(e.target.closest&&e.target.closest('.hc'))tip.classList.remove('on');});

var sp=document.getElementById('spark');
if(sp&&rows.length>1){
  var data=rows.map(function(r){return +r.getAttribute('data-h')||0;}).reverse(),W=300,H=64,mx=Math.max.apply(null,data.concat([1])),st=W/(data.length-1);
  var pts=data.map(function(v,i){return (i*st).toFixed(1)+','+(H-4-(v/mx)*(H-12)).toFixed(1);});
  sp.innerHTML='<div>高風險封數趨勢（舊 → 新，共 '+data.length+' 次，最新 '+data[data.length-1]+' 封）</div><svg viewBox="0 0 300 64" preserveAspectRatio="none" role="img" aria-label="高風險封數趨勢"><line class="ax" x1="0" y1="60" x2="300" y2="60"/><polygon class="area" points="0,60 '+pts.join(' ')+' 300,60"/><polyline class="ln" pathLength="1" points="'+pts.join(' ')+'"/></svg>';
  PD.onView([sp],function(){sp.classList.add('in');},.4);
}else if(sp){sp.style.display='none';}
})();
</script>
"""

# ── 偵測規則展示頁 ────────────────────────────────────────────
RULES_HTML = COMMON_CSS + """
<style>
.play { display: grid; border: 1px solid #141414; background: #fff; }
@media (min-width: 900px) { .play { grid-template-columns: 1.35fr 1fr; } }
.play .in { padding: 1rem 1.15rem 1.2rem; }
@media (min-width: 900px) { .play .in { border-right: 1px solid #141414; } }
.play .pn { padding: 1rem 1.15rem 1.2rem; border-top: 1px solid #141414; background: #f1f1f1; }
@media (min-width: 900px) { .play .pn { border-top: 0; } }
.lb { font-family: var(--mono); font-size: 11px; font-weight: 600; letter-spacing: .08em; text-transform: uppercase; color: #141414; margin-bottom: .45rem; }
#pt { width: 100%; min-height: 6.5rem; border: 1px solid #d4d4d4; background: #f1f1f1; padding: .6rem .75rem; font: 15px/1.9 var(--sans); resize: vertical; }
#mirror { min-height: 4.5rem; padding: .5rem 0; font: 15px/2 var(--sans); white-space: pre-wrap; word-break: break-word; }
#mirror mark { background: var(--hl); color: #141414; padding: .05em .12em; }
#mirror u { text-decoration: underline wavy #c8321e; text-underline-offset: 4px; }
.hits { list-style: none; margin: .6rem 0 0; padding: 0; font-size: 13px; }
.hits li { display: flex; justify-content: space-between; gap: 1rem; padding: .35rem 0; border-top: 1px dashed #9a9a9a; }
.hits li small { font-family: var(--mono); color: #4a4a4a; }
.score { font-family: var(--serif); font-weight: 900; font-size: 3rem; line-height: 1; }
.score small { font-family: var(--mono); font-size: 12px; font-weight: 400; color: #4a4a4a; margin-left: .4rem; }
.meter { height: .8rem; border: 1px solid #141414; background: #fff; margin: .7rem 0 .3rem; }
.meter i { display: block; height: 100%; width: 0; background: #141414; transition: width .3s; }
.seg { display: flex; border: 1px solid #141414; font-family: var(--mono); font-size: 11.5px; margin: .6rem 0 .2rem; }
.seg i { font-style: normal; padding: .45rem .55rem; white-space: nowrap; overflow: hidden; border-right: 1px solid #141414; }
.seg i:last-child { border-right: 0; }
.seg .a { background: #141414; color: #f1f1f1; } .seg .b { background: #4a4a4a; color: #f1f1f1; } .seg .c { background: var(--hl); } .seg .d { background: #ffe0ee; }
.scale { display: flex; border: 1px solid #141414; font-family: var(--mono); font-size: 11.5px; }
.scale i { font-style: normal; padding: .5rem .6rem; color: #fff; }
.scale .lo { flex: 40; background: #2e6a4d; } .scale .md { flex: 30; background: #a8650f; } .scale .hi { flex: 30; background: #c8321e; }
.ticks { display: flex; font-family: var(--mono); font-size: 11px; color: #6b6b6b; margin-top: .25rem; }
.ticks span:nth-child(1) { flex: 40; } .ticks span:nth-child(2) { flex: 30; } .ticks span:nth-child(3) { flex: 30; }
.fz { display: grid; gap: 1.4rem; }
@media (min-width: 900px) { .fz { grid-template-columns: 1fr 1fr; } }
.fz .box { border: 1px solid #141414; background: #fff; padding: 1rem 1.1rem 1.15rem; }
.fz .box h3 { font-size: 1rem; font-weight: 700; }
.fz .box p { font-size: 12.5px; color: #4a4a4a; line-height: 1.75; margin-top: .5rem; }
.kwq{display:flex;align-items:center;gap:1rem;margin:0 0 1rem;font-family:var(--mono);font-size:12px}
.kwq input{flex:1;max-width:26rem;border:1px solid #141414;padding:.5rem .7rem;font:13px var(--mono);background:#fff}
#kwc{color:#6b6b6b}
.card.xp{cursor:pointer;transition:box-shadow .15s,opacity .55s,transform .55s}
.card.xp:hover,.card.open{box-shadow:4px 4px 0 #141414}
.card .kws span[role="button"]{cursor:pointer;transition:background .12s,color .12s}
.card .kws span[role="button"]:hover{background:#141414;color:#f1f1f1}
.card .ex{display:none;margin-top:.4rem;padding-top:.7rem;border-top:1px dashed #9a9a9a}
.card.open .ex{display:block;animation:pdIn .3s ease both}
.card .ex p{font:13.5px/1.9 var(--sans);color:#141414}
.card .ex .sample-btn{margin-top:.5rem;padding:.3rem .7rem}
.card[data-gi="1"] .kws span{background:#ffe58a}.card[data-gi="2"] .kws span{background:#bfe0ff}.card[data-gi="3"] .kws span{background:#c5ecd2}
#mirror mark[data-g="0"],.card .ex mark[data-g="0"]{background:#ffc3dc}
#mirror mark[data-g="1"],.card .ex mark[data-g="1"]{background:#ffe58a}
#mirror mark[data-g="2"],.card .ex mark[data-g="2"]{background:#bfe0ff}
#mirror mark[data-g="3"],.card .ex mark[data-g="3"]{background:#c5ecd2}
.card .ex mark{color:#141414;padding:.05em .12em}
.hits li[data-g] span::before{content:"";display:inline-block;width:.65rem;height:.65rem;margin-right:.45rem;border:1px solid #141414;background:#ffc3dc}
.hits li[data-g="1"] span::before{background:#ffe58a}.hits li[data-g="2"] span::before{background:#bfe0ff}.hits li[data-g="3"] span::before{background:#c5ecd2}
@media (prefers-reduced-motion: reduce){.card.open .ex{animation:none}}


</style>
<div class="hdr"><div class="hdr-left"><a href="/">phishing-detector</a></div><div class="hdr-nav"><a href="/rules">偵測規則</a><a href="/whitelist">白名單</a><a href="/history">案件簿</a><a href="/paste">貼信送檢</a></div></div>
<div class="dz dz-wide">
  <aside class="dz-side">
<div class="bl">
    <div class="ftab"><mark>FILE</mark><span>rules</span></div>
    <h1 class="pg-title"><span class="hl">偵測規則一覽</span></h1>
    <p class="pg-sub">以下為系統實際使用中的規則（關鍵字清單直接讀取自偵測程式，與實際判斷同源）。規則引擎僅是四層分析中的第一層，其分數會再與 ML、HTML/URL、AI 判讀依固定權重融合。</p>
</div>
<div class="br">
    <div class="nums">
      <div><b>{{ kw_total }}</b><span>關鍵字（4 類）</span></div>
      <div><b>{{ url_items|length }}</b><span>URL 結構規則</span></div>
      <div><b>{{ html_items|length }}</b><span>HTML 結構規則</span></div>
      <div><b>{{ whitelist_count }}</b><span>白名單網域</span></div>
    </div>
  
</div>
</aside>
    <ul class="idx" id="idx">
      <li><a href="#try"><em>00</em><span>試試看</span></a></li>
      <li><a href="#kw"><em>01</em><span>關鍵字規則 R1–R6</span></a></li>
      <li><a href="#url"><em>02</em><span>URL 結構 U1–U8</span></a></li>
      <li><a href="#html"><em>03</em><span>HTML 結構 H1–H7</span></a></li>
      <li><a href="#fuse"><em>04</em><span>融合與分級</span></a></li>
    </ul>
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
    <div class="kwq"><input id="kwq" type="search" placeholder="搜尋關鍵字，例如 密碼、verify…" aria-label="搜尋關鍵字"><span id="kwc"></span></div>
 <div class="cards" id="kwcards">
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
function cnt(id,v){var el=document.getElementById(id),from=+el.textContent||0;if(from===v)return;var tk=(el._tk=(el._tk||0)+1);PD.tween(from,v,350,function(x){if(el._tk===tk)el.textContent=Math.round(x);});}
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
    for(k=0;k<WORDS.length;k++){if(PD.kwAt(low,i,WORDS[k][0])){found=WORDS[k];break;}}
    if(found){flush();el=document.createElement('mark');el.setAttribute('data-g',found[1]);el.textContent=t.slice(i,i+found[0].length);out.appendChild(el);
      (hit[found[1]]=hit[found[1]]||{})[found[0]]=1;i+=found[0].length;}
    else{buf+=t[i];i++;}
  }
  flush();
  var raw=0,ul=document.getElementById('hits');ul.textContent='';
  Object.keys(hit).forEach(function(g){var grp=G[g],n=Object.keys(hit[g]).length,pts=n*per(grp[4]);raw+=pts;
    var li=document.createElement('li'),a=document.createElement('span'),b=document.createElement('small');
    a.textContent=grp[0]+' '+grp[1];b.textContent=Object.keys(hit[g]).join('、')+'　+'+pts;li.setAttribute('data-g',g);li.appendChild(a);li.appendChild(b);ul.appendChild(li);});
  if(links){var p=Math.min(3+links,8);raw+=p;var li2=document.createElement('li'),a2=document.createElement('span'),b2=document.createElement('small');
    a2.textContent='R5 含有連結';b2.textContent=links+' 個連結　+'+p;li2.appendChild(a2);li2.appendChild(b2);ul.appendChild(li2);}
  if(!ul.children.length){var e=document.createElement('li');e.textContent='沒有命中任何規則';ul.appendChild(e);}
  var norm=Math.min(raw*5,100);
  cnt('raw',raw);cnt('norm',norm);document.getElementById('mt').style.width=norm+'%';
}
document.addEventListener('DOMContentLoaded',function(){
  document.getElementById('pt').addEventListener('input',run);run();
  var EX={R1:'您的帳戶將於 24 小時內停用，請立即處理。',R2:'恭喜您中獎，免費領取限量禮品，並可申請退款。',R3:'請回覆您的帳號、密碼與信用卡號以完成驗證。',R4:'請立即匯款或轉帳，付款後我們將為您處理。'};
 function hlGroup(text,gi){
  var low=text.toLowerCase(),frag=document.createDocumentFragment(),buf='',i=0,k,f,ws=WORDS.filter(function(w){return w[1]===gi;});
  function fl(){if(buf){frag.appendChild(document.createTextNode(buf));buf='';}}
  while(i<text.length){
   f=null;for(k=0;k<ws.length;k++){if(PD.kwAt(low,i,ws[k][0])){f=ws[k];break;}}
   if(f){fl();var m=document.createElement('mark');m.textContent=text.slice(i,i+f[0].length);m.setAttribute('data-g',gi);frag.appendChild(m);i+=f[0].length;}
   else{buf+=text[i];i++;}
  }
  fl();return frag;
 }
 function put(text,replace,scroll){
  var pt=document.getElementById('pt');
  pt.value=replace?text:(pt.value?pt.value+' ':'')+text;
  pt.dispatchEvent(new Event('input'));
  if(scroll)document.getElementById('try').scrollIntoView({behavior:PD.RM?'auto':'smooth'});
 }
 var cards=PD.all('#kwcards .card');
 cards.forEach(function(c){
  var rid=(c.querySelector('.rid')||{}).textContent,gi=-1;
  G.forEach(function(g,k){if(g[0]===rid)gi=k;});
  c.setAttribute('data-gi',gi);
  if(gi<0)return;
  PD.all('.kws span',c).forEach(function(s){
   s.setAttribute('role','button');s.setAttribute('tabindex','0');s.title='點一下加入上方試玩區';
   function add(){put(s.textContent,false,false);PD.toast('已加入「'+s.textContent+'」到試玩區',{type:'ok',ms:1800});}
   s.addEventListener('click',function(e){e.stopPropagation();add();});
   s.addEventListener('keydown',function(e){if(e.key==='Enter'||e.key===' '){e.preventDefault();e.stopPropagation();add();}});
  });
  if(!EX[rid])return;
  c.classList.add('xp');c.setAttribute('tabindex','0');c.setAttribute('role','button');c.setAttribute('aria-expanded','false');c.title='點一下看範例';
  var ex=document.createElement('div');ex.className='ex';
  var p=document.createElement('p');p.appendChild(hlGroup(EX[rid],gi));
  var b=document.createElement('button');b.type='button';b.className='sample-btn';b.textContent='放進試玩區';
  b.addEventListener('click',function(e){e.stopPropagation();put(EX[rid],true,true);});
  ex.appendChild(p);ex.appendChild(b);c.appendChild(ex);
  function tg(){var o=c.classList.toggle('open');c.setAttribute('aria-expanded',o?'true':'false');}
  c.addEventListener('click',function(e){if(e.target.closest('button'))return;tg();});
  c.addEventListener('keydown',function(e){if((e.key==='Enter'||e.key===' ')&&e.target===c){e.preventDefault();tg();}});
 });
 var q=document.getElementById('kwq'),qc=document.getElementById('kwc');
 q.addEventListener('input',function(){
  var v=q.value.trim().toLowerCase(),n=0;
  cards.forEach(function(c){
   var meta=((c.querySelector('.rid')||{}).textContent+(c.querySelector('h3')||{}).textContent+(c.querySelector('p')||{}).textContent).toLowerCase().indexOf(v)>=0,m=0;
   PD.all('.kws span',c).forEach(function(s){var ok=!v||meta||s.textContent.toLowerCase().indexOf(v)>=0;s.style.display=ok?'':'none';if(ok)m++;});
   c.style.display=(!v||m>0)?'':'none';n+=(v?m:0);
  });
  qc.textContent=v?('找到 '+n+' 個關鍵字'):'';
 });

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
.dom s { color: #6b6b6b; }
.verdict { display: flex; flex-wrap: wrap; align-items: center; gap: .9rem 1.2rem; }
.verdict .st { font-size: 1.15rem; padding: .1rem .8rem; }
.verdict p { font-size: 13.5px; line-height: 1.8; color: #4a4a4a; flex: 1; min-width: 14rem; }
.chips { display: flex; flex-wrap: wrap; gap: .5rem; padding: 0 1.15rem 1.1rem; }
.chips button { font-family: var(--mono); font-size: 11.5px; padding: .3rem .6rem; border: 1px solid #141414; background: transparent; cursor: pointer; }
.chips button:hover { background: var(--hl); }
.chips a { font-family: var(--mono); font-size: 11.5px; color: #141414; align-self: center; text-underline-offset: 3px; }
.pass { position: relative; background: #fff; border: 1px solid #141414; padding: .95rem 1rem 1rem; display: flex; flex-direction: column; gap: .35rem; }
.pass .dn { font-family: var(--mono); font-weight: 600; font-size: 13.5px; word-break: break-all; padding-right: 1.6rem; }
.pass .dt { font-family: var(--mono); font-size: 11px; color: #6b6b6b; }
.pass .st { align-self: flex-start; margin-top: .5rem; font-size: .7rem; }
.pass .x { position: absolute; right: .55rem; top: .5rem; width: 1.5rem; height: 1.5rem; border: 0; background: transparent; font: 400 1.2rem/1 var(--mono); color: #6b6b6b; cursor: pointer; }
.pass .x:hover { background: #c8321e; color: #fff; }
.side-form { margin-top: 1.5rem; }
.side-form .lb, .lb { font-family: var(--mono); font-size: 11px; font-weight: 600; letter-spacing: .08em; text-transform: uppercase; margin-bottom: .45rem; }
.side-form .r { display: flex; gap: .5rem; }
.side-form input { flex: 1; min-width: 0; border: 1px solid #141414; padding: .55rem .7rem; font: 13px var(--mono); }
.rst { margin-top: 1rem; font-family: var(--mono); font-size: 11.5px; padding: .3rem .6rem; border: 1px solid #141414; background: transparent; cursor: pointer; }
.rst:hover { background: var(--hl); }
.pass.new{animation:passIn .5s cubic-bezier(.2,1.3,.4,1) both}
@keyframes passIn{from{opacity:0;transform:translateY(-14px) scale(.94)}to{opacity:1;transform:none}}
.pass.gone{animation:passOut .28s ease-in forwards;pointer-events:none}
@keyframes passOut{to{opacity:0;transform:scale(.92)}}
.out>*{animation:pdIn .3s ease both}
.dom .hl{background-repeat:no-repeat;background-size:0 100%;animation:sweepHl .6s .1s ease-out forwards}
@keyframes sweepHl{to{background-size:100% 100%}}
.verdict .st{animation:stampSlam .4s cubic-bezier(.2,1.7,.4,1) .15s both}
@keyframes stampSlam{from{opacity:0;transform:rotate(12deg) scale(2)}to{opacity:1;transform:rotate(-4deg) scale(1)}}
@media (prefers-reduced-motion: reduce){.pass.new,.pass.gone,.out>*,.verdict .st{animation:none}.dom .hl{animation:none;background-size:100% 100%}}


</style>
<script>
var WL = {{ domains|map(attribute=0)|list|tojson }};
var pending = {}, chkTok = 0, chkTimer = null;
function escH(x) { return String(x).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
function post(url, body) {
  return fetch(url, {method:'POST', headers:{'Content-Type':'application/json'}, body: body === undefined ? undefined : JSON.stringify(body)}).then(function (r) { return r.json(); });
}
function cards() { return Array.prototype.slice.call(document.querySelectorAll('.cards .pass')); }
function findCard(domain) { return cards().filter(function (c) { return c.querySelector('.dn').textContent === domain; })[0]; }
function setCount() {
  const n = cards().filter(function (c) { return !c.classList.contains('gone'); }).length;
  document.getElementById('wl-count').textContent = n; document.getElementById('wl-count2').textContent = n;
}
function hidePending() {
  Object.keys(pending).forEach(function (d) { const c = findCard(d); if (c) { c.classList.add('gone'); c.style.display = 'none'; } });
}
function refreshList() {
  return fetch('/whitelist').then(function (r) { return r.text(); }).then(function (html) {
    const doc = new DOMParser().parseFromString(html, 'text/html'), nc = doc.querySelector('.cards'), cur = document.querySelector('.cards');
    if (!nc || !cur) throw new Error('no list');
    const old = {}; cards().forEach(function (c) { old[c.querySelector('.dn').textContent] = 1; });
    cur.innerHTML = nc.innerHTML;
    cards().forEach(function (c) { if (!old[c.querySelector('.dn').textContent]) c.classList.add('new'); });
    hidePending();
    WL = cards().filter(function (c) { return c.style.display !== 'none'; }).map(function (c) { return c.querySelector('.dn').textContent; });
    setCount(); buildChips(); checkSender();
  });
}
function addDomain() {
  const inp = document.getElementById('domain-input'), domain = inp.value.trim();
  if (!domain) { PD.toast('請輸入網域', {type:'err'}); inp.focus(); return; }
  post('/whitelist/add', {domain: domain}).then(function (d) {
    if (!d.success) { PD.toast(d.error || '發放失敗', {type:'err'}); return; }
    inp.value = '';
    return refreshList().then(function () { PD.toast('已發放通行：' + (d.domain || domain), {type:'ok'}); });
  }).catch(function () { PD.toast('發放失敗，請稍後再試', {type:'err'}); });
}
function commitDelete(domain) {
  const p = pending[domain]; if (!p) return;
  delete pending[domain];
  function restore(msg) { p.card.classList.remove('gone'); p.card.style.display = ''; WL.push(domain); setCount(); PD.toast(msg || '撤銷失敗，已復原', {type:'err'}); }
  post('/whitelist/delete', {domain: domain}).then(function (d) { if (d.success) { if (p.card.parentNode) p.card.parentNode.removeChild(p.card); } else restore(d.error); }).catch(function () { restore(); });
}
function deleteDomain(domain) {
  const card = findCard(domain); if (!card || pending[domain]) return;
  card.classList.add('gone');
  card.addEventListener('animationend', function f() { if (card.classList.contains('gone')) card.style.display = 'none'; card.removeEventListener('animationend', f); });
  if (PD.RM) card.style.display = 'none';
  WL = WL.filter(function (x) { return x !== domain; }); setCount();
  pending[domain] = { card: card, timer: setTimeout(function () { commitDelete(domain); }, 6000) };
  PD.toast('已撤銷通行：' + domain, { ms: 6000, undo: function () {
    const p = pending[domain]; if (!p) return;
    clearTimeout(p.timer); delete pending[domain];
    card.style.display = ''; card.classList.remove('gone'); WL.push(domain); setCount();
  } });
}
window.addEventListener('pagehide', function () {
  Object.keys(pending).forEach(function (d) {
    clearTimeout(pending[d].timer);
    try { navigator.sendBeacon('/whitelist/delete', new Blob([JSON.stringify({domain: d})], {type: 'application/json'})); } catch (e) {}
  });
});
function resetWhitelist() {
  PD.toast('要重發預設通行嗎？只會補回被撤銷的預設網域，不會撤銷你發放的網域。', { ms: 9000, action: { label: '還原', fn: function () {
    post('/whitelist/reset').then(function (d) {
      if (!d.success) { PD.toast(d.error || '還原失敗', {type:'err'}); return; }
      return refreshList().then(function () { PD.toast('已重發預設通行', {type:'ok'}); });
    }).catch(function () { PD.toast('還原失敗，請稍後再試', {type:'err'}); });
  } } });
}
function checkSender(value) {
  const input = document.getElementById('check-input');
  if (value !== undefined) input.value = value;
  const sender = input.value.trim(), out = document.getElementById('check-out'), my = ++chkTok;
  if (!sender) { out.innerHTML = '<p class="pg-sub">請輸入寄件者信箱，例如 name@example.com</p>'; return; }
  post('/whitelist/check', {sender: sender}).then(function (d) {
    if (my !== chkTok) return;
    if (!d.success) { out.innerHTML = '<p class="pg-sub">' + escH(d.error || '檢查失敗') + '</p>'; return; }
    const dom = d.domain;
    if (d.matched) {
      const wl = d.whitelist_domain, pre = dom.slice(0, dom.length - wl.length);
      out.innerHTML = '<div class="dom">' + escH(pre) + '<span class="hl">' + escH(wl) + '</span></div>' +
        '<div class="verdict"><span class="st grn">放行</span><p>' + escH(d.mode) + '：寄件網域命中白名單「' + escH(wl) + '」，系統將略過分析，直接判定為安全。</p></div>';
    } else {
      const fake = WL.find(function (w) { return dom.indexOf(w) >= 0; });
      let shown = escH(dom), why = '未命中任何白名單網域，將進入完整四層分析。';
      if (fake) {
        const k = dom.indexOf(fake);
        shown = escH(dom.slice(0, k)) + '<u>' + escH(fake) + '</u>' + escH(dom.slice(k + fake.length));
        why = '網域中雖然出現「' + escH(fake) + '」，但它不是網域結尾，所以不命中，將進入完整四層分析。';
      }
      out.innerHTML = '<div class="dom">' + shown + '</div><div class="verdict"><span class="st red">不命中</span><p>' + why + '</p></div>';
    }
  }).catch(function () { if (my === chkTok) out.innerHTML = '<p class="pg-sub">檢查失敗，請稍後再試</p>'; });
}
function buildChips() {
  const box = document.querySelector('.chips'); if (!box) return;
  Array.prototype.slice.call(box.querySelectorAll('.dyn')).forEach(function (b) { box.removeChild(b); });
  if (!WL.length) return;
  const base = WL[0], typo = base.replace('o', '0') !== base ? base.replace('o', '0') : base + 'x', first = box.querySelector('a');
  [['範例④：白名單網域放在前面（不命中）', 'alert@' + base + '.verify-login.xyz'], ['範例⑤：相似拼字（不命中）', 'alert@' + typo]].forEach(function (x) {
    const b = document.createElement('button'); b.type = 'button'; b.className = 'dyn'; b.textContent = x[0];
    b.addEventListener('click', function () { checkSender(x[1]); });
    box.insertBefore(b, first);
  });
}
document.addEventListener('DOMContentLoaded', function () {
  document.getElementById('domain-input').addEventListener('keydown', function (e) { if (e.key === 'Enter') addDomain(); });
  const ci = document.getElementById('check-input');
  ci.addEventListener('keydown', function (e) { if (e.key === 'Enter') { clearTimeout(chkTimer); checkSender(); } });
  ci.addEventListener('input', function () { clearTimeout(chkTimer); chkTimer = setTimeout(function () { checkSender(); }, 350); });
  buildChips();
  checkSender('no-reply@accounts.google.com');
});
</script>
<div class="hdr"><div class="hdr-left"><a href="/">phishing-detector</a></div><div class="hdr-nav"><a href="/rules">偵測規則</a><a href="/whitelist">白名單</a><a href="/history">案件簿</a><a href="/paste">貼信送檢</a></div></div>
<div class="dz dz-wide dz-split">
  <aside class="dz-side">
<div class="bl">
    <div class="ftab"><mark>FILE</mark><span>whitelist</span></div>
    <h1 class="pg-title"><span class="hl">白名單設定</span></h1>
    <p class="pg-sub">加入白名單後，來自該網域及其子網域的信件將直接標記為安全，不進行 AI 分析。請只加入確定可信任的網域。</p>
</div>
<div class="br">
    <div class="nums"><div><b id="wl-count">{{ count }}</b><span>目前白名單網域</span></div><div><b>2</b><span>比對方式：完全相同／子網域</span></div></div>
    <div class="side-form">
      <div class="lb">發放通行</div>
      <div class="r"><input type="text" id="domain-input" placeholder="例如：example.com"><button class="add-btn" onclick="addDomain()">發放</button></div>
      <button class="rst" onclick="resetWhitelist()">重發預設通行</button>
    </div>
  
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

    <div class="sh"><span class="n">02</span><h2>目前白名單（<span id="wl-count2">{{ count }}</span> 個）</h2><p>每個網域及其子網域都會被放行。</p></div>
    <div class="cards">
    {% for d in domains %}
      <div class="pass{% if d[1] %} custom{% endif %}">
        <button class="x" title="撤銷" onclick="deleteDomain('{{ d[0] }}')">×</button>
        <div class="dn">{{ d[0] }}</div>
        <div class="dt">{{ ('發放時間：' ~ d[1][:10]) if d[1] else '預設網域' }}</div>
        <span class="st grn">已放行 CLEARED</span>
      </div>
    {% endfor %}
    </div>
  </main>
</div>
"""


for _n in ("HOME_HTML","LOADING_HTML","ERROR_HTML","PASTE_HTML","RESULT_HTML","HISTORY_HTML","RULES_HTML","WHITELIST_HTML"):
    globals()[_n] += DESIGN2_CSS

_TITLES = {
    "HOME_HTML": "phishing-detector｜找出可疑郵件",
    "LOADING_HTML": "送檢中｜phishing-detector",
    "ERROR_HTML": "ERR_TITLE｜phishing-detector",
    "PASTE_HTML": "貼信送檢｜phishing-detector",
    "RESULT_HTML": "檢驗報告｜phishing-detector",
    "HISTORY_HTML": "案件簿｜phishing-detector",
    "RULES_HTML": "偵測規則｜phishing-detector",
    "WHITELIST_HTML": "白名單｜phishing-detector",
}
for _n, _ti in _TITLES.items():
    globals()[_n] = globals()[_n].replace('<meta name="viewport" content="width=device-width, initial-scale=1">', '<meta name="viewport" content="width=device-width, initial-scale=1">\n<title>' + _ti + '</title>', 1)
