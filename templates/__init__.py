"""HTML 頁面模板套件。

原 templates.py（約 3,900 行）依頁面拆成多個模組；對外介面不變：
    from templates import HOME_HTML, render_paste_page, ...
"""
from ._base import COMMON_CSS, DESIGN2_CSS, kw_json as _kw_json
from .home import HOME_HTML, render_home_page
from .loading import LOADING_HTML
from .error import ERROR_HTML, render_error
from .paste import PASTE_HTML, SAMPLE_EMAILS, render_paste_page
from .result import RESULT_HTML
from .history import HISTORY_HTML
from .rules import RULES_HTML
from .whitelist import WHITELIST_HTML

__all__ = [
    "COMMON_CSS", "DESIGN2_CSS",
    "HOME_HTML", "LOADING_HTML", "ERROR_HTML", "PASTE_HTML", "RESULT_HTML",
    "HISTORY_HTML", "RULES_HTML", "WHITELIST_HTML",
    "SAMPLE_EMAILS", "render_home_page", "render_error", "render_paste_page",
]
