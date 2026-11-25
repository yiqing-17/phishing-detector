"""貼上分析頁"""
from ._base import COMMON_CSS, finish
from ._base import kw_json as _kw_json

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
.pnote { margin: .9rem 0 0; max-width: 34rem; font-size: 12.5px; line-height: 1.75; color: #555; }
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
/* ── 送檢轉場（方案 A）：只在送出時建立，不影響原本表單 ── */
.sx{position:fixed;inset:0;z-index:9000;display:grid;place-items:center;color:#f1f1f1;overflow:hidden}
.sx-wipe{position:absolute;inset:0;background:#141414;clip-path:inset(0 100% 0 0);animation:sxaWipe .33s cubic-bezier(.7,0,.2,1) forwards}
.sx-edge{position:absolute;top:0;bottom:0;left:0;width:6px;background:var(--hl);animation:sxaEdge .33s cubic-bezier(.7,0,.2,1) forwards}
@keyframes sxaWipe{to{clip-path:inset(0)}}
@keyframes sxaEdge{to{transform:translateX(100vw)}}
.sx-live{position:absolute;left:-9999px;width:1px;height:1px;overflow:hidden}
.sx-skip{position:absolute;top:1.2rem;right:1.4rem;z-index:3;font:600 12px var(--mono);letter-spacing:.08em;color:#f1f1f1;background:transparent;border:1px solid #f1f1f1;padding:.4rem .8rem;cursor:pointer;border-radius:0}
.sx-skip:hover,.sx-skip:focus-visible{background:var(--hl);color:#141414;border-color:var(--hl);outline:0}
.sx-lbl{position:absolute;top:1.3rem;left:1.5rem;z-index:3;display:flex;gap:.7rem;align-items:baseline;font:600 12px var(--mono);letter-spacing:.12em}
.sx-lbl .no{background:var(--hl);color:#141414;padding:.05rem .45rem;font-weight:700}
.sx-lbl .ct{font-style:normal;color:var(--hl)}
.sx.pre .sx-lbl{visibility:hidden}
.sx-stage{position:relative;z-index:2;width:min(620px,calc(100% - 2.4rem));display:grid;gap:1rem;justify-items:center}
.sx .sx-letter{width:100%;margin:0;padding:1.1rem 1.4rem 1.2rem;color:#141414;animation:sxaIn .42s cubic-bezier(.2,.8,.2,1) .16s backwards}
@keyframes sxaIn{from{transform:translateX(-18vw) rotate(-5deg)}}
.sx-row{display:grid;grid-template-columns:4.2rem minmax(0,1fr);gap:.4rem;padding:.12rem 0;font:12px var(--mono)}
.sx-row span{color:#6b6b6b;letter-spacing:.06em}
.sx-row b{font-weight:600;font-size:13px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.sx-body{position:relative;margin-top:.8rem;padding-top:.8rem;border-top:1px dashed #b5b5b5;font:14px/1.9 var(--sans);white-space:pre-wrap;word-break:break-word;display:-webkit-box;-webkit-line-clamp:6;-webkit-box-orient:vertical;overflow:hidden}
.sx-body mark{color:inherit;background-color:transparent;background-image:linear-gradient(var(--c,#ffc3dc),var(--c,#ffc3dc));background-repeat:no-repeat;background-size:100% 100%;padding:0 .08em;margin:0 -.08em}
.sx-body mark[data-u]{background-image:linear-gradient(#ff6fae,#ff6fae);background-size:0 3px;background-position:0 100%;transition:background-size .35s ease}
.sx.p3 .sx-body mark[data-u],.sx.p4 .sx-body mark[data-u]{background-size:100% 3px}
.sx.pre .sx-body mark[data-g]{background-size:0 100%}
.sx.p1 .sx-body mark[data-g]{animation:sxaInk .32s ease backwards;animation-delay:var(--d,0s)}
@keyframes sxaInk{from{background-size:0 100%}}
.sx-scan{position:absolute;left:-1rem;right:-1rem;top:0;height:4px;background:var(--hl);box-shadow:0 0 0 1px #141414;visibility:hidden;z-index:2}
.sx.p1 .sx-scan{visibility:visible;animation:sxaScan .52s linear forwards}
.sx.p2 .sx-scan{display:none}
@keyframes sxaScan{from{transform:translateY(0)}to{transform:translateY(var(--h,200px))}}
.sx-bar{width:100%;height:4px;background:#3a3a3a;visibility:hidden}
.sx.p2 .sx-bar{visibility:visible}
.sx-bar i{display:block;height:100%;background:var(--hl);transform-origin:left;transform:scaleX(0)}
.sx.p2 .sx-bar i{animation:sxaBar .38s linear forwards}
@keyframes sxaBar{to{transform:scaleX(1)}}
.sx-doms{display:flex;gap:.5rem;flex-wrap:wrap;justify-content:center;min-height:1.6rem;font:600 12px var(--mono)}
.sx-doms span{background:var(--hl);color:#141414;padding:.1rem .55rem;animation:sxaChip .25s ease backwards}
@keyframes sxaChip{from{clip-path:inset(0 100% 0 0)}}
.sx-sq{display:flex;gap:.4rem;visibility:hidden}
.sx.p4 .sx-sq{visibility:visible}
.sx-sq i{width:26px;height:12px;border:1px solid #f1f1f1;background:transparent}
.sx.p4 .sx-sq i:nth-child(-n+3){background:var(--hl);border-color:var(--hl);animation:sxaSq .2s ease backwards}
.sx.p4 .sx-sq i:nth-child(2){animation-delay:.08s}
.sx.p4 .sx-sq i:nth-child(3){animation-delay:.16s}
@keyframes sxaSq{from{background-color:transparent}}
.sx-sq i.w{animation:sxaPulse .7s ease-in-out infinite alternate}
@keyframes sxaPulse{to{background:var(--hl);border-color:var(--hl)}}
.sx-sq i.ok{background:var(--hl);border-color:var(--hl);animation:none}
.sx-stamp{position:absolute;right:-.9rem;bottom:-1.2rem;z-index:3;font:900 1.9rem var(--serif);letter-spacing:.06em;color:#141414;background:var(--hl);border:3px solid #141414;padding:.1rem .7rem;transform:rotate(-9deg);visibility:hidden;line-height:1.2}
.sx-stamp small{display:block;font:600 10px var(--mono);letter-spacing:.2em;text-align:center}
.sx.done .sx-stamp{visibility:visible;animation:sxaStamp .28s cubic-bezier(.2,1.4,.4,1) backwards}
@keyframes sxaStamp{from{transform:rotate(-9deg) scale(1.9)}}
.sx.out .sx-letter{animation:sxaOut .36s cubic-bezier(.6,0,.9,.4) forwards}
@keyframes sxaOut{to{transform:translate(20vw,-16vh) rotate(6deg)}}
.sx.out .sx-bar,.sx.out .sx-doms,.sx.out .sx-sq{visibility:hidden}
.sx.fast *{animation-duration:.01s!important;animation-delay:0s!important;transition-duration:.01s!important}
@media (max-width:640px){.sx-skip{top:.8rem;right:.8rem}.sx-lbl{top:.9rem;left:1rem}.sx-stage{width:calc(100% - 2.2rem)}.sx-stamp{font-size:1.5rem;right:-.5rem}}
@media (prefers-reduced-motion: reduce){.sx *{animation:none!important;transition:none!important}}
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
 PD.tween(from, raw, 300, function (x) { if (pmCur === raw) el.textContent = '規則分數 ' + Math.round(x) + ' → 正規化 ' + Math.min(Math.round(x) * 5, 100) + ' / 100（僅 R1–R6）'; });
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
<script>
document.addEventListener('DOMContentLoaded', function () {
  const form = document.querySelector('form[action="/paste_analyze"]');
  if (!form || !window.fetch || !window.FormData || !window.Promise || typeof WORDS === 'undefined') return;
  const T = { wipe: 330, p1: 520, p2: 380, p3: 420, p4: 360, stamp: 280, hold: 300, out: 360 };
  const NAMES = ['', '規則引擎', 'ML 模型', '連結還原', 'AI 語意判讀'];
  let busy = false, st = null, ov = null;
  function host(u) { try { return new URL(u).hostname; } catch (e) { return ''; } }
  function scanText(t) {
    const low = t.toLowerCase(), frag = document.createDocumentFragment();
    let buf = '', i = 0, k, end, found, el, kw = 0;
    const urls = [];
    function flush() { if (buf) { frag.appendChild(document.createTextNode(buf)); buf = ''; } }
    while (i < t.length) {
      if (low.startsWith('http://', i) || low.startsWith('https://', i)) {
        end = i; while (end < t.length && !isSp(t[end])) end++;
        flush(); el = document.createElement('mark'); el.setAttribute('data-u', '1'); el.textContent = t.slice(i, end); frag.appendChild(el); urls.push(t.slice(i, end)); i = end; continue;
      }
      found = null;
      for (k = 0; k < WORDS.length; k++) { if (PD.kwAt(low, i, WORDS[k][0])) { found = WORDS[k]; break; } }
      if (found) {
        flush(); el = document.createElement('mark'); el.setAttribute('data-g', found[1]); el.style.setProperty('--c', PCOL[found[1]] || PCOL[0]);
        el.textContent = t.slice(i, i + found[0].length); frag.appendChild(el); kw++; i += found[0].length;
      } else { buf += t[i]; i++; }
    }
    flush();
    return { frag: frag, kw: kw, urls: urls };
  }
  function wait(ms) {
    return new Promise(function (res) {
      if (!st || st.skip) { res(); return; }
      const id = setTimeout(fin, ms);
      function fin() { clearTimeout(id); res(); }
      st.res.push(fin);
    });
  }
  function skipNow() { if (!st || st.skip) return; st.skip = true; if (ov) ov.classList.add('fast'); st.res.splice(0).forEach(function (f) { f(); }); }
  function say(s) { if (ov) ov.querySelector('.sx-live').textContent = s; }
  function setCt(s) { if (ov) ov.querySelector('.sx-lbl .ct').textContent = s; }
  function phase(n, ct) {
    ov.querySelector('.sx-lbl .no').textContent = '0' + n;
    ov.querySelector('.sx-lbl .tx').textContent = NAMES[n];
    setCt(ct || '');
    ov.classList.add('p' + n);
    say('第 ' + n + ' 層　' + NAMES[n] + (ct ? '，' + ct : ''));
  }
  function lock(on) {
    ['.hdr', '.dz'].forEach(function (s) { const e = document.querySelector(s); if (e) { if (on) e.setAttribute('inert', ''); else e.removeAttribute('inert'); } });
  }
  function cleanup() { if (ov && ov.parentNode) ov.parentNode.removeChild(ov); ov = null; st = null; busy = false; lock(false); }
  function build(sender, subject) {
    const o = document.createElement('div');
    o.className = 'sx pre';
    o.setAttribute('role', 'dialog'); o.setAttribute('aria-modal', 'true'); o.setAttribute('aria-label', '送檢中');
    o.innerHTML = '<div class="sx-wipe"></div><div class="sx-edge"></div><div class="sx-live" aria-live="polite"></div>'
      + '<button type="button" class="sx-skip">略過　Esc</button>'
      + '<div class="sx-lbl"><b class="no"></b><span class="tx"></span><em class="ct"></em></div>'
      + '<div class="sx-stage"><div class="mail sx-letter"><div class="lh"></div>'
      + '<div class="sx-row"><span>寄件者</span><b class="sx-from"></b></div>'
      + '<div class="sx-row"><span>主　旨</span><b class="sx-subj"></b></div>'
      + '<div class="sx-body"></div><div class="sx-scan"></div><div class="sx-stamp">已送檢<small>FILED</small></div></div>'
      + '<div class="sx-bar"><i></i></div><div class="sx-doms"></div><div class="sx-sq"><i></i><i></i><i></i><i></i></div></div>';
    const m = /@([^ >]+)/.exec(sender);
    o.querySelector('.lh').textContent = m ? m[1] : '待檢驗郵件';
    o.querySelector('.sx-from').textContent = sender || '(未提供寄件者)';
    o.querySelector('.sx-subj').textContent = subject || '(無主旨)';
    o.querySelector('.sx-skip').addEventListener('click', skipNow);
    return o;
  }
  async function play(body, html) {
    const letter = ov.querySelector('.sx-letter'), bd = ov.querySelector('.sx-body');
    const res = scanText(body.slice(0, 4000));
    bd.appendChild(res.frag);
    const doms = [];
    function addDom(u) { const d = host(u); if (d && doms.indexOf(d) < 0) doms.push(d); }
    res.urls.forEach(addDom);
    if (html.trim()) {
      try { new DOMParser().parseFromString(html, 'text/html').querySelectorAll('a[href]').forEach(function (a) { const h = a.getAttribute('href') || ''; if (h.indexOf('http') === 0) addDom(h); }); } catch (e) {}
    }
    await wait(T.wipe);
    const H = Math.max(letter.offsetHeight, 1);
    ov.querySelector('.sx-scan').style.setProperty('--h', H + 'px');
    bd.querySelectorAll('mark[data-g]').forEach(function (m) {
      const y = Math.max(0, Math.min(1, (bd.offsetTop + m.offsetTop) / H));
      m.style.setProperty('--d', (y * T.p1 * 0.0009).toFixed(2) + 's');
    });
    ov.classList.remove('pre');
    phase(1, '命中 ' + res.kw);
    PD.tween(0, res.kw, T.p1 * 0.9, function (x) { if (ov && ov.classList.contains('p1') && !ov.classList.contains('p2')) setCt('命中 ' + Math.round(x)); });
    await wait(T.p1);
    phase(2);
    await wait(T.p2);
    phase(3, doms.length ? '連結 ' + doms.length : '未發現連結');
    const dm = ov.querySelector('.sx-doms');
    doms.slice(0, 3).forEach(function (d, i) { const sp = document.createElement('span'); sp.textContent = d; sp.style.animationDelay = (i * 0.07) + 's'; dm.appendChild(sp); });
    await wait(T.p3);
    phase(4);
    await wait(T.p4);
    if (st && !st.settled) { setCt('等待回覆…'); ov.querySelector('.sx-sq i:nth-child(4)').classList.add('w'); }
  }
  async function finish(r) {
    const ok = r.redirected && /[/]result[/]/.test(r.url);
    if (!ok) { cleanup(); document.open(); document.write(r.text); document.close(); return; }
    const q = ov.querySelector('.sx-sq i:nth-child(4)');
    q.classList.remove('w'); q.classList.add('ok');
    setCt('');
    ov.classList.add('done'); say('已送檢，前往結果頁');
    await wait(T.stamp + T.hold);
    ov.classList.add('out');
    await wait(T.out);
    try { sessionStorage.setItem('pdSx', String(Date.now())); } catch (e) {}
    location.href = r.url;
  }
  form.addEventListener('submit', function (e) {
    if (PD.RM) return;
    if (busy) { e.preventDefault(); return; }
    const bodyEl = document.getElementById('body-input');
    if (!bodyEl.value.trim()) return;
    e.preventDefault(); busy = true;
    const sender = document.getElementById('sender-input').value.trim(), subject = document.getElementById('subject-input').value.trim();
    const html = document.getElementById('html-input').value;
    st = { skip: false, res: [], settled: false };
    ov = build(sender, subject);
    document.body.appendChild(ov); lock(true);
    ov.querySelector('.sx-skip').focus();
    say('開始送檢');
    const respP = fetch('/paste_analyze', { method: 'POST', body: new FormData(form), credentials: 'same-origin' })
      .then(function (r) { return r.text().then(function (txt) { if (st) st.settled = true; return { redirected: r.redirected, url: r.url, text: txt }; }); });
    let played;
    try { played = play(bodyEl.value, html); } catch (err) { played = Promise.resolve(); }
    Promise.all([played.catch(function () {}), respP]).then(function (a) { return finish(a[1]); }).catch(function () { cleanup(); form.submit(); });
  });
  document.addEventListener('keydown', function (e) { if (busy && e.key === 'Escape') skipNow(); });
  window.addEventListener('pageshow', function (ev) { if (ev.persisted) cleanup(); });
});
</script>
<header class="hdr"><div class="hdr-left"><a href="/">phishing-detector</a></div><div class="hdr-nav"><a href="/rules">偵測規則</a><a href="/whitelist">白名單</a><a href="/history">案件簿</a><a href="/paste">貼信送檢</a></div></header>
<div class="dz dz-short">
  <aside class="dz-side">
    <div class="ftab"><mark>FILE</mark><span>paste</span></div>
    <h1 class="pg-title"><span class="hl">貼上郵件，直接送檢</span></h1>
    <p class="pg-sub">不需要 Google 帳號授權，將郵件的寄件者、主旨與內文貼上即可，系統會以相同的四層式（規則引擎 + ML + HTML / URL + AI Agent）架構進行分析。</p>
    <form method="GET" action="/paste" class="sample-form">
      <div class="lb" style="font-family:var(--mono);font-size:11px;font-weight:600;letter-spacing:.08em;margin-top:1.8rem">快速調閱測試信件</div>
      <div class="sr">
        <select name="sample" class="sample-select" aria-label="選擇範例信">
          <option value="">請選擇測試範例</option>
          <option value="account" SELECT_ACCOUNT>帳戶停用釣魚信</option>
          <option value="prize" SELECT_PRIZE>中獎詐騙信</option>
          <option value="delivery" SELECT_DELIVERY>假物流通知</option>
          <option value="normal" SELECT_NORMAL>正常商業信件</option>
          <option value="wl_real" SELECT_WL_REAL>白名單演示 ①：google.com 官方寄件者（貼信模式無法驗證寄件者，仍會完整分析）</option>
          <option value="wl_fake" SELECT_WL_FAKE>白名單演示 ②：偽冒網域 google.com.verify-login.xyz（不命中白名單）</option>
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
      <p class="pnote">貼上的內容只存在伺服器記憶體、不寫入資料庫；預估風險達中等以上時，寄件者、主旨、內文前 3,000 字與連結清單會送到第三方 AI 服務 Groq 分析。請勿貼上密碼或其他敏感資料。</p>
    </form>
    <div class="pv">
      <div class="lb"><span>預檢標記（即時）</span><em id="pv-stat"></em></div>
      <div class="lgd" id="lgd"></div>
 <div class="pm"><span class="tk"><i id="pm"></i></span><span id="pmv">規則分數 0 → 正規化 0 / 100（僅 R1–R6）</span></div>
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

PASTE_HTML = finish(PASTE_HTML, "貼信送檢｜phishing-detector")
