import socket
from unittest import mock

import pytest

import agent_tools as t


# ── lookalike_check ─────────────────────────────────────────
@pytest.mark.parametrize('domain', [
    'paypa1.com', 'rnicrosoft.com', 'cathaybk-tw.top', 'goggle.com',
    'paypal.secure-login.top', 'paypal.com.evil.top', 'paypal.top',
])
def test_lookalike_flags(domain):
    r = t.lookalike_check(domain)
    assert r['signals'] == ['lookalike_domain'], domain


@pytest.mark.parametrize('domain', [
    'paypal.com', 'www.paypal.com', 'mail.google.com', 'esunbank.com.tw',
    'applepie.com', 'example.com', 'news.cathaybk.com.tw',
])
def test_lookalike_clean(domain):
    assert t.lookalike_check(domain)['signals'] == [], domain


# ── check_auth_headers ──────────────────────────────────────
def test_auth_fail_and_reply_to_mismatch():
    r = t.check_auth_headers({
        'From': 'Bank <service@bank.com>',
        'Reply-To': 'help@evil.top',
        'Authentication-Results': 'mx.google.com; dkim=pass header.i=@bank.com; spf=fail; dmarc=fail (p=NONE)',
    })
    assert set(r['signals']) == {'dmarc_fail', 'spf_fail', 'reply_to_mismatch'}
    assert r['dkim'] == 'pass'


def test_auth_all_pass_has_no_signals():
    r = t.check_auth_headers({'From': 'a@x.com', 'Authentication-Results': 'spf=pass; dkim=pass; dmarc=pass'})
    assert r['signals'] == []


def test_auth_unavailable_is_not_a_signal():
    assert t.check_auth_headers({})['signals'] == []
    assert t.check_auth_headers({})['status'] == 'unavailable'


# ── SSRF 防護 ───────────────────────────────────────────────
@pytest.mark.parametrize('url', [
    'http://127.0.0.1/', 'http://10.0.0.5/x', 'http://169.254.169.254/latest/meta-data',
    'http://192.168.1.1/', 'http://[::1]/', 'http://localhost/', 'ftp://example.com/',
    'http://example.com:8080/', 'http://user:pw@example.com/', 'file:///etc/passwd',
])
def test_expand_url_blocks_unsafe_targets(url):
    with mock.patch('agent_tools.requests.head') as head, mock.patch('agent_tools.requests.get') as get:
        r = t.expand_url(url)
    assert r['blocked'] is True
    head.assert_not_called()
    get.assert_not_called()


def test_hostname_resolving_to_private_ip_is_blocked():
    fake = [(socket.AF_INET, 0, 0, '', ('10.1.2.3', 0))]
    with mock.patch('agent_tools.socket.getaddrinfo', return_value=fake), \
         mock.patch('agent_tools.requests.head') as head:
        r = t.expand_url('http://innocent-looking.example/')
    assert r['blocked'] is True
    head.assert_not_called()


def test_redirect_to_private_ip_is_blocked_mid_chain():
    public = [(socket.AF_INET, 0, 0, '', ('93.184.216.34', 0))]
    resp = mock.Mock(status_code=302, headers={'Location': 'http://169.254.169.254/'})
    with mock.patch('agent_tools.socket.getaddrinfo', return_value=public), \
         mock.patch('agent_tools.requests.head', return_value=resp):
        r = t.expand_url('http://bit.ly/abc')
    assert r['blocked'] is True
    assert r['hops'] == 1


def test_expand_url_follows_redirects_and_flags_cross_domain():
    public = [(socket.AF_INET, 0, 0, '', ('93.184.216.34', 0))]
    seq = [
        mock.Mock(status_code=301, headers={'Location': 'https://a.example.net/p'}),
        mock.Mock(status_code=302, headers={'Location': '/login'}),
        mock.Mock(status_code=302, headers={'Location': 'https://secure-login.top/x'}),
        mock.Mock(status_code=200, headers={}),
    ]
    with mock.patch('agent_tools.socket.getaddrinfo', return_value=public), \
         mock.patch('agent_tools.requests.head', side_effect=seq):
        r = t.expand_url('http://short.example/abc')
    assert r['final_host'] == 'secure-login.top'
    assert r['hops'] == 3
    assert set(r['signals']) == {'redirect_cross_domain', 'redirect_many'}


def test_redirect_loop_is_capped():
    public = [(socket.AF_INET, 0, 0, '', ('93.184.216.34', 0))]
    loop = mock.Mock(status_code=302, headers={'Location': 'http://loop.example/'})
    with mock.patch('agent_tools.socket.getaddrinfo', return_value=public), \
         mock.patch('agent_tools.requests.head', return_value=loop):
        r = t.expand_url('http://loop.example/')
    assert r['error'] == '跳轉次數超過上限'


# ── domain_age / dns_lookup ─────────────────────────────────
def _rdap(days):
    from datetime import datetime, timedelta, timezone
    d = (datetime.now(timezone.utc) - timedelta(days=days)).strftime('%Y-%m-%dT%H:%M:%SZ')
    return mock.Mock(status_code=200, json=lambda: {'events': [{'eventAction': 'registration', 'eventDate': d}]})


def test_domain_age_signals():
    with mock.patch('agent_tools.requests.get', return_value=_rdap(2)):
        assert t.domain_age('evil.top')['signals'] == ['domain_age_lt7']
    with mock.patch('agent_tools.requests.get', return_value=_rdap(20)):
        assert t.domain_age('evil.top')['signals'] == ['domain_age_lt30']
    with mock.patch('agent_tools.requests.get', return_value=_rdap(4000)):
        assert t.domain_age('old.com')['signals'] == []


def test_domain_age_unknown_is_not_a_signal():
    with mock.patch('agent_tools.requests.get', return_value=mock.Mock(status_code=404)):
        r = t.domain_age('whatever.tw')
    assert r['status'] == 'unknown' and r['signals'] == []
    import requests
    with mock.patch('agent_tools.requests.get', side_effect=requests.Timeout):
        assert t.domain_age('x.com')['signals'] == []


def test_dns_lookup():
    err = socket.gaierror(socket.EAI_NONAME, 'nx')
    with mock.patch('agent_tools.socket.getaddrinfo', side_effect=err):
        assert t.dns_lookup('nope.example')['signals'] == ['no_dns']
    err2 = socket.gaierror(socket.EAI_AGAIN, 'timeout')
    with mock.patch('agent_tools.socket.getaddrinfo', side_effect=err2):
        assert t.dns_lookup('slow.example')['signals'] == []
