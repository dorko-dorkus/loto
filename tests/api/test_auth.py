import importlib

import jwt
from fastapi.testclient import TestClient

import apps.api.main as main


def test_bearer_token(monkeypatch):
    monkeypatch.setenv("AUTH_REQUIRED", "true")
    monkeypatch.setenv("JWT_SECRET", "secret")
    importlib.reload(main)
    client = TestClient(main.app)
    payload = {"workorder": "WO-1"}
    token = jwt.encode({"sub": "tester"}, "secret", algorithm="HS256")
    monkeypatch.setattr(
        main,
        "authenticate_user",
        lambda *_, **__: main.OIDCUser(
            iss="iss",
            sub="sub",
            aud="aud",
            exp=0,
            iat=0,
            roles=["planner"],
        ),
    )
    resp_ok = client.post(
        "/schedule", json=payload, headers={"Authorization": f"Bearer {token}"}
    )
    assert resp_ok.status_code == 202
    resp_fail = client.post("/schedule", json=payload)
    assert resp_fail.status_code == 401
    assert resp_fail.headers["X-Env"] == main.ENV_BADGE
    resp_public = client.get("/healthz")
    assert resp_public.status_code == 200
    monkeypatch.setenv("AUTH_REQUIRED", "false")
    importlib.reload(main)
