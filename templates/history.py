"""歷史紀錄（案件簿）頁"""
from ._base import COMMON_CSS, finish

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
.lg{display:inline-flex;align-items:center;font:12px var(--mono);color:#141414;background:#fff;border:1px solid #141414;border-radius:0;padding:.3rem .7rem;cursor:pointer}
.lg b{font-weight:600;margin-left:.5rem;color:#4a4a4a}
.lg:hover{background:#ececec}
.lg[aria-pressed="true"]{background:#141414;color:#f1f1f1}
.lg[aria-pressed="true"] b{color:#d0d0d0}
.lg[aria-pressed="true"] .dot{border-color:#f1f1f1}
.lg:disabled{opacity:.45;cursor:default}
.lg:focus-visible{outline:2px solid #141414;outline-offset:2px}
.lr{transition:background .15s,opacity .2s}
.lr.dim{opacity:.28}
.heat .hc{transition:filter .2s}
.heat .hc.dim{filter:opacity(.22)}
.bar3 i{transition:transform .7s cubic-bezier(.2,.7,.2,1) calc(var(--k,0) * .12s),opacity .2s ease 0s}
.led.f-h .bar3 i:not(.h),.led.f-m .bar3 i:not(.m),.led.f-l .bar3 i:not(.l),.led.f-w .bar3 i:not(.w){opacity:.22}
.lr.lk{outline:2px solid #141414;outline-offset:-2px}
.led .lr:first-of-type.lk{outline-color:#ffb6d5;outline-offset:-5px}
.heat .hc.lk{outline:2px solid #141414;outline-offset:2px}
.lr .dlt{font:11.5px var(--mono);color:#6b6b6b}
.lr .dlt.up{color:#c8321e}.lr .dlt.dn{color:#2e6a4d}
.led .lr:first-of-type .dlt{color:#b5b5b5}
.led .lr:first-of-type .dlt.up{color:#ff8a78}.led .lr:first-of-type .dlt.dn{color:#7fd6a0}
@media (min-width:900px){.lr .tm{grid-column:1;grid-row:1}.lr .bar3{grid-column:2;grid-row:1}.lr .nm{grid-column:3;grid-row:1}.lr .dlt{grid-column:2;grid-row:2;margin-top:-1rem}}
@media (prefers-reduced-motion: reduce) { .bar3 i, .spark .ln { transition: none; } .lr.open .more { animation: none; } }


</style>
<header class="hdr"><div class="hdr-left"><a href="/">phishing-detector</a></div><div class="hdr-nav"><a href="/rules">偵測規則</a><a href="/whitelist">白名單</a><a href="/history">案件簿</a><a href="/paste">貼信送檢</a></div></header>
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
      <div data-role="total"><b>{{ history|sum(attribute=2) }}</b><span>郵件總數</span></div>
      <div data-bar="share"><b style="color:#c8321e">{{ history|sum(attribute=3) }}</b><span>高風險</span></div>
      <div data-bar="share"><b style="color:#a8650f">{{ history|sum(attribute=4) }}</b><span>中風險</span></div>
    </div>
    <div class="spark" id="spark"></div>
 {% endif %}
  
</div>
</aside>
  <main class="dz-main">
    {% if history %}
    <div class="sh"><span class="n">01</span><h2>近期案件</h2></div>
    <div class="leg" role="group" aria-label="依風險等級篩選案件">
      <button type="button" class="lg" data-k="h" aria-pressed="false"{{ ' disabled' if not history|sum(attribute=3) }}><i class="dot h"></i>高風險<b>{{ history|sum(attribute=3) }}</b></button>
      <button type="button" class="lg" data-k="m" aria-pressed="false"{{ ' disabled' if not history|sum(attribute=4) }}><i class="dot m"></i>中風險<b>{{ history|sum(attribute=4) }}</b></button>
      <button type="button" class="lg" data-k="l" aria-pressed="false"{{ ' disabled' if not history|sum(attribute=5) }}><i class="dot l"></i>安全<b>{{ history|sum(attribute=5) }}</b></button>
      <button type="button" class="lg" data-k="w" aria-pressed="false"{{ ' disabled' if not history|sum(attribute=6) }}><i class="dot w"></i>白名單<b>{{ history|sum(attribute=6) }}</b></button>
    </div>
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
var led=document.querySelector('.led'),lgs=PD.all('.lg'),hcs=PD.all('.hc'),cur='';
rows.slice().reverse().forEach(function(r,i){var c=hcs[i];if(c){r._hc=c;c._lr=r;}});
function mark(el,on){if(el)el.classList.toggle('lk',on);}
rows.forEach(function(r){
  ['mouseenter','focus'].forEach(function(t){r.addEventListener(t,function(){mark(r._hc,true);});});
  ['mouseleave','blur'].forEach(function(t){r.addEventListener(t,function(){mark(r._hc,false);});});
});
hcs.forEach(function(c){
  ['mouseenter','focus'].forEach(function(t){c.addEventListener(t,function(){mark(c._lr,true);});});
  ['mouseleave','blur'].forEach(function(t){c.addEventListener(t,function(){mark(c._lr,false);});});
});
function applyFilter(k){
  cur=k;
  ['h','m','l','w'].forEach(function(x){if(led)led.classList.remove('f-'+x);});
  if(k&&led)led.classList.add('f-'+k);
  rows.forEach(function(r){
    var off=!!k&&!(+r.getAttribute('data-'+k));
    r.classList.toggle('dim',off);
    if(r._hc)r._hc.classList.toggle('dim',off);
  });
  lgs.forEach(function(b){b.setAttribute('aria-pressed',b.getAttribute('data-k')===k?'true':'false');});
}
lgs.forEach(function(b){b.addEventListener('click',function(){var k=b.getAttribute('data-k');applyFilter(cur===k?'':k);});});
rows.forEach(function(r,i){
  var nx=rows[i+1],bar=r.querySelector('.bar3');
  if(!nx||!bar)return;
  var d=(+r.getAttribute('data-h')||0)-(+nx.getAttribute('data-h')||0),e=document.createElement('div');
  e.className='dlt'+(d>0?' up':d<0?' dn':'');
  e.textContent='較上次　高風險 '+(d>0?'+'+d:d<0?'−'+(-d):'持平');
  bar.insertAdjacentElement('afterend',e);
});
})();
</script>
"""


HISTORY_HTML = finish(HISTORY_HTML, "案件簿｜phishing-detector")
