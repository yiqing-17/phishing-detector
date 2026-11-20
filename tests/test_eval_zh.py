"""中文評估集的回歸護欄 + 規則誤報修正測試（離線）。"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'eval'))
import analysis
import evaluate


def test_zh_eval_floor_after_fix():
    out, _, _ = evaluate.run('all', verbose=False)
    m = out['fusion_after_fix']
    assert m['FPR'] <= 0.10, m
    assert m['recall'] >= 0.80, m
    # 修正後的誤報率必須明顯低於修正前（ML 不可靠時的假訊號）
    assert m['FPR'] < out['fusion_before_fix']['FPR']


def test_weak_words_alone_do_not_score():
    assert analysis.rule_based_score('您的付款已完成，信用卡扣款 NT$149，帳號資料如附件。')[0] == 0
    assert analysis.rule_based_score('Thanks for your payment of $20. Your invoice is attached.')[0] == 0


def test_disclaimer_is_not_treated_as_asking_for_password():
    assert analysis.rule_based_score('本行不會以電子郵件要求您提供密碼或 OTP。')[0] == 0


def test_weak_words_count_when_corroborated():
    s, _ = analysis.rule_based_score('請立即提供您的密碼與信用卡')
    assert s >= 8


def test_zh_scam_words_detected():
    s, why = analysis.rule_based_score('您涉及洗錢，請勿告知他人，並將存款轉至監管帳戶。')
    assert s >= 9 and any('詐騙話術' in w for w in why)
