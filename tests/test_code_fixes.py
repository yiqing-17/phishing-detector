"""修正項目的回歸測試：H4 規則、規則編號、IR 額度、錯誤頁不洩漏 traceback。"""
import re
from types import SimpleNamespace as NS

import analysis
import flask_app
from ratelimit import RateLimiter


def test_h4_hidden_element_is_detected():
    # 弱訊號需有強訊號（此處為含誘導字樣的可疑網域連結）佐證才計分
    html = ('<a href="https://secure-login.evil.top/verify">go</a>'
            '<div style="display:none">x</div><span style="visibility : hidden">y</span>')
    score, findings = analysis.analyze_html(html)
    assert ('隱藏元素', ['2 個']) in findings
    strong_only, _ = analysis.analyze_html('<a href="https://secure-login.evil.top/verify">go</a>')
    assert score - strong_only == 3


def test_weak_html_signals_alone_are_not_scored():
    # 合法電子報常見：隱藏預覽文字、1px 追蹤圖、品牌字樣 → 單獨出現不應計分也不應列為風險
    html = ('<div style="display:none">preview</div>'
            '<img src="https://t.example.com/p.gif" width="1" height="1">'
            '<p>Your Google order has shipped</p>')
    score, findings = analysis.analyze_html(html)
    assert score == 0 and findings == []


def test_repeated_html_url_finding_counts_once():
    one = '<a href="https://shop.example.com/account/a">a</a>'
    many = ''.join(f'<a href="https://shop.example.com/account/{c}">x</a>' for c in 'abcdef')
    assert analysis.analyze_html(many)[0] == analysis.analyze_html(one)[0]


def test_h4_not_triggered_by_visible_style():
    _, findings = analysis.analyze_html('<div style="display:block">x</div>')
    assert all(cat != '隱藏元素' for cat, _ in findings)


def test_self_test_includes_h4():
    data = flask_app.app.test_client().get('/self_test').get_json()
    names = {t['name']: t['passed'] for t in data['tests']}
    assert names.get('HTML 隱藏元素規則（H4）') is True


def test_rules_page_ids_are_unique_and_text_is_current():
    page = flask_app.app.test_client().get('/rules').get_data(as_text=True)
    ids = re.findall(r'<div class="rid">(R\d)</div>', page)
    assert ids == ['R1', 'R2', 'R3', 'R4', 'R5', 'R6', 'R7']
    assert 'rule_score ≥ 4' not in page and '關鍵字（4 類）' not in page
    assert '預估分數 ≥ 40' in page


def test_paste_page_text_is_current():
    page = flask_app.app.test_client().get('/paste').get_data(as_text=True)
    assert '三層式' not in page and '內文前 3,000 字' in page


def test_paste_error_does_not_leak_traceback(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError('secret-internal-detail')
    monkeypatch.setattr(flask_app, 'full_pipeline', boom)
    flask_app._limiter = RateLimiter()
    r = flask_app.app.test_client().post('/paste_analyze', data={'body': 'hello world'})
    text = r.get_data(as_text=True)
    assert 'Traceback' not in text and 'secret-internal-detail' not in text
    assert '分析時發生錯誤' in text


class _Req:
    def __init__(self, data): self._d = data
    def execute(self): return self._d


def _fake_service(n):
    msgs = {str(i): {'id': str(i), 'labelIds': ['INBOX'], 'payload': {'headers': [
        {'name': 'From', 'value': f'x{i}@evil{i}.top'}, {'name': 'Subject', 'value': f's{i}'}]}} for i in range(n)}
    messages = NS(
        list=lambda **k: _Req({'messages': [{'id': i} for i in msgs]}),
        get=lambda userId, id, format: _Req(msgs[id]))
    return NS(users=lambda: NS(messages=lambda: messages))


def test_ir_llm_budget_counts_every_high_risk_incident(monkeypatch, tmp_path):
    """70–84 分的高風險信也要用掉 IR LLM 額度（舊版只在 >=85 時才扣）。"""
    monkeypatch.chdir(tmp_path)
    flask_app.init_db()
    monkeypatch.setattr(flask_app, 'IR_LLM_PER_SCAN', 3)
    monkeypatch.setattr(flask_app, 'Credentials', lambda **k: object())
    monkeypatch.setattr(flask_app, 'build', lambda *a, **k: _fake_service(5))
    report = {'risk_level': 'high', 'risk_score': 75, 'agent_meta': {'triggered': False, 'status': 'skipped'}}
    monkeypatch.setattr(flask_app, 'full_pipeline', lambda *a, **k: (dict(report), 0, [], 0, None))
    flags = []

    def fake_entry(*a, use_llm=True, **k):
        flags.append(use_llm)
        return {'level': 'high', 'risk_score': 75, 'ir': {'id': 'IR-X'}}
    monkeypatch.setattr(flask_app, 'build_analyzed_entry', fake_entry)
    flask_app._scans['t1'] = {'done': False, 'owner': 'u' * 32}
    flask_app.do_scan({'token': 't'}, 't1', 'u' * 32)
    assert flask_app._scans['t1'].get('error') is None
    assert flags == [True, True, True, False, False]
