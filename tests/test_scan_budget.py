import time
from types import SimpleNamespace as NS

import agent
import analysis

PHISH = ('From: a@evil-bank.top\nSubject: 帳戶異常\nBody: 您的帳戶異常，請立即至 https://evil-bank.top/login '
         '驗證身分並輸入密碼，否則帳戶將被凍結，限時24小時。')


class Recorder:
    """有 with_options 的假 client：記錄每次被要求的逾時與重試設定。"""
    def __init__(self):
        self.opts, self.calls = [], 0
        self.chat = NS(completions=NS(create=self._create))

    def with_options(self, **kw):
        self.opts.append(kw)
        return self

    def _create(self, **kw):
        self.calls += 1
        content = '{"category":"釣魚信件","suspicious_points":[],"explanation":"x","recommended_action":"x"}'
        return NS(choices=[NS(message=NS(content=content, tool_calls=None))])


def test_llm_calls_get_hard_timeout_and_no_retries():
    rec = Recorder()
    agent.run_investigation(rec, PHISH, ['https://evil-bank.top/login'])
    assert rec.opts and all(o['max_retries'] == 0 for o in rec.opts)
    assert all(1.0 <= o['timeout'] <= agent.LLM_CALL_TIMEOUT for o in rec.opts)


def test_timed_client_falls_back_for_clients_without_with_options():
    plain = NS(chat=None)
    assert agent.timed_client(plain, 5) is plain


def test_use_agent_false_makes_no_llm_call_and_records_reason(monkeypatch):
    rec = Recorder()
    monkeypatch.setattr(analysis, 'groq_client', rec)
    rep = analysis.full_pipeline(PHISH, sender='a@evil-bank.top', use_agent=False)[0]
    assert rec.calls == 0
    assert rep['agent_meta']['triggered'] is False
    assert rep['agent_meta']['skipped_reason'] == 'scan_budget'
    assert rep['risk_score'] >= 40            # 靜態分析照常運作，只是少了 Agent


def test_gen_ir_use_llm_false_skips_llm_and_keeps_severity(monkeypatch):
    rec = Recorder()
    monkeypatch.setattr(analysis, 'groq_client', rec)
    _, ir = analysis.gen_ir({'sender': 's', 'subject': 'x'}, {'risk_score': 90, 'explainable_findings': []}, use_llm=False)
    assert rec.calls == 0 and ir['severity'] == 'Critical'
    assert '不要點擊連結或附件' in ir['immediate_actions']


def test_tools_are_skipped_once_total_budget_is_spent(monkeypatch):
    """一輪裡有多個工具時，超過總預算就不再發出新的網路請求。"""
    ran = []
    monkeypatch.setattr(agent, '_dispatch', lambda name, args, ctx: (ran.append(name), {'signals': []})[1])

    class Slow:
        def __init__(self):
            self.n = 0
            self.chat = NS(completions=NS(create=self._c))

        def _c(self, **kw):
            self.n += 1
            if self.n == 1:
                time.sleep(0.3)           # 第一次呼叫就用掉整個預算
                calls = [NS(id=str(i), function=NS(name='dns_lookup', arguments='{"domain":"d%d.top"}' % i)) for i in range(3)]
                return NS(choices=[NS(message=NS(content='', tool_calls=calls))])
            return NS(choices=[NS(message=NS(content='{"category":"x","explanation":"x","recommended_action":"x","suspicious_points":[]}', tool_calls=None))])

    res = agent.run_investigation(Slow(), PHISH, ['https://d0.top', 'https://d1.top', 'https://d2.top'], timeout_s=0.1)
    assert ran == []                       # 預算已耗盡 → 三個工具都沒真的執行
    assert '逾時' in res['error']
