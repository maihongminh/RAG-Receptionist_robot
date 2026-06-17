import json

from app import main


def test_health_returns_ok():
    assert main.health() == {"status": "ok"}


def test_ready_returns_200_when_dependencies_are_ready(monkeypatch):
    monkeypatch.setattr(
        main,
        "get_readiness_status",
        lambda: (True, {"status": "ready", "checks": {"database": {"ok": True}}}),
    )

    response = main.ready()

    assert response.status_code == 200
    assert json.loads(response.body)["status"] == "ready"


def test_ready_returns_503_when_dependency_fails(monkeypatch):
    monkeypatch.setattr(
        main,
        "get_readiness_status",
        lambda: (
            False,
            {
                "status": "not_ready",
                "checks": {"database": {"ok": False, "error": "connection failed"}},
            },
        ),
    )

    response = main.ready()

    assert response.status_code == 503
    body = json.loads(response.body)
    assert body["status"] == "not_ready"
    assert body["checks"]["database"]["ok"] is False
