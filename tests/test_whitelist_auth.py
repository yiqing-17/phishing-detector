"""白名單必須搭配驗證：只看 From 的寄件者不可信。"""
from unittest import mock
import pytest
import analysis
import storage
from email_parser import get_trusted_auth

GOOD = ('mx.google.com; dkim=pass header.i=@google.com header.s=20230601 header.b=abc; '
        'spf=pass (google.com: domain of a@google.com designates 1.2.3.4 as permitted sender) smtp.mailfrom=a@google.com; '
        'dmarc=pass (p=REJECT sp=REJECT dis=NONE) header.from=google.com')
BAD = ('mx.google.com; dkim=none; spf=fail (google.com: domain of a@google.com does not designate 9.9.9.9) '
       'smtp.mailfrom=a@google.com; dmarc=fail (p=REJECT sp=REJECT dis=REJECT) header.from=google.com')
FORGED = 'mx.google.com; dkim=pass; spf=pass; dmarc=pass header.from=google.com'


def msg(*values):
    return {'payload': {'headers': [{'name': 'Authentication-Results', 'value': v} for v in values]}}


@pytest.fixture(autouse=True)
def default_whitelist(monkeypatch):
    monkeypatch.setattr(storage, 'get_whitelist', lambda uid=None: ['google.com'])


def test_parse_pass_and_fail():
    a = get_trusted_auth(msg(GOOD))
    assert (a['available'], a['dmarc'], a['spf'], a['dkim'], a['header_from']) == (True, 'pass', 'pass', 'pass', 'google.com')
    assert get_trusted_auth(msg(BAD))['dmarc'] == 'fail'


def test_only_topmost_trusted_header_counts():
    """Gmail 自己的標頭在最上面；攻擊者偽造的 pass 在下面，不可蓋過它。"""
    a = get_trusted_auth(msg(BAD, FORGED))
    assert a['dmarc'] == 'fail'


def test_untrusted_authserv_is_ignored():
    assert get_trusted_auth(msg('evil.example; dmarc=pass header.from=google.com'))['available'] is False
    assert get_trusted_auth({'payload': {'headers': []}})['available'] is False


def test_trusted_requires_dmarc_pass_and_aligned_from():
    assert storage.whitelist_verdict('a@google.com', get_trusted_auth(msg(GOOD)))[0] == 'trusted'


def test_subdomain_not_aligned_is_not_trusted():
    assert storage.whitelist_verdict('x@accounts.google.com', get_trusted_auth(msg(GOOD)))[0] == 'unverified'


def test_spoofed_whitelisted_sender_is_flagged():
    assert storage.whitelist_verdict('a@google.com', get_trusted_auth(msg(BAD)))[0] == 'spoof_suspect'


def test_no_auth_means_unverified_not_trusted():
    assert storage.whitelist_verdict('a@google.com', None)[0] == 'unverified'
    assert storage.whitelist_verdict('a@google.com', {'available': False})[0] == 'unverified'


def test_non_whitelisted_sender():
    assert storage.whitelist_verdict('a@evil.com', get_trusted_auth(msg(GOOD)))[0] == 'none'


def test_spoof_floor_forces_at_least_medium():
    text = 'From: a@google.com\nSubject: hello\nBody: see you at lunch tomorrow'
    note = {'verdict': 'spoof_suspect', 'domain': 'google.com', 'hit': 'google.com', 'floor': 40}
    with mock.patch.object(analysis, 'groq_client', None):
        base, *_ = analysis.full_pipeline(text, sender='a@google.com')
        rep, *_ = analysis.full_pipeline(text, sender='a@google.com', wl_note=note)
    assert base['risk_level'] == 'low'
    assert rep['risk_level'] == 'medium' and rep['risk_score'] == 40
    assert rep['score_validation']['consistent'] is True
    assert rep['explainable_findings'][0]['source'] == '白名單驗證'


def test_unverified_note_does_not_change_score():
    text = 'From: a@google.com\nSubject: hello\nBody: see you at lunch tomorrow'
    note = {'verdict': 'unverified', 'domain': 'google.com', 'hit': 'google.com', 'floor': 0}
    with mock.patch.object(analysis, 'groq_client', None):
        base, *_ = analysis.full_pipeline(text, sender='a@google.com')
        rep, *_ = analysis.full_pipeline(text, sender='a@google.com', wl_note=note)
    assert rep['risk_score'] == base['risk_score']



def test_unverified_reason_names_the_failing_check(monkeypatch):
    monkeypatch.setattr(storage, 'get_whitelist', lambda uid=None: ['skims.com'])
    sender = 'SKIMS <no-reply@emails.skims.com>'
    ok = {'available': True, 'dmarc': 'pass', 'spf': 'pass', 'dkim': 'pass', 'header_from': 'emails.skims.com'}
    assert storage.whitelist_verdict(sender, ok)[0] == 'trusted'
    assert storage.whitelist_reason(sender, ok) .startswith('SPF=')           # 全過時只剩資訊列
    none = dict(ok, dmarc='none')
    assert storage.whitelist_verdict(sender, none)[0] == 'unverified'
    assert 'DMARC=none' in storage.whitelist_reason(sender, none)
    skew = dict(ok, header_from='skims.com')
    assert storage.whitelist_verdict(sender, skew)[0] == 'unverified'
    assert 'header.from=skims.com' in storage.whitelist_reason(sender, skew)
    assert '貼信模式' in storage.whitelist_reason(sender, None)
