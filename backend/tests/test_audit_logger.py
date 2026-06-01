from app.auth import audit_logger
from app.auth.audit_logger import AuditLogger
from app.auth.permissions import PermissionDecision
from app.core.request_context import set_request_context
from app.core.schemas import AuthContext, Intent, ToolResult


def test_audit_logger_writes_auth_event(monkeypatch):
    calls: list[dict] = []
    monkeypatch.setattr(
        audit_logger,
        "execute",
        lambda query, params: calls.append(params),
    )

    AuditLogger().log_auth_event(
        event_type="login_success",
        account_id="account-1",
        session_id="session-1",
        user_id="user-1",
        role="patient",
        clinic_id="clinic-1",
    )

    assert calls
    assert calls[0]["event_type"] == "login_success"
    assert calls[0]["account_id"] == "account-1"
    assert calls[0]["session_id"] == "session-1"


def test_audit_logger_includes_request_context(monkeypatch):
    calls: list[dict] = []
    monkeypatch.setattr(
        audit_logger,
        "execute",
        lambda query, params: calls.append(params),
    )
    set_request_context("request-1", started_at=0.0)

    AuditLogger().log_auth_event(event_type="login_failed", reason="invalid_password")

    assert calls
    assert calls[0]["request_id"] == "request-1"
    assert isinstance(calls[0]["latency_ms"], float)


def test_audit_logger_writes_policy_decision(monkeypatch):
    calls: list[dict] = []
    monkeypatch.setattr(
        audit_logger,
        "execute",
        lambda query, params: calls.append(params),
    )

    AuditLogger().log_policy_decision(
        auth=AuthContext(
            account_id="account-1",
            session_id="session-1",
            role="patient",
            patient_id="patient-1",
            clinic_id="clinic-1",
        ),
        intent=Intent(
            intent="appointment_lookup",
            requires_auth=True,
            data_source="auth",
        ),
        decision=PermissionDecision(allowed=True, reason="allowed"),
    )

    assert calls
    assert calls[0]["event_type"] == "policy_decision"
    assert calls[0]["allowed"] is True
    assert calls[0]["intent"] == "appointment_lookup"


def test_audit_logger_writes_tool_result(monkeypatch):
    calls: list[dict] = []
    monkeypatch.setattr(
        audit_logger,
        "execute",
        lambda query, params: calls.append(params),
    )

    AuditLogger().log_tool_result(
        auth=AuthContext(
            account_id="account-1",
            session_id="session-1",
            role="doctor",
            doctor_id="doctor-1",
            clinic_id="clinic-1",
        ),
        intent=Intent(
            intent="appointment_lookup",
            requires_auth=True,
            data_source="auth",
        ),
        result=ToolResult(
            tool_name="clinic.lookup_private_data",
            source="robo_app.appointments",
            rows=[{"id": "appointment-1"}],
        ),
    )

    assert calls
    assert calls[0]["event_type"] == "tool_result"
    assert calls[0]["tool_name"] == "clinic.lookup_private_data"
    assert calls[0]["row_count"] == 1
