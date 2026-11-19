"""Deterministic investigation tools used by the phishing-investigation agent.

Design rules
------------
* Every tool returns plain data plus a ``signals`` list of machine-readable codes.
  The agent (LLM) never produces scores; scores come from ``agent.SIGNAL_POINTS``.
* "unknown" (lookup failed / no data) is never reported as "safe" and never as a
  risk signal - it simply produces no signal.
* ``expand_url`` is the only tool that touches an attacker-controlled host, so it
  is guarded against SSRF (private / loopback / link-local addresses, odd ports,
  non-http schemes, redirect chains, short timeouts, no cookies, no body download).
"""
import ipaddress
import re
import socket
from datetime import datetime, timezone
from email.utils import parseaddr
from urllib.parse import urljoin, urlparse

import requests

USER_AGENT = 'Mozilla/5.0 (compatible; phishing-detector-investigator/1.0)'
MAX_REDIRECTS = 5
HTTP_TIMEOUT = 3
RDAP_TIMEOUT = 4

# ── 網域工具 ─────────────────────────────────────────────────
_SECOND_LEVEL_SUFFIXES = {
    'com.tw', 'org.tw', 'gov.tw', 'edu.tw', 'net.tw', 'idv.tw',
    'co.uk', 'org.uk', 'ac.uk', 'com.au', 'com.cn', 'com.hk',
    'co.jp', 'co.kr', 'com.sg', 'com.my',
}


def registrable_domain(host):
    """簡化版 registrable domain（不依賴 tldextract / Public Suffix List）。"""
    host = (host or '').lower().strip('.')
    parts = host.split('.')
    if len(parts) <= 2:
        return host
    if '.'.join(parts[-2:]) in _SECOND_LEVEL_SUFFIXES:
        return '.'.join(parts[-3:])
    return '.'.join(parts[-2:])


def _domain_of_address(value):
    addr = parseaddr(value or '')[1].lower()
    if '@' not in addr:
        return ''
    return addr.rsplit('@', 1)[1].strip('.')


# ── Tool 1：仿冒網域比對（純本地，不連線）────────────────────
# 品牌 → 官方 registrable domain。可自行擴充。
OFFICIAL_DOMAINS = {
    'paypal': {'paypal.com'},
    'microsoft': {'microsoft.com', 'live.com', 'office.com', 'outlook.com', 'microsoftonline.com'},
    'apple': {'apple.com', 'icloud.com'},
    'amazon': {'amazon.com', 'amazon.co.jp', 'amazon.co.uk'},
    'google': {'google.com', 'gmail.com', 'googlemail.com', 'google.com.tw', 'youtube.com'},
    'facebook': {'facebook.com', 'fb.com', 'facebookmail.com'},
    'netflix': {'netflix.com'},
    'shopee': {'shopee.tw', 'shopee.com', 'shopee.sg'},
    'cathaybk': {'cathaybk.com.tw'},
    'ctbcbank': {'ctbcbank.com'},
    'esunbank': {'esunbank.com.tw', 'esunbank.com'},
    'fubon': {'fubon.com'},
    'taishinbank': {'taishinbank.com.tw'},
    'chunghwapost': {'post.gov.tw'},
}

_CONFUSABLES = str.maketrans({'0': 'o', '1': 'l', '3': 'e', '5': 's', '$': 's', '@': 'a'})


def _deconfuse(token):
    token = token.lower().translate(_CONFUSABLES)
    return token.replace('rn', 'm').replace('vv', 'w')


def _edit_distance(a, b):
    if a == b:
        return 0
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def lookalike_check(domain):
    """檢查網域是否疑似仿冒知名品牌（同形字、近似拼寫、品牌名放在子網域或連字號後）。"""
    host = (domain or '').lower().strip('.')
    reg = registrable_domain(host)
    rest = host[:-len(reg)].strip('.') if host.endswith(reg) else ''
    reg_label = reg.split('.')[0]

    raw_tokens = [t for t in re.split(r'[.\-_]', rest) if t] + [t for t in reg_label.split('-') if t]
    matches = []
    for brand, officials in OFFICIAL_DOMAINS.items():
        if reg in officials:
            continue
        for token in raw_tokens:
            norm = _deconfuse(token)
            if norm == brand:
                reason = '品牌名稱出現在非官方網域' if token == brand else '使用相似字元仿冒品牌名稱'
            elif len(brand) >= 6 and _edit_distance(norm, brand) == 1:
                reason = '網域拼字與品牌名稱僅差一個字元'
            else:
                continue
            matches.append({'brand': brand, 'token': token, 'reason': reason})
            break
    return {
        'domain': host,
        'registrable_domain': reg,
        'matches': matches,
        'signals': ['lookalike_domain'] if matches else [],
    }


# ── Tool 2：寄件者身分驗證（讀信件標頭，不連線）──────────────
_AUTH_RE = re.compile(r'\b(spf|dkim|dmarc)\s*=\s*([a-z]+)', re.I)


def check_auth_headers(headers):
    """解析 Authentication-Results 的 SPF/DKIM/DMARC，並比對 From 與 Reply-To。"""
    h = {str(k).lower(): str(v) for k, v in (headers or {}).items()}
    if not h:
        return {'status': 'unavailable', 'note': '沒有可用的郵件標頭（例如貼信模式）', 'signals': []}

    results = {}
    for name, value in _AUTH_RE.findall(h.get('authentication-results', '')):
        name, value = name.lower(), value.lower()
        # DKIM 可能有多組簽章：只要有一組 pass 就視為 pass
        if name not in results or (name == 'dkim' and value == 'pass'):
            results[name] = value

    signals = []
    if results.get('dmarc') == 'fail':
        signals.append('dmarc_fail')
    if results.get('spf') in ('fail', 'softfail'):
        signals.append('spf_fail')
    if results.get('dkim') == 'fail':
        signals.append('dkim_fail')

    from_domain = _domain_of_address(h.get('from', ''))
    reply_domain = _domain_of_address(h.get('reply-to', ''))
    mismatch = bool(
        from_domain and reply_domain
        and registrable_domain(from_domain) != registrable_domain(reply_domain)
    )
    if mismatch:
        signals.append('reply_to_mismatch')

    return {
        'status': 'ok' if results else 'no_authentication_results',
        'spf': results.get('spf', 'none'),
        'dkim': results.get('dkim', 'none'),
        'dmarc': results.get('dmarc', 'none'),
        'from_domain': from_domain,
        'reply_to_domain': reply_domain,
        'reply_to_mismatch': mismatch,
        'note': '驗證通過只代表該網域確實寄出此信，不代表內容安全。',
        'signals': signals,
    }


# ── Tool 3：展開網址（唯一會連到外部主機的工具，含 SSRF 防護）──
def _host_is_public(host):
    """解析主機的所有 A/AAAA 位址，只有全部為公開位址才回傳 True。"""
    if not host or host.lower() in ('localhost',) or host.lower().endswith(('.local', '.internal', '.localhost')):
        return False
    try:
        ip = ipaddress.ip_address(host)
        return ip.is_global
    except ValueError:
        pass
    try:
        infos = socket.getaddrinfo(host, None)
    except (socket.gaierror, UnicodeError):
        return False
    addrs = {info[4][0] for info in infos}
    if not addrs:
        return False
    for addr in addrs:
        try:
            if not ipaddress.ip_address(addr.split('%')[0]).is_global:
                return False
        except ValueError:
            return False
    return True


def _validate_url(url):
    p = urlparse(url)
    if p.scheme not in ('http', 'https'):
        return '只允許 http / https'
    if p.port not in (None, 80, 443):
        return '只允許 80 / 443 連接埠'
    if p.username or p.password:
        return '網址含帳號密碼，拒絕連線'
    if not _host_is_public(p.hostname or ''):
        return '目標不是公開網路位址，拒絕連線'
    return ''


def expand_url(url):
    """追蹤跳轉（最多 5 次）。只讀標頭，不下載內容、不帶 cookie、不執行 JS。"""
    chain = [url]
    current = url
    for _ in range(MAX_REDIRECTS + 1):
        err = _validate_url(current)
        if err:
            return _expand_result(url, chain, error=err, blocked=True)
        try:
            resp = requests.head(current, allow_redirects=False, timeout=HTTP_TIMEOUT,
                                 headers={'User-Agent': USER_AGENT})
            if resp.status_code in (405, 501):
                resp = requests.get(current, allow_redirects=False, timeout=HTTP_TIMEOUT,
                                    headers={'User-Agent': USER_AGENT}, stream=True)
                resp.close()
        except requests.RequestException as e:
            return _expand_result(url, chain, error=f'連線失敗：{type(e).__name__}')
        if resp.status_code in (301, 302, 303, 307, 308) and resp.headers.get('Location'):
            current = urljoin(current, resp.headers['Location'])
            chain.append(current)
            continue
        return _expand_result(url, chain, status_code=resp.status_code)
    return _expand_result(url, chain, error='跳轉次數超過上限')


def _expand_result(original, chain, status_code=None, error='', blocked=False):
    final = chain[-1]
    final_host = (urlparse(final).hostname or '').lower()
    orig_host = (urlparse(original).hostname or '').lower()
    hops = len(chain) - 1
    signals = []
    if hops >= 1 and registrable_domain(final_host) != registrable_domain(orig_host):
        signals.append('redirect_cross_domain')
    if hops >= 3:
        signals.append('redirect_many')
    return {
        'original_url': original,
        'chain': chain,
        'hops': hops,
        'final_url': final,
        'final_host': final_host,
        'status_code': status_code,
        'error': error,
        'blocked': blocked,
        'signals': signals,
    }


# ── Tool 4：網域年齡（RDAP）──────────────────────────────────
def domain_age(domain):
    reg = registrable_domain(domain)
    try:
        resp = requests.get(f'https://rdap.org/domain/{reg}', timeout=RDAP_TIMEOUT,
                            headers={'User-Agent': USER_AGENT, 'Accept': 'application/rdap+json'})
        if resp.status_code != 200:
            return {'domain': reg, 'status': 'unknown', 'age_days': None,
                    'note': f'RDAP 無資料（HTTP {resp.status_code}）', 'signals': []}
        created = None
        for ev in resp.json().get('events', []):
            if ev.get('eventAction') == 'registration':
                created = ev.get('eventDate')
                break
        if not created:
            return {'domain': reg, 'status': 'unknown', 'age_days': None,
                    'note': 'RDAP 未提供註冊日期', 'signals': []}
        dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        age = (datetime.now(timezone.utc) - dt).days
    except (requests.RequestException, ValueError):
        return {'domain': reg, 'status': 'unknown', 'age_days': None,
                'note': 'RDAP 查詢失敗', 'signals': []}
    signals = []
    if age < 7:
        signals.append('domain_age_lt7')
    elif age < 30:
        signals.append('domain_age_lt30')
    return {'domain': reg, 'status': 'ok', 'age_days': age, 'registered': created, 'signals': signals}


# ── Tool 5：DNS 是否可解析 ──────────────────────────────────
def dns_lookup(domain):
    host = (domain or '').lower().strip('.')
    try:
        socket.getaddrinfo(host, None)
    except socket.gaierror as e:
        if e.errno in (socket.EAI_NONAME, getattr(socket, 'EAI_NODATA', socket.EAI_NONAME)):
            return {'domain': host, 'resolves': False, 'status': 'ok', 'signals': ['no_dns']}
        return {'domain': host, 'resolves': None, 'status': 'unknown', 'signals': []}
    except UnicodeError:
        return {'domain': host, 'resolves': None, 'status': 'unknown', 'signals': []}
    return {'domain': host, 'resolves': True, 'status': 'ok', 'signals': []}
