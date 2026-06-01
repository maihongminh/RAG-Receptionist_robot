from __future__ import annotations

import time
from collections import defaultdict, deque


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str, *, max_attempts: int, window_seconds: int) -> bool:
        now = time.monotonic()
        cutoff = now - window_seconds
        hits = self._hits[key]
        while hits and hits[0] < cutoff:
            hits.popleft()
        if len(hits) >= max_attempts:
            return False
        hits.append(now)
        return True


login_rate_limiter = InMemoryRateLimiter()
