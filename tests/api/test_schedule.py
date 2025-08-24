import importlib

from fastapi.testclient import TestClient

import apps.api.main as main
from loto.integrations.stores_adapter import DemoStoresAdapter
from tests.job_utils import wait_for_job


def _planner():
    return main.OIDCUser(
        iss="iss", sub="sub", aud="aud", exp=0, iat=0, roles=["planner"]
    )


def test_schedule_endpoint(monkeypatch):
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
    assert data["seed"] == "0"
    assert data["blocked_by_parts"] is False
    assert data["rulepack_sha256"] == main.RULE_PACK_HASH


def test_schedule_inventory_gating(monkeypatch):
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
        assert data["blocked_by_parts"] is True
        assert data["schedule"] == []
        assert data["rulepack_sha256"] == main.RULE_PACK_HASH
    finally:
        DemoStoresAdapter._INVENTORY["P-200"]["reorder_point"] = original


def test_schedule_inventory_gating_strict(monkeypatch):
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
        assert job_data["result"]["missing_parts"] == [
            {"item_id": "P-200", "quantity": 1}
        ]
    finally:
        DemoStoresAdapter._INVENTORY["P-200"]["reorder_point"] = original
