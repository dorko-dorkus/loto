import importlib

from fastapi.testclient import TestClient

import apps.api.main as main
from tests.job_utils import wait_for_job


def _override(email: str):
    def _inner(*args, **kwargs):
        return main.OIDCUser(
            iss="iss",
            sub="sub",
            aud="aud",
            exp=0,
            iat=0,
            email=email,
        )

    return _inner


def test_schedule_requires_auth():
    importlib.reload(main)
    client = TestClient(main.app)
    res = client.post("/schedule", json={"workorder": "WO-1"})
    assert res.status_code == 401


def test_viewer_forbidden_and_role(monkeypatch):
    monkeypatch.setenv("PLANNER_EMAIL_DOMAIN", "planner.test")
    importlib.reload(main)
    client = TestClient(main.app)
    monkeypatch.setattr(main, "authenticate_user", _override("user@viewer.test"))
    res = client.post(
        "/schedule", json={"workorder": "WO-1"}, headers={"Authorization": "Bearer x"}
    )
    assert res.status_code == 403
    res = client.get("/healthz", headers={"Authorization": "Bearer x"})
    assert res.status_code == 200
    assert res.json()["role"] == "viewer"


def test_planner_allowed(monkeypatch):
    monkeypatch.setenv("PLANNER_EMAIL_DOMAIN", "planner.test")
    importlib.reload(main)
    client = TestClient(main.app)
    monkeypatch.setattr(main, "authenticate_user", _override("user@planner.test"))
    res = client.post(
        "/schedule", json={"workorder": "WO-1"}, headers={"Authorization": "Bearer x"}
    )
    assert res.status_code == 202
    job = res.json()["job_id"]
    wait_for_job(client, job)
    res = client.get("/healthz", headers={"Authorization": "Bearer x"})
    assert res.json()["role"] == "planner"
