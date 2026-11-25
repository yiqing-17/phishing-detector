import analysis

LURE = 'URL 含有登入或驗證誘導字樣'


def test_official_account_endpoint_is_not_flagged_as_a_lure():
    assert LURE not in analysis.analyze_url('https://accounts.google.com/accountchooser')
    assert LURE not in analysis.analyze_url('https://myaccount.google.com/notifications')


def test_official_exemption_is_exact_host_and_https_only():
    assert LURE in analysis.analyze_url('https://accounts.google.com.evil.top/login')
    assert LURE in analysis.analyze_url('https://evilaccounts.google.com.example.com/account')
    assert LURE in analysis.analyze_url('http://accounts.google.com/login')   # 非 https 不豁免


def test_lure_words_on_ordinary_hosts_are_still_flagged():
    assert LURE in analysis.analyze_url('https://secure-login-bank.top/verify')
    assert LURE in analysis.analyze_url('https://example.com/account/update')


def test_same_url_finding_repeated_across_links_counts_once():
    one = 'Visit https://shop.example.com/account/a now'
    many = ' '.join(f'https://shop.example.com/account/{c}' for c in 'abcde')
    s1, _ = analysis.rule_based_score(one)
    s5, _ = analysis.rule_based_score('Visit ' + many + ' now')
    # 只允許「連結數量」的基礎分增加（3+n，上限 8），不再每個連結重複加 URL 風險分
    assert s5 - s1 <= 4
