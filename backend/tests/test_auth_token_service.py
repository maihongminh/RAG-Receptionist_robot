import pytest

from app.auth import login_service, token_service
from app.auth.auth_context import AuthContextResolver
from app.auth.login_service import AuthLoginError, AuthLoginService
from app.auth.password_service import hash_password, verify_password
from app.auth.token_service import AuthTokenError, AuthTokenService
from app.core.schemas import AskRequest, AuthContext, AuthLoginRequest


class FakeSettings:
    auth_token_secret = "test-secret"
    auth_token_ttl_seconds = 3600


class ExpiredSettings:
    auth_token_secret = "test-secret"
    auth_token_ttl_seconds = -1


def test_auth_token_round_trip(monkeypatch):
    monkeypatch.setattr(token_service, "get_settings", lambda: FakeSettings())
    service = AuthTokenService()

    token, expires_in = service.issue(AuthContext(role="patient", patient_id="patient-1"))
    auth = service.verify(token)

    assert expires_in == 3600
    assert auth.role == "patient"
    assert auth.patient_id == "patient-1"


def test_auth_token_rejects_expired_token(monkeypatch):
    monkeypatch.setattr(token_service, "get_settings", lambda: ExpiredSettings())
    service = AuthTokenService()

    token, _ = service.issue(AuthContext(role="patient", patient_id="patient-1"))

    with pytest.raises(AuthTokenError):
        service.verify(token)


def test_login_service_validates_patient_and_issues_token(monkeypatch):
    monkeypatch.setattr(token_service, "get_settings", lambda: FakeSettings())
    monkeypatch.setattr(
        login_service,
        "fetch_one",
        lambda query, params: {"id": params["patient_id"], "clinic_id": "clinic-1"},
    )

    response = AuthLoginService().login(
        AuthLoginRequest(role="patient", patient_id="patient-1")
    )

    assert response.token_type == "bearer"
    assert response.auth.role == "patient"
    assert response.auth.patient_id == "patient-1"
    assert response.auth.clinic_id == "clinic-1"
    assert response.access_token


def test_login_service_validates_email_password_account(monkeypatch):
    monkeypatch.setattr(token_service, "get_settings", lambda: FakeSettings())
    password_hash = hash_password("demo123", salt="test-salt")
    monkeypatch.setattr(
        login_service,
        "fetch_one",
        lambda query, params: {
            "id": "account-1",
            "email": params["email"],
            "password_hash": password_hash,
            "role": "doctor",
            "user_id": "user-1",
            "clinic_id": "clinic-1",
            "patient_id": None,
            "doctor_id": "doctor-1",
            "staff_id": "doctor-1",
            "is_active": True,
        },
    )

    response = AuthLoginService().login(
        AuthLoginRequest(email="doctor@example.test", password="demo123")
    )

    assert response.auth.role == "doctor"
    assert response.auth.doctor_id == "doctor-1"
    assert response.auth.clinic_id == "clinic-1"
    assert response.access_token


def test_login_service_rejects_invalid_password(monkeypatch):
    monkeypatch.setattr(
        login_service,
        "fetch_one",
        lambda query, params: {
            "id": "account-1",
            "email": params["email"],
            "password_hash": hash_password("demo123", salt="test-salt"),
            "role": "patient",
            "user_id": "user-1",
            "clinic_id": "clinic-1",
            "patient_id": "patient-1",
            "doctor_id": None,
            "staff_id": None,
            "is_active": True,
        },
    )

    with pytest.raises(AuthLoginError):
        AuthLoginService().login(
            AuthLoginRequest(email="patient@example.test", password="wrong")
        )


def test_password_hash_round_trip():
    password_hash = hash_password("demo123", salt="test-salt")

    assert verify_password("demo123", password_hash)
    assert not verify_password("wrong", password_hash)


def test_login_service_rejects_missing_patient_id():
    with pytest.raises(AuthLoginError):
        AuthLoginService().login(AuthLoginRequest(role="patient"))


def test_auth_context_resolver_prefers_bearer_token(monkeypatch):
    monkeypatch.setattr(token_service, "get_settings", lambda: FakeSettings())
    token, _ = AuthTokenService().issue(AuthContext(role="doctor", doctor_id="doctor-1"))

    auth = AuthContextResolver().resolve(
        AskRequest(
            question="tôi có lịch hẹn nào không",
            auth=AuthContext(role="patient", patient_id="patient-1"),
        ),
        authorization=f"Bearer {token}",
    )

    assert auth.role == "doctor"
    assert auth.doctor_id == "doctor-1"
