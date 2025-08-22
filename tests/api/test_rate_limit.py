import importlib

from fastapi.testclient import TestClient

import apps.api.main as main


def test_rate_limit(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_CAPACITY", "2")
    monkeypatch.setenv("RATE_LIMIT_INTERVAL", "60")
    importlib.reload(main)
    client = TestClient(main.app)
    payload = {"workorder": "WO-1"}
    assert client.post("/schedule", json=payload).status_code == 200
    assert client.post("/schedule", json=payload).status_code == 200
    res = client.post("/schedule", json=payload)
    assert res.status_code == 429
    assert res.headers["X-Env"] == main.ENV_BADGE
    monkeypatch.setenv("RATE_LIMIT_CAPACITY", "10")
    monkeypatch.setenv("RATE_LIMIT_INTERVAL", "60")
    importlib.reload(main)
