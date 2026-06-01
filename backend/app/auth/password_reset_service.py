from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.auth.audit_logger import AuditLogger
from app.auth.password_service import hash_password
from app.auth.session_service import AuthSessionService
from app.config import get_settings
from app.db import execute, fetch_one


class AuthPasswordResetError(ValueError):
    pass


class AuthPasswordResetService:
    def __init__(self) -> None:
        self.audit_logger = AuditLogger()
        self.session_service = AuthSessionService()

    def request_reset(self, email: str) -> str | None:
        normalized_email = email.strip().lower()
        row = fetch_one(
            """
            SELECT id
            FROM robo_auth.accounts
            WHERE lower(email) = lower(%(email)s)
              AND status = 'active'
            LIMIT 1
            """,
            {"email": normalized_email},
        )
        if not row:
            self.audit_logger.log_auth_event(
                event_type="password_reset_requested",
                reason="account_not_found",
                metadata={"email": normalized_email},
            )
            return None

        reset_token = self._new_reset_token()
        execute(
            """
            UPDATE robo_auth.password_reset_tokens
            SET used_at = now()
            WHERE account_id = %(account_id)s
              AND used_at IS NULL
            """,
            {"account_id": row["id"]},
        )
        execute(
            """
            INSERT INTO robo_auth.password_reset_tokens (
              id,
              account_id,
              token_hash,
              expires_at
            )
            VALUES (
              %(id)s,
              %(account_id)s,
              %(token_hash)s,
              %(expires_at)s
            )
            """,
            {
                "id": str(uuid4()),
                "account_id": row["id"],
                "token_hash": self._hash_token(reset_token),
                "expires_at": datetime.now(timezone.utc)
                + timedelta(seconds=get_settings().auth_password_reset_token_ttl_seconds),
            },
        )
        self.audit_logger.log_auth_event(
            event_type="password_reset_requested",
            account_id=row["id"],
            metadata={"email": normalized_email},
        )
        return reset_token

    def complete_reset(self, reset_token: str, new_password: str) -> None:
        if len(new_password) < get_settings().auth_min_password_length:
            raise AuthPasswordResetError(
                f"New password must be at least {get_settings().auth_min_password_length} characters."
            )

        token_hash = self._hash_token(reset_token)
        row = fetch_one(
            """
            SELECT id, account_id
            FROM robo_auth.password_reset_tokens
            WHERE token_hash = %(token_hash)s
              AND used_at IS NULL
              AND expires_at > now()
            LIMIT 1
            """,
            {"token_hash": token_hash},
        )
        if not row:
            self.audit_logger.log_auth_event(
                event_type="password_reset_failed",
                reason="invalid_or_expired_token",
            )
            raise AuthPasswordResetError("Invalid or expired reset token.")

        execute(
            """
            UPDATE robo_auth.accounts
            SET password_hash = %(password_hash)s,
                password_algorithm = 'pbkdf2_sha256',
                password_updated_at = now(),
                failed_login_count = 0,
                locked_until = NULL,
                updated_at = now()
            WHERE id = %(account_id)s
            """,
            {
                "account_id": row["account_id"],
                "password_hash": hash_password(new_password),
            },
        )
        execute(
            """
            UPDATE robo_auth.password_reset_tokens
            SET used_at = now()
            WHERE id = %(id)s
            """,
            {"id": row["id"]},
        )
        self.session_service.revoke_other_sessions(row["account_id"], keep_session_id=None)
        self.audit_logger.log_auth_event(
            event_type="password_reset_completed",
            account_id=row["account_id"],
        )

    def _new_reset_token(self) -> str:
        return secrets.token_urlsafe(48)

    def _hash_token(self, token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()
