import pytest
from fastapi import HTTPException

from app.auth import audit_logger
from app.api.auth import me
from app.api.ask import ask
from app.core.schemas import AskRequest


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
