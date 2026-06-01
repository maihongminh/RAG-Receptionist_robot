from __future__ import annotations

import time
from contextvars import ContextVar


_request_id: ContextVar[str | None] = ContextVar("request_id", default=None)
_started_at: ContextVar[float | None] = ContextVar("started_at", default=None)


def set_request_context(request_id: str, started_at: float | None = None) -> None:
    _request_id.set(request_id)
    _started_at.set(started_at if started_at is not None else time.perf_counter())


def get_request_id() -> str | None:
    return _request_id.get()


def get_elapsed_ms() -> float | None:
    started_at = _started_at.get()
    if started_at is None:
        return None
    return round((time.perf_counter() - started_at) * 1000, 2)
