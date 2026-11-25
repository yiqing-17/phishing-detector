"""首頁"""
from ._base import COMMON_CSS, finish
from ._base import kw_json as _kw_json

HOME_HTML = COMMON_CSS + """
<style>
html,body{background:var(--paper);color:#141414;font-family:var(--sans);-webkit-font-smoothing:antialiased;scroll-behavior:smooth}
.wrap{max-width:1360px;margin:0 auto;padding:0 2rem}
.mono{font-family:var(--mono)}
.hero{padding:clamp(2.5rem,7vh,5rem) 0 clamp(3rem,8vh,6rem)}
.hero .wrap{display:grid;gap:3rem;align-items:center}
@media(min-width:1000px){.hero .wrap{grid-template-columns:1fr 1.02fr;gap:3rem;min-height:calc(100svh - 3rem - 12.5rem)}}
h1{font-family:var(--serif);font-weight:900;font-size:clamp(2.3rem,4.7vw,4.4rem);line-height:1.2;letter-spacing:-.01em;text-wrap:balance}
h1 .hl{background:linear-gradient(transparent 56%,var(--hl) 56%)}
.sub{margin-top:1.5rem;max-width:36rem;color:#4a4a4a;font-size:16px;line-height:1.85}
.cta{margin-top:2.25rem;display:flex;flex-direction:column;gap:.6rem;max-width:30rem}
.priv{margin:1.1rem 0 0;max-width:30rem;font-size:12.5px;line-height:1.75;color:#555}
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
.step{display:grid;grid-template-columns:2.6rem 1fr;gap:.3rem 1rem;align-content:center;min-height:56vh;padding:1.4rem 0;border-top:1px solid #d4d4d4;opacity:.85;transition:opacity .35s,background .15s}
.step.act{opacity:1}
.step h3{transition:opacity .35s}.step:not(.act) h3{opacity:.5}
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
.qpick{display:flex;justify-content:space-between;gap:1rem;margin-top:-.2rem;font:12.5px var(--sans);color:#4a4a4a}
.qpick b{flex:none;white-space:nowrap;font:600 12px var(--mono);color:#141414}
.qpick.off{display:none}
.qmail .pk{display:inline-block;position:relative;margin:0;padding:0 1px;border:0;border-radius:0;background:none;color:inherit;font:inherit;line-height:inherit;text-align:inherit;cursor:pointer;word-break:break-all}
.qmail .pk:hover:not(:disabled){text-decoration:underline dotted #141414;text-underline-offset:3px}
.qmail .lw{white-space:nowrap}.qmail .lw .pk{white-space:normal}
.qmail .pk:disabled{cursor:default}
.qmail .pk::after{content:"";position:absolute;inset:-1px -2px;border:1.5px dashed #141414;pointer-events:none;clip-path:inset(0 100% 0 0);transition:clip-path .28s ease-out}
.qmail .pk.on::after{clip-path:inset(0 0 0 0)}
.qmail .pk:focus-visible{outline:2px solid #141414;outline-offset:2px}
.qcmp{margin:.2rem 0 .8rem;padding:.7rem .9rem;border:1px solid #141414;background:#fff;font:13.5px/1.8 var(--sans)}
.qcmp .sw{display:inline-block;width:.95rem;height:.7rem;margin:0 .35rem -.05rem 0}
.qcmp .sw.h{background:var(--hl)}
.qcmp .sw.o{border:1.5px dashed #141414;box-sizing:border-box}
.qcmp small{display:block;color:#6b6b6b;font-size:12.5px}
@media(pointer:coarse){.qmail .pk{min-height:28px;padding:.2rem .2rem;margin:.05rem 0}}
@media(prefers-reduced-motion:reduce){.qmail .pk::after{transition:none}}
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
/* 手機：印章縮小並上移，避免壓住信頭網域 */
@media(max-width:480px){.stamp{font-size:1.35rem;top:-1.95rem;right:-.8rem}.stamp small{font-size:.52rem}.vstamp{font-size:1.35rem;top:-1.75rem}.vstamp small{font-size:.52rem}.qmail .vstamp{top:-1.9rem;right:-.6rem}}
</style>
<header class="hdr"><div class="hdr-left"><a href="/">phishing-detector</a></div><div class="hdr-nav"><a href="/rules">偵測規則</a><a href="/whitelist">白名單</a><a href="/history">案件簿</a><a href="/paste">貼信送檢</a></div></header>
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
    <p class="priv">只讀取信件（Gmail 唯讀權限），不會修改或刪除。掃描結束後伺服器不再保留授權憑證，可隨時到 Google 帳戶撤銷授權。信件內容只存在伺服器記憶體（約 1 小時後清除）、不寫入資料庫；案件簿保存統計數字，高風險信的事件單會保存寄件者、主旨（各 120 字內）與處理紀錄。預估風險達中等以上的信件（每次掃描最多 6 封），會把寄件者、主旨、內文前 3,000 字與信中的連結清單送到第三方 AI 服務 Groq 分析，伺服器也會對信中連結發出標頭請求並查詢 rdap.org 的網域註冊資料（內文可能含個資，請自行評估）。</p>
  </div>
  <div class="docwrap" data-parallax="0.05">
    <div class="stamp" role="button" tabindex="0" aria-label="可疑 SUSPICIOUS 印章，重播標記動畫" title="點擊重播">可疑<small>SUSPICIOUS</small></div>
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
    <div class="qpick" id="qpick"><span>先圈出你覺得可疑的地方（也可以不圈），再判斷。</span><b id="qpc" aria-live="polite">已圈 0</b></div>
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
  <h2>ML 層<span class="hl">英文資料集</span>測試結果</h2>
  <div class="mt-ds">資料集　Phishing Email Dataset（英文），清理後 82,077 筆（訓練 65,661 / 測試 16,416）。僅以「完全相同文字」去重，來源間的近似重複可能使數字偏高；此模型不適用中文信件，中文信件由規則引擎判斷。</div>
  <div class="mt4 bigstats">
    <div class="bs"><span class="k">Accuracy</span><b><span class="cu" data-to="98.41">98.41</span><i>%</i></b><span class="bb" style="--w:98.41%"></span></div>
    <div class="bs"><span class="k">Precision</span><b><span class="cu" data-to="98.28">98.28</span><i>%</i></b><span class="bb" style="--w:98.28%"></span></div>
    <div class="bs"><span class="k">Recall</span><b><span class="cu" data-to="98.68">98.68</span><i>%</i></b><span class="bb" style="--w:98.68%"></span></div>
    <div class="bs"><span class="k">F1</span><b><span class="cu" data-to="98.48">98.48</span><i>%</i></b><span class="bb" style="--w:98.48%"></span></div>
  </div>
  <p class="note">以上僅為第 2 層 ML 模型在<b>英文</b>測試資料上的表現，不代表整體四層系統在真實信箱中的準確率。</p>
  <h3 style="margin-top:28px">整體系統・中文實測（不含 Agent）</h3>
  <div class="mt-ds">自建合成中文信件，門檻 40。第一列為主測試集（n=50）；第二列為「困難樣本」（n=32：帶官方連結的正常信、無連結的詐騙），該集只評估、不調參。</div>
  <div class="mt4 bigstats">
    <div class="bs"><span class="k">主測試集 Recall</span><b>88<i>%</i></b><span class="bb" style="--w:88%"></span></div>
    <div class="bs"><span class="k">主測試集 誤報率</span><b>0<i>%</i></b><span class="bb" style="--w:0%"></span></div>
    <div class="bs"><span class="k">困難樣本 Recall</span><b>50<i>%</i></b><span class="bb" style="--w:50%"></span></div>
    <div class="bs"><span class="k">困難樣本 誤報率</span><b>40<i>%</i></b><span class="bb" style="--w:40%"></span></div>
  </div>
  <p class="note">樣本數小、皆為人工撰寫，信賴區間很寬；完整方法、限制與重現指令見 repo 的 eval/RESULTS.md。</p>
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
   {phish:true,from:'service@twbank-secure.example',hw:'網址和顯示文字不一樣',subj:'【重要】|您的帳戶|將於 24 小時內|凍結',
    body:['親愛的客戶：|偵測到您的帳戶|有異常登入。|請立即|點擊「',{l:'登入驗證',u:'http://twbank-secure.example/verify'},'」，|輸入帳號與密碼，|否則帳戶|將被停用。'],
    ml:['hot','偏高','整體用詞接近釣魚樣本'],url:['hot','不一致','連結顯示為銀行登入，實際網域卻是 twbank-secure.example'],ai:['hot','索取憑證','信件要求輸入帳號與密碼']},
   {phish:false,from:'amy.chen@company.example',hw:'沒有連結，也沒有要資料',subj:'週五專案會議|改期',
    body:['各位好，','週五的專案會議|改到下午三點，|議程請見附件。','有問題再跟我說，|謝謝。'],
    ml:['cool','偏低','用詞接近一般工作信件'],url:['cool','無連結','內文沒有網址，也沒有隱藏元素'],ai:['cool','意圖正常','只是通知時間變更，沒有索取資訊']},
   {phish:false,from:'receipts@shop.example',hw:'只通知出貨，沒要任何資料',subj:'您的訂單 #A1024 |已出貨',
    body:['您的訂單 #A1024 |已出貨，|預計 2 日內送達。','可到官網「訂單查詢」頁面|查看物流，|不需要提供|任何個人資料。'],
    ml:['cool','偏低','用詞接近訂單通知'],url:['cool','無連結','沒有可點擊的網址'],ai:['cool','意圖正常','單純通知出貨，沒有要求付款或登入']},
   {phish:true,from:'no-reply@parcel-tw.example',hw:'小額運費是常見誘餌',subj:'包裹無法投遞，|請補繳運費',
    body:['您的包裹地址不完整，|請立即|點擊 ',{l:'補繳運費',u:'http://parcel-tw-pay.example/pay'},' 完成付款 NT$25，|逾期將退回寄件人。'],
    ml:['hot','偏高','運費補繳類用詞常見於釣魚樣本'],url:['hot','不一致','連結指向 parcel-tw-pay.example，與寄件網域不同'],ai:['hot','誘導付款','以小額運費誘使輸入付款資料']},
   {phish:true,from:'support@paypa1-help.example',hw:'paypa1：數字 1 假扮字母 l',subj:'Action required:| your account is suspended',
    body:['Your account has been suspended. |Verify now |to avoid permanent closure. |Enter your password |and credit card number at ',{l:'http://paypal.com/login',u:'http://paypa1-help.example/login'},'.'],
    ml:['hot','偏高','用詞接近釣魚樣本'],url:['hot','仿冒網域','paypa1 把字母 l 換成數字 1，且顯示網址與實際不符'],ai:['hot','索取憑證','要求提供密碼與信用卡號']}
  ];
  Q.forEach(function(q){q.subjc=q.subj.split('|');q.subj=q.subjc.join('');q.bodyc=q.body.map(function(p){return typeof p==='string'?p.split('|'):p;});q.body=q.bodyc.map(function(p){return Array.isArray(p)?p.join(''):p;});q.bodyc.forEach(function(e,k){if(Array.isArray(e))return;e.pre='';e.post='';var pv=q.bodyc[k-1],nx=q.bodyc[k+1],m1,m2;if(Array.isArray(pv)){m1=/[「『（(]+$/.exec(pv[pv.length-1]);if(m1){e.pre=m1[0];pv[pv.length-1]=pv[pv.length-1].slice(0,pv[pv.length-1].length-m1[0].length);}}if(Array.isArray(nx)){m2=/^[」』）),，。、；：！？.]+/.exec(nx[0]);if(m2){e.post=m2[0];nx[0]=nx[0].slice(m2[0].length);}}});});
  var qi=0,qok=0,qov=0,qrh=0,qmk=0,answered=false,visible=false,chunks=[];
  var elMail=document.getElementById('qmail'),elAct=document.getElementById('qact'),elRes=document.getElementById('qres'),elN=document.getElementById('qn'),elS=document.getElementById('qs');
  var qpick=document.getElementById('qpick'),qpc=document.getElementById('qpc');
  function hitRanges(txt){
    var low=txt.toLowerCase(),r=[],i,k;
    for(i=0;i<low.length;i++){
      for(k=0;k<groups.length;k++){
        var g=groups[k],hit=null;
        for(var m=0;m<g.words.length;m++){if(PD.kwAt(low,i,g.words[m])&&(!hit||g.words[m].length>hit.length))hit=g.words[m];}
        if(hit){r.push([i,i+hit.length,g.id]);i+=hit.length-1;break;}
      }
    }
    return r;
  }
  function hlText(txt){
    var r=hitRanges(txt),out='',pos=0;
    r.forEach(function(x){out+=esc(txt.slice(pos,x[0]))+'<mark data-r="'+x[2]+'">'+esc(txt.slice(x[0],x[1]))+'</mark>';pos=x[1];});
    return out+esc(txt.slice(pos));
  }
  function isWord(t){
    for(var i=0;i<t.length;i++){var c=t.charCodeAt(i);if((c>=48&&c<=57)||(c>=65&&c<=90)||(c>=97&&c<=122)||(c>=13312&&c<=40959))return true;}
    return false;
  }
  function pkPart(txt,pieces,isLink){
    var r=hitRanges(txt),pos=0,out='';
    pieces.forEach(function(p){
      var core=p.replace(/^ +/,'').replace(/ +$/,''),lead=p.length-p.replace(/^ +/,'').length,trail=p.length-lead-core.length,s0=pos+lead,e0=s0+core.length;
      pos+=p.length;
      if(!isWord(core)){out+=esc(p);return;}
      var c={txt:core,s:s0,r:r,on:false,hit:r.some(function(x){return x[0]<e0&&x[1]>s0;}),i:chunks.length};
      chunks.push(c);
      out+=esc(p.slice(0,lead))+'<button type="button" class="pk'+(isLink?' lnk':'')+'" data-i="'+c.i+'" aria-pressed="false">'+esc(core)+'</button>'+esc(p.slice(p.length-trail));
    });
    return out;
  }
  function markChunk(c){
    var out='',pos=c.s,e=c.s+c.txt.length;
    c.r.forEach(function(x){var a=Math.max(x[0],c.s),b=Math.min(x[1],e);if(a>=b)return;out+=esc(c.txt.slice(pos-c.s,a-c.s))+'<mark data-r="'+x[2]+'">'+esc(c.txt.slice(a-c.s,b-c.s))+'</mark>';pos=b;});
    return out+esc(c.txt.slice(pos-c.s));
  }
  function layer1(q){
    var full=('from: '+q.from+' subject: '+q.subj+' body: '+q.body.map(function(p){return typeof p==='string'?p:p.l;}).join('')).toLowerCase(),raw=0,hits=[];
    groups.forEach(function(g){var h=g.words.filter(function(w){for(var i=0;i<full.length;i++){if(PD.kwAt(full,i,w))return true;}return false;});raw+=h.length*g.w;h.forEach(function(w){hits.push(w);});});
    return{raw:raw,hits:hits};
  }
  function showQ(){
    answered=false;var q=Q[qi];
    elN.textContent=(qi+1)+' / '+Q.length;elS.textContent='答對 '+qok;chunks=[];qpick.className='qpick';qpc.textContent='已圈 0';
    elMail.className='qmail';void elMail.offsetWidth;elMail.className='qmail in';
    var pf=pkPart(q.from,[q.from],false),ps=pkPart(q.subj,q.subjc,false),pb=q.bodyc.map(function(e){if(Array.isArray(e))return pkPart(e.join(''),e.filter(function(x){return x!=='';}),false);var b=pkPart(e.l,[e.l],true);return (e.pre||e.post)?'<span class="lw">'+esc(e.pre)+b+esc(e.post)+'</span>':b;}).join('');
    elMail.innerHTML='<div class="lh">'+esc(q.from.split('@')[1])+'</div><dl><div><dt>寄件者</dt><dd>'+pf+'</dd></div><div><dt>主　旨</dt><dd>'+ps+'</dd></div></dl><p>'+pb+'</p><div class="status" id="qst">將游標移到藍色連結上，看它真正會連到哪裡。</div>';
    all('.pk',elMail).forEach(function(b){chunks[+b.getAttribute('data-i')].el=b;});
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
    qpick.className='qpick off';
    var ov=0,ms=0,ex=0,hc=0,mk=0;
    chunks.forEach(function(c){c.el.disabled=true;c.el.innerHTML=markChunk(c);if(c.hit){hc++;c.el.classList.add('hit');}if(c.on)mk++;if(c.hit&&c.on)ov++;else if(c.hit)ms++;else if(c.on)ex++;});
    qov+=ov;qrh+=hc;qmk+=mk;
    var cmpHtml='<div class="qcmp">'+(mk?'<span class="sw o"></span>你圈了 '+mk+' 處　<span class="sw h"></span>規則引擎命中 '+hc+' 處<br>重疊 '+ov+'．漏標 '+ms+'．多標 '+ex+(ex?'<small>'+(q.phish?'多標不算錯：規則引擎沒命中的地方，可能由其他層抓到。':'這封是正常信件：你圈的地方規則引擎都沒有命中，不算破綻。')+'</small>':''):(hc?'你這題沒有圈選；規則引擎命中 '+hc+' 處（粉色標記）。':'你這題沒有圈選；規則引擎沒有命中任何關鍵字。'))+'</div>';
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
    elRes.innerHTML='<div class="qfb '+(right?'ok':'no')+'"><span>'+(right?'猜對了':'差一點')+'</span>　'+(q.phish?'這是釣魚信':'這封是正常信件')+'</div>'+cmpHtml+'<ul class="layers">'+rows.map(function(r,i){return '<li><b>'+(i+1)+'</b><span class="nm">'+r[0]+'</span><span class="ds">'+r[1]+'</span></li>';}).join('')+'</ul><div class="qnext"><button type="button" class="btn" id="qnext"><span>'+(last?'看結果':'下一封')+'</span><span class="key">→</span></button></div>';
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
    var pkmsg=qmk?'你一共圈了 '+qmk+' 處，其中 '+qov+' 處和規則引擎的命中重疊（規則引擎共命中 '+qrh+' 處）。':'你這次沒有圈選。下次先圈出可疑的地方，再看規則引擎抓到什麼。';
    elRes.className='qres on';
    elRes.innerHTML='<div class="qsum"><b>'+qok+' / '+Q.length+'</b><p>'+msg+'</p><p>'+pkmsg+'</p><div class="qnext"><a class="btn" href="/paste" data-key="p"><span>貼上你的信試試</span><span class="key">P</span></a><a class="btn o" href="/login"><span>授權 Google 送檢</span><span class="key">S</span></a><button type="button" class="btn o" id="qagain"><span>再玩一次</span><span class="key">R</span></button></div></div>';
    document.getElementById('qagain').addEventListener('click',function(){qi=0;qok=0;qov=0;qrh=0;qmk=0;elMail.style.display='';showQ();});
  }
  elMail.addEventListener('click',function(e){
    var b=e.target.closest?e.target.closest('.pk'):null;if(!b||answered)return;
    var c=chunks[+b.getAttribute('data-i')];if(!c)return;
    c.on=!c.on;b.classList.toggle('on',c.on);b.setAttribute('aria-pressed',c.on?'true':'false');
    qpc.textContent='已圈 '+chunks.filter(function(x){return x.on;}).length;
    if(b.classList.contains('lnk')){var lq=Q[qi].body.filter(function(p){return typeof p!=='string';})[0],st=document.getElementById('qst');if(lq&&st){st.className='status on';st.innerHTML='<span class="k">顯示文字</span> '+esc(lq.l)+' <span class="k">→ 實際連結</span> <span class="u">'+esc(lq.u)+'</span>';}}
  });
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

HOME_HTML = finish(HOME_HTML, "phishing-detector｜找出可疑郵件")
