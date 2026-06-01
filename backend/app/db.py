from contextlib import contextmanager
from typing import Any

from app.config import get_settings


@contextmanager
def get_connection():
    try:
        import psycopg
        from psycopg.rows import dict_row
    except ImportError as exc:
        raise RuntimeError(
            "Missing psycopg dependency. Install backend requirements first."
        ) from exc

    settings = get_settings()
    with psycopg.connect(settings.database_url, row_factory=dict_row) as conn:
        yield conn


def fetch_all(query: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params or {})
            rows = cur.fetchall()
            return [dict(row) for row in rows]


def fetch_one(query: str, params: dict[str, Any] | None = None) -> dict[str, Any] | None:
    rows = fetch_all(query, params)
    return rows[0] if rows else None


def execute(query: str, params: dict[str, Any] | None = None) -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params or {})
