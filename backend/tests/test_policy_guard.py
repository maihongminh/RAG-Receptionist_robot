from app.auth.policy_guard import PolicyGuard
from app.core.schemas import AuthContext, Intent


def test_guest_can_access_public_tool():
    intent = Intent(
        domain="clinic",
        intent="service_price",
        data_source="sql",
    )

    decision = PolicyGuard().authorize(intent, AuthContext(role="guest"))

    assert decision.allowed is True


def test_guest_cannot_access_personal_data():
    intent = Intent(
        domain="clinic",
        intent="personal_data",
        requires_auth=True,
        data_source="auth",
    )

    decision = PolicyGuard().authorize(intent, AuthContext(role="guest"))

    assert decision.allowed is False
    assert "Authentication" in decision.reason


def test_patient_private_data_requires_patient_id():
    intent = Intent(
        domain="clinic",
        intent="personal_data",
        requires_auth=True,
        data_source="auth",
    )

    decision = PolicyGuard().authorize(intent, AuthContext(role="patient"))

    assert decision.allowed is False
    assert "patient_id" in decision.reason


def test_patient_private_data_allowed_with_patient_id():
    intent = Intent(
        domain="clinic",
        intent="personal_data",
        requires_auth=True,
        data_source="auth",
    )

    decision = PolicyGuard().authorize(
        intent,
        AuthContext(role="patient", patient_id="patient-1"),
    )

    assert decision.allowed is True


def test_unknown_role_falls_back_to_guest_permissions():
    intent = Intent(
        domain="clinic",
        intent="personal_data",
        requires_auth=True,
        data_source="auth",
    )

    decision = PolicyGuard().authorize(intent, AuthContext(role="unknown"))

    assert decision.allowed is False


def test_guest_can_access_public_knowledge_search():
    intent = Intent(
        domain="clinic",
        intent="knowledge_search",
        data_source="rag",
    )

    decision = PolicyGuard().authorize(intent, AuthContext(role="guest"))

    assert decision.allowed is True


def test_guest_can_access_booking_request_placeholder():
    intent = Intent(
        domain="clinic",
        intent="appointment_booking",
        data_source="none",
    )

    decision = PolicyGuard().authorize(intent, AuthContext(role="guest"))

    assert decision.allowed is True


def test_guest_cannot_access_lab_result_lookup():
    intent = Intent(
        domain="clinic",
        intent="lab_result_lookup",
        requires_auth=True,
        data_source="auth",
    )

    decision = PolicyGuard().authorize(intent, AuthContext(role="guest"))

    assert decision.allowed is False


def test_patient_lab_result_lookup_allowed_with_patient_id():
    intent = Intent(
        domain="clinic",
        intent="lab_result_lookup",
        requires_auth=True,
        data_source="auth",
    )

    decision = PolicyGuard().authorize(
        intent,
        AuthContext(role="patient", patient_id="patient-1"),
    )

    assert decision.allowed is True


def test_patient_profile_summary_allowed_with_patient_id():
    intent = Intent(
        domain="clinic",
        intent="patient_profile_summary",
        requires_auth=True,
        data_source="auth",
    )

    decision = PolicyGuard().authorize(
        intent,
        AuthContext(role="patient", patient_id="patient-1"),
    )

    assert decision.allowed is True


def test_doctor_cannot_access_patient_profile_summary_without_dedicated_scope():
    intent = Intent(
        domain="clinic",
        intent="patient_profile_summary",
        requires_auth=True,
        data_source="auth",
    )

    decision = PolicyGuard().authorize(
        intent,
        AuthContext(role="doctor", doctor_id="doctor-1"),
    )

    assert decision.allowed is False
