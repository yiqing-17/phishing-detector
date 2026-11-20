from ratelimit import RateLimiter, client_ip


def test_limit_and_window_reset():
    r = RateLimiter()
    assert all(r.allow('k', 3, 60, now=100)[0] for _ in range(3))
    ok, wait = r.allow('k', 3, 60, now=101)
    assert ok is False and 1 <= wait <= 60
    assert r.allow('k', 3, 60, now=161)[0] is True      # 視窗過後恢復
    assert r.allow('other', 3, 60, now=101)[0] is True   # 不同 key 互不影響


def test_client_ip_uses_rightmost_forwarded():
    assert client_ip('10.0.0.1', '6.6.6.6, 1.2.3.4') == '1.2.3.4'   # 最左邊可被偽造
    assert client_ip('10.0.0.1', '') == '10.0.0.1'
    assert client_ip(None, '') == 'unknown'


def test_paste_endpoint_is_limited(monkeypatch):
    import flask_app
    monkeypatch.setitem(flask_app.RATE_LIMITS, 'paste', (2, 3600))
    flask_app._limiter = RateLimiter()
    c = flask_app.app.test_client()
    codes = [c.post('/paste_analyze', data={'body': ''}).status_code for _ in range(3)]
    assert codes[:2] != [429, 429] and codes[2] == 429
