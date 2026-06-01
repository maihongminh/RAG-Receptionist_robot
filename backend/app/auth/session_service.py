from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.db import execute, fetch_one


class AuthSessionService:
    def create(self, account_id: str, ttl_seconds: int) -> str:
        session_id = str(uuid4())
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
        execute(
            """
            INSERT INTO robo_auth.sessions (id, account_id, expires_at)
            VALUES (%(id)s, %(account_id)s, %(expires_at)s)
            """,
            {
                "id": session_id,
                "account_id": account_id,
                "expires_at": expires_at,
            },
        )
        return session_id

    def is_active(self, session_id: str) -> bool:
        row = fetch_one(
            """
            SELECT id
            FROM robo_auth.sessions
            WHERE id = %(session_id)s
              AND revoked_at IS NULL
              AND (expires_at IS NULL OR expires_at > now())
            LIMIT 1
            """,
            {"session_id": session_id},
        )
        return row is not None

    def revoke(self, session_id: str) -> None:
        execute(
            """
            UPDATE robo_auth.sessions
            SET revoked_at = now(),
                updated_at = now()
            WHERE id = %(session_id)s
              AND revoked_at IS NULL
            """,
            {"session_id": session_id},
        )
