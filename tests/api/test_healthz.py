import importlib

from fastapi.testclient import TestClient


def test_healthz_reports_rate_limit(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_CAPACITY", "5")
    monkeypatch.setenv("RATE_LIMIT_INTERVAL", "30")
    import apps.api.main as main

    importlib.reload(main)

    client = TestClient(main.app)
    res = client.get("/healthz")
    assert res.status_code == 200
    data = res.json()
    assert data["rate_limit"]["capacity"] == 5
    assert data["rate_limit"]["interval"] == 30.0
    for path in main.RATE_LIMIT_PATHS:
        assert path in data["rate_limit"]["counters"]
    assert res.headers["X-Env"] == main.ENV_BADGE

    monkeypatch.delenv("RATE_LIMIT_CAPACITY", raising=False)
    monkeypatch.delenv("RATE_LIMIT_INTERVAL", raising=False)
    importlib.reload(main)
