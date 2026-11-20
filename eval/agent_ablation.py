"""Agent 消融實驗：同一批信件，比較「不含 Agent」與「含 Agent」的偵測結果、成本與延遲。

用法
  真實實驗（需要網路 + GROQ_API_KEY；工具會真的查 RDAP / DNS / 跳轉）：
      export GROQ_API_KEY=...
      python eval/agent_ablation.py --split test --live
      python eval/agent_ablation.py --split all  --live --trigger 20     # 掃描觸發門檻
  離線流程驗證（假模型，數字沒有科學意義，只確認腳本可跑）：
      python eval/agent_ablation.py --split test --offline

輸出：終端表格 + eval/ablation_<split>_<mode>.json（逐封結果，供畫圖與錯誤分析）。

解讀時請一併檢查（腳本會印出）：
  * 觸發率：Agent 只在預估分數 >= trigger 才啟動，沒觸發的信件 Agent 不可能改變結果。
  * 只有加分、沒有扣分：Agent 只能 FN→TP 或 TN→FP，不會修正誤報。
  * 文字模式沒有信件標頭 → check_auth_headers 一律 unavailable，SPF/DKIM/DMARC 訊號不會出現。
  * 資料集的釣魚網域若是虛構的，no_dns 會對每一封都觸發（見 --by-signal），不能算真實偵測力。
"""
import argparse
import json
import math
import os
import statistics
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.dirname(__file__))
import analysis  # noqa: E402
from evaluate import load, metrics  # noqa: E402

THRESHOLD = 40


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - h) / d, (c + h) / d)


def mcnemar_exact(b, c):
    """b、c = 兩種設定「一對一錯」的不一致配對數。回傳雙尾精確 p 值。"""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    p = sum(math.comb(n, i) for i in range(0, k + 1)) / 2 ** n
    return min(1.0, 2 * p)


class CountingClient:
    """包住真實 / 假 client，統計 API 呼叫次數與 token。"""

    def __init__(self, inner):
        self.inner = inner
        self.calls = self.pt = self.ct = 0
        self.chat = type('C', (), {})()
        self.chat.completions = type('D', (), {'create': self._create})()

    def _create(self, **kw):
        self.calls += 1
        r = self.inner.chat.completions.create(**kw)
        u = getattr(r, 'usage', None)
        if u is not None:
            self.pt += getattr(u, 'prompt_tokens', 0) or 0
            self.ct += getattr(u, 'completion_tokens', 0) or 0
        return r

    def reset(self):
        self.calls = self.pt = self.ct = 0


def make_client(live):
    if live:
        key = os.environ.get('GROQ_API_KEY')
        if not key:
            sys.exit('--live 需要環境變數 GROQ_API_KEY')
        from groq import Groq
        return CountingClient(Groq(api_key=key))
    from fake_llm import ScriptedClient
    return CountingClient(ScriptedClient('benign'))


def run_one(row, client):
    """回傳 (baseline_score, agent_score, meta)。"""
    sender = row.get('from', '')
    analysis.groq_client = None
    base = analysis.full_pipeline(row['text'], sender=sender)[0]['risk_score']
    analysis.groq_client = client
    client.reset()
    t0 = time.monotonic()
    rep = analysis.full_pipeline(row['text'], sender=sender)[0]
    wall = time.monotonic() - t0
    meta = rep['agent_meta']
    return base, rep['risk_score'], {
        'triggered': meta['triggered'], 'status': meta['status'], 'error': meta['error'],
        'signals': meta['signals'], 'pre_score': meta['pre_score'],
        'tools': [s['tool'] for s in rep['agent_trace']],
        'wall_s': round(wall, 2), 'api_calls': client.calls,
        'prompt_tokens': client.pt, 'completion_tokens': client.ct,
    }


def fmt(m):
    lo, hi = wilson(m['TP'], m['TP'] + m['FN'])
    return (f"TP{m['TP']:>3} FN{m['FN']:>3} FP{m['FP']:>3} TN{m['TN']:>3}  "
            f"P={m['precision']:.2f} R={m['recall']:.2f}(95%CI {lo:.2f}-{hi:.2f}) "
            f"F1={m['F1']:.2f} FPR={m['FPR']:.2f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--split', default='test')
    ap.add_argument('--live', action='store_true')
    ap.add_argument('--offline', action='store_true')
    ap.add_argument('--trigger', type=int, default=None, help='覆寫 Agent 觸發門檻（預設 analysis.AGENT_TRIGGER_SCORE）')
    ap.add_argument('--limit', type=int, default=0)
    ap.add_argument('--dataset', default=None, help='改用其他 jsonl（需有 label/text/from）')
    a = ap.parse_args()
    if a.live == a.offline:
        sys.exit('請擇一：--live 或 --offline')
    if a.trigger is not None:
        analysis.AGENT_TRIGGER_SCORE = a.trigger

    if a.dataset:
        rows = [json.loads(l) for l in open(a.dataset, encoding='utf-8')]
        rows = [r for r in rows if a.split == 'all' or r.get('split') == a.split]
    else:
        rows = load(a.split)
    if a.limit:
        rows = rows[:a.limit]
    client = make_client(a.live)
    mode = 'live' if a.live else 'offline'

    res = []
    for i, r in enumerate(rows, 1):
        b, s, meta = run_one(r, client)
        res.append({'id': r['id'], 'label': r['label'], 'category': r.get('category'),
                    'base': b, 'agent': s, **meta})
        print(f'\r[{i}/{len(rows)}]', end='', file=sys.stderr)
    print(file=sys.stderr)

    y = [r['label'] for r in res]
    mb = metrics(y, [r['base'] for r in res], THRESHOLD)
    ma = metrics(y, [r['agent'] for r in res], THRESHOLD)
    print(f"\n== Agent 消融  split={a.split}  n={len(res)}  mode={mode}  trigger={analysis.AGENT_TRIGGER_SCORE}  門檻={THRESHOLD} ==")
    if mode == 'offline':
        print('!! 離線假模型：以下只驗證流程，不是 Agent 的真實效果 !!')
    print('不含 Agent :', fmt(mb))
    print('含   Agent :', fmt(ma))

    ok_b = [(r['base'] >= THRESHOLD) == (r['label'] == 1) for r in res]
    ok_a = [(r['agent'] >= THRESHOLD) == (r['label'] == 1) for r in res]
    fixed = sum(1 for x, z in zip(ok_b, ok_a) if not x and z)
    broke = sum(1 for x, z in zip(ok_b, ok_a) if x and not z)
    print(f'逐封比較：Agent 改對 {fixed} 封、改錯 {broke} 封；McNemar 精確檢定 p = {mcnemar_exact(fixed, broke):.3f}')

    trig = [r for r in res if r['triggered']]
    print(f"觸發率：{len(trig)}/{len(res)}（{len(trig)/max(1,len(res)):.0%}）；"
          f"狀態分佈：{ {s: sum(1 for r in trig if r['status']==s) for s in {r['status'] for r in trig}} }")
    missed_untriggered = [r['id'] for r in res if r['label'] == 1 and r['base'] < THRESHOLD and not r['triggered']]
    print(f'未達觸發門檻、Agent 根本沒機會處理的漏報：{len(missed_untriggered)} 封 {missed_untriggered}')
    if trig:
        lat = [r['wall_s'] for r in trig]
        print(f"延遲（觸發的信件）：平均 {statistics.mean(lat):.1f}s、中位 {statistics.median(lat):.1f}s、最大 {max(lat):.1f}s")
        print(f"每封 API 呼叫 {statistics.mean(r['api_calls'] for r in trig):.1f} 次、"
              f"工具 {statistics.mean(len(r['tools']) for r in trig):.1f} 個；"
              f"token 合計 prompt {sum(r['prompt_tokens'] for r in trig)} / completion {sum(r['completion_tokens'] for r in trig)}")
        sig = {}
        for r in trig:
            for s in r['signals']:
                sig.setdefault(s, {0: 0, 1: 0})[r['label']] += 1
        if sig:
            print('訊號 × 標籤（正常/釣魚）：', {k: f'{v[0]}/{v[1]}' for k, v in sorted(sig.items())})
            if 'no_dns' in sig and sig['no_dns'][1] >= 0.8 * max(1, sum(1 for r in trig if r['label'] == 1)):
                print('⚠ no_dns 幾乎在每封釣魚信都出現：資料集的網域可能是虛構的，這不是真實偵測力。')

    out = os.path.join(os.path.dirname(__file__), f'ablation_{a.split}_{mode}.json')
    json.dump({'split': a.split, 'mode': mode, 'trigger': analysis.AGENT_TRIGGER_SCORE,
               'baseline': mb, 'agent': ma, 'rows': res}, open(out, 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print('逐封結果 →', out)


if __name__ == '__main__':
    main()
