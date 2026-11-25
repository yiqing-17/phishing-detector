"""白名單頁"""
from ._base import COMMON_CSS, finish

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
function hashStr(s) { var h = 7; for (var i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) | 0; return Math.abs(h); }
function clampN(v, a, b) { return Math.max(a, Math.min(b, v)); }
function stampSvg(domain, custom, dd, hs) {
  var n = domain.length, up = escH(domain.toUpperCase()), word = custom ? 'GRANTED' : 'CLEARED';
  var shape = n <= 12 ? (hs % 3 === 0 ? 'rect' : 'circle') : (n <= 22 ? (hs % 2 ? 'oval' : 'rect') : 'rect');
  var sub = custom ? ('GRANTED' + (dd ? ' · ' + dd : '')) : 'DEFAULT · CLEARED';
  var mono = 'font-family="IBM Plex Mono,ui-monospace,monospace"';
  if (shape === 'circle') {
    var id = 'rp' + hs, txt = up + ' · ' + word + ' · ', chars = txt.length, fs = 9.4;
    var sp = Math.max(0, (272 - chars * fs * 0.6) / chars);
    return '<svg viewBox="0 0 120 120" data-shape="circle"><g style="filter:url(#ink)"><circle cx="60" cy="60" r="53" fill="none" stroke="currentColor" stroke-width="3"/><circle cx="60" cy="60" r="35" fill="none" stroke="currentColor" stroke-width="1.2"/><path id="' + id + '" d="M60,60 m-44,0 a44,44 0 1,1 88,0 a44,44 0 1,1 -88,0" fill="none"/><text ' + mono + ' font-size="' + fs + '" font-weight="700" letter-spacing="' + sp.toFixed(2) + '" fill="currentColor"><textPath href="#' + id + '">' + txt + '</textPath></text><text x="60" y="' + (dd ? 62 : 68) + '" text-anchor="middle" font-family="Georgia,serif" font-size="26" font-weight="900" fill="currentColor">✓</text>' + (dd ? '<text x="60" y="80" text-anchor="middle" ' + mono + ' font-size="8" fill="currentColor">' + escH(dd) + '</text>' : '') + '</g></svg>';
  }
  var f2 = clampN(128 / (n * 0.6), 7.5, 13);
  if (shape === 'oval') {
    return '<svg viewBox="0 0 170 100" data-shape="oval"><g style="filter:url(#ink)"><ellipse cx="85" cy="50" rx="80" ry="42" fill="none" stroke="currentColor" stroke-width="3"/><ellipse cx="85" cy="50" rx="72" ry="34" fill="none" stroke="currentColor" stroke-width="1"/><text x="85" y="52" text-anchor="middle" ' + mono + ' font-size="' + f2.toFixed(1) + '" font-weight="700" fill="currentColor">' + escH(domain) + '</text><text x="85" y="67" text-anchor="middle" ' + mono + ' font-size="7.4" letter-spacing="1.2" fill="currentColor">' + escH(sub) + '</text></g></svg>';
  }
  var head = '<svg viewBox="0 0 170 82" data-shape="rect"><g style="filter:url(#ink)"><rect x="2" y="2" width="166" height="78" fill="none" stroke="currentColor" stroke-width="2.8"/><rect x="8" y="8" width="154" height="66" fill="none" stroke="currentColor" stroke-width="1"/>';
  var subTxt = '<text x="85" y="%Y%" text-anchor="middle" ' + mono + ' font-size="7.4" letter-spacing="1.2" fill="currentColor">' + escH(sub) + '</text></g></svg>';
  if (n > 24) {
    var mid = n / 2, cut = -1, best = 1e9;
    for (var i = 1; i < n - 1; i++) { if (domain.charAt(i) === '.' && Math.abs(i - mid) < best) { best = Math.abs(i - mid); cut = i + 1; } }
    if (cut < 0) cut = Math.ceil(mid);
    var l1 = domain.slice(0, cut), l2 = domain.slice(cut), f4 = clampN(144 / (Math.max(l1.length, l2.length) * 0.6), 7.5, 12);
    return head + '<text x="85" y="33" text-anchor="middle" ' + mono + ' font-size="' + f4.toFixed(1) + '" font-weight="700" fill="currentColor">' + escH(l1) + '</text><text x="85" y="48" text-anchor="middle" ' + mono + ' font-size="' + f4.toFixed(1) + '" font-weight="700" fill="currentColor">' + escH(l2) + '</text>' + subTxt.replace('%Y%', '64');
  }
  var f3 = clampN(144 / (n * 0.6), 7.5, 13);
  return head + '<text x="85" y="40" text-anchor="middle" ' + mono + ' font-size="' + f3.toFixed(1) + '" font-weight="700" fill="currentColor">' + escH(domain) + '</text>' + subTxt.replace('%Y%', '58');
}
function decoratePasses() {
  cards().forEach(function (c) {
    if (c.getAttribute('data-st')) return;
    c.setAttribute('data-st', '1');
    const dn = c.querySelector('.dn').textContent.trim(), custom = c.classList.contains('custom'), hs = hashStr(dn);
    const m = /([0-9]{4})-([0-9]{2})-([0-9]{2})/.exec((c.querySelector('.dt') || {}).textContent || '');
    const w = document.createElement('span'); w.className = 'stamp-svg'; w.setAttribute('aria-hidden', 'true');
    w.innerHTML = stampSvg(dn, custom, m ? m[2] + '.' + m[3] : '', hs);
    c.insertBefore(w, c.firstChild);
    c.style.setProperty('--r', ((hs % 19) - 9) + 'deg'); c.style.setProperty('--j', (hs % 9) - 4);
    c.title = dn + (custom ? '（你發放的通行）' : '（預設通行）');
  });
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
    decoratePasses();
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
        '<div class="verdict"><span class="st grn">放行</span><p>' + escH(d.mode) + '：寄件網域命中白名單「' + escH(wl) + '」。Gmail 掃描時需 DMARC 驗證通過才會略過分析；驗證失敗會視為疑似冒用，貼信模式無法驗證寄件者，仍會完整分析。</p></div>';
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
  decoratePasses();
  buildChips();
  checkSender('no-reply@accounts.google.com');
});
</script>
<header class="hdr"><div class="hdr-left"><a href="/">phishing-detector</a></div><div class="hdr-nav"><a href="/rules">偵測規則</a><a href="/whitelist">白名單</a><a href="/history">案件簿</a><a href="/paste">貼信送檢</a></div></header>
<svg width="0" height="0" style="position:absolute" aria-hidden="true" focusable="false"><defs><filter id="ink"><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="4" result="t"/><feColorMatrix in="t" type="matrix" values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 -2.4 2.0" result="m"/><feComposite in="SourceGraphic" in2="m" operator="in"/></filter></defs></svg>
<div class="dz dz-wide dz-split">
  <aside class="dz-side">
<div class="bl">
    <div class="ftab"><mark>FILE</mark><span>whitelist</span></div>
    <h1 class="pg-title"><span class="hl">白名單設定</span></h1>
    <p class="pg-sub">加入白名單後，來自該網域的信件在 Gmail 的 DMARC 驗證通過時，才會直接標記為安全、不進行分析；驗證失敗會視為疑似冒用並提高風險，沒有驗證結果（如貼信模式）則照常完整分析。請只加入確定可信任的網域。</p>
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

WHITELIST_HTML = finish(WHITELIST_HTML, "白名單｜phishing-detector")
