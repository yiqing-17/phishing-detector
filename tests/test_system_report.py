"""is_system_report：不可被主旨關鍵字或空的 MY_EMAIL 繞過。"""
import pytest
import storage


@pytest.fixture
def me(monkeypatch):
    monkeypatch.setattr(storage, 'MY_EMAIL', 'me@gmail.com')


def test_genuine_self_sent_report_is_skipped(me):
    assert storage.is_system_report('Me <me@gmail.com>', '[警告] 偵測到釣魚信件', ['SENT', 'INBOX']) is True


def test_attacker_subject_marker_does_not_bypass(me):
    assert storage.is_system_report('evil@phish.example', '[正常] 您的帳戶已被暫停', ['INBOX']) is False
    assert storage.is_system_report('evil@phish.example', 'AI 釣魚偵測報告', ['INBOX']) is False


def test_spoofed_from_without_sent_label_is_analyzed(me):
    assert storage.is_system_report('me@gmail.com', '[警告] 請立即點擊', ['INBOX']) is False


def test_lookalike_address_is_not_confused_with_me(me):
    assert storage.is_system_report('x@evil.com <me@gmail.com.evil.com>', '[警告] x', ['SENT']) is False
    assert storage.is_system_report('"me@gmail.com" <evil@x.com>', '[警告] x', ['SENT']) is False


def test_empty_my_email_never_skips(monkeypatch):
    monkeypatch.setattr(storage, 'MY_EMAIL', '')
    assert storage.is_system_report('anyone@x.com', '警告：偵測到釣魚', ['SENT']) is False
    assert storage.is_system_report('', '[正常]', ['SENT']) is False


def test_sent_by_me_but_unrelated_subject_is_analyzed(me):
    assert storage.is_system_report('me@gmail.com', '週末聚餐', ['SENT']) is False
