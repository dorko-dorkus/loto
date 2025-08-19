from fastapi.testclient import TestClient

from apps.api.main import RULE_PACK_HASH, app
from loto.integrations.stores_adapter import DemoStoresAdapter


def test_schedule_endpoint():
    client = TestClient(app)
    payload = {"workorder": "WO-1"}
    res = client.post("/schedule", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "schedule" in data
    assert len(data["schedule"]) > 0
    first = data["schedule"][0]
    assert {"date", "p10", "p50", "p90", "price", "hats"} <= first.keys()
    assert data["seed"] == "0"
    assert data["blocked_by_parts"] is False
    assert data["rulepack_sha256"] == RULE_PACK_HASH


def test_schedule_inventory_gating():
    client = TestClient(app)
    original = DemoStoresAdapter._INVENTORY["P-200"]["available"]
    try:
        DemoStoresAdapter._INVENTORY["P-200"]["available"] = 0
        res = client.post("/schedule", json={"workorder": "WO-1"})
        assert res.status_code == 200
        data = res.json()
        assert data["blocked_by_parts"] is True
        assert data["schedule"] == []
        assert data["rulepack_sha256"] == RULE_PACK_HASH
    finally:
        DemoStoresAdapter._INVENTORY["P-200"]["available"] = original


def test_schedule_inventory_gating_strict():
    client = TestClient(app)
    original = DemoStoresAdapter._INVENTORY["P-200"]["available"]
    try:
        DemoStoresAdapter._INVENTORY["P-200"]["available"] = 0
        res = client.post("/schedule?strict=true", json={"workorder": "WO-1"})
        assert res.status_code == 409
        data = res.json()
        assert data["blocked_by_parts"] is True
        assert data["missing_parts"] == [{"item_id": "P-200", "quantity": 1}]
    finally:
        DemoStoresAdapter._INVENTORY["P-200"]["available"] = original
