import pytest

from app.auth import admin_service, audit_logger
from app.auth.admin_service import AuthAdminForbidden, AuthAdminService
from app.core.schemas import AuthContext


@pytest.fixture(autouse=True)
def disable_audit_db(monkeypatch):
    monkeypatch.setattr(audit_logger, "execute", lambda query, params: None)


def test_list_accounts_requires_admin_role():
    with pytest.raises(AuthAdminForbidden):
        AuthAdminService().list_accounts(AuthContext(role="patient", patient_id="patient-1"))


def test_list_accounts_scopes_clinic_admin(monkeypatch):
    captured: dict = {}

    def fake_fetch_all(query, params):
        captured["query"] = query
        captured["params"] = params
        return [
            {
                "id": "account-1",
                "email": "patient.demo@robo.local",
                "status": "active",
                "failed_login_count": 0,
                "locked_until": None,
                "last_login_at": None,
                "password_updated_at": None,
                "created_at": "2026-01-01 00:00:00+00",
                "roles": "patient",
                "clinic_ids": "clinic-1",
                "identity_types": "patient",
                "active_session_count": 1,
            }
        ]

    monkeypatch.setattr(admin_service, "fetch_all", fake_fetch_all)

    rows = AuthAdminService().list_accounts(
        AuthContext(role="clinic_admin", clinic_id="clinic-1"),
        query="patient",
    )

    assert captured["params"]["admin_clinic_id"] == "clinic-1"
    assert captured["params"]["query"] == "%patient%"
    assert "scope_ar.clinic_id = %(admin_clinic_id)s" in captured["query"]
    assert rows[0].roles == ["patient"]
    assert rows[0].clinic_ids == ["clinic-1"]


def test_system_admin_list_accounts_has_no_clinic_scope(monkeypatch):
    captured: dict = {}

    def fake_fetch_all(query, params):
        captured["query"] = query
        captured["params"] = params
        return []

    monkeypatch.setattr(admin_service, "fetch_all", fake_fetch_all)

    AuthAdminService().list_accounts(AuthContext(role="system_admin"))

    assert "admin_clinic_id" not in captured["params"]
    assert "WHERE (true)" in captured["query"]


def test_revoke_sessions_keeps_current_session_for_self(monkeypatch):
    revoked_params: dict = {}
    monkeypatch.setattr(
        AuthAdminService,
        "_account_in_scope",
        lambda self, auth, account_id: True,
    )

    def fake_fetch_all(query, params):
        revoked_params.update(params)
        return [{"id": "session-old"}]

    monkeypatch.setattr(admin_service, "fetch_all", fake_fetch_all)

    response = AuthAdminService().revoke_sessions(
        AuthContext(
            account_id="account-admin",
            session_id="session-current",
            role="clinic_admin",
            clinic_id="clinic-1",
        ),
        "account-admin",
    )

    assert revoked_params["keep_session_id"] == "session-current"
    assert response.affected_count == 1


def test_unlock_account_clears_lock(monkeypatch):
    executed: list[dict] = []
    monkeypatch.setattr(
        AuthAdminService,
        "_account_in_scope",
        lambda self, auth, account_id: True,
    )
    monkeypatch.setattr(
        admin_service,
        "execute",
        lambda query, params: executed.append(params),
    )

    response = AuthAdminService().unlock_account(
        AuthContext(
            account_id="account-admin",
            session_id="session-current",
            role="clinic_admin",
            clinic_id="clinic-1",
        ),
        "account-1",
    )

    assert executed[0]["account_id"] == "account-1"
    assert response.affected_count == 1
