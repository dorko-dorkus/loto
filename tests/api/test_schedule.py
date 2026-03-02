import importlib

import pytest
from _pytest.monkeypatch import MonkeyPatch
from fastapi.testclient import TestClient

import apps.api.main as main
from apps.api.schemas import ScheduleResponse
from loto.integrations.stores_adapter import DemoStoresAdapter
from tests.job_utils import wait_for_job


def _planner() -> main.OIDCUser:
    return main.OIDCUser(
        iss="iss", sub="sub", aud="aud", exp=0, iat=0, roles=["planner"]
    )


def test_schedule_endpoint(monkeypatch: MonkeyPatch) -> None:
    importlib.reload(main)
    client = TestClient(main.app)
    monkeypatch.setattr(main, "authenticate_user", lambda *a, **kw: _planner())
    payload = {"workorder": "WO-1"}
    res = client.post("/schedule", json=payload, headers={"Authorization": "Bearer x"})
    assert res.status_code == 202
    job = res.json()["job_id"]
    data = wait_for_job(client, job)["result"]
    assert "schedule" in data
    assert len(data["schedule"]) > 0
    first = data["schedule"][0]
    assert {"date", "p10", "p50", "p90", "price", "hats"} <= first.keys()
    assert data["status"] == "feasible"
    assert data["provenance"]["plan_id"] == "WO-1"
    assert data["provenance"]["random_seed"] == "0"
    assert (
        data["p10"] is not None and data["p50"] is not None and data["p90"] is not None
    )
    assert data["expected_makespan"] is not None
    assert data["rulepack_sha256"] == main.RULE_PACK_HASH


def test_schedule_inventory_gating(monkeypatch: MonkeyPatch) -> None:
    importlib.reload(main)
    client = TestClient(main.app)
    monkeypatch.setattr(main, "authenticate_user", lambda *a, **kw: _planner())
    original = DemoStoresAdapter._INVENTORY["P-200"]["reorder_point"]
    try:
        DemoStoresAdapter._INVENTORY["P-200"]["reorder_point"] = 2
        res = client.post(
            "/schedule",
            json={"workorder": "WO-1"},
            headers={"Authorization": "Bearer x"},
        )
        assert res.status_code == 202
        job = res.json()["job_id"]
        data = wait_for_job(client, job)["result"]
        assert data["status"] == "blocked_by_parts"
        assert data["schedule"] == []
        assert data["missing_parts"] == [{"item_id": "P-200", "quantity": 1}]
        assert data["gating_reason"] == "missing required parts"
        assert data["rulepack_sha256"] == main.RULE_PACK_HASH
    finally:
        DemoStoresAdapter._INVENTORY["P-200"]["reorder_point"] = original


def test_schedule_inventory_gating_strict(monkeypatch: MonkeyPatch) -> None:
    importlib.reload(main)
    client = TestClient(main.app)
    monkeypatch.setattr(main, "authenticate_user", lambda *a, **kw: _planner())
    original = DemoStoresAdapter._INVENTORY["P-200"]["reorder_point"]
    try:
        DemoStoresAdapter._INVENTORY["P-200"]["reorder_point"] = 2
        res = client.post(
            "/schedule?strict=true",
            json={"workorder": "WO-1"},
            headers={"Authorization": "Bearer x"},
        )
        assert res.status_code == 202
        job = res.json()["job_id"]
        job_data = wait_for_job(client, job)
        assert job_data["status"] == "failed"
        assert job_data["result"]["status"] == "failed"
        assert job_data["result"]["error_code"] == "PARTS_BLOCKED_STRICT"
        assert job_data["result"]["provenance"]["plan_id"] == "WO-1"
        assert job_data["result"]["missing_parts"] == [
            {"item_id": "P-200", "quantity": 1}
        ]
    finally:
        DemoStoresAdapter._INVENTORY["P-200"]["reorder_point"] = original


def test_schedule_schema_requires_provenance_and_status_contract() -> None:
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        ScheduleResponse.model_validate(
            {
                "status": "feasible",
                "provenance": {"plan_id": "WO-1"},
                "schedule": [],
                "rulepack_sha256": "abc",
            }
        )
