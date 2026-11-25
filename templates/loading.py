"""掃描中頁面"""
from ._base import COMMON_CSS, finish

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
<header class="hdr"><div class="hdr-left"><a href="/">phishing-detector</a></div><div class="hdr-nav"><a href="/rules">偵測規則</a><a href="/whitelist">白名單</a><a href="/history">案件簿</a><a href="/paste">貼信送檢</a></div></header>
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
      setTimeout(function () { const u = '/result/' + d.scan_id; if (window.PDX) PDX.go(u); else window.location.href = u; }, PD.RM ? 900 : 1500);
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


LOADING_HTML = finish(LOADING_HTML, "送檢中｜phishing-detector")
