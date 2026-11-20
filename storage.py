"""SQLite persistence and visitor-scoped whitelist helpers."""
import json
import re
from datetime import datetime
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
    c.execute('''CREATE TABLE IF NOT EXISTS incidents
        (id TEXT PRIMARY KEY, uid TEXT NOT NULL, subject TEXT, sender TEXT, severity TEXT,
         risk_score INTEGER, status TEXT NOT NULL, created_at TEXT, updated_at TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS incident_events
        (id INTEGER PRIMARY KEY AUTOINCREMENT, incident_id TEXT NOT NULL, ts TEXT, from_status TEXT,
         to_status TEXT, note TEXT)''')
    c.execute('CREATE INDEX IF NOT EXISTS idx_inc_uid ON incidents (uid, updated_at)')
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

def whitelist_reason(sender, auth=None, uid=None):
    """白名單命中但未被信任時，說明「哪一項沒過」，讓使用者能判斷是設定問題還是真的可疑。"""
    domain, hit, _ = whitelist_match(sender, uid)
    if not hit:
        return ''
    if not auth or not auth.get('available'):
        return '沒有取得 Gmail 的 Authentication-Results（貼信模式，或標頭缺失）'
    parts = []
    if auth.get('dmarc') != 'pass':
        parts.append(f"DMARC={auth.get('dmarc')}（需要 pass）")
    if (auth.get('header_from') or '').lower() != domain:
        parts.append(f"header.from={auth.get('header_from') or '（空）'} 與寄件網域 {domain} 不一致")
    parts.append(f"SPF={auth.get('spf')}、DKIM={auth.get('dkim')}")
    return '；'.join(parts)


def whitelist_verdict(sender, auth=None, uid=None):
    """白名單不再只看 From（From 可以偽造）。回傳 (verdict, domain, hit, mode)：

    trusted        命中白名單，且 Gmail 的 DMARC 驗證通過、header.from 與寄件網域一致 → 可略過分析
    spoof_suspect  命中白名單，但 DMARC / SPF / DKIM 明確失敗 → 疑似冒用，完整分析並至少列為中風險
    unverified     命中白名單，但沒有可信的驗證結果（貼信模式、標頭缺失）→ 不能信 From，完整分析
    none           未命中白名單
    """
    domain, hit, mode = whitelist_match(sender, uid)
    if not hit:
        return 'none', domain, '', ''
    if not auth or not auth.get('available'):
        return 'unverified', domain, hit, mode
    if auth.get('dmarc') == 'pass' and auth.get('header_from', '').lower() == domain:
        return 'trusted', domain, hit, mode
    if 'fail' in (auth.get('dmarc'), auth.get('dkim')) or auth.get('spf') in ('fail', 'softfail'):
        return 'spoof_suspect', domain, hit, mode
    return 'unverified', domain, hit, mode


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


# ── 事件（Incident）生命週期 ─────────────────────────────────
# Open → Triaged → Contained → Closed；任何未結案階段都可標為 False Positive；結案後可重開。
# 結案（Closed / False Positive）必須填寫處理說明，確保每個事件都有可稽核的結論。
INCIDENT_TRANSITIONS = {
    'Open': ('Triaged', 'False Positive'),
    'Triaged': ('Contained', 'False Positive'),
    'Contained': ('Closed', 'False Positive'),
    'False Positive': ('Open',),
    'Closed': ('Open',),
}
NOTE_REQUIRED = ('Closed', 'False Positive', 'Open')   # 重開也要說明原因（Open 僅在重開時需要，見下）
MAX_NOTE = 500


def create_incident(uid, ir, db='phishing.db'):
    """建立事件（同一 id 只建一次）。ir 為 result_builder 產生的 IR 摘要。"""
    now = datetime.now().isoformat(timespec='seconds')
    conn = sqlite3.connect(db)
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO incidents (id, uid, subject, sender, severity, risk_score, status, created_at, updated_at)'
              ' VALUES (?,?,?,?,?,?,?,?,?)',
              (ir['id'], uid, (ir.get('email_subject') or '')[:120], (ir.get('email_sender') or '')[:120],
               ir.get('severity', 'High'), int(ir.get('risk_score') or 0), 'Open', now, now))
    if c.rowcount:
        c.execute('INSERT INTO incident_events (incident_id, ts, from_status, to_status, note) VALUES (?,?,?,?,?)',
                  (ir['id'], now, '', 'Open', '系統自動建立'))
    conn.commit()
    conn.close()


def _row_to_incident(c, row):
    inc = dict(zip(('id', 'subject', 'sender', 'severity', 'risk_score', 'status', 'created_at', 'updated_at'), row))
    c.execute('SELECT ts, from_status, to_status, note FROM incident_events WHERE incident_id=? ORDER BY id', (inc['id'],))
    inc['events'] = [dict(zip(('ts', 'from', 'to', 'note'), r)) for r in c.fetchall()]
    inc['allowed_next'] = list(INCIDENT_TRANSITIONS.get(inc['status'], ()))
    # 處理時效：建立 → 首次分流（MTTA）、建立 → 最近一次結案（MTTR）
    def secs(a, b):
        try:
            return int((datetime.fromisoformat(b) - datetime.fromisoformat(a)).total_seconds())
        except (TypeError, ValueError):
            return None
    tri = next((e['ts'] for e in inc['events'] if e['to'] == 'Triaged'), None)
    clo = next((e['ts'] for e in reversed(inc['events']) if e['to'] in ('Closed', 'False Positive')), None)
    inc['time_to_triage_s'] = secs(inc['created_at'], tri) if tri else None
    inc['time_to_resolve_s'] = secs(inc['created_at'], clo) if clo and inc['status'] in ('Closed', 'False Positive') else None
    return inc


_COLS = 'id, subject, sender, severity, risk_score, status, created_at, updated_at'


def get_incident(uid, incident_id, db='phishing.db'):
    conn = sqlite3.connect(db)
    c = conn.cursor()
    c.execute(f'SELECT {_COLS} FROM incidents WHERE id=? AND uid=?', (incident_id, uid))
    row = c.fetchone()
    inc = _row_to_incident(c, row) if row else None
    conn.close()
    return inc


def list_incidents(uid, db='phishing.db'):
    conn = sqlite3.connect(db)
    c = conn.cursor()
    c.execute(f'SELECT {_COLS} FROM incidents WHERE uid=? ORDER BY updated_at DESC LIMIT 100', (uid,))
    rows = c.fetchall()
    out = [_row_to_incident(c, r) for r in rows]
    conn.close()
    return out


def transition_incident(uid, incident_id, new_status, note='', db='phishing.db'):
    """回傳 (ok, error_message, incident)。只能操作自己的事件，且必須符合狀態機。"""
    note = (note or '').strip()[:MAX_NOTE]
    inc = get_incident(uid, incident_id, db)
    if not inc:
        return False, '找不到這個事件', None
    cur = inc['status']
    if new_status not in INCIDENT_TRANSITIONS.get(cur, ()):
        return False, f'不能從 {cur} 直接改為 {new_status}', inc
    needs_note = new_status in ('Closed', 'False Positive') or cur in ('Closed', 'False Positive')
    if needs_note and len(note) < 5:
        return False, '結案、判定誤報或重開事件時，請填寫至少 5 個字的處理說明', inc
    now = datetime.now().isoformat(timespec='seconds')
    conn = sqlite3.connect(db)
    c = conn.cursor()
    c.execute('UPDATE incidents SET status=?, updated_at=? WHERE id=? AND uid=? AND status=?',
              (new_status, now, incident_id, uid, cur))
    if c.rowcount != 1:      # 併發：狀態已被改動
        conn.close()
        return False, '事件狀態已變更，請重新整理', get_incident(uid, incident_id, db)
    c.execute('INSERT INTO incident_events (incident_id, ts, from_status, to_status, note) VALUES (?,?,?,?,?)',
              (incident_id, now, cur, new_status, note))
    conn.commit()
    conn.close()
    return True, '', get_incident(uid, incident_id, db)
