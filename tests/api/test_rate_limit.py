import importlib

from fastapi.testclient import TestClient

import apps.api.main as main


def test_rate_limit(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_CAPACITY", "2")
    monkeypatch.setenv("RATE_LIMIT_INTERVAL", "60")
    importlib.reload(main)
    client = TestClient(main.app)

    assert client.get("/version").status_code == 200
    assert client.get("/version").status_code == 200
    res = client.get("/version")
    assert res.status_code == 429
    assert res.headers["X-Env"] == main.ENV_BADGE
    assert "Retry-After" in res.headers

    importlib.reload(main)
    client = TestClient(main.app)
    payload = {"workorder": "WO-1"}
    monkeypatch.setattr(
        main,
        "authenticate_user",
        lambda *a, **kw: main.OIDCUser(
            iss="iss",
            sub="sub",
            aud="aud",
            exp=0,
            iat=0,
            roles=["planner"],
        ),
    )
    res = client.post("/schedule", json=payload, headers={"Authorization": "Bearer x"})
    assert res.status_code == 202
    res = client.post("/schedule", json=payload, headers={"Authorization": "Bearer x"})
    assert res.status_code == 202
    res = client.post("/schedule", json=payload, headers={"Authorization": "Bearer x"})
    assert res.status_code == 429
    assert res.headers["X-Env"] == main.ENV_BADGE
    assert "Retry-After" in res.headers

    monkeypatch.setenv("RATE_LIMIT_CAPACITY", "100000")
    monkeypatch.setenv("RATE_LIMIT_INTERVAL", "60")
    importlib.reload(main)
