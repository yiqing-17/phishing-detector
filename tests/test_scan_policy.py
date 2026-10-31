import unittest

from scan_policy import analyze_email


class AnalyzeEmailTests(unittest.TestCase):
    def setUp(self):
        self.calls = []

    def pipeline(self, text, html):
        self.calls.append((text, html))
        return (
            {"risk_level": "high", "risk_score": 91},
            4,
            None,
            27,
            0.83,
        )

    @staticmethod
    def build_entry(sender, subject, body, report, html_score, rule_score, spam_prob):
        return {
            "level": report["risk_level"],
            "risk_score": report["risk_score"],
            "explainable_findings": [],
        }

    @staticmethod
    def whitelist_match(sender, uid):
        return "accounts.google.com", "google.com", "子網域比對"

    def test_whitelisted_sender_still_runs_analysis_and_keeps_its_risk(self):
        entry = analyze_email(
            sender="Support <help@accounts.google.com>",
            subject="Urgent account check",
            body="Enter your password now",
            text="From: help@accounts.google.com",
            html="<form>",
            uid="visitor",
            whitelist_match=self.whitelist_match,
            full_pipeline=self.pipeline,
            build_entry=self.build_entry,
        )

        self.assertEqual(len(self.calls), 1)
        self.assertEqual(entry["level"], "high")
        self.assertEqual(entry["risk_score"], 91)
        self.assertEqual(entry["explainable_findings"][0]["title"], "白名單提示")
        self.assertIn("仍完成四層分析", entry["explainable_findings"][0]["detail"])

    def test_unmatched_sender_gets_no_whitelist_finding(self):
        entry = analyze_email(
            sender="sender@example.net",
            subject="Notice",
            body="hello",
            text="mail",
            html="",
            uid="visitor",
            whitelist_match=lambda sender, uid: ("example.net", "", ""),
            full_pipeline=self.pipeline,
            build_entry=self.build_entry,
        )

        self.assertEqual(len(self.calls), 1)
        self.assertEqual(entry["explainable_findings"], [])


if __name__ == "__main__":
    unittest.main()

