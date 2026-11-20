"""SQLite persistence and visitor-scoped whitelist helpers."""
import re
from email.utils import parseaddr
import secrets
import sqlite3
from flask import session
from config import DEFAULT_WHITELIST, MY_EMAIL, SKIP_SUBJECTS

# ── 資料庫 ───────────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect('phishing.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS scan_history
        (id TEXT PRIMARY KEY, scan_time TEXT, total INTEGER,
         high INTEGER, medium INTEGER, low INTEGER, whitelist INTEGER, skipped INTEGER)''')
    # 舊版沒有 uid 欄位：補上；舊紀錄 uid 為空字串，不屬於任何訪客（不會被顯示）
    cols = [r[1] for r in c.execute('PRAGMA table_info(scan_history)')]
    if 'uid' not in cols:
        c.execute("ALTER TABLE scan_history ADD COLUMN uid TEXT DEFAULT ''")
    c.execute('CREATE INDEX IF NOT EXISTS idx_hist_uid ON scan_history (uid, scan_time)')
    # 舊版全站共用白名單：保留資料表不動（僅供日後手動匯入），程式不再讀取
    c.execute('''CREATE TABLE IF NOT EXISTS whitelist
        (id INTEGER PRIMARY KEY AUTOINCREMENT, domain TEXT UNIQUE, added_time TEXT)''')
    # 個人白名單只記錄「每個人的修改」：預設網域存在程式裡，這裡只存新增（add）與刪除預設（del）
    c.execute('''CREATE TABLE IF NOT EXISTS user_whitelist
        (uid TEXT NOT NULL, domain TEXT NOT NULL, action TEXT NOT NULL, added_time TEXT,
         PRIMARY KEY (uid, domain))''')
    c.execute('CREATE TABLE IF NOT EXISTS app_meta (key TEXT PRIMARY KEY, value TEXT)')
    conn.commit()
    conn.close()


def get_uid():
    """每個瀏覽器一個匿名識別碼（存在簽章過的 cookie）。
    白名單、掃描記錄、Google 授權憑證與掃描結果都以它區分，不同訪客互相看不到。"""
    uid = session.get('uid', '')
    if not re.fullmatch(r'[0-9a-f]{32}', uid or ''):
        uid = secrets.token_hex(16)
        session['uid'] = uid
    session.permanent = True
    return uid

def get_whitelist_rows(uid=None):
    """回傳這位訪客的白名單 [(domain, added_time)]：自行新增的在前（新到舊），預設網域在後（added_time 為空字串）。"""
    uid = uid or get_uid()
    conn = sqlite3.connect('phishing.db')
    c = conn.cursor()
    c.execute('SELECT domain, action, added_time FROM user_whitelist WHERE uid=?', (uid,))
    rows = c.fetchall()
    conn.close()
    removed = {d for d, a, _ in rows if a == 'del'}
    added = sorted([(d, t or '') for d, a, t in rows if a == 'add'], key=lambda x: x[1], reverse=True)
    added_set = {d for d, _ in added}
    out = list(added)
    out += [(d, '') for d in DEFAULT_WHITELIST if d not in removed and d not in added_set]
    return out

def get_whitelist(uid=None):
    return [d for d, _ in get_whitelist_rows(uid)]

def extract_sender_domain(sender):
    """從 From 標頭取出真正的 email domain。"""
    m = re.search(r'<([^>]+)>', sender or '')
    email_addr = (m.group(1) if m else sender or '').strip().lower()
    if '@' not in email_addr:
        return ''
    return email_addr.rsplit('@', 1)[1].strip().rstrip('.')

def normalize_whitelist_domain(value):
    """正規化白名單網域，只接受純網域名稱。"""
    value = (value or '').strip().lower()
    value = re.sub(r'^https?://', '', value)
    value = value.split('/', 1)[0].split('?', 1)[0].split('#', 1)[0]
    value = value.rstrip('.')
    if ':' in value:
        return ''
    if not re.fullmatch(r'[a-z0-9](?:[a-z0-9.-]{0,251}[a-z0-9])?', value):
        return ''
    if '.' not in value or '..' in value or value.startswith('.'):
        return ''
    labels = value.split('.')
    if any(not x or len(x) > 63 or x.startswith('-') or x.endswith('-') for x in labels):
        return ''
    return value

def whitelist_match(sender, uid=None):
    """回傳 (寄件網域, 命中的白名單網域, 比對方式)；未命中時命中網域為空字串。"""
    domain = extract_sender_domain(sender)
    if not domain:
        return '', '', ''
    for d in get_whitelist(uid):
        if domain == d:
            return domain, d, '精確網域比對'
        if domain.endswith('.' + d):
            return domain, d, '子網域比對'
    return domain, '', ''

def is_whitelisted(sender, uid=None):
    return bool(whitelist_match(sender, uid)[1])

def is_system_report(sender, subject, label_ids=()):
    """辨識「本系統自己寄給自己的報告信」。

    舊版只看主旨關鍵字，攻擊者在釣魚信主旨加「[正常]」就能繞過分析；
    而且 MY_EMAIL 未設定時 `'' in sender` 恆為真。現在必須同時符合：
      1. MY_EMAIL 已設定；
      2. 寄件地址（解析後）與 MY_EMAIL 完全相同；
      3. 該信帶有 Gmail 的 SENT 標籤（只有從本人帳號寄出的信才有，外部偽造的信不會有）；
      4. 主旨含系統報告標記。
    任何一項不符就照一般信件分析。
    """
    my = (MY_EMAIL or '').strip().lower()
    if not my or 'SENT' not in (label_ids or ()):
        return False
    addr = parseaddr(sender or '')[1].strip().lower()
    if addr != my:
        return False
    subject = subject or ''
    return any(kw in subject for kw in SKIP_SUBJECTS) or \
        any(kw in subject for kw in ['釣魚', '警告', '偵測'])

def save_scan(scan_id, scan_time, total, high, med, low, wl, skipped, uid=''):
    conn = sqlite3.connect('phishing.db')
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO scan_history '
              '(id, scan_time, total, high, medium, low, whitelist, skipped, uid) VALUES (?,?,?,?,?,?,?,?,?)',
              (scan_id, scan_time, total, len(high), len(med), len(low), wl, skipped, uid))
    conn.commit()
    conn.close()

def get_history(uid=None):
    uid = uid or get_uid()
    conn = sqlite3.connect('phishing.db')
    c = conn.cursor()
    c.execute('SELECT id, scan_time, total, high, medium, low, whitelist, skipped, uid FROM scan_history '
              'WHERE uid=? ORDER BY scan_time DESC LIMIT 20', (uid,))
    rows = c.fetchall()
    conn.close()
    return rows

