"""Gmail MIME parsing helpers."""
import base64
from bs4 import BeautifulSoup

def get_header(msg, name):
    for h in msg['payload']['headers']:
        if h['name'].lower() == name.lower(): return h['value']
    return ''

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
