"""Gmail MIME parsing helpers."""
import base64
import re
from bs4 import BeautifulSoup

def get_header(msg, name):
    for h in msg['payload']['headers']:
        if h['name'].lower() == name.lower(): return h['value']
    return ''

_AGENT_HEADERS = ('From', 'Reply-To', 'Return-Path', 'Authentication-Results')

def get_agent_headers(msg):
    """取出調查 Agent 需要的標頭（Authentication-Results 可能出現多次，全部串起來）。"""
    out = {}
    for h in msg.get('payload', {}).get('headers', []):
        for name in _AGENT_HEADERS:
            if h['name'].lower() == name.lower():
                out[name] = (out[name] + '; ' + h['value']) if name in out else h['value']
    return out

_TRUSTED_AUTHSERV = 'mx.google.com'


def get_trusted_auth(msg):
    """取出 Gmail 自己（收件端）做的 SPF/DKIM/DMARC 驗證結果。

    只信「最上面第一個」authserv-id 為 mx.google.com 的 Authentication-Results：
    收件伺服器會把自己的標頭加在最上方，攻擊者偽造的標頭只能出現在它下面，
    所以不能把所有同名標頭串起來，也不能取後面的。
    回傳 {'available': bool, 'dmarc','spf','dkim', 'header_from'}。"""
    for h in msg.get('payload', {}).get('headers', []):
        if h.get('name', '').lower() != 'authentication-results':
            continue
        v = h.get('value', '')
        if not v.strip().lower().startswith(_TRUSTED_AUTHSERV):
            continue
        low = v.lower()
        def res(name):
            m = re.search(r'(?:^|[;\s])' + name + r'=(\w+)', low)
            return m.group(1) if m else 'none'
        m = re.search(r'dmarc=\w+[^;]*?header\.from=([^\s;]+)', low)
        return {'available': True, 'dmarc': res('dmarc'), 'spf': res('spf'),
                'dkim': res('dkim'), 'header_from': (m.group(1).strip('<>').rstrip('.') if m else '')}
    return {'available': False, 'dmarc': 'none', 'spf': 'none', 'dkim': 'none', 'header_from': ''}


def _walk_parts(payload):
    yield payload
    for part in payload.get('parts', []) or []:
        yield from _walk_parts(part)

def _decode_part(part):
    data = part.get('body', {}).get('data', '')
    if not data:
        return ''
    try:
        return base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
    except Exception:
        return ''

def get_body(msg):
    # 優先取得 text/plain；若信件只有 HTML，退回 HTML 去除標籤後的文字。
    payload = msg.get('payload', {})
    for part in _walk_parts(payload):
        if part.get('mimeType') == 'text/plain':
            text = _decode_part(part)
            if text:
                return text[:5000]
    for part in _walk_parts(payload):
        if part.get('mimeType') == 'text/html':
            html = _decode_part(part)
            if html:
                return BeautifulSoup(html, 'html.parser').get_text(' ', strip=True)[:5000]
    return ''

def get_html(msg):
    payload = msg.get('payload', {})
    for part in _walk_parts(payload):
        if part.get('mimeType') == 'text/html':
            html = _decode_part(part)
            if html:
                return html[:20000]
    return ''
