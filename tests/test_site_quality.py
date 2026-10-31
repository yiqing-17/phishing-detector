import unittest

from site_quality import (
    add_home_privacy_note,
    apply_model_metrics,
    correct_legacy_copy,
    inject_locale_assets,
    resolve_language,
)


class SiteQualityTests(unittest.TestCase):
    def test_language_query_overrides_saved_preference(self):
        self.assertEqual(resolve_language("en", "zh"), "en")

    def test_locale_assets_are_injected_after_page_styles(self):
        page = '<meta charset="utf-8"><style>base</style><main>page</main>'

        updated = inject_locale_assets(page, "en")

        self.assertIn('document.documentElement.lang="en"', updated)
        self.assertIn('/static/site.css', updated)
        self.assertIn('/static/i18n.js', updated)
        self.assertGreater(updated.index('/static/i18n.js'), updated.index('</style>'))

    def test_locale_asset_injection_falls_back_to_traditional_chinese(self):
        updated = inject_locale_assets('<meta charset="utf-8">', "fr")

        self.assertIn('document.documentElement.lang="zh"', updated)

    def test_legacy_allowlist_copy_is_corrected_even_without_javascript(self):
        page = "已知安全網域自動略過重複分析。加入白名單後，來自該網域及其子網域的信件將直接標記為安全，不進行 AI 分析。請只加入確定可信任的網域。"
        updated = correct_legacy_copy(page)

        self.assertNotIn("直接標記為安全", updated)
        self.assertIn("所有郵件仍會完成四層分析", updated)
        self.assertIn("不會略過分析或保證郵件安全", updated)

    def test_rules_playground_textarea_gets_an_accessible_name(self):
        updated = inject_locale_assets('<textarea id="pt">sample</textarea>', "zh")

        self.assertIn('<textarea id="pt" aria-label="輸入文字">', updated)

    def test_home_privacy_note_is_localized_and_says_what_is_stored(self):
        page = '<div class="cta"><a>Analyze</a></div><div class="docwrap">'

        english = add_home_privacy_note(page, "en")
        chinese = add_home_privacy_note(page, "zh")

        self.assertIn("Read-only access", english)
        self.assertIn("scan history stores counts only", english)
        self.assertIn("Gmail 僅讀取最近 15 封郵件", chinese)
        self.assertEqual(english.count('class="trust-note"'), 1)

    def test_home_privacy_note_does_not_change_other_pages(self):
        page = '<main>not the home page</main>'
        self.assertEqual(add_home_privacy_note(page, "en"), page)

    def test_invalid_language_uses_saved_preference_or_traditional_chinese(self):
        self.assertEqual(resolve_language("fr", "en"), "en")
        self.assertEqual(resolve_language("fr", "fr"), "zh")

    def test_home_metrics_are_rendered_from_model_report(self):
        html = (
            '<div class="mt-ds">資料集　Phishing Email Dataset，清理後 82,077 筆'
            '（訓練 65,661 / 測試 16,416）</div>'
            '<span class="cu" data-to="98.41">98.41</span>'
            '<span class="cu" data-to="98.28">98.28</span>'
            '<span class="cu" data-to="98.68">98.68</span>'
            '<span class="cu" data-to="98.48">98.48</span>'
        )
        metrics = {
            "dataset": "Phishing Email Dataset",
            "dataset_rows_after_cleaning": 100,
            "train_rows": 80,
            "test_rows": 20,
            "accuracy": 0.90,
            "precision": 0.91,
            "recall": 0.92,
            "f1": 0.915,
        }

        updated = apply_model_metrics(html, metrics)

        self.assertIn("清理後 100 筆（訓練 80 / 測試 20）", updated)
        self.assertIn('data-to="90.00">90.00', updated)
        self.assertIn('data-to="91.50">91.50', updated)

    def test_home_metrics_are_not_claimed_when_report_is_missing(self):
        html = '<div class="mt4 bigstats">metrics</div>'

        updated = apply_model_metrics(html, {})

        self.assertNotIn('class="mt4 bigstats"', updated)
        self.assertIn("模型測試數據尚未提供", updated)

    def test_home_metrics_are_hidden_when_dataset_counts_do_not_reconcile(self):
        metrics = {
            "dataset": "Dataset",
            "dataset_rows_after_cleaning": 100,
            "train_rows": 79,
            "test_rows": 20,
            "accuracy": 0.90,
            "precision": 0.91,
            "recall": 0.92,
            "f1": 0.915,
        }
        updated = apply_model_metrics('<div class="mt4 bigstats">metrics</div>', metrics)

        self.assertNotIn('class="mt4 bigstats"', updated)
        self.assertIn("模型測試數據尚未提供", updated)


if __name__ == "__main__":
    unittest.main()

