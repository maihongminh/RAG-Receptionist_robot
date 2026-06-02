import pytest
from fastapi import HTTPException

from app.auth import audit_logger
from app.api import auth as auth_api
from app.api.auth import me
from app.api.ask import ask
from app.core.schemas import (
    AuthAdminAccountSummary,
    AuthPasswordResetCompleteRequest,
    AuthPasswordResetRequest,
    AskRequest,
)


def test_auth_me_audits_invalid_token(monkeypatch):
    calls: list[dict] = []
    monkeypatch.setattr(
        audit_logger,
        "execute",
        lambda query, params: calls.append(params),
    )
    with pytest.raises(HTTPException) as exc_info:
        me(authorization="Bearer invalid")

    assert exc_info.value.status_code == 401
    assert calls
    assert calls[0]["event_type"] == "token_rejected"
    assert calls[0]["metadata"]


def test_ask_audits_invalid_token(monkeypatch):
    calls: list[dict] = []
    monkeypatch.setattr(
        audit_logger,
        "execute",
        lambda query, params: calls.append(params),
    )
    with pytest.raises(HTTPException) as exc_info:
        ask(
            AskRequest(question="tôi có lịch hẹn nào không", domain="clinic"),
            authorization="Bearer invalid",
        )

    assert exc_info.value.status_code == 401
    assert calls
    assert calls[0]["event_type"] == "token_rejected"
    assert calls[0]["metadata"]


def test_password_reset_request_does_not_expose_token_by_default(monkeypatch):
    class FakeSettings:
        auth_password_reset_expose_token = False

    monkeypatch.setattr(auth_api, "get_settings", lambda: FakeSettings())
    monkeypatch.setattr(
        auth_api.AuthPasswordResetService,
        "request_reset",
        lambda self, email: "reset-token",
    )

    response = auth_api.request_password_reset(AuthPasswordResetRequest(email="patient.demo@robo.local"))

    assert response.ok is True
    assert response.reset_token is None


def test_password_reset_request_can_expose_token_for_local_dev(monkeypatch):
    class FakeSettings:
        auth_password_reset_expose_token = True

    monkeypatch.setattr(auth_api, "get_settings", lambda: FakeSettings())
    monkeypatch.setattr(
        auth_api.AuthPasswordResetService,
        "request_reset",
        lambda self, email: "reset-token",
    )

    response = auth_api.request_password_reset(AuthPasswordResetRequest(email="patient.demo@robo.local"))

    assert response.ok is True
    assert response.reset_token == "reset-token"


def test_password_reset_complete_returns_bad_request_on_invalid_token(monkeypatch):
    def fail_complete(self, reset_token, new_password):
        raise auth_api.AuthPasswordResetError("Invalid or expired reset token.")

    monkeypatch.setattr(auth_api.AuthPasswordResetService, "complete_reset", fail_complete)

    with pytest.raises(HTTPException) as exc_info:
        auth_api.complete_password_reset(
            AuthPasswordResetCompleteRequest(reset_token="bad-token", new_password="new-password")
        )

    assert exc_info.value.status_code == 400


def test_admin_accounts_rejects_non_admin(monkeypatch):
    monkeypatch.setattr(
        auth_api,
        "_auth_from_bearer",
        lambda authorization: (
            "token",
            auth_api.AuthContext(role="patient", patient_id="patient-1"),
        ),
    )

    with pytest.raises(HTTPException) as exc_info:
        auth_api.list_admin_accounts(authorization="Bearer token")

    assert exc_info.value.status_code == 403


def test_admin_accounts_returns_scoped_rows(monkeypatch):
    monkeypatch.setattr(
        auth_api,
        "_auth_from_bearer",
        lambda authorization: (
            "token",
            auth_api.AuthContext(role="clinic_admin", clinic_id="clinic-1"),
        ),
    )
    monkeypatch.setattr(
        auth_api.AuthAdminService,
        "list_accounts",
        lambda self, auth, query, limit: [
            AuthAdminAccountSummary(
                id="account-1",
                email="patient.demo@robo.local",
                status="active",
                roles=["patient"],
                clinic_ids=["clinic-1"],
            )
        ],
    )

    response = auth_api.list_admin_accounts(query="patient", authorization="Bearer token")

    assert response.accounts[0].email == "patient.demo@robo.local"
