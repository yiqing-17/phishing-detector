"""偵測規則頁"""
from ._base import COMMON_CSS, finish

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
/* 結構規則（R6/R7、U、H）標題帶分組色：只有顏色，沿用詞庫四色 */
:is(#kwcards,#url + .cards,#html + .cards) .card[data-cg="0"]{--cc:#ffb6d5}
:is(#kwcards,#url + .cards,#html + .cards) .card[data-cg="1"]{--cc:#ffe58a}
:is(#kwcards,#url + .cards,#html + .cards) .card[data-cg="2"]{--cc:#bfe0ff}
:is(#kwcards,#url + .cards,#html + .cards) .card[data-cg="3"]{--cc:#c5ecd2}
.card[data-cg="0"] .clip mark{background:#ffc3dc}.card[data-cg="1"] .clip mark{background:#ffe58a}.card[data-cg="2"] .clip mark{background:#bfe0ff}.card[data-cg="3"] .clip mark{background:#c5ecd2}
.card[data-cg="1"] .kws span{background:#ffe58a}.card[data-cg="2"] .kws span{background:#bfe0ff}.card[data-cg="3"] .kws span{background:#c5ecd2}
.card .kws{gap:.5rem .6rem}.card div.kws span{padding:.18rem .3em}
@media (pointer:coarse){.card .kws span[role="button"]{padding:.5rem .65em;line-height:1.2}}


</style>
<header class="hdr"><div class="hdr-left"><a href="/">phishing-detector</a></div><div class="hdr-nav"><a href="/rules">偵測規則</a><a href="/whitelist">白名單</a><a href="/history">案件簿</a><a href="/paste">貼信送檢</a></div></header>
<div class="dz dz-wide">
  <aside class="dz-side">
<div class="bl">
    <div class="ftab"><mark>FILE</mark><span>rules</span></div>
    <h1 class="pg-title"><span class="hl">偵測規則一覽</span></h1>
    <p class="pg-sub">以下為系統實際使用中的規則（關鍵字清單直接讀取自偵測程式，與實際判斷同源）。規則引擎僅是四層分析中的第一層，其分數會再與 ML、HTML/URL、AI 判讀依固定權重融合。</p>
</div>
<div class="br">
    <div class="nums">
      <div data-bar="max"><b>{{ kw_total }}</b><span>關鍵字（5 類）</span></div>
      <div data-bar="max"><b>{{ url_items|length }}</b><span>URL 結構規則</span></div>
      <div data-bar="max"><b>{{ html_items|length }}</b><span>HTML 結構規則</span></div>
      <div><b>{{ whitelist_count }}</b><span>白名單網域</span></div>
    </div>
  
</div>
</aside>
    <nav class="idx" id="idx" aria-label="規則索引">
      <a href="#try"><em>00</em><span>試試看</span></a>
      <a href="#kw"><em>01</em><span>關鍵字規則 R1–R7</span></a>
      <a href="#url"><em>02</em><span>URL 結構 U1–U8</span></a>
      <a href="#html"><em>03</em><span>HTML 結構 H1–H7</span></a>
      <a href="#fuse"><em>04</em><span>融合與分級</span></a>
    </nav>
  <main class="dz-main">
    <div class="sh" id="try"><span class="n">00</span><h2>試試看</h2>
      <p>貼上一段文字，命中的關鍵字會被螢光筆標出，並依下方 R1–R6 的計分方式估算。僅為前端示意，不含 URL / HTML 結構規則、ML 與 AI 判讀，實際結果以後端為準。</p></div>
    <div class="play">
      <div class="in">
        <div class="lb">輸入文字</div>
        <textarea id="pt" aria-label="輸入文字">親愛的客戶，您的帳戶將於 24 小時內停用，請立即點擊 https://example.com/verify 驗證密碼。</textarea>
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
      <article class="card"><span class="st red">+min(3 + 連結數, 8)</span><div class="rid">R6</div><h3>含有連結</h3><p>郵件內文出現 http(s) 網址</p><div class="kws"><span>https?://…</span></div></article>
      <article class="card"><span class="st red">每個網址 +min(2×命中數, 8)</span><div class="rid">R7</div><h3>URL 風險</h3><p>對內文每個網址（最多 10 個）套用 U1–U8</p><div class="kws"><span>U1 – U8</span></div></article>
    </div>
    <p class="note2">規則分數會正規化為 <b>min(原始分數 × 5, 100)</b> 後再進入融合。</p>

    <div class="sh" id="url"><span class="n">02</span><h2>URL 結構規則 U1–U8</h2><p>U1–U8 只解析網址字串，不連線、不開啟目標網站（第四層 Agent 的 expand_url 工具另有 SSRF 防護，見下方說明）。</p></div>
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

    <div class="sh" id="fuse"><span class="n">04</span><h2>融合與分級</h2><p>各層分數依固定權重融合；寄件網域命中<a href="/whitelist" style="color:#141414;text-decoration:underline">白名單</a>者，需通過 Gmail 的 DMARC 驗證才會略過分析（防止偽造寄件者）。</p></div>
    <div class="fz">
      <div class="box"><h3>Agent 已啟動</h3>
        <div class="seg"><i class="a" style="flex:35">規則 35%</i><i class="b" style="flex:35">ML 35%</i><i class="c" style="flex:15">HTML/URL 15%</i><i class="d" style="flex:15">Agent 15%</i></div>
        <p>規則＋ML＋HTML 的預估分數 ≥ 40 才啟動調查 Agent。Agent 分數來自工具回傳的訊號（不採 LLM 自己給的分數），只加分、不會讓最終分數低於預估分數。</p></div>
      <div class="box"><h3>Agent 未啟動</h3>
        <div class="seg"><i class="a" style="flex:42.5">規則 42.5%</i><i class="b" style="flex:42.5">ML 42.5%</i><i class="c" style="flex:15">HTML/URL 15%</i></div>
        <p>未達門檻、每次掃描的 Agent 額度用完或調查失敗時改用。</p></div>
    </div>
    <p class="note2">ML 僅適用英文信：信件以中文為主或落在模型詞彙內的詞太少時，ML 不納入融合、權重移給規則引擎（規則 70% + HTML 15% + Agent 15%；未啟動 Agent 時為規則 85% + HTML 15%）。</p>
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
    a2.textContent='R6 含有連結';b2.textContent=links+' 個連結　+'+p;li2.appendChild(a2);li2.appendChild(b2);ul.appendChild(li2);}
  if(!ul.children.length){var e=document.createElement('li');e.textContent='沒有命中任何規則';ul.appendChild(e);}
  var norm=Math.min(raw*5,100);
  cnt('raw',raw);cnt('norm',norm);document.getElementById('mt').style.width=norm+'%';
}
document.addEventListener('DOMContentLoaded',function(){
  document.getElementById('pt').addEventListener('input',run);run();
  var EX={R1:'您的帳戶將於 24 小時內停用，請立即處理。',R2:'恭喜您中獎，免費領取限量禮品，並可申請退款。',R3:'請回覆您的帳號、密碼與信用卡號以完成驗證。',R4:'請立即匯款或轉帳，付款後我們將為您處理。',R5:'您的包裹需補繳運費，請加入群組並依指示入金。'};
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
 var EXS={
  R6:'請點擊 <mark>https://example.com/verify</mark> 完成驗證。',
  R7:'http://<mark>192.168.4.7</mark>/<mark>login</mark>',
  U1:'http://<mark>203.0.113.7</mark>/pay',
  U2:'http://google.com<mark>@</mark>evil.example/',
  U3:'http://<mark>xn--</mark>pple-43d.example/',
  U4:'http://my-bank<mark>.xyz</mark>/',
  U5:'http://example.com/<mark>0123456789…（超過 100 字元）</mark>',
  U6:'http://<mark>mail.shop.cdn.img.store</mark>.example/',
  U7:'<mark>bit.ly</mark>/3xYzAbC',
  U8:'http://example.com/<mark>login</mark>/<mark>verify</mark>?<mark>account</mark>=1',
  H1:'&lt;a href="http://<mark>203.0.113.7</mark>/x"&gt;領取&lt;/a&gt;',
  H2:'&lt;a href="http://<mark>evil.example</mark>/"&gt;<mark>paypal.com</mark>&lt;/a&gt;',
  H3:'&lt;img src="t.gif" <mark>width="1" height="1"</mark>&gt;',
  H4:'&lt;div style="<mark>display:none</mark>"&gt;…&lt;/div&gt;',
  H5:'<mark>&lt;form</mark> action="/submit"&gt;',
  H6:'&lt;input <mark>type="password"</mark>&gt;',
  H7:'Your <mark>Microsoft</mark> account needs attention.'
 };
 var CG={R6:2,R7:2,U1:2,U2:1,U3:2,U4:2,U5:1,U6:2,U7:1,U8:0,H1:2,H2:1,H3:1,H4:1,H5:0,H6:0,H7:3};
 var cards=PD.all('#kwcards .card');
 PD.all('.dz-main .cards .card').forEach(function(c){
  var rid=(c.querySelector('.rid')||{}).textContent,gi=-1;
  G.forEach(function(g,k){if(g[0]===rid)gi=k;});
  c.setAttribute('data-gi',gi);
  if(CG[rid]!==undefined)c.setAttribute('data-cg',CG[rid]);
  PD.all('.kws span',c).forEach(function(s){
   if(gi<0)return;
   s.setAttribute('role','button');s.setAttribute('tabindex','0');s.title='點一下加入上方試玩區';
   function add(){put(s.textContent,false,false);PD.toast('已加入「'+s.textContent+'」到試玩區',{type:'ok',ms:1800});}
   s.addEventListener('click',function(e){e.stopPropagation();add();});
   s.addEventListener('keydown',function(e){if(e.key==='Enter'||e.key===' '){e.preventDefault();e.stopPropagation();add();}});
  });
  var txt=EX[rid],html=EXS[rid];
  if(!txt&&!html)return;
  var clip=document.createElement('div');clip.className='clip'+(html?' code':'');
  if(txt){
   clip.appendChild(hlGroup(txt,gi));
   clip.title='點一下放進上方試玩區';clip.setAttribute('role','button');clip.setAttribute('tabindex','0');
   clip.addEventListener('click',function(){put(txt,true,true);});
   clip.addEventListener('keydown',function(e){if(e.key==='Enter'||e.key===' '){e.preventDefault();put(txt,true,true);}});
  }else{clip.innerHTML=html;}
  c.insertBefore(clip,c.querySelector('p'));
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



RULES_HTML = finish(RULES_HTML, "偵測規則｜phishing-detector")
