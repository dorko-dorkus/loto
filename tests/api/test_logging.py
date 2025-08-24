import json
import logging

from fastapi.testclient import TestClient

import apps.api.main as main
from loto.loggers import JsonFormatter


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
        res = client.post(
            "/schedule", json=payload, headers={"Authorization": "Bearer x"}
        )
    assert res.status_code == 200
    record = next(
        (r for r in caplog.records if r.getMessage() == "request complete"),
        None,
    )
    assert record is not None
    data = json.loads(JsonFormatter().format(record))
    assert data["msg"] == "request complete"
    assert data["level"] == "info"
    assert data["seed"] == 0
    assert data["request_id"]
    assert data["rule_hash"] == main.RULE_PACK_HASH
