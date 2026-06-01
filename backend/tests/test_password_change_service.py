import pytest

from app.auth import audit_logger, password_change_service
from app.auth.password_change_service import AuthPasswordChangeError, AuthPasswordChangeService
from app.auth.password_service import hash_password
from app.core.schemas import AuthChangePasswordRequest, AuthContext


class FakeSettings:
    auth_min_password_length = 8


@pytest.fixture(autouse=True)
def disable_audit_db(monkeypatch):
    monkeypatch.setattr(audit_logger, "execute", lambda query, params: None)


def test_change_password_updates_hash_and_revokes_other_sessions(monkeypatch):
    executed: list[dict] = []
    revoked: list[tuple[str, str | None]] = []
    monkeypatch.setattr(password_change_service, "get_settings", lambda: FakeSettings())
    monkeypatch.setattr(
        password_change_service,
        "fetch_one",
        lambda query, params: {
            "id": params["account_id"],
            "password_hash": hash_password("old-password", salt="test-salt"),
        },
    )
    monkeypatch.setattr(
        password_change_service,
        "execute",
        lambda query, params: executed.append(params),
    )
    monkeypatch.setattr(
        password_change_service.AuthSessionService,
        "revoke_other_sessions",
        lambda self, account_id, keep_session_id: revoked.append((account_id, keep_session_id)),
    )

    AuthPasswordChangeService().change_password(
        AuthContext(
            account_id="account-1",
            session_id="session-1",
            role="patient",
        ),
        AuthChangePasswordRequest(
            current_password="old-password",
            new_password="new-password",
        ),
    )

    assert executed
    assert executed[0]["account_id"] == "account-1"
    assert executed[0]["password_hash"] != "old-password"
    assert revoked == [("account-1", "session-1")]


def test_change_password_rejects_wrong_current_password(monkeypatch):
    monkeypatch.setattr(password_change_service, "get_settings", lambda: FakeSettings())
    monkeypatch.setattr(
        password_change_service,
        "fetch_one",
        lambda query, params: {
            "id": params["account_id"],
            "password_hash": hash_password("old-password", salt="test-salt"),
        },
    )

    with pytest.raises(AuthPasswordChangeError, match="incorrect"):
        AuthPasswordChangeService().change_password(
            AuthContext(
                account_id="account-1",
                session_id="session-1",
                role="patient",
            ),
            AuthChangePasswordRequest(
                current_password="wrong-password",
                new_password="new-password",
            ),
        )
