from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from apps.api.main import app
from loto.constants import CHECKLIST_HAND_BACK, DOC_CATEGORY
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


def test_requires_maximo_wo_number() -> None:
    wo = {"permit_id": "PRM-X", "permit_verified": True, "maximo_wo": None}
    with pytest.raises(StatusValidationError):
        validate_status_change(wo, "SCHED", "INPRG")


def test_closeout_requires_permit_document() -> None:
    payload = {"status": "COMP", "currentStatus": "INPRG"}
    resp = client.post("/workorders/WO-4/status", json=payload)
    assert resp.status_code == 400
    assert (
        "Permit closeout requires permit document upload and checklist confirmation"
        in resp.text
    )


def test_closeout_requires_checklist_confirmation() -> None:
    wo = {
        "permit_id": "PRM-X",
        "permit_verified": True,
        "attachments": [{"category": DOC_CATEGORY}],
        "checklist": {CHECKLIST_HAND_BACK: False},
    }
    with pytest.raises(StatusValidationError):
        validate_status_change(wo, "INPRG", "COMP")


def test_closeout_allows_when_requirements_met() -> None:
    payload = {"status": "COMP", "currentStatus": "INPRG"}
    resp = client.post("/workorders/WO-2/status", json=payload)
    assert resp.status_code == 200
    assert resp.json()["status"] == "COMP"


def test_hold_requires_reason() -> None:
    payload = {"status": "HOLD", "currentStatus": "INPRG"}
    resp = client.post("/workorders/WO-2/status", json=payload)
    assert resp.status_code == 400
    assert "Hold reason is required" in resp.text


def test_hold_and_resume() -> None:
    payload = {
        "status": "HOLD",
        "currentStatus": "INPRG",
        "reason": "Awaiting parts",
    }
    resp = client.post("/workorders/WO-2/status", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "HOLD"
    assert body["holdReason"] == "Awaiting parts"

    payload = {"status": "INPRG", "currentStatus": "HOLD"}
    resp = client.post("/workorders/WO-2/status", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "INPRG"
    assert body.get("holdReason") is None
