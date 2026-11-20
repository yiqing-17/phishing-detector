"""極簡的記憶體內速率限制（滑動視窗，不需額外套件）。

用途：保護會消耗 Groq 額度的端點（/paste_analyze、/scan）。
限制：資料只存在單一程序的記憶體；Render 重啟會歸零，所以 Procfile 只開 1 個 worker。
"""
import threading
import time
from collections import defaultdict, deque


class RateLimiter:
    def __init__(self):
        self._hits = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, key, limit, window_s, now=None):
        """回傳 (是否允許, 需等待秒數)。"""
        now = time.time() if now is None else now
        with self._lock:
            q = self._hits[key]
            while q and q[0] <= now - window_s:
                q.popleft()
            if len(q) >= limit:
                return False, max(1, int(q[0] + window_s - now) + 1)
            q.append(now)
            if len(self._hits) > 5000:            # 防止 key 無限增長
                for k in [k for k, v in self._hits.items() if not v][:1000]:
                    self._hits.pop(k, None)
            return True, 0


def client_ip(environ_remote_addr, forwarded_for):
    """Render 的代理會把真實連線 IP 附加在 X-Forwarded-For 最右邊；
    最左邊是用戶端自己填的，可以偽造，所以取最右邊。"""
    if forwarded_for:
        parts = [p.strip() for p in forwarded_for.split(',') if p.strip()]
        if parts:
            return parts[-1]
    return environ_remote_addr or 'unknown'
