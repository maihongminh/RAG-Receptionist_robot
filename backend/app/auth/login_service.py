from datetime import datetime, timedelta, timezone

from app.auth.audit_logger import AuditLogger
from app.auth.token_service import AuthTokenService
from app.auth.password_service import verify_password
from app.auth.session_service import AuthSessionService
from app.config import get_settings
from app.core.schemas import AuthContext, AuthLoginRequest, AuthLoginResponse
from app.db import execute, fetch_one


class AuthLoginError(ValueError):
    pass


class AuthLoginService:
    def __init__(self) -> None:
        self.token_service = AuthTokenService()
        self.session_service = AuthSessionService()
        self.audit_logger = AuditLogger()

    def login(self, payload: AuthLoginRequest) -> AuthLoginResponse:
        auth = self._resolve_auth_context(payload)
        expires_in = self.token_service.settings.auth_token_ttl_seconds
        if auth.account_id:
            session_id = self.session_service.create(auth.account_id, expires_in)
            auth = auth.model_copy(update={"session_id": session_id})
            execute(
                """
                UPDATE robo_auth.accounts
                SET last_login_at = now(),
                    failed_login_count = 0,
                    updated_at = now()
                WHERE id = %(account_id)s
                """,
                {"account_id": auth.account_id},
            )
            token, expires_in = self.token_service.issue(auth, session_id=session_id)
            self.audit_logger.log_auth_event(
                event_type="login_success",
                account_id=auth.account_id,
                session_id=auth.session_id,
                user_id=auth.user_id,
                role=str(auth.role),
                clinic_id=auth.clinic_id,
            )
        else:
            token, expires_in = self.token_service.issue(auth)
        return AuthLoginResponse(access_token=token, expires_in=expires_in, auth=auth)

    def _resolve_auth_context(self, payload: AuthLoginRequest) -> AuthContext:
        if payload.email or payload.password:
            return self._account_password_auth(payload)
        if not get_settings().auth_allow_legacy_role_login:
            raise AuthLoginError("email/password login is required.")
        if not payload.role:
            raise AuthLoginError("Login requires email/password or role/scope.")
        if payload.role == "guest":
            return AuthContext(role="guest")
        if payload.role == "patient":
            return self._patient_auth(payload)
        if payload.role == "doctor":
            return self._doctor_auth(payload)
        if payload.role in {"receptionist", "clinic_admin"}:
            return self._clinic_staff_auth(payload)
        if payload.role == "system_admin":
            raise AuthLoginError("system_admin login is not enabled in MVP.")
        raise AuthLoginError(f"Unsupported role: {payload.role}")

    def _account_password_auth(self, payload: AuthLoginRequest) -> AuthContext:
        if not payload.email or not payload.password:
            raise AuthLoginError("email/password login requires both email and password.")

        row = fetch_one(
            """
            SELECT
              a.id AS account_id,
              a.email,
              a.password_hash,
              a.locked_until,
              a.status = 'active'
                AND (a.locked_until IS NULL OR a.locked_until <= now()) AS is_active,
              ar.role,
              COALESCE(ar.clinic_id, ai.clinic_id) AS clinic_id,
              ai.user_id,
              ai.patient_id,
              ai.doctor_id,
              ai.staff_id
            FROM robo_auth.accounts a
            JOIN robo_auth.account_roles ar
              ON ar.account_id = a.id
             AND ar.is_active = true
            LEFT JOIN robo_auth.account_identities ai
              ON ai.account_id = a.id
             AND ai.is_primary = true
            WHERE lower(a.email) = lower(%(email)s)
              AND a.status = 'active'
            ORDER BY ar.is_primary DESC, ar.created_at ASC
            LIMIT 1
            """,
            {"email": payload.email.strip()},
        )
        if not row:
            self.audit_logger.log_auth_event(
                event_type="login_failed",
                reason="account_not_found",
                metadata={"email": payload.email.strip().lower()},
            )
            raise AuthLoginError("Invalid email or password.")
        if not row.get("is_active"):
            self.audit_logger.log_auth_event(
                event_type="login_failed",
                account_id=row["account_id"],
                reason="account_locked",
                metadata={"email": payload.email.strip().lower()},
            )
            raise AuthLoginError("Account is temporarily locked. Please try again later.")
        if not verify_password(payload.password, row["password_hash"]):
            self._record_failed_login(row["account_id"])
            self.audit_logger.log_auth_event(
                event_type="login_failed",
                account_id=row["account_id"],
                reason="invalid_password",
                metadata={"email": payload.email.strip().lower()},
            )
            raise AuthLoginError("Invalid email or password.")

        role = row["role"]
        if role == "patient":
            if not row.get("patient_id"):
                raise AuthLoginError("Patient account is missing patient scope.")
            return AuthContext(
                account_id=row["account_id"],
                role="patient",
                user_id=row.get("user_id") or row["account_id"],
                patient_id=row["patient_id"],
                clinic_id=row.get("clinic_id"),
            )
        if role == "doctor":
            if not row.get("doctor_id"):
                raise AuthLoginError("Doctor account is missing doctor scope.")
            return AuthContext(
                account_id=row["account_id"],
                role="doctor",
                user_id=row.get("user_id") or row["account_id"],
                doctor_id=row["doctor_id"],
                staff_id=row.get("staff_id"),
                clinic_id=row.get("clinic_id"),
            )
        if role in {"receptionist", "clinic_admin"}:
            if not row.get("clinic_id"):
                raise AuthLoginError(f"{role} account is missing clinic scope.")
            return AuthContext(
                account_id=row["account_id"],
                role=role,
                user_id=row.get("user_id") or row.get("staff_id") or row["account_id"],
                staff_id=row.get("staff_id"),
                clinic_id=row["clinic_id"],
            )
        if role == "system_admin":
            return AuthContext(
                account_id=row["account_id"],
                role="system_admin",
                user_id=row.get("user_id") or row["account_id"],
            )
        raise AuthLoginError(f"Unsupported account role: {role}")

    def _record_failed_login(self, account_id: str) -> None:
        settings = get_settings()
        locked_until = datetime.now(timezone.utc) + timedelta(seconds=settings.auth_lock_seconds)
        execute(
            """
            UPDATE robo_auth.accounts
            SET failed_login_count = failed_login_count + 1,
                locked_until = CASE
                  WHEN failed_login_count + 1 >= %(max_failed)s THEN %(locked_until)s
                  ELSE locked_until
                END,
                updated_at = now()
            WHERE id = %(account_id)s
            """,
            {
                "account_id": account_id,
                "max_failed": settings.auth_max_failed_login_attempts,
                "locked_until": locked_until,
            },
        )

    def _patient_auth(self, payload: AuthLoginRequest) -> AuthContext:
        if not payload.patient_id:
            raise AuthLoginError("patient login requires patient_id.")
        row = fetch_one(
            """
            SELECT id, clinic_id
            FROM robo_app.patients
            WHERE id = %(patient_id)s
            LIMIT 1
            """,
            {"patient_id": payload.patient_id},
        )
        if not row:
            raise AuthLoginError("Patient not found.")
        return AuthContext(
            role="patient",
            user_id=row["id"],
            patient_id=row["id"],
            clinic_id=row.get("clinic_id"),
        )

    def _doctor_auth(self, payload: AuthLoginRequest) -> AuthContext:
        doctor_id = payload.doctor_id or payload.staff_id
        if not doctor_id:
            raise AuthLoginError("doctor login requires doctor_id.")
        row = fetch_one(
            """
            SELECT id, clinic_id, role
            FROM robo_app.staff
            WHERE id = %(doctor_id)s
              AND role ILIKE 'doctor'
              AND COALESCE(is_active, true) = true
            LIMIT 1
            """,
            {"doctor_id": doctor_id},
        )
        if not row:
            raise AuthLoginError("Doctor not found or inactive.")
        return AuthContext(
            role="doctor",
            user_id=row["id"],
            doctor_id=row["id"],
            clinic_id=row.get("clinic_id"),
        )

    def _clinic_staff_auth(self, payload: AuthLoginRequest) -> AuthContext:
        if not payload.clinic_id:
            raise AuthLoginError(f"{payload.role} login requires clinic_id.")
        clinic = fetch_one(
            """
            SELECT id
            FROM robo_app.clinics
            WHERE id = %(clinic_id)s
              AND status = 'active'
            LIMIT 1
            """,
            {"clinic_id": payload.clinic_id},
        )
        if not clinic:
            raise AuthLoginError("Clinic not found or inactive.")

        user_id = payload.staff_id
        if payload.staff_id:
            staff = fetch_one(
                """
                SELECT id
                FROM robo_app.staff
                WHERE id = %(staff_id)s
                  AND clinic_id = %(clinic_id)s
                  AND role = %(role)s
                  AND COALESCE(is_active, true) = true
                LIMIT 1
                """,
                {
                    "staff_id": payload.staff_id,
                    "clinic_id": payload.clinic_id,
                    "role": payload.role,
                },
            )
            if not staff:
                raise AuthLoginError("Staff account not found or inactive.")
            user_id = staff["id"]

        return AuthContext(
            role=payload.role,
            user_id=user_id,
            clinic_id=payload.clinic_id,
        )
