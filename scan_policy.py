"""Email scanning policy shared by Gmail and paste submissions."""


def analyze_email(
    *,
    sender,
    subject,
    body,
    text,
    html,
    uid,
    whitelist_match,
    full_pipeline,
    build_entry,
):
    """Always analyze a message; a whitelist match is explanatory context only."""
    domain, matched_domain, match_method = whitelist_match(sender, uid)
    report, html_score, _, rule_score, spam_prob = full_pipeline(text, html)
    entry = build_entry(
        sender, subject, body, report, html_score, rule_score, spam_prob
    )

    if matched_domain:
        findings = list(entry.get("explainable_findings") or [])
        findings.insert(0, {
            "source": "白名單",
            "severity": "low",
            "title": "白名單提示",
            "detail": (
                f"寄件網域 {domain} 命中白名單「{matched_domain}」（{match_method}）。"
                "白名單只表示網域比對命中，不能驗證寄件者真實身分；"
                "此郵件仍完成四層分析。"
            ),
        })
        entry["explainable_findings"] = findings

    return entry

