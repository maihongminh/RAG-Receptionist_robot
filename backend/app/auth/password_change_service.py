from app.auth.audit_logger import AuditLogger
from app.auth.password_service import hash_password, verify_password
from app.auth.session_service import AuthSessionService
from app.config import get_settings
from app.core.schemas import AuthContext, AuthChangePasswordRequest
from app.db import execute, fetch_one


class AuthPasswordChangeError(ValueError):
    pass


class AuthPasswordChangeService:
    def __init__(self) -> None:
        self.audit_logger = AuditLogger()
        self.session_service = AuthSessionService()

    def change_password(
        self,
        auth: AuthContext,
        payload: AuthChangePasswordRequest,
    ) -> None:
        if not auth.account_id:
            raise AuthPasswordChangeError("Authenticated account is required.")
        if len(payload.new_password) < get_settings().auth_min_password_length:
            raise AuthPasswordChangeError(
                f"New password must be at least {get_settings().auth_min_password_length} characters."
            )
        if payload.current_password == payload.new_password:
            raise AuthPasswordChangeError("New password must be different from current password.")

        row = fetch_one(
            """
            SELECT id, password_hash
            FROM robo_auth.accounts
            WHERE id = %(account_id)s
              AND status = 'active'
            LIMIT 1
            """,
            {"account_id": auth.account_id},
        )
        if not row:
            raise AuthPasswordChangeError("Account not found or inactive.")
        if not verify_password(payload.current_password, row["password_hash"]):
            self.audit_logger.log_auth_event(
                event_type="password_change_failed",
                account_id=auth.account_id,
                session_id=auth.session_id,
                user_id=auth.user_id,
                role=str(auth.role),
                clinic_id=auth.clinic_id,
                reason="invalid_current_password",
            )
            raise AuthPasswordChangeError("Current password is incorrect.")

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
                "account_id": auth.account_id,
                "password_hash": hash_password(payload.new_password),
            },
        )
        self.session_service.revoke_other_sessions(auth.account_id, auth.session_id)
        self.audit_logger.log_auth_event(
            event_type="password_changed",
            account_id=auth.account_id,
            session_id=auth.session_id,
            user_id=auth.user_id,
            role=str(auth.role),
            clinic_id=auth.clinic_id,
        )
