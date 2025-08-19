import json
import logging

from fastapi.testclient import TestClient

from apps.api.main import RULE_PACK_HASH, app
from loto.loggers import JsonFormatter


def test_structured_logging(caplog):
    client = TestClient(app)
    payload = {"workorder": "WO-99"}
    with caplog.at_level(logging.INFO):
        client.post("/schedule", json=payload)
    record = next(r for r in caplog.records if r.getMessage() == "request complete")
    data = json.loads(JsonFormatter().format(record))
    assert data["msg"] == "request complete"
    assert data["level"] == "info"
    assert data["seed"] == 0
    assert data["request_id"]
    assert data["rule_hash"] == RULE_PACK_HASH
