import importlib

from fastapi.testclient import TestClient

import apps.api.main as main


def test_bearer_token(monkeypatch):
    monkeypatch.setenv("AUTH_REQUIRED", "true")
    monkeypatch.setenv("AUTH_TOKEN", "secret")
    importlib.reload(main)
    client = TestClient(main.app)
    payload = {"workorder": "WO-1"}
    resp_ok = client.post(
        "/schedule", json=payload, headers={"Authorization": "Bearer secret"}
    )
    assert resp_ok.status_code == 200
    resp_fail = client.post("/schedule", json=payload)
    assert resp_fail.status_code == 401
    assert resp_fail.headers["X-Env"] == main.ENV_BADGE
    resp_public = client.get("/healthz")
    assert resp_public.status_code == 200
    monkeypatch.delenv("AUTH_REQUIRED", raising=False)
    monkeypatch.delenv("AUTH_TOKEN", raising=False)
    importlib.reload(main)
