"""錯誤頁"""
from ._base import COMMON_CSS, finish

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
<header class="hdr"><div class="hdr-left"><a href="/">phishing-detector</a></div><div class="hdr-nav"><a href="/rules">偵測規則</a><a href="/whitelist">白名單</a><a href="/history">案件簿</a><a href="/paste">貼信送檢</a></div></header>
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

ERROR_HTML = finish(ERROR_HTML, "ERR_TITLE｜phishing-detector")
