import importlib

from fastapi.testclient import TestClient

import apps.api.main as main
from loto.integrations.stores_adapter import DemoStoresAdapter


def _client():
    importlib.reload(main)
    return TestClient(main.app)


def test_workorder_blocked_by_parts(monkeypatch):
    client = _client()
    original = DemoStoresAdapter._INVENTORY["P-200"]["reorder_point"]
    try:
        DemoStoresAdapter._INVENTORY["P-200"]["reorder_point"] = 2
        res = client.get("/workorders/WO-1")
        assert res.status_code == 200
        assert res.json()["blocked_by_parts"] is True
    finally:
        DemoStoresAdapter._INVENTORY["P-200"]["reorder_point"] = original


def test_workorder_not_blocked(monkeypatch):
    client = _client()
    res = client.get("/workorders/WO-1")
    assert res.status_code == 200
    assert res.json()["blocked_by_parts"] is False
