import json
import logging

from fastapi.testclient import TestClient

import apps.api.main as main
from tests.job_utils import wait_for_job


def test_structured_logging(caplog, monkeypatch):
    client = TestClient(main.app)
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
    payload = {"workorder": "WO-99"}
    with caplog.at_level(logging.INFO):
        caplog.handler.setFormatter(logging.getLogger().handlers[0].formatter)
        res = client.post(
            "/schedule", json=payload, headers={"Authorization": "Bearer x"}
        )
    assert res.status_code == 202
    job = res.json()["job_id"]
    wait_for_job(client, job)
    lines = caplog.text.splitlines()
    data = next(
        json.loads(line)
        for line in lines
        if json.loads(line).get("msg") == "request complete"
    )
    assert data["msg"] == "request complete"
    assert data["level"] == "info"
    assert data["seed"] == 0
    assert data["request_id"]
    assert data["rule_hash"] == main.RULE_PACK_HASH
