from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from apps.api.main import app
from loto.permits import StatusValidationError, validate_status_change

client = TestClient(app)


def test_parent_workorder_requires_permit() -> None:
    payload = {"status": "INPRG", "currentStatus": "SCHED"}
    resp = client.post("/workorders/WO-1/status", json=payload)
    assert resp.status_code == 400
    assert "Permit must be recorded and verified before work can start." in resp.text


def test_parent_workorder_allows_when_permit_verified() -> None:
    payload = {"status": "INPRG", "currentStatus": "SCHED"}
    resp = client.post("/workorders/WO-2/status", json=payload)
    assert resp.status_code == 200
    assert resp.json()["status"] == "INPRG"


def test_child_task_validation() -> None:
    child = {"permit_id": None, "permit_verified": False}
    with pytest.raises(StatusValidationError):
        validate_status_change(child, "SCHED", "INPRG")
