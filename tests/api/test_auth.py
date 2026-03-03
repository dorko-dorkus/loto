import importlib

import jwt
from _pytest.monkeypatch import MonkeyPatch
from fastapi.testclient import TestClient

import apps.api.main as main


def _set_base_env(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("MAXIMO_BASE_URL", "https://example.maximo")
    monkeypatch.setenv("MAXIMO_APIKEY", "apikey")
    monkeypatch.setenv("OIDC_CLIENT_ID", "client")
    monkeypatch.setenv("OIDC_CLIENT_SECRET", "secret")
    monkeypatch.setenv("OIDC_ISSUER", "https://issuer.example")


def test_bearer_token(monkeypatch: MonkeyPatch) -> None:
    _set_base_env(monkeypatch)
    monkeypatch.setenv("AUTH_REQUIRED", "true")
    monkeypatch.setenv("JWT_SECRET", "secret")
    monkeypatch.setenv("AUTH_MODE", "")
    monkeypatch.delenv("OIDC_DISABLED", raising=False)
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


def test_schedule_dev_mode_without_oidc_discovery(monkeypatch: MonkeyPatch) -> None:
    _set_base_env(monkeypatch)
    monkeypatch.setenv("AUTH_MODE", "dev")
    monkeypatch.delenv("OIDC_DISABLED", raising=False)
    importlib.reload(main)

    monkeypatch.setattr(
        main,
        "authenticate_user",
        lambda *a, **kw: (_ for _ in ()).throw(
            AssertionError("OIDC auth should be bypassed in dev mode")
        ),
    )
    client = TestClient(main.app)
    res = client.post("/schedule", json={"workorder": "WO-1"})
    assert res.status_code == 202


def test_schedule_default_mode_non_planner_forbidden(monkeypatch: MonkeyPatch) -> None:
    _set_base_env(monkeypatch)
    monkeypatch.setenv("AUTH_MODE", "")
    monkeypatch.delenv("OIDC_DISABLED", raising=False)
    importlib.reload(main)

    client = TestClient(main.app)
    monkeypatch.setattr(
        main,
        "authenticate_user",
        lambda *_, **__: main.OIDCUser(
            iss="iss",
            sub="sub",
            aud="aud",
            exp=0,
            iat=0,
            roles=["viewer"],
        ),
    )

    res = client.post(
        "/schedule",
        json={"workorder": "WO-1"},
        headers={"Authorization": "Bearer x"},
    )
    assert res.status_code == 403
