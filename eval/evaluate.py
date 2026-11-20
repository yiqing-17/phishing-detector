"""中文測試集評估（純離線、不呼叫 Groq/網路，因此「不含 Agent」）。
用法：python eval/evaluate.py [dev|test|all]
比較：規則-only / ML-only / 修正前融合(規則+ML) / 修正後融合(ML 不適用則移除)。
注意：文字模式沒有 HTML，html 分數固定 0。"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import analysis

def load(split):
    p = os.path.join(os.path.dirname(__file__), 'dataset_zh_hard.jsonl' if split == 'hard' else 'dataset_zh.jsonl')
    rows = [json.loads(l) for l in open(p, encoding='utf-8')]
    return [r for r in rows if split == 'all' or r['split'] == split]

def raw_ml(text):
    X = analysis.vectorizer.transform([text]); m = analysis.model
    return float(m.predict_proba(X)[0][list(m.classes_).index(1)])

def scores(r):
    rs, _ = analysis.rule_based_score(r['text'])
    p = raw_ml(r['text'])
    ok = analysis.ml_reliability(r['text'])[0]
    return {
        'rules_only': min(rs * 5, 100),
        'ml_only': p * 100,
        'fusion_before_fix': analysis.calculate_risk_score(rs, p, 0, None),
        'fusion_after_fix': analysis.calculate_risk_score(rs, p if ok else None, 0, None),
    }

def metrics(y, s, thr):
    tp = sum(1 for a, b in zip(y, s) if a == 1 and b >= thr); fn = sum(1 for a, b in zip(y, s) if a == 1 and b < thr)
    fp = sum(1 for a, b in zip(y, s) if a == 0 and b >= thr); tn = sum(1 for a, b in zip(y, s) if a == 0 and b < thr)
    pr = tp / (tp + fp) if tp + fp else 0.0; rc = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * pr * rc / (pr + rc) if pr + rc else 0.0
    return dict(TP=tp, FN=fn, FP=fp, TN=tn, precision=pr, recall=rc, F1=f1, FPR=fp / (fp + tn) if fp + tn else 0.0)

def run(split='all', verbose=True):
    rows = load(split); y = [r['label'] for r in rows]
    sc = [scores(r) for r in rows]
    out = {}
    for k in sc[0]:
        out[k] = metrics(y, [s[k] for s in sc], 40)
    if verbose:
        print(f"\n== split={split}  n={len(rows)}  (釣魚 {sum(y)} / 正常 {len(y)-sum(y)})  門檻=40（中風險以上視為偵測）==")
        print(f"{'設定':<20}{'TP':>4}{'FN':>4}{'FP':>4}{'TN':>4}{'Prec':>7}{'Recall':>8}{'F1':>7}{'FPR':>7}")
        for k, m in out.items():
            print(f"{k:<20}{m['TP']:>4}{m['FN']:>4}{m['FP']:>4}{m['TN']:>4}{m['precision']:>7.2f}{m['recall']:>8.2f}{m['F1']:>7.2f}{m['FPR']:>7.2f}")
    return out, rows, sc

if __name__ == '__main__':
    split = sys.argv[1] if len(sys.argv) > 1 else 'dev'
    out, rows, sc = run(split)
    if '--errors' in sys.argv:
        for r, s in zip(rows, sc):
            v = s['fusion_after_fix']
            if (r['label'] == 1 and v < 40) or (r['label'] == 0 and v >= 40):
                print(('漏 ' if r['label'] else '誤 '), r['id'], r['category'], v, r['subject'])
