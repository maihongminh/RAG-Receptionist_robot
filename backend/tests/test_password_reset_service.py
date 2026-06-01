import pytest

from app.auth import audit_logger, password_reset_service
from app.auth.password_reset_service import AuthPasswordResetError, AuthPasswordResetService


class FakeSettings:
    auth_password_reset_token_ttl_seconds = 900
    auth_min_password_length = 8


@pytest.fixture(autouse=True)
def disable_audit_db(monkeypatch):
    monkeypatch.setattr(audit_logger, "execute", lambda query, params: None)


def test_request_reset_creates_token_for_existing_account(monkeypatch):
    executed: list[dict] = []
    monkeypatch.setattr(password_reset_service, "get_settings", lambda: FakeSettings())
    monkeypatch.setattr(
        password_reset_service,
        "fetch_one",
        lambda query, params: {"id": "account-1"},
    )
    monkeypatch.setattr(
        password_reset_service,
        "execute",
        lambda query, params: executed.append(params),
    )
    monkeypatch.setattr(
        password_reset_service.AuthPasswordResetService,
        "_new_reset_token",
        lambda self: "reset-token-1",
    )

    reset_token = AuthPasswordResetService().request_reset("USER@example.test")

    assert reset_token == "reset-token-1"
    assert len(executed) == 2
    assert executed[0]["account_id"] == "account-1"
    assert executed[1]["account_id"] == "account-1"
    assert executed[1]["token_hash"] != "reset-token-1"


def test_complete_reset_updates_password_and_revokes_sessions(monkeypatch):
    executed: list[dict] = []
    revoked: list[tuple[str, str | None]] = []
    monkeypatch.setattr(password_reset_service, "get_settings", lambda: FakeSettings())
    monkeypatch.setattr(
        password_reset_service,
        "fetch_one",
        lambda query, params: {"id": "token-1", "account_id": "account-1"},
    )
    monkeypatch.setattr(
        password_reset_service,
        "execute",
        lambda query, params: executed.append(params),
    )
    monkeypatch.setattr(
        password_reset_service.AuthSessionService,
        "revoke_other_sessions",
        lambda self, account_id, keep_session_id: revoked.append((account_id, keep_session_id)),
    )

    AuthPasswordResetService().complete_reset("reset-token-1", "new-password")

    assert executed
    assert executed[0]["account_id"] == "account-1"
    assert executed[0]["password_hash"] != "new-password"
    assert revoked == [("account-1", None)]


def test_complete_reset_rejects_invalid_token(monkeypatch):
    monkeypatch.setattr(password_reset_service, "get_settings", lambda: FakeSettings())
    monkeypatch.setattr(password_reset_service, "fetch_one", lambda query, params: None)

    with pytest.raises(AuthPasswordResetError, match="Invalid or expired"):
        AuthPasswordResetService().complete_reset("bad-token", "new-password")
