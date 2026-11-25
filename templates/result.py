"""結果頁"""
from ._base import COMMON_CSS, finish

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
.stamp-lg.red { color: #c8321e; } .stamp-lg.org { color: #925709; } .stamp-lg.grn { color: #2e6a4d; } .stamp-lg.ink { color: #141414; }
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
.vc{position:relative;margin:2.4rem 0 0;border:1px solid #141414;background:#fff;padding:1.2rem 1.4rem 1.1rem;scroll-margin-top:5.5rem}
.vc .vch{margin-bottom:.7rem;font:600 11px var(--mono);letter-spacing:.14em;color:#6b6b6b}
.vc .vcl{margin:0;padding-right:9.5rem;font-family:var(--serif);font-weight:900;font-size:1.55rem;line-height:1.4}
.vc.nost .vcl{padding-right:0}
.vc .vst{position:absolute;right:1.1rem;top:.9rem;padding:.1rem .7rem .15rem;border:3px solid currentColor;font-family:var(--serif);font-weight:900;font-size:1.5rem;line-height:1.15;text-align:center;transform:rotate(-6deg);mix-blend-mode:multiply;opacity:.95}
.vc .vst small{display:block;font:600 .55rem var(--mono);letter-spacing:.2em}
.vc .vst.red{color:#c8321e}.vc .vst.org{color:#925709}.vc .vst.grn{color:#2e6a4d}.vc .vst.ink{color:#141414}
.js .vc.arm .vst{opacity:0}
.vc.go .vst{animation:stampin .45s cubic-bezier(.2,1.7,.4,1) both}
.vc .vr{list-style:none;margin:1rem 0 0;padding:0}
.vc .vr li{border-top:1px solid #d4d4d4}
.vc .vri{display:grid;grid-template-columns:5.2rem minmax(0,1fr);gap:.2rem 1rem;align-items:baseline;width:100%;padding:.7rem .2rem;border:0;background:none;font:inherit;color:inherit;text-align:left;cursor:pointer}
.vc .vri:hover .vrt{text-decoration:underline dotted;text-underline-offset:3px}
.vc .vri:focus-visible,.vc .vgo:focus-visible{outline:2px solid #141414;outline-offset:-2px}
.vc .vrt{font-weight:700}
.vc .vrs{grid-column:2;font:11px var(--mono);color:#6b6b6b}
.vc .vnone{margin:1rem 0 0;padding:.7rem 0;border-top:1px solid #d4d4d4;font-size:14px;color:#4a4a4a}
.vc .vcf{display:flex;flex-wrap:wrap;align-items:baseline;gap:.4rem .8rem;margin-top:.2rem;padding-top:.8rem;border-top:1px solid #141414;font-size:14px;line-height:1.7}
.vc .vcf .k{padding:0 .4rem;background:var(--hl);font:600 11px var(--mono);letter-spacing:.1em}
.vc .vgo{margin-left:auto;padding:.3rem .2rem;border:0;background:none;color:inherit;font:600 12.5px var(--mono);cursor:pointer;text-decoration:underline;text-underline-offset:3px}
.vc .vcn{margin:.8rem 0 0;font-size:12.5px;line-height:1.7;color:#6b6b6b}
.vc .vcl + .vcf{margin-top:1rem}
.why li{transition:background-color .6s}
.why li.fl{background:var(--hl)}
.why li,.sh{scroll-margin-top:5.5rem}
@media(max-width:560px){.vc{padding:1.1rem 1rem}.vc .vcl{padding-right:0;padding-top:3.6rem;font-size:1.3rem}.vc.nost .vcl{padding-top:0}.vc .vst{font-size:1.2rem}.vc .vri{grid-template-columns:4.4rem minmax(0,1fr)}.vc .vgo{margin-left:0}}
@media(pointer:coarse){.vc .vri,.vc .vgo{min-height:44px}}
@media(prefers-reduced-motion:reduce){.why li{transition:none}.vc.go .vst{animation:none}}
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
/* ── 調查台（方案 B）：信與四層合併，逐層聚光 ── */
.ivg{display:grid;grid-template-columns:minmax(0,1.5fr) minmax(0,1fr);gap:1.6rem;align-items:start}
.iv .mdoc{margin:0}
.ivr{display:grid;gap:.8rem;position:sticky;top:1rem}
.ivl{display:grid;gap:.5rem}
.ivb{display:grid;grid-template-columns:1.6rem minmax(0,1fr) auto;align-items:center;gap:.5rem;text-align:left;padding:.7rem .8rem;border:0;border-left:4px solid transparent;background:#e6e6e6;color:#555;font:600 13px var(--sans);cursor:pointer;border-radius:0}
.ivb b{display:grid;place-items:center;width:1.4rem;height:1.4rem;border-radius:50%;background:#141414;color:#f1f1f1;font:700 11px var(--mono)}
.ivb .sc{font:700 15px var(--serif);color:#141414}
.ivb:hover,.ivb.hot{background:#dadada}
.ivb.on{background:var(--hl);color:#141414;border-left-color:#141414}
.ivb:focus-visible{outline:2px solid #141414;outline-offset:2px}
.ivd{min-height:9.2rem;padding:.9rem 1rem;background:#fff;border:1.5px solid #141414;font-size:13.5px;line-height:1.7;color:#333}
.ivd .t{font:700 14px var(--sans);color:#141414;margin-bottom:.15rem}
.ivd .m{font:12px var(--mono);color:#6b6b6b}
.ivtag{display:none;position:absolute;top:.6rem;right:.8rem;z-index:2;background:var(--hl);color:#141414;font:700 11px var(--mono);padding:.1rem .5rem;letter-spacing:.08em}
.iv[data-whole="1"] .ivtag{display:block}
.iv[data-whole="1"] .mdoc{outline:3px solid var(--hl);outline-offset:-3px}
.iv .mdoc dd,.iv .mdoc .mbody,.iv .mdoc mark.m{transition:color .25s ease,background-color .25s ease}
.iv[data-spot="1"] .mdoc dd,.iv[data-spot="1"] .mdoc .mbody,.iv[data-spot="3"] .mdoc dd,.iv[data-spot="3"] .mdoc .mbody{color:#a3a3a3}
.iv[data-spot="1"] mark.m:not([data-n="1"]),.iv[data-spot="3"] mark.m:not([data-n="3"]){background-image:none;background-color:#e9e9e9;color:#a3a3a3}
.iv[data-spot="3"] mark.m[data-n="3"]{text-decoration:underline;text-decoration-color:#ff6fae;text-decoration-thickness:3px;text-underline-offset:.15em}
.acc{margin-top:1.4rem}
.acch{display:flex;align-items:baseline;gap:.8rem;flex-wrap:wrap;font:600 12px var(--mono);letter-spacing:.08em}
.acch b{font:900 1.8rem var(--serif);letter-spacing:0;min-width:3.4rem}
.acc.arm .acf{visibility:hidden}
.acr{margin-left:auto;font:600 12px var(--mono);letter-spacing:.08em;border:1px solid #141414;background:transparent;color:#141414;padding:.3rem .7rem;cursor:pointer;border-radius:0}
.acr:hover,.acr:focus-visible{background:var(--hl);outline:0}
.atrk{position:relative;display:block;height:10px;background:#dcdcdc;margin:.5rem 0 .9rem}
.atrk .as{position:absolute;top:0;bottom:0;background:var(--hl);border-left:2px solid #141414;transform-origin:left;transition:transform .55s cubic-bezier(.3,.7,.3,1)}
.atrk.arm .as{transform:scaleX(0)}
.atrk.arm .as.on{transform:scaleX(1)}
.atrk .tk{position:absolute;top:-3px;bottom:-3px;width:1px;background:#141414;opacity:.5}
@media (max-width:1180px){.ivg{grid-template-columns:1fr}.ivr{position:static}.ivl{grid-template-columns:repeat(4,minmax(0,1fr));gap:.35rem}.ivb{grid-template-columns:1fr;gap:.25rem;padding:.55rem .45rem;border-left:0;border-bottom:4px solid transparent;justify-items:start}.ivb.on{border-bottom-color:#141414}.ivb .nm{font-size:11px}}
@media (prefers-reduced-motion: reduce){.atrk .as,.iv .mdoc dd,.iv .mdoc .mbody,.iv .mdoc mark.m{transition:none}}

</style>
<script>
const emailData = PLACEHOLDER_DATA;
const RULE_KW = KEYWORDS_PLACEHOLDER;

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, c => ({
    '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'
  }[c]));
}


/* ── IR 事件狀態流轉：後端為唯一真相，前端只負責顯示與送出 ── */
function irRenderFlow(box, inc) {
  var h = '<div class="irfl-h"><b>目前狀態：' + escapeHtml(inc.status) + '</b>';
  if (inc.time_to_triage_s != null) h += '<span>分流耗時 ' + inc.time_to_triage_s + ' 秒</span>';
  if (inc.time_to_resolve_s != null) h += '<span>結案耗時 ' + inc.time_to_resolve_s + ' 秒</span>';
  h += '</div>';
  if (inc.allowed_next && inc.allowed_next.length) {
    h += '<input class="irfl-note" maxlength="500" placeholder="處理說明（結案／誤報／重開時必填，至少 5 字）">' +
      '<div class="irfl-b">' + inc.allowed_next.map(function (st) {
        return '<button type="button" class="ir-dl-btn" data-st="' + escapeHtml(st) + '">→ ' + escapeHtml(st) + '</button>';
      }).join('') + '</div>';
  }
  h += '<div class="irfl-msg" aria-live="polite"></div><ol class="irfl-ev">' + (inc.events || []).map(function (e) {
    return '<li>' + escapeHtml((e.ts || '').replace('T', ' ')) + '　' + escapeHtml(e.from ? e.from + ' → ' : '') + escapeHtml(e.to) +
      (e.note ? '：' + escapeHtml(e.note) : '') + '</li>';
  }).join('') + '</ol>';
  box.innerHTML = h;
  box.querySelectorAll('button[data-st]').forEach(function (b) {
    b.addEventListener('click', function () { irTransition(box, b.getAttribute('data-st')); });
  });
}
function irLoadFlow(box) {
  fetch('/incidents', { credentials: 'same-origin' }).then(function (r) { return r.json(); }).then(function (d) {
    var inc = (d.incidents || []).filter(function (x) { return x.id === box.getAttribute('data-id'); })[0];
    if (inc) irRenderFlow(box, inc); else box.innerHTML = '';
  }).catch(function () { box.innerHTML = ''; });
}
function irTransition(box, status) {
  var note = (box.querySelector('.irfl-note') || {}).value || '';
  fetch('/incident/' + encodeURIComponent(box.getAttribute('data-id')) + '/transition', {
    method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status: status, note: note })
  }).then(function (r) { return r.json(); }).then(function (d) {
    if (d.incident) irRenderFlow(box, d.incident);
    if (!d.success) { var m = box.querySelector('.irfl-msg'); if (m) m.textContent = d.error || '更新失敗'; }
  }).catch(function () { var m = box.querySelector('.irfl-msg'); if (m) m.textContent = '網路錯誤，請稍後再試'; });
}
function irInitFlows() { document.querySelectorAll('.irflow').forEach(irLoadFlow); }
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

/* ── 調查台（方案 B）：信與四層合併，逐層聚光；累計條用真實貢獻值 ── */
let IVX = null;
function ivBuild(d, sub, bd, H) {
  const layers = d.layers || {}, order = ['rule', 'ml', 'html', 'llm'];
  let btn = '';
  order.forEach(function (key, n) {
    const x = layers[key]; if (!x) return;
    const scT = x.score == null ? '—' : Number(x.score).toFixed(0);
    btn += '<button type="button" class="ivb" data-k="' + key + '" aria-pressed="false"><b>' + (n + 1) + '</b><span class="nm">' + escapeHtml(x.name) + '</span><span class="sc">' + scT + '</span></button>';
  });
  const rb = d.risk_breakdown || {}, comps = rb.components || [], fin = rb.rounded_final != null ? rb.rounded_final : d.risk_score;
  let acc = '';
  if (comps.length && rb.raw_total != null) {
    let cum = 0, segs = '';
    comps.forEach(function (c, i) { const w = Math.max(0, Number(c.contribution) || 0); segs += '<i class="as" data-i="' + i + '" style="left:' + cum.toFixed(2) + '%;width:' + w.toFixed(2) + '%"></i>'; cum += w; });
    acc = '<div class="acc"><div class="acch"><span>累計風險分數</span><b class="acv">' + Number(rb.raw_total).toFixed(1) + '</b><span class="acf">→ 最終 ' + escapeHtml(String(fin)) + ' / 100</span><button type="button" class="acr">重播</button></div>' +
      '<span class="atrk">' + segs + '<u class="tk" style="left:40%"></u><u class="tk" style="left:70%"></u></span>' +
      comps.map(function (c) { return '<div class="brow"><span>' + escapeHtml(c.name) + '</span><span>' + Number(c.score).toFixed(1) + ' × ' + c.weight + '% = ' + Number(c.contribution).toFixed(1) + '</span></div>'; }).join('') +
      '<div class="btot">公式計算值：' + Number(rb.raw_total).toFixed(1) + ' → 最終 ' + escapeHtml(String(fin)) + ' / 100</div></div>';
  }
  const fnote = d.fusion_formula ? '<div class="fnote">風險融合公式：' + escapeHtml(d.fusion_formula) + '。最終分數由系統固定公式計算，不直接採用單一模型結果。</div>' : '';
  return H('調查台', '滑過或點選一層，信上對應處就會聚光；累計條依各層的真實貢獻累加。') +
    '<div class="iv" data-spot="" data-whole=""><div class="ivg"><article class="mdoc"><dl><div><dt>寄件者</dt><dd>' + escapeHtml(d.sender) + '</dd></div><div><dt>主　旨</dt><dd>' + sub.html + '</dd></div></dl><div class="mbody">' + bd.html + '</div><span class="ivtag">整封信判斷</span></article>' +
    '<div class="ivr"><div class="ivl">' + btn + '</div><div class="ivd" aria-live="polite"></div></div></div>' + acc + fnote + '</div>';
}
function initIV(panel, d) {
  const iv = panel.querySelector('.iv'); if (!iv) return;
  const layers = d.layers || {}, order = ['rule', 'ml', 'html', 'llm'];
  const btns = Array.prototype.slice.call(iv.querySelectorAll('.ivb')), dbox = iv.querySelector('.ivd');
  const rb = d.risk_breakdown || {}, comps = rb.components || [];
  const acc = iv.querySelector('.acc'), trk = iv.querySelector('.atrk'), acv = iv.querySelector('.acv'), segs = iv.querySelectorAll('.as');
  const compOf = {};
  order.forEach(function (k) { const x = layers[k]; if (!x) return; comps.forEach(function (c, i) { if (c.name === x.name) compOf[k] = i; }); });
  const seq = order.filter(function (k) { return layers[k]; });
  const canHover = !!(window.matchMedia && window.matchMedia('(hover: hover)').matches);
  let pinned = '', hover = '', timers = [], playing = false, tok = 0, touched = false;
  function hint() { dbox.innerHTML = '<div class="t">調查台</div><div>滑過或點選一層，信上對應處就會聚光。ML 與 AI 判斷的是整封信，會把整封信框起來。</div>'; }
  function detail(k) {
    const x = layers[k]; if (!x) return;
    const n = order.indexOf(k) + 1;
    const scT = x.score == null ? '未提供分數' : Number(x.score).toFixed(0) + ' / 100';
    const meta = (k === 'ml' && x.probability != null) ? '釣魚機率 ' + Number(x.probability).toFixed(1) + '%' : '融合權重 ' + Number(x.weight || 0).toFixed(1) + '%';
    const ci = compOf[k], c = (ci != null) ? comps[ci] : null;
    let where;
    if (k === 'rule') { const m = iv.querySelectorAll('mark.m[data-n="1"]').length; where = m ? '信中標出 ' + m + ' 處關鍵字。' : '信中沒有可標示的關鍵字。'; }
    else if (k === 'html') { const m = iv.querySelectorAll('mark.m[data-n="3"]').length; where = m ? '信中標出 ' + m + ' 個連結。' : '風險來自 HTML 原始碼，純文字內容沒有可標示處。'; }
    else where = '針對整封信判斷，無法標示在單一詞上。';
    dbox.innerHTML = '<div class="t">' + n + '　' + escapeHtml(x.name) + '　<span class="m">' + escapeHtml(scT) + '</span></div>' +
      '<div>' + escapeHtml(x.status || '—') + '</div><div>' + escapeHtml(where) + '</div>' +
      '<div class="m">' + escapeHtml(meta) + (c ? '　貢獻 ' + Number(c.contribution).toFixed(1) + '（' + Number(c.score).toFixed(1) + ' × ' + c.weight + '%）' : (x.score == null ? '　未計入總分' : '')) + '</div>';
  }
  function apply() {
    const k = hover || pinned, n = k ? order.indexOf(k) + 1 : 0;
    iv.setAttribute('data-spot', n ? String(n) : '');
    iv.setAttribute('data-whole', (k === 'ml' || k === 'llm') ? '1' : '');
    btns.forEach(function (b) { const bk = b.getAttribute('data-k'); b.classList.toggle('on', bk === k); b.setAttribute('aria-pressed', (bk === pinned && !playing) ? 'true' : 'false'); });
    if (k) detail(k); else hint();
  }
  function stop() { tok++; timers.forEach(clearTimeout); timers = []; playing = false; }
  function showFinal() {
    if (!acc) return;
    trk.classList.remove('arm'); acc.classList.remove('arm');
    acv.textContent = Number(rb.raw_total).toFixed(1);
  }
  function interrupt() { touched = true; if (playing) { stop(); pinned = ''; showFinal(); } }
  function play() {
    stop(); playing = true; pinned = ''; hover = '';
    const my = tok;
    if (acc) { acc.classList.add('arm'); trk.classList.add('arm'); segs.forEach(function (s) { s.classList.remove('on'); }); acv.textContent = '0.0'; }
    apply();
    let i = 0, run = 0;
    function step() {
      if (my !== tok) return;
      if (i >= seq.length) { playing = false; pinned = ''; apply(); showFinal(); return; }
      const k = seq[i++]; pinned = k; apply();
      const ci = compOf[k];
      let gap = 700;
      if (acc && ci != null && comps[ci]) {
        gap = 950; segs[ci].classList.add('on');
        const from = run; run += Math.max(0, Number(comps[ci].contribution) || 0);
        PD.tween(from, run, 600, function (x) { if (my === tok) acv.textContent = x.toFixed(1); });
      }
      timers.push(setTimeout(step, gap));
    }
    step();
  }
  btns.forEach(function (b) {
    const k = b.getAttribute('data-k');
    if (canHover) {
      b.addEventListener('mouseenter', function () { interrupt(); hover = k; apply(); });
      b.addEventListener('mouseleave', function () { hover = ''; apply(); });
      b.addEventListener('focus', function () { interrupt(); hover = k; apply(); });
      b.addEventListener('blur', function () { hover = ''; apply(); });
    }
    b.addEventListener('click', function () { interrupt(); pinned = (pinned === k) ? '' : k; apply(); });
  });
  iv.querySelectorAll('mark.m').forEach(function (m) {
    const k = order[Number(m.getAttribute('data-n')) - 1];
    m.addEventListener('mouseenter', function () { btns.forEach(function (b) { b.classList.toggle('hot', b.getAttribute('data-k') === k); }); });
    m.addEventListener('mouseleave', function () { btns.forEach(function (b) { b.classList.remove('hot'); }); });
  });
  const rp = iv.querySelector('.acr'); if (rp) rp.addEventListener('click', play);
  IVX = { stop: stop };
  hint();
  if (acc && !PD.RM) PD.onView([iv.querySelector('.ivg')], function () { timers.push(setTimeout(function () { if (!touched) play(); }, 350)); }, 0.6);
}
function verdictHtml(d, V, score, layers) {
  const lv = d.level, ex = d.explainable_findings || [];
  const rs0 = d.risk_score, sv = (rs0 !== null && rs0 !== undefined && rs0 !== '' && Number(rs0) >= 0) ? Number(rs0) : null;
  const sc = sv !== null ? '（風險 ' + sv + ' / 100）' : '';
  const T = { high: '高度可疑' + sc, medium: '有可疑之處，建議人工確認' + sc, low: '目前沒有發現明顯風險' + sc, wl: '寄件網域在白名單且 DMARC 驗證通過，已放行' }[lv] || '這封信無法判定';
  const stamp = V[1] ? '<div class="vst ' + V[2] + '" aria-hidden="true">' + V[0] + '<small>' + V[1] + '</small></div>' : '';
  let rs = '';
  if (lv === 'high' || lv === 'medium' || lv === 'low') {
    const rank = function (v) { return v === 'high' ? 0 : v === 'low' ? 2 : 1; };
    const top = ex.map(function (x, i) { return { x: x, i: i }; }).sort(function (a, b) { return rank(a.x.severity) - rank(b.x.severity) || a.i - b.i; }).slice(0, 3);
    if (top.length) {
      rs = '<ol class="vr">' + top.map(function (t) {
        const x = t.x, cls = x.severity === 'high' ? 'red' : x.severity === 'low' ? 'grn' : 'org';
        const lab = x.severity === 'high' ? '高風險' : x.severity === 'low' ? '低風險' : '注意';
        return '<li><button type="button" class="vri" data-fi="' + t.i + '"><span class="st ' + cls + '">' + lab + '</span><span class="vrt">' + escapeHtml(x.title || '') + '</span><span class="vrs">' + escapeHtml(x.source || '') + '</span></button></li>';
      }).join('') + '</ol>';
    } else if (lv === 'low') rs = '<p class="vnone">沒有發現可疑證據。</p>';
  }
  const step = d.action ? '<div class="vcf"><span class="k">第一步</span><span>' + escapeHtml(d.action) + '</span><button type="button" class="vgo">看完整建議行動 ↓</button></div>' : '';
  const notes = [];
  if (layers.llm && layers.llm.score == null) notes.push('AI 層未提供分數，此結論來自其餘各層。');
  notes.push('系統自動判讀，仍需人工確認。');
  return '<section class="vc arm' + (stamp ? '' : ' nost') + '" role="region" aria-label="判決書"><div class="vch">判決書</div>' + stamp + '<p class="vcl">' + escapeHtml(T) + '</p>' + rs + step + '<p class="vcn">' + notes.map(escapeHtml).join('　') + '</p></section>';
}
function initVC(panel) {
  const vc = panel.querySelector('.vc'); if (!vc) return;
  vc.addEventListener('click', function (e) {
    const b = e.target.closest ? e.target.closest('button') : null; if (!b) return;
    let el = null;
    if (b.classList.contains('vri')) {
      el = panel.querySelectorAll('.why li')[Number(b.getAttribute('data-fi'))];
      if (el) { el.classList.add('fl'); setTimeout(function () { el.classList.remove('fl'); }, 1800); }
    } else if (b.classList.contains('vgo')) {
      el = Array.prototype.slice.call(panel.querySelectorAll('.sh')).filter(function (h) { return h.textContent.indexOf('建議行動') > -1; })[0];
    }
    if (el) el.scrollIntoView({ behavior: PD.RM ? 'auto' : 'smooth', block: 'start' });
  });
  const go = function () { vc.classList.remove('arm'); vc.classList.add('go'); };
  if (PD.RM || !window.IntersectionObserver) go(); else PD.onView([vc], go, 0.4);
}
function showDetail(idx, element) {
  const d = emailData[idx];
  if (!d) return;
  if (IVX) IVX.stop();
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
  const useIV = !!(d.body && Object.keys(layers).length);
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
    html += useIV ? ivBuild(d, sub, bd, H) : H('原信批註', '標記為規則引擎關鍵字與連結的比對結果；ML 與 AI 針對整封信判斷，無法標示在單一詞上。') +
      '<article class="mdoc"><dl><div><dt>寄件者</dt><dd>' + escapeHtml(d.sender) + '</dd></div><div><dt>主　旨</dt><dd>' + sub.html + '</dd></div></dl>' +
      '<div class="mbody">' + bd.html + '</div>' + (notes ? '<ul class="notes">' + notes + '</ul>' : '') + '</article>';
  }

  html += verdictHtml(d, V, score, layers);

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
  if (layerHtml && !useIV) {
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
    html += H('為什麼會被判定為可疑？') + '<ul class="why">' + ex.map(function (x, i) {
      const cls = x.severity === 'high' ? 'red' : x.severity === 'low' ? 'grn' : 'org';
      const lab = x.severity === 'high' ? '高風險' : x.severity === 'low' ? '低風險' : '注意';
      return '<li data-fi="' + i + '"><div><span class="st ' + cls + '">' + lab + '</span></div><div><div class="src">' + escapeHtml(x.source || '') + '</div><div class="hd">' + escapeHtml(x.title || '') + '</div><div class="dt">' + escapeHtml(x.detail || '') + '</div></div></li>';
    }).join('') + '</ul>';
  }
  let evHtml = '';
  order.forEach(function (key) {
    const x = layers[key]; if (!x || !x.findings || !x.findings.length) return;
    evHtml += '<details class="ev"><summary>' + escapeHtml(x.name) + ' — 偵測證據（' + x.findings.length + '）</summary>' +
      x.findings.slice(0, 6).map(function (v) { return '<div class="it">' + escapeHtml(v) + '</div>'; }).join('') + '</details>';
  });
  if (evHtml) html += H('各層偵測證據') + evHtml;

  /* 4b AI Agent 調查過程 */
  const am = d.agent_meta || {}, atr = d.agent_trace || [];
  function agentSummary(s) {
    const r = s.result || {};
    if (r.error) return '⚠ ' + r.error;
    if (s.tool === 'check_auth_headers') return r.status === 'unavailable' ? '無可用標頭（貼信模式）' : 'SPF=' + r.spf + '　DKIM=' + r.dkim + '　DMARC=' + r.dmarc + (r.reply_to_mismatch ? '　Reply-To 與寄件網域不同' : '');
    if (s.tool === 'expand_url') return r.hops + ' 次跳轉 → ' + (r.final_host || '—') + (r.blocked ? '（已阻擋）' : '');
    if (s.tool === 'domain_age') return r.age_days == null ? '查無註冊資料（未知，不視為安全）' : '註冊 ' + r.age_days + ' 天';
    if (s.tool === 'lookalike_check') return (r.matches && r.matches.length) ? '疑似仿冒：' + r.matches.map(function (m) { return m.brand; }).join('、') : '未發現仿冒';
    if (s.tool === 'dns_lookup') return r.resolves === true ? '可解析' : r.resolves === false ? '無法解析' : '未知';
    return '';
  }
  if (atr.length) {
    html += H('AI Agent 調查過程', 'Agent 決定要查什麼；風險分數只來自工具查到的證據。查無資料視為未知，不會降低風險。') +
      '<div class="agent-tl">' + atr.map(function (s) {
        const sig = (s.signal_labels || []).map(function (l) { return '<span class="st red" style="margin-left:6px">' + escapeHtml(l) + '</span>'; }).join('');
        const arg = s.args && (s.args.url || s.args.domain) ? '（' + escapeHtml(s.args.url || s.args.domain) + '）' : '';
        return '<div class="it" style="border-left:3px solid #999;padding-left:10px;margin:6px 0"><b>步驟 ' + s.step + '　' + escapeHtml(s.tool) + '</b>' + arg + '<div>' + escapeHtml(agentSummary(s)) + sig + '</div></div>';
      }).join('') + '</div>';
  } else if (am.status && am.status !== 'skipped' && am.error) {
    html += H('AI Agent 調查過程') + '<p style="font-size:13.5px;color:#666">調查未取得工具結果：' + escapeHtml(am.error) + '</p>';
  } else if (am.pre_score != null && !am.triggered) {
    html += H('AI Agent 調查過程') + '<p style="font-size:13.5px;color:#666">未啟動：預估風險 ' + escapeHtml(String(am.pre_score)) + ' 未達中等風險門檻 ' + escapeHtml(String(am.trigger_score)) + '，為節省成本不進行調查。</p>';
  }

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
      '<div class="irn">事件流程：Open → Triaged → Contained → Closed（也可標為 False Positive）。本系統只產生處置建議並記錄每次狀態變更，<b>不會自動通知他人、也不會自動結案</b>；結案需填寫處理說明。</div>' +
      '<div class="irflow" id="irflow-' + escapeHtml(ir.id) + '" data-id="' + escapeHtml(ir.id) + '"></div>' +
      '<div class="irdl"><button class="ir-dl-btn" onclick="downloadIR(' + idx + ',&quot;txt&quot;)">下載 IR 報告 (.txt)</button><button class="ir-dl-btn" onclick="downloadIR(' + idx + ',&quot;json&quot;)">下載 (.json)</button></div></div>';
  }

  panel.innerHTML = html.replace('<div class="sh" style="margin-top:2.2rem;display:none"></div>', '');
  irInitFlows();
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
  function hotLc(n, on) { panel.querySelectorAll('.lc').forEach(function (lc) { const b = lc.querySelector('.ln b'); if (b && b.textContent === n) lc.classList.toggle('hot', on); }); }
  panel.querySelectorAll('mark.m').forEach(function (m) { const n = m.getAttribute('data-n'); m.addEventListener('mouseenter', function () { hotLc(n, true); }); m.addEventListener('mouseleave', function () { hotLc(n, false); }); });
  panel.querySelectorAll('.notes li').forEach(function (li) { const n = li.getAttribute('data-n'); li.addEventListener('mouseenter', function () { hotLc(n, true); }); li.addEventListener('mouseleave', function () { hotLc(n, false); }); });
  initIV(panel, d);
  initVC(panel);
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
<header class="hdr"><div class="hdr-left"><a href="/">phishing-detector</a></div><div class="hdr-nav"><a href="/rules">偵測規則</a><a href="/whitelist">白名單</a><a href="/history">案件簿</a><a href="/paste">貼信送檢</a></div></header>
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


RESULT_HTML = finish(RESULT_HTML, "檢驗報告｜phishing-detector")
