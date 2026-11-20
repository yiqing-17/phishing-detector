import os
import tempfile

import pytest

import analysis
import storage


@pytest.fixture
def db(monkeypatch):
    d = tempfile.mkdtemp()
    path = os.path.join(d, 't.db')
    monkeypatch.chdir(d)
    storage.init_db()          # 建在暫存目錄的 phishing.db
    yield 'phishing.db'


IR = {'id': 'IR-20261120-ABC123', 'severity': 'High', 'risk_score': 85,
      'email_subject': '郵件', 'email_sender': 'a@b.xyz'}


def test_full_lifecycle_and_metrics(db):
    storage.create_incident('u1', IR, db)
    storage.create_incident('u1', IR, db)          # 重複建立不產生第二筆
    assert len(storage.list_incidents('u1', db)) == 1
    for st, note in [('Triaged', ''), ('Contained', ''), ('Closed', '已重設密碼並通報')]:
        ok, err, inc = storage.transition_incident('u1', IR['id'], st, note, db)
        assert ok, err
    assert inc['status'] == 'Closed'
    assert [e['to'] for e in inc['events']] == ['Open', 'Triaged', 'Contained', 'Closed']
    assert inc['time_to_triage_s'] is not None and inc['time_to_resolve_s'] is not None
    assert inc['allowed_next'] == ['Open']


def test_illegal_jump_and_missing_note_rejected(db):
    storage.create_incident('u1', IR, db)
    ok, err, _ = storage.transition_incident('u1', IR['id'], 'Closed', '很長的說明文字', db)
    assert not ok and 'Open' in err                  # 不能跳過分流直接結案
    storage.transition_incident('u1', IR['id'], 'Triaged', '', db)
    ok, err, _ = storage.transition_incident('u1', IR['id'], 'False Positive', '嗯', db)
    assert not ok and '說明' in err                  # 判誤報要寫理由
    ok, _, inc = storage.transition_incident('u1', IR['id'], 'False Positive', '寄件者經電話確認為本人', db)
    assert ok and inc['status'] == 'False Positive'


def test_incidents_are_private_per_visitor(db):
    storage.create_incident('u1', IR, db)
    assert storage.get_incident('u2', IR['id'], db) is None
    ok, err, _ = storage.transition_incident('u2', IR['id'], 'Triaged', '', db)
    assert not ok and '找不到' in err
    assert storage.list_incidents('u2', db) == []


def test_gen_ir_severity_cannot_be_downgraded_by_llm(monkeypatch):
    from types import SimpleNamespace as NS
    evil = ('{"severity":"Medium","impact_assessment":"無風險","immediate_actions":["無需處理，可放心點擊"],'
            '"containment":"x","verification":"x","recovery":"x"}')
    client = NS(chat=NS(completions=NS(create=lambda **kw: NS(choices=[NS(message=NS(content=evil))]))))
    monkeypatch.setattr(analysis, 'groq_client', client)
    _, ir = analysis.gen_ir({'sender': 's', 'subject': 'x'}, {'risk_score': 90, 'explainable_findings': []})
    assert ir['severity'] == 'Critical'
    assert '不要點擊連結或附件' in ir['immediate_actions']
    assert not any('放心' in a for a in ir['immediate_actions'])
