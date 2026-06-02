from __future__ import annotations

from app.auth.audit_logger import AuditLogger
from app.core.schemas import (
    AuthAdminAccountDetail,
    AuthAdminAccountSummary,
    AuthAdminActionResponse,
    AuthAdminIdentityRow,
    AuthAdminRoleRow,
    AuthAdminSessionRow,
    AuthContext,
)
from app.db import execute, fetch_all, fetch_one


class AuthAdminError(ValueError):
    pass


class AuthAdminForbidden(AuthAdminError):
    pass


class AuthAdminService:
    def __init__(self) -> None:
        self.audit_logger = AuditLogger()

    def list_accounts(
        self,
        auth: AuthContext,
        query: str = "",
        limit: int = 50,
    ) -> list[AuthAdminAccountSummary]:
        self._require_admin(auth)
        params = self._scope_params(auth)
        params["query"] = f"%{query.strip().lower()}%" if query.strip() else None
        params["limit"] = max(1, min(int(limit or 50), 100))

        rows = fetch_all(
            f"""
            SELECT
              a.id,
              a.email,
              a.status,
              a.failed_login_count,
              a.locked_until::text AS locked_until,
              a.last_login_at::text AS last_login_at,
              a.password_updated_at::text AS password_updated_at,
              a.created_at::text AS created_at,
              COALESCE(string_agg(DISTINCT ar.role, ','), '') AS roles,
              COALESCE(string_agg(DISTINCT COALESCE(ar.clinic_id, ai.clinic_id), ','), '') AS clinic_ids,
              COALESCE(string_agg(DISTINCT ai.identity_type, ','), '') AS identity_types,
              COUNT(DISTINCT s.id)::integer AS active_session_count
            FROM robo_auth.accounts a
            LEFT JOIN robo_auth.account_roles ar
              ON ar.account_id = a.id
             AND ar.is_active = true
            LEFT JOIN robo_auth.account_identities ai
              ON ai.account_id = a.id
            LEFT JOIN robo_auth.sessions s
              ON s.account_id = a.id
             AND s.revoked_at IS NULL
             AND (s.expires_at IS NULL OR s.expires_at > now())
            WHERE {self._scope_sql(auth)}
              AND (
                %(query)s::text IS NULL
                OR lower(a.email) LIKE %(query)s
                OR lower(a.id) LIKE %(query)s
                OR lower(COALESCE(ar.role, '')) LIKE %(query)s
              )
            GROUP BY
              a.id,
              a.email,
              a.status,
              a.failed_login_count,
              a.locked_until,
              a.last_login_at,
              a.password_updated_at,
              a.created_at
            ORDER BY a.created_at DESC, a.email
            LIMIT %(limit)s
            """,
            params,
        )
        return [self._summary_from_row(row) for row in rows]

    def get_account(self, auth: AuthContext, account_id: str) -> AuthAdminAccountDetail:
        self._require_admin(auth)
        account = self._get_account_summary(auth, account_id)
        if not account:
            raise AuthAdminError("Account not found in your admin scope.")

        rows_params = {"account_id": account_id}
        roles = [
            AuthAdminRoleRow(**row)
            for row in fetch_all(
                """
                SELECT
                  id,
                  role,
                  clinic_id,
                  organization_id,
                  is_primary,
                  is_active,
                  created_at::text AS created_at
                FROM robo_auth.account_roles
                WHERE account_id = %(account_id)s
                ORDER BY is_primary DESC, created_at ASC
                """,
                rows_params,
            )
        ]
        identities = [
            AuthAdminIdentityRow(**row)
            for row in fetch_all(
                """
                SELECT
                  id,
                  identity_type,
                  user_id,
                  patient_id,
                  staff_id,
                  doctor_id,
                  clinic_id,
                  organization_id,
                  is_primary,
                  created_at::text AS created_at
                FROM robo_auth.account_identities
                WHERE account_id = %(account_id)s
                ORDER BY is_primary DESC, created_at ASC
                """,
                rows_params,
            )
        ]
        sessions = [
            AuthAdminSessionRow(**row)
            for row in fetch_all(
                """
                SELECT
                  id,
                  expires_at::text AS expires_at,
                  revoked_at::text AS revoked_at,
                  created_at::text AS created_at,
                  updated_at::text AS updated_at,
                  (
                    revoked_at IS NULL
                    AND (expires_at IS NULL OR expires_at > now())
                  ) AS is_active
                FROM robo_auth.sessions
                WHERE account_id = %(account_id)s
                ORDER BY created_at DESC
                LIMIT 20
                """,
                rows_params,
            )
        ]
        return AuthAdminAccountDetail(
            account=account,
            roles=roles,
            identities=identities,
            sessions=sessions,
        )

    def unlock_account(self, auth: AuthContext, account_id: str) -> AuthAdminActionResponse:
        self._require_admin(auth)
        if not self._account_in_scope(auth, account_id):
            raise AuthAdminError("Account not found in your admin scope.")

        execute(
            """
            UPDATE robo_auth.accounts
            SET failed_login_count = 0,
                locked_until = NULL,
                updated_at = now()
            WHERE id = %(account_id)s
            """,
            {"account_id": account_id},
        )
        self.audit_logger.log_auth_event(
            event_type="admin_account_unlocked",
            account_id=auth.account_id,
            session_id=auth.session_id,
            user_id=auth.user_id,
            role=str(auth.role),
            clinic_id=auth.clinic_id,
            metadata={"target_account_id": account_id},
        )
        return AuthAdminActionResponse(ok=True, affected_count=1)

    def revoke_sessions(self, auth: AuthContext, account_id: str) -> AuthAdminActionResponse:
        self._require_admin(auth)
        if not self._account_in_scope(auth, account_id):
            raise AuthAdminError("Account not found in your admin scope.")

        revoked = fetch_all(
            """
            UPDATE robo_auth.sessions
            SET revoked_at = now(),
                updated_at = now()
            WHERE account_id = %(account_id)s
              AND revoked_at IS NULL
              AND (%(keep_session_id)s::text IS NULL OR id <> %(keep_session_id)s)
            RETURNING id
            """,
            {
                "account_id": account_id,
                "keep_session_id": auth.session_id if auth.account_id == account_id else None,
            },
        )
        self.audit_logger.log_auth_event(
            event_type="admin_sessions_revoked",
            account_id=auth.account_id,
            session_id=auth.session_id,
            user_id=auth.user_id,
            role=str(auth.role),
            clinic_id=auth.clinic_id,
            metadata={"target_account_id": account_id, "revoked_count": len(revoked)},
        )
        return AuthAdminActionResponse(ok=True, affected_count=len(revoked))

    def _get_account_summary(
        self,
        auth: AuthContext,
        account_id: str,
    ) -> AuthAdminAccountSummary | None:
        params = self._scope_params(auth)
        params["account_id"] = account_id
        row = fetch_one(
            f"""
            SELECT
              a.id,
              a.email,
              a.status,
              a.failed_login_count,
              a.locked_until::text AS locked_until,
              a.last_login_at::text AS last_login_at,
              a.password_updated_at::text AS password_updated_at,
              a.created_at::text AS created_at,
              COALESCE(string_agg(DISTINCT ar.role, ','), '') AS roles,
              COALESCE(string_agg(DISTINCT COALESCE(ar.clinic_id, ai.clinic_id), ','), '') AS clinic_ids,
              COALESCE(string_agg(DISTINCT ai.identity_type, ','), '') AS identity_types,
              COUNT(DISTINCT s.id)::integer AS active_session_count
            FROM robo_auth.accounts a
            LEFT JOIN robo_auth.account_roles ar
              ON ar.account_id = a.id
             AND ar.is_active = true
            LEFT JOIN robo_auth.account_identities ai
              ON ai.account_id = a.id
            LEFT JOIN robo_auth.sessions s
              ON s.account_id = a.id
             AND s.revoked_at IS NULL
             AND (s.expires_at IS NULL OR s.expires_at > now())
            WHERE a.id = %(account_id)s
              AND {self._scope_sql(auth)}
            GROUP BY
              a.id,
              a.email,
              a.status,
              a.failed_login_count,
              a.locked_until,
              a.last_login_at,
              a.password_updated_at,
              a.created_at
            LIMIT 1
            """,
            params,
        )
        return self._summary_from_row(row) if row else None

    def _account_in_scope(self, auth: AuthContext, account_id: str) -> bool:
        return self._get_account_summary(auth, account_id) is not None

    def _summary_from_row(self, row: dict) -> AuthAdminAccountSummary:
        item = dict(row)
        item["roles"] = self._split_csv(item.get("roles"))
        item["clinic_ids"] = self._split_csv(item.get("clinic_ids"))
        item["identity_types"] = self._split_csv(item.get("identity_types"))
        return AuthAdminAccountSummary(**item)

    def _require_admin(self, auth: AuthContext) -> None:
        if auth.role == "system_admin":
            return
        if auth.role == "clinic_admin" and auth.clinic_id:
            return
        raise AuthAdminForbidden("Admin role is required.")

    def _scope_sql(self, auth: AuthContext) -> str:
        if auth.role == "system_admin":
            return "(true)"
        return """
        (
        EXISTS (
          SELECT 1
          FROM robo_auth.account_roles scope_ar
          WHERE scope_ar.account_id = a.id
            AND scope_ar.is_active = true
            AND scope_ar.clinic_id = %(admin_clinic_id)s
        )
        OR EXISTS (
          SELECT 1
          FROM robo_auth.account_identities scope_ai
          WHERE scope_ai.account_id = a.id
            AND scope_ai.clinic_id = %(admin_clinic_id)s
        )
        )
        """

    def _scope_params(self, auth: AuthContext) -> dict:
        if auth.role == "system_admin":
            return {}
        return {"admin_clinic_id": auth.clinic_id}

    def _split_csv(self, value: str | None) -> list[str]:
        if not value:
            return []
        return sorted({part for part in value.split(",") if part})
