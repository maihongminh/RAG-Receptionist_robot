from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.db import execute, fetch_one
from app.core.schemas import AuthContext


class AuthSessionError(ValueError):
    pass


class AuthSessionService:
    def create(self, account_id: str, ttl_seconds: int) -> tuple[str, str]:
        session_id = str(uuid4())
        refresh_token = self._new_refresh_token()
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
        execute(
            """
            INSERT INTO robo_auth.sessions (
              id,
              account_id,
              refresh_token_hash,
              expires_at
            )
            VALUES (
              %(id)s,
              %(account_id)s,
              %(refresh_token_hash)s,
              %(expires_at)s
            )
            """,
            {
                "id": session_id,
                "account_id": account_id,
                "refresh_token_hash": self._hash_refresh_token(refresh_token),
                "expires_at": expires_at,
            },
        )
        return session_id, refresh_token

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

    def revoke_other_sessions(self, account_id: str, keep_session_id: str | None) -> None:
        execute(
            """
            UPDATE robo_auth.sessions
            SET revoked_at = now(),
                updated_at = now()
            WHERE account_id = %(account_id)s
              AND revoked_at IS NULL
              AND (%(keep_session_id)s::text IS NULL OR id <> %(keep_session_id)s)
            """,
            {
                "account_id": account_id,
                "keep_session_id": keep_session_id,
            },
        )

    def refresh(self, refresh_token: str, ttl_seconds: int) -> tuple[AuthContext, str]:
        token_hash = self._hash_refresh_token(refresh_token)
        row = fetch_one(
            """
            SELECT
              s.id AS session_id,
              a.id AS account_id,
              ar.role,
              COALESCE(ar.clinic_id, ai.clinic_id) AS clinic_id,
              ai.user_id,
              ai.patient_id,
              ai.doctor_id,
              ai.staff_id
            FROM robo_auth.sessions s
            JOIN robo_auth.accounts a
              ON a.id = s.account_id
            JOIN robo_auth.account_roles ar
              ON ar.account_id = a.id
             AND ar.is_active = true
            LEFT JOIN robo_auth.account_identities ai
              ON ai.account_id = a.id
             AND ai.is_primary = true
            WHERE s.refresh_token_hash = %(refresh_token_hash)s
              AND s.revoked_at IS NULL
              AND (s.expires_at IS NULL OR s.expires_at > now())
              AND a.status = 'active'
              AND (a.locked_until IS NULL OR a.locked_until <= now())
            ORDER BY ar.is_primary DESC, ar.created_at ASC
            LIMIT 1
            """,
            {"refresh_token_hash": token_hash},
        )
        if not row:
            raise AuthSessionError("Invalid or expired refresh token.")

        new_refresh_token = self._new_refresh_token()
        execute(
            """
            UPDATE robo_auth.sessions
            SET refresh_token_hash = %(refresh_token_hash)s,
                expires_at = %(expires_at)s,
                updated_at = now()
            WHERE id = %(session_id)s
            """,
            {
                "session_id": row["session_id"],
                "refresh_token_hash": self._hash_refresh_token(new_refresh_token),
                "expires_at": datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds),
            },
        )
        return self._auth_from_row(row), new_refresh_token

    def _auth_from_row(self, row: dict) -> AuthContext:
        role = row["role"]
        base = {
            "account_id": row["account_id"],
            "session_id": row["session_id"],
            "role": role,
            "user_id": row.get("user_id") or row["account_id"],
            "clinic_id": row.get("clinic_id"),
            "staff_id": row.get("staff_id"),
        }
        if role == "patient":
            return AuthContext(**base, patient_id=row.get("patient_id"))
        if role == "doctor":
            return AuthContext(**base, doctor_id=row.get("doctor_id"))
        return AuthContext(**base)

    def _new_refresh_token(self) -> str:
        return secrets.token_urlsafe(48)

    def _hash_refresh_token(self, refresh_token: str) -> str:
        return hashlib.sha256(refresh_token.encode("utf-8")).hexdigest()
