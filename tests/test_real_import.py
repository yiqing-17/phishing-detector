import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'eval'))

import analysis
import import_mailbox as im
import url_eval


def test_deidentify_removes_personal_data_but_keeps_detection_features():
    src = ('王小明您好，請至 https://evil.top/pay?uid=SECRETTOKEN 補繳；客服 0912-345-678，身分證 A123456789，'
           '卡號 4111 1111 1111 1111，來信 me@gmail.com，朋友 bob@yahoo.com，寄件 scam@evil.top')
    out, n = im.deidentify(src, names=['王小明'], my_emails=['me@gmail.com'], keep_addrs=['scam@evil.top'])
    for secret in ('王小明', 'SECRETTOKEN', '345-678', 'A123456789', '4111', 'me@gmail.com', 'bob@'):
        assert secret not in out, secret
    assert 'https://evil.top/pay' in out          # 網域與路徑保留（偵測特徵）
    assert 'scam@evil.top' in out                 # 寄件者位址保留
    assert n['recipient'] >= 2 and n['id'] == 1 and n['card'] == 1


def test_long_url_path_tokens_are_masked():
    out, _ = im.deidentify('https://a.example/' + 'x' * 40 + '/ok', [], [], [])
    assert 'x' * 40 not in out and out.endswith('/ok')


def test_url_carriers_contain_no_scam_wording():
    for c in url_eval.CARRIERS:
        score, found = analysis.rule_based_score(c.format(u='https://www.google.com/'))
        assert not any('詐騙話術' in f for f in found), (c, found)


def test_read_domains_handles_165_style_csv(tmp_path):
    p = tmp_path / 's.csv'
    p.write_text('民國年月,網域,網站性質\n115/01,Evil-One.TOP,假投資\n115/01,https://two.example.com/x,假冒\n115/02,Evil-One.top,假投資\n115/02,not a domain,x\n',
                 encoding='utf-8')
    assert url_eval.read_domains(str(p)) == ['evil-one.top', 'two.example.com']
