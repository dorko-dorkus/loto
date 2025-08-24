from __future__ import annotations

from dataclasses import dataclass

from fastapi.testclient import TestClient

from apps.api.main import app
from loto.integrations.stores_adapter import DemoStoresAdapter
from loto.inventory import (
    InventoryRecord,
    InventoryStatus,
    Reservation,
    StockItem,
    check_wo_parts_required,
    ingest_inventory,
)
from tests.job_utils import wait_for_job


@dataclass
class WorkOrder:
    reservations: list[Reservation]


def test_missing_or_low_stock_blocks_work_order():
    work_order = WorkOrder(
        reservations=[
            Reservation(item_id="valve", quantity=2),
            Reservation(item_id="gasket", quantity=1),
        ]
    )

    stock = {"valve": StockItem(item_id="valve", quantity=1)}

    status = check_wo_parts_required(work_order, stock.get)

    assert isinstance(status, InventoryStatus)
    assert status.blocked
    assert {r.item_id for r in status.missing} == {"valve", "gasket"}


def test_adequate_stock_marks_work_order_ready():
    work_order = WorkOrder(reservations=[Reservation(item_id="bolt", quantity=4)])

    stock = {"bolt": StockItem(item_id="bolt", quantity=10)}

    status = check_wo_parts_required(work_order, stock.get)

    assert status.ready
    assert not status.missing


def test_blueprint_inventory_gating(monkeypatch):
    monkeypatch.setattr(
        "loto.service.blueprints.validate_fk_integrity", lambda *a, **k: None
    )
    client = TestClient(app)
    original = DemoStoresAdapter._INVENTORY["P-200"]["available"]
    try:
        DemoStoresAdapter._INVENTORY["P-200"]["available"] = 0
        res = client.post("/blueprint", json={"workorder_id": "WO-1"})
        assert res.status_code == 202
        job = res.json()["job_id"]
        data = wait_for_job(client, job)["result"]
        assert data["blocked_by_parts"] is True

        DemoStoresAdapter._INVENTORY["P-200"]["available"] = 1
        res = client.post("/blueprint", json={"workorder_id": "WO-1"})
        assert res.status_code == 202
        job = res.json()["job_id"]
        data = wait_for_job(client, job)["result"]
        assert data["blocked_by_parts"] is False
    finally:
        DemoStoresAdapter._INVENTORY["P-200"]["available"] = original


def test_ingest_inventory_normalizes_units():
    records = [
        InventoryRecord(description="Bolt", unit="Each", qty_onhand=1, reorder_point=0),
        InventoryRecord(
            description="Pipe", unit="Metre", qty_onhand=1, reorder_point=0
        ),
        InventoryRecord(
            description="Sand", unit="Kilogram", qty_onhand=1, reorder_point=0
        ),
        InventoryRecord(
            description="Water", unit="Litre", qty_onhand=1, reorder_point=0
        ),
    ]
    normalised = ingest_inventory(records)
    assert [r.unit for r in normalised] == ["ea", "m", "kg", "L"]
