import json
import logging

from fastapi.testclient import TestClient

from apps.api.main import app
from loto.loggers import JsonFormatter


def test_structured_logging(caplog):
    client = TestClient(app)
    payload = {
        "tasks": {"a": {"duration": 1}},
        "runs": 1,
        "seed": 99,
        "power_curve": [[0, 1], [1, 1]],
        "price_curve": [[0, 1], [1, 1]],
    }
    with caplog.at_level(logging.INFO):
        client.post("/schedule", json=payload)
    record = next(r for r in caplog.records if r.getMessage() == "request complete")
    data = json.loads(JsonFormatter().format(record))
    assert data["msg"] == "request complete"
    assert data["level"] == "info"
    assert data["seed"] == 99
    assert data["request_id"]
    assert "rule_hash" in data
