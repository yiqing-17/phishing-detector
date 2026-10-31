"""Flask routes and application wiring for the phishing detector."""
import json
import os
import secrets
import sqlite3
import threading
import uuid
from datetime import datetime, timedelta
from flask import Flask, g, jsonify, redirect, render_template_string, request, session
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from config import (
    BASE_URL, COOKIE_SECURE, FLASK_SECRET_KEY, GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET, GOOGLE_PROJECT_ID, GROQ_API_KEY,
    SCOPES, DEFAULT_WHITELIST,
)
from storage import (
    get_history, get_uid, get_whitelist, get_whitelist_rows, init_db,
    is_system_report, is_whitelisted, normalize_whitelist_domain,
    save_scan, whitelist_match,
)
from analysis import (
    Groq, RULE_HTML_ITEMS, RULE_KEYWORD_GROUPS, RULE_URL_ITEMS,
    analyze_html, analyze_url, full_pipeline,
    model, model_metrics, run_risk_score_self_test, vectorizer,
)
from email_parser import get_body, get_header, get_html
from result_builder import build_analyzed_entry
from scan_policy import analyze_email
from site_quality import (
    add_home_privacy_note,
    apply_model_metrics,
    correct_legacy_copy,
    inject_locale_assets,
    resolve_language,
)
from templates import (
    HISTORY_HTML, HOME_HTML, LOADING_HTML, RESULT_HTML,
    RULES_HTML, WHITELIST_HTML, _kw_json, render_error, render_home_page, render_paste_page,
)


init_db()

# ── Flask ─────────────────────────────────────────────────────
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2 MB
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = COOKIE_SECURE


@app.errorhandler(413)
def handle_payload_too_large(e):
    if request.path.startswith('/api') or request.is_json:
        return jsonify({"ok": False, "error": "內容過大，請縮短郵件內容後再試。"}), 413
    return render_error('內容過大', '郵件內容太長，請縮短後再送檢。'), 413

@app.errorhandler(404)
def handle_not_found(e):
    if request.path.startswith('/api') or request.is_json:
        return jsonify({"ok": False, "error": "找不到要求的頁面。"}), 404
    return render_error('查無此案', '找不到你要的頁面，可能已經移走，或網址打錯了。'), 404

@app.errorhandler(500)
def handle_internal_error(e):
    app.logger.exception("Unhandled application error")
    if request.path.startswith('/api') or request.is_json:
        return jsonify({"ok": False, "error": "系統暫時發生錯誤，請稍後再試。"}), 500
    return render_error('案件退回', '系統暫時發生錯誤，請稍後再試。'), 500

app.secret_key = FLASK_SECRET_KEY or secrets.token_hex(32)
if not FLASK_SECRET_KEY and BASE_URL.startswith('https://'):
    print('WARNING: FLASK_SECRET_KEY 未設定，已使用隨機暫時金鑰；正式部署請設定環境變數。')
# HttpOnly / SameSite / Secure 已於上方依 BASE_URL 設定（https 時預設啟用 Secure），此處只補長效 session
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=365)
_creds = {}     # uid -> Google 授權憑證（只存在伺服器記憶體，掃描結束即清除）
_scans = {}     # scan_id -> 掃描結果（含 owner，只有擁有者能讀）


@app.after_request
def add_security_headers(response):
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault(
        "Permissions-Policy",
        "camera=(), microphone=(), geolocation=()"
    )
    if response.mimetype == 'text/html':
        language = getattr(g, 'language', 'zh')
        response.headers['Content-Language'] = language
        vary = {value.strip() for value in response.headers.get('Vary', '').split(',') if value.strip()}
        if '*' not in vary:
            vary.add('Cookie')
            response.headers['Vary'] = ', '.join(sorted(vary))
        page = response.get_data(as_text=True)
        if request.path == '/scan':
            page = page.replace('白名單／略過', '略過（系統通知）')
        elif not request.path.startswith('/result/'):
            page = correct_legacy_copy(page)
        response.set_data(inject_locale_assets(page, language))
    return response


@app.before_request
def select_language():
    requested = request.args.get('lang')
    if requested in ('zh', 'en'):
        session['language'] = requested
    g.language = resolve_language(requested, session.get('language'))

@app.route('/')
def index():
    page = correct_legacy_copy(render_home_page(RULE_KEYWORD_GROUPS))
    page = apply_model_metrics(page, model_metrics)
    return add_home_privacy_note(page, getattr(g, 'language', 'zh'))

def create_google_flow(state=None):
    """建立 Google OAuth Flow。優先使用環境變數，沒有才讀 credentials.json。"""
    redirect_uri = f'{BASE_URL}/callback'
    if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
        config = {
            'web': {
                'client_id': GOOGLE_CLIENT_ID,
                'project_id': GOOGLE_PROJECT_ID,
                'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
                'token_uri': 'https://oauth2.googleapis.com/token',
                'auth_provider_x509_cert_url': 'https://www.googleapis.com/oauth2/v1/certs',
                'client_secret': GOOGLE_CLIENT_SECRET,
                'redirect_uris': [redirect_uri]
            }
        }
        return Flow.from_client_config(config, scopes=SCOPES,
                                       redirect_uri=redirect_uri, state=state)

    if os.path.exists('credentials.json'):
        return Flow.from_client_secrets_file(
            'credentials.json', scopes=SCOPES,
            redirect_uri=redirect_uri, state=state)

    raise RuntimeError(
        '找不到 Google OAuth 設定。請設定 GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET，'
        '或放置 credentials.json。'
    )

@app.route('/login')
def login():
    import secrets, hashlib, base64 as _b64
    cv = secrets.token_urlsafe(64)
    cc = _b64.urlsafe_b64encode(hashlib.sha256(cv.encode()).digest()).rstrip(b'=').decode()
    get_uid()
    session['code_verifier'] = cv
    flow = create_google_flow()
    auth_url, state = flow.authorization_url(prompt='consent', access_type='offline',
                                              hl=getattr(g, 'language', 'zh'),
                                              code_challenge=cc, code_challenge_method='S256')
    session['oauth_state'] = state
    return redirect(auth_url)

@app.route('/callback')
def callback():
    try:
        uid = get_uid()
        flow = create_google_flow(state=session.get('oauth_state',''))
        auth_resp = request.url
        flow.fetch_token(authorization_response=auth_resp,
                         code_verifier=session.get('code_verifier',''))
        creds = flow.credentials
        session.pop('code_verifier', None); session.pop('oauth_state', None)
        _creds[uid] = {
            'token': creds.token, 'refresh_token': creds.refresh_token,
            'token_uri': creds.token_uri, 'client_id': creds.client_id,
            'client_secret': creds.client_secret, 'scopes': list(creds.scopes)
        }
        return redirect('/scan')
    except Exception as e:
        import traceback
        detail = traceback.format_exc()
        return render_error('Google Gmail 授權失敗', '請確認 Google OAuth 的重新導向 URI、Client ID / Secret 與 Gmail API 設定。', detail), 500

def _scan_progress(scan_id, level):
    """記錄每封信完成後的風險等級，供掃描中頁面顯示真實進度（不含信件內容）。"""
    st = _scans.get(scan_id)
    if st is not None and not st.get('done'):
        st.setdefault('progress', []).append(level)

def do_scan(token_data, scan_id, uid):
    try:
        creds = Credentials(**token_data)
        service = build('gmail','v1',credentials=creds)
        results_api = service.users().messages().list(
            userId='me', maxResults=15, labelIds=['INBOX']).execute()
        messages = results_api.get('messages', [])
        inbox_count = len(messages)
        _scans[scan_id]['inbox_total'] = inbox_count
        _scans[scan_id]['progress'] = []
        all_emails = []
        high_list, med_list, low_list = [], [], []
        wl_list = []
        skipped = 0

        for msg_ref in messages:
            msg = service.users().messages().get(
                userId='me', id=msg_ref['id'], format='full').execute()
            sender  = get_header(msg, 'From')
            subject = get_header(msg, 'Subject') or '(無主旨)'
            body    = get_body(msg)
            html    = get_html(msg)
            text    = f"From: {sender}\nSubject: {subject}\nBody: {body}"

            if is_system_report(sender, subject):
                skipped += 1
                _scan_progress(scan_id, 'sk')
                continue

            entry = analyze_email(
                sender=sender, subject=subject, body=body, text=text, html=html, uid=uid,
                whitelist_match=whitelist_match, full_pipeline=full_pipeline,
                build_entry=build_analyzed_entry,
            )

            if any(x.get('title') == '白名單提示' for x in entry.get('explainable_findings', [])):
                wl_list.append(entry)

            if entry['level'] == 'high':
                high_list.append(entry)
            elif entry['level'] == 'medium':
                med_list.append(entry)
            else:
                low_list.append(entry)
            all_emails.append(entry)
            _scan_progress(scan_id, entry['level'])

        scan_time = datetime.now().strftime('%Y-%m-%d %H:%M')
        # Keep persistent risk buckets mutually exclusive; allowlist matches are in-memory annotations.
        save_scan(scan_id, scan_time,
                  len(high_list)+len(med_list)+len(low_list),
                  high_list, med_list, low_list, 0, skipped, uid)

        _scans[scan_id] = {
            'owner': uid,
            'done': True,
            'all_emails': all_emails,
            'high': len(high_list), 'med': len(med_list),
            'low': len(low_list), 'wl': len(wl_list), 'skipped': skipped,
            'total': len(all_emails),
            'inbox_messages_fetched': inbox_count
        }
    except Exception as e:
        import traceback
        _scans[scan_id] = {'owner': uid, 'done': True, 'error': traceback.format_exc()}
    finally:
        _creds.pop(uid, None)   # 掃描結束就清除授權憑證，不長期留在伺服器記憶體

@app.route('/scan')
def scan():
    uid = get_uid()
    token_data = _creds.get(uid)
    if not token_data: return redirect('/')
    scan_id = str(uuid.uuid4())[:8]
    _scans[scan_id] = {'done': False, 'owner': uid}
    session['last_scan_id'] = scan_id
    threading.Thread(target=do_scan, args=(token_data, scan_id, uid)).start()
    return LOADING_HTML

@app.route('/scan_status')
def scan_status():
    uid = get_uid()
    scan_id = session.get('last_scan_id', '')
    st = _scans.get(scan_id) if scan_id else None
    if st and st.get('owner') == uid:
        return jsonify({'done': st.get('done',False), 'scan_id': scan_id,
                        'total': st.get('inbox_total'), 'progress': st.get('progress', [])})
    return jsonify({'done': False, 'scan_id': ''})

@app.route('/paste')
def paste_page():
    return render_paste_page(request.args.get('sample', '').strip(), rule_keyword_groups=RULE_KEYWORD_GROUPS)

@app.route('/paste_analyze', methods=['POST'])
def paste_analyze():
    uid = get_uid()
    sender  = request.form.get('sender', '').strip() or '(未提供寄件者)'
    subject = request.form.get('subject', '').strip() or '(無主旨)'
    body    = request.form.get('body', '').strip()
    html    = request.form.get('html', '').strip()

    if not body:
        err = '<div class="err-box">請貼上郵件內文再送出。</div>'
        return render_paste_page(error=err, rule_keyword_groups=RULE_KEYWORD_GROUPS)

    text = f"From: {sender}\nSubject: {subject}\nBody: {body}"

    try:
        entry = analyze_email(
            sender=sender, subject=subject, body=body, text=text, html=html, uid=uid,
            whitelist_match=whitelist_match, full_pipeline=full_pipeline,
            build_entry=build_analyzed_entry,
        )
        high = int(entry['level'] == 'high')
        med = int(entry['level'] == 'medium')
        low = int(entry['level'] == 'low')
        wl = int(any(x.get('title') == '白名單提示' for x in entry.get('explainable_findings', [])))

        scan_id = str(uuid.uuid4())[:8]
        _scans[scan_id] = {
            'done': True,
            'owner': uid,
            'all_emails': [entry],
            'high': high, 'med': med, 'low': low, 'wl': wl, 'skipped': 0,
            'total': 1
        }
        scan_time = datetime.now().strftime('%Y-%m-%d %H:%M')
        # The case result retains the allowlist hint; history stores non-overlapping risk counts.
        save_scan(scan_id, scan_time, 1, ['x'] * high, ['x'] * med, ['x'] * low, 0, 0, uid)
        return redirect(f'/result/{scan_id}')
    except Exception:
        import traceback
        err = f'<div class="err-box"><pre>{traceback.format_exc()}</pre></div>'
        return render_paste_page(error=err, rule_keyword_groups=RULE_KEYWORD_GROUPS)

@app.route('/result/<scan_id>')
def result(scan_id):
    data = _scans.get(scan_id)
    if not data or not data.get('done') or data.get('owner') != get_uid(): return redirect('/')
    if 'error' in data:
        return render_error('案件退回', '這批信件在檢驗途中出了問題，詳細資訊如下。', data['error']), 500

    all_emails = data['all_emails']

    # 建立左側列表 HTML
    import html as html_lib

    def make_item(e, idx):
        level = e.get('level', 'wl')
        dot = {'high':'dot-high','medium':'dot-med','low':'dot-low','wl':'dot-wl'}.get(level,'dot-wl')
        score_text = f"{e.get('risk_score', -1)}/100 · {e.get('category','')}" if e.get('risk_score', -1) >= 0 else '白名單 · 略過分析'
        reason = ''
        findings = e.get('explainable_findings') or []
        if findings:
            reason = str(findings[0].get('title') or findings[0].get('detail') or '')
        elif e.get('explanation'):
            reason = str(e.get('explanation'))
        reason = html_lib.escape(reason[:70])
        subject = html_lib.escape(str(e.get('subject','')))
        sender = html_lib.escape(str(e.get('sender','')))
        category = html_lib.escape(str(e.get('category','')))
        item_subject = html_lib.escape(str(e.get('subject', '')))
        accessible_label = (
            '開啟郵件分析結果：' + item_subject
            if getattr(g, 'language', 'zh') == 'zh'
            else 'Open email analysis: ' + item_subject
        )
        return (f'<div class="email-item" role="button" tabindex="0" '
                f'aria-label="{accessible_label}" data-idx="{idx}" '
                f'onkeydown="if(event.key===\'Enter\'||event.key===\' \'){{event.preventDefault();this.click();}}" '
                f'onclick="showDetail({idx}, this)">'
                f'<div class="risk-dot {dot}"></div>'
                f'<div class="item-body">'
                f'<div class="item-subj">{subject}</div>'
                f'<div class="item-from">{sender}</div>'
                f'<div class="item-score">{html_lib.escape(score_text)}</div>'
                f'{f"<div class=\"item-reason {level}\">› {reason}</div>" if reason else ""}'
                f'</div></div>')

    high_items  = [make_item(e,i) for i,e in enumerate(all_emails) if e['level']=='high']
    med_items   = [make_item(e,i) for i,e in enumerate(all_emails) if e['level']=='medium']
    low_items   = [make_item(e,i) for i,e in enumerate(all_emails) if e['level']=='low']
    wl_items    = [make_item(e,i) for i,e in enumerate(all_emails) if e['level']=='wl']

    list_html = ''
    if high_items:  list_html += '<div class="list-sec">高風險</div>' + ''.join(high_items)
    if med_items:   list_html += '<div class="list-sec">中風險</div>' + ''.join(med_items)
    if low_items:   list_html += '<div class="list-sec">安全</div>' + ''.join(low_items)
    if wl_items:    list_html += '<div class="list-sec">白名單</div>' + ''.join(wl_items)

    # 把資料注入 JS
    import html as html_lib
    emails_json = json.dumps(all_emails, ensure_ascii=False).replace(
        '<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')

    page = RESULT_HTML.replace('KEYWORDS_PLACEHOLDER', _kw_json(RULE_KEYWORD_GROUPS))
    page = page.replace('TOTAL_COUNT', str(data['total']))
    page = page.replace('HIGH_COUNT',  str(data['high']))
    page = page.replace('MED_COUNT',   str(data['med']))
    page = page.replace('LOW_COUNT',   str(data['low']))
    page = page.replace('WL_COUNT',    str(data['wl']))
    page = page.replace('SK_COUNT',    str(data['skipped']))
    total_for_pct = max(int(data.get('total', 0)), 1)
    analyzed_count = int(data.get('high', 0)) + int(data.get('med', 0)) + int(data.get('low', 0))
    page = page.replace('HIGH_PCT', f"{data['high'] / total_for_pct * 100:.2f}")
    page = page.replace('MED_PCT', f"{data['med'] / total_for_pct * 100:.2f}")
    page = page.replace('LOW_PCT', f"{data['low'] / total_for_pct * 100:.2f}")
    # Allowlist matches are a subset of analyzed risk buckets, never a separate slice.
    page = page.replace('WL_PCT', '0.00')
    page = page.replace('ANALYZED_COUNT', str(analyzed_count))
    # Correct static template copy before inserting subject/body values from the email.
    page = correct_legacy_copy(page)
    # 使用者內容（信件列表、信件資料）最後才注入，避免內容中的字串被誤替換
    page = page.replace('LIST_PLACEHOLDER', list_html)
    page = page.replace('PLACEHOLDER_DATA', emails_json)
    return page


@app.route('/history')
def history():
    rows = get_history()
    return render_template_string(HISTORY_HTML, history=rows)

@app.route('/rules')
def rules_page():
    kw_total = sum(len(g[3]) for g in RULE_KEYWORD_GROUPS)
    return render_template_string(
        RULES_HTML, groups=RULE_KEYWORD_GROUPS, url_items=RULE_URL_ITEMS,
        html_items=RULE_HTML_ITEMS, kw_total=kw_total,
        whitelist_count=len(get_whitelist()))

@app.route('/whitelist/check', methods=['POST'])
def whitelist_check():
    """白名單檢測：輸入寄件者，回傳是否命中及命中的規則（供展示用，不寫入資料庫）。"""
    data = request.get_json(silent=True) or {}
    sender = str(data.get('sender', ''))[:200]
    domain, hit, mode = whitelist_match(sender)
    if not domain:
        return jsonify({'success': False, 'error': '無法從輸入中解析出寄件網域，請輸入如 name@example.com'}), 400
    return jsonify({'success': True, 'domain': domain, 'matched': bool(hit),
                    'whitelist_domain': hit, 'mode': mode})

@app.route('/whitelist')
def whitelist_page():
    domains = get_whitelist_rows()
    return render_template_string(WHITELIST_HTML, domains=domains, count=len(domains))

@app.route('/whitelist/add', methods=['POST'])
def whitelist_add():
    uid = get_uid()
    data = request.get_json(silent=True) or {}
    domain = normalize_whitelist_domain(data.get('domain', ''))
    if not domain:
        return jsonify({'success':False,'error':'網域格式不正確，請輸入例如 example.com'}), 400
    current = get_whitelist(uid)
    if domain in current:
        return jsonify({'success':False,'error':'這個網域已經在白名單中'})
    if len(current) >= 300:
        return jsonify({'success':False,'error':'白名單數量已達上限（300）'}), 400
    try:
        conn = sqlite3.connect('phishing.db')
        c = conn.cursor()
        if domain in DEFAULT_WHITELIST:     # 之前刪掉的預設網域：取消刪除即可
            c.execute('DELETE FROM user_whitelist WHERE uid=? AND domain=?', (uid, domain))
        else:
            c.execute('INSERT OR REPLACE INTO user_whitelist (uid, domain, action, added_time) VALUES (?,?,?,?)',
                      (uid, domain, 'add', datetime.now().isoformat()))
        conn.commit(); conn.close()
        return jsonify({'success':True,'domain':domain})
    except Exception:
        return jsonify({'success':False,'error':'發放通行失敗'})

@app.route('/whitelist/reset', methods=['POST'])
def whitelist_reset():
    """還原預設白名單（補回被刪除的預設網域，不影響自行新增的網域）。只影響目前這位訪客。"""
    uid = get_uid()
    conn = sqlite3.connect('phishing.db')
    c = conn.cursor()
    c.execute("DELETE FROM user_whitelist WHERE uid=? AND action='del'", (uid,))
    conn.commit(); conn.close()
    return jsonify({'success': True})

@app.route('/whitelist/delete', methods=['POST'])
def whitelist_delete():
    uid = get_uid()
    data = request.get_json(silent=True) or {}
    domain = normalize_whitelist_domain(data.get('domain', ''))
    if not domain:
        return jsonify({'success':False,'error':'網域格式不正確'}), 400
    if domain not in get_whitelist(uid):
        return jsonify({'success':True,'deleted':False})
    conn = sqlite3.connect('phishing.db')
    c = conn.cursor()
    if domain in DEFAULT_WHITELIST:         # 預設網域：記一筆「刪除」
        c.execute('INSERT OR REPLACE INTO user_whitelist (uid, domain, action, added_time) VALUES (?,?,?,?)',
                  (uid, domain, 'del', datetime.now().isoformat()))
    else:
        c.execute('DELETE FROM user_whitelist WHERE uid=? AND domain=?', (uid, domain))
    conn.commit(); conn.close()
    return jsonify({'success':True,'deleted':True})

def run_system_self_test():
    """執行不依賴 Gmail / Groq 的本機系統自我檢測。"""
    tests = []

    def add(name, passed, detail=''):
        tests.append({'name': name, 'passed': bool(passed), 'detail': detail})

    # 1. 模型與向量器
    add('ML 模型已載入', model is not None and hasattr(model, 'predict_proba'),
        'predict_proba 可用' if model is not None else '模型未載入')
    add('TF-IDF 已載入', vectorizer is not None and hasattr(vectorizer, 'transform'),
        'transform 可用' if vectorizer is not None else '向量器未載入')

    # 2. 風險公式與門檻
    for item in run_risk_score_self_test():
        add('風險公式：' + item['name'], item['passed'],
            f"actual={item['actual']}, expected={item['expected']}")

    # 3. URL 分析
    url_findings = analyze_url('https://example.xyz/login/verify')
    add('URL 風險分析', len(url_findings) >= 2, str(url_findings))

    # 4. HTML 分析
    sample_html = '''<html><body>
        <a href="https://evil.xyz/login">https://google.com/login</a>
        <img src="https://evil.xyz/p.gif" width="1" height="1">
        <form><input type="password"></form>
        <div style="display:none">hidden</div>
    </body></html>'''
    html_score, html_findings = analyze_html(sample_html)
    add('HTML 風險分析', html_score > 0 and len(html_findings) >= 3,
        f'score={html_score}, findings={len(html_findings)}')

    # 5. 白名單
    normalized = normalize_whitelist_domain('https://Example.COM/path')
    add('白名單網域正規化', normalized == 'example.com', normalized)
    add('白名單子網域比對', is_whitelisted('User <a@accounts.google.com>'),
        'google.com 子網域應通過' if is_whitelisted('User <a@accounts.google.com>') else '比對失敗')

    # 6. Flask 路由
    route_paths = {str(rule.rule) for rule in app.url_map.iter_rules()}
    required_routes = {'/', '/health', '/self_test', '/paste', '/history', '/whitelist'}
    missing = sorted(required_routes - route_paths)
    add('核心路由存在', not missing, 'missing=' + ','.join(missing))

    passed = sum(1 for x in tests if x['passed'])
    total = len(tests)
    return {
        'status': 'ok' if passed == total else 'warning',
        'passed': passed,
        'total': total,
        'tests': tests,
        'external_services_tested': False,
        'note': '自我檢測不會連線 Gmail 或 Groq。'
    }


@app.route('/self_test')
def self_test():
    return jsonify(run_system_self_test())


@app.route('/health')
def health():
    ml_ready = model is not None and vectorizer is not None
    self_test = run_system_self_test()
    return jsonify({
        'status': 'ok' if self_test['status'] == 'ok' else 'warning',
        'time': datetime.now().isoformat(),
        'ml_model_loaded': model is not None,
        'tfidf_loaded': vectorizer is not None,
        'gmail_oauth_configured': bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET),
        'ai_configured': bool(GROQ_API_KEY and Groq is not None),
        'ml_ready': ml_ready,
        'self_test': {
            'status': self_test['status'],
            'passed': self_test['passed'],
            'total': self_test['total']
        }
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

