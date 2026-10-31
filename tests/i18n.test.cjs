const assert = require('node:assert/strict');
const { localizeText, resolveLocale, shouldTranslate } = require('../static/i18n.js');

assert.equal(resolveLocale('en', 'zh'), 'en');
assert.equal(resolveLocale('fr', 'en'), 'en');
assert.equal(resolveLocale('fr', 'fr'), 'zh');

assert.equal(localizeText('偵測規則', 'en'), 'Detection rules');
assert.equal(localizeText('開啟郵件分析結果：Invoice update', 'en'), 'Open email analysis: Invoice update');
assert.equal(
  localizeText('白名單只提供網域比對提示；所有郵件仍會完成四層分析。', 'en'),
  'Allowlist matches are domain hints; every message still goes through all four analysis layers.',
);
assert.equal(localizeText('目前白名單（14 個）', 'en'), 'Current allowlist (14 domains)');
assert.equal(localizeText('Current allowlist (14 個）', 'en'), 'Current allowlist (14 domains)');
assert.equal(localizeText('14 個）', 'en'), '14 domains)');
assert.equal(localizeText('個）', 'en'), 'domains)');
assert.equal(localizeText('子網域比對：The sender matched.', 'en'), 'Domain match: The sender matched.');
assert.equal(localizeText('Current allowlist (14 個）', 'en'), 'Current allowlist (14 domains)');
assert.equal(localizeText('R1 緊急語句', 'en'), 'R1 Urgent language');
assert.equal(localizeText('範例④：白名單網域放在前面（不命中）', 'en'), 'Example 4: allowlist domain appears first (no match)');
assert.equal(localizeText('貼上郵件的純文字內容（必填）...', 'en'), 'Paste the email text (required)…');
assert.match(
  localizeText('寄件網域命中白名單「google.com」，系統將略過分析，直接判定為安全。', 'en'),
  /still goes through all four analysis layers/,
);
assert.match(
  localizeText('已知安全網域自動略過重複分析。', 'zh'),
  /所有郵件仍會完成四層分析/,
);
assert.equal(shouldTranslate('alert@accounts.google.com', true), false);
assert.equal(shouldTranslate('案件簿', false), true);

process.stdout.write('i18n helpers: 12 assertions passed\n');

