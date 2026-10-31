"""Pure helpers for locale selection and evidence-based home page metrics."""

import html
import json
import math
import re


SUPPORTED_LANGUAGES = {"zh", "en"}
_METRIC_KEYS = ("accuracy", "precision", "recall", "f1")


def resolve_language(requested, saved="zh"):
    """Choose an explicit supported locale, then a saved one, then Traditional Chinese."""
    if requested in SUPPORTED_LANGUAGES:
        return requested
    if saved in SUPPORTED_LANGUAGES:
        return saved
    return "zh"


def correct_legacy_copy(page):
    """Replace unsafe legacy allowlist claims in static interface copy."""
    safe_copy = {
        "已知安全網域自動略過重複分析。": "白名單只提供網域比對提示；所有郵件仍會完成四層分析。",
        "加入白名單後，來自該網域及其子網域的信件將直接標記為安全，不進行 AI 分析。請只加入確定可信任的網域。":
            "加入白名單只會顯示網域比對提示，不會略過分析或保證郵件安全；寄件者欄位可能遭偽冒。",
        "每個網域及其子網域都會被放行。": "白名單命中只作為網域提示；每封郵件仍會進入四層分析。",
        "白名單安全信件": "白名單命中提示",
        "白名單 · 略過分析": "白名單提示 · 仍完成分析",
        "已放行 CLEARED": "網域比對提示",
        "寄件網域命中白名單者直接略過全部分析。":
            "寄件網域命中白名單只代表網域比對符合；所有郵件仍會完成四層分析。",
        "者直接略過全部分析。": "者僅代表網域比對命中；所有郵件仍完成四層分析。",
        "白名單演示 ①：google.com 官方寄件者（會被略過）":
            "白名單演示 ①：google.com 寄件網域命中（仍進行分析）",
    }
    for outdated, corrected in safe_copy.items():
        page = page.replace(outdated, corrected)
    return page


def inject_locale_assets(page, language):
    """Set the document language and load the shared polish assets on HTML pages."""
    language = language if language in SUPPORTED_LANGUAGES else "zh"
    page = re.sub(
        r'<textarea id="pt"(?![^>]*\baria-label=)',
        '<textarea id="pt" aria-label="輸入文字"',
        page,
        count=1,
    )
    boot = (
        '<script>document.documentElement.lang=' + json.dumps(language) + ';</script>'
    )
    assets = '<link rel="stylesheet" href="/static/site.css"><script defer src="/static/i18n.js"></script>'
    style_end = page.rfind("</style>")
    if style_end >= 0:
        insert_at = style_end + len("</style>")
        return page[:insert_at] + boot + assets + page[insert_at:]
    return page.replace('<meta charset="utf-8">', '<meta charset="utf-8">' + boot + assets, 1)


def add_home_privacy_note(page, language="zh"):
    """Add a concise, source-verified Gmail and scan-history privacy note to the hero."""
    if language == "en":
        note = (
            '<p class="trust-note"><b>Read-only access</b> Gmail access is read-only and scans up to '
            '15 recent inbox messages. Email content and results stay in server memory; scan history '
            'stores counts only.</p>'
        )
    else:
        note = (
            '<p class="trust-note"><b>唯讀權限</b> Gmail 僅讀取最近 15 封郵件。郵件內容與分析結果暫存在伺服器記憶體；'
            '案件簿只保存掃描數量摘要。</p>'
        )
    match = re.search(r'<div class="cta">.*?</div>', page, flags=re.DOTALL)
    if not match or 'class="trust-note"' in page:
        return page
    return page[:match.end()] + note + page[match.end():]


def _home_values(metrics):
    if not isinstance(metrics, dict):
        return None
    try:
        values = {key: float(metrics[key]) * 100 for key in _METRIC_KEYS}
        counts = {
            "rows": int(metrics["dataset_rows_after_cleaning"]),
            "train": int(metrics["train_rows"]),
            "test": int(metrics["test_rows"]),
        }
        dataset = str(metrics["dataset"])
    except (KeyError, TypeError, ValueError, OverflowError):
        return None
    if (not dataset or any(not math.isfinite(v) or v < 0 or v > 100 for v in values.values())
            or any(v < 0 for v in counts.values()) or counts["rows"] == 0
            or counts["rows"] != counts["train"] + counts["test"]):
        return None
    return {**{k: f"{v:.2f}" for k, v in values.items()}, **counts, "dataset": dataset}


def apply_model_metrics(page, metrics):
    """Render homepage metrics only when the model report contains valid values."""
    values = _home_values(metrics)
    if values is None:
        page = re.sub(
            r'<div class="mt-ds">.*?</div>',
            "",
            page,
            count=1,
            flags=re.DOTALL,
        )
        page = re.sub(
            r'<div class="mt4 bigstats">.*?</div>',
            '<p class="note">模型測試數據尚未提供。</p>',
            page,
            count=1,
            flags=re.DOTALL,
        )
        return page

    dataset_text = (
        f'資料集　{html.escape(values["dataset"])}，清理後 {values["rows"]:,} 筆'
        f'（訓練 {values["train"]:,} / 測試 {values["test"]:,}）'
    )
    page = re.sub(
        r'(<div class="mt-ds">).*?(</div>)',
        lambda match: match.group(1) + dataset_text + match.group(2),
        page,
        count=1,
        flags=re.DOTALL,
    )

    sequence = iter(values[key] for key in _METRIC_KEYS)

    def replace_metric(match):
        value = next(sequence)
        return f'{match.group(1)}{value}{match.group(2)}{value}{match.group(3)}'

    page = re.sub(
        r'(<span class="cu" data-to=")[^"]*(">)[^<]*(</span>)',
        replace_metric,
        page,
        count=4,
    )
    widths = iter(values[key] for key in _METRIC_KEYS)
    page = re.sub(
        r'(<span class="bb" style="--w:)[0-9.]+(%"></span>)',
        lambda match: match.group(1) + next(widths) + match.group(2),
        page,
        count=4,
    )
    return page

