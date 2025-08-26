from __future__ import annotations

import importlib

import pytest
from fastapi.testclient import TestClient

import apps.api.workorder_endpoints as work_endpoints
import loto.constants as constants
from apps.api import main as main_module
from apps.api.demo_data import demo_data


class MissingReceiverHatsAdapter:
    def has_required(
        self, hats_ids: list[str], permit_types: list[str]
    ) -> tuple[bool, list[str]]:
        return False, ["Permit receiver missing"]


class ExpiredReceiverHatsAdapter:
    def has_required(
        self, hats_ids: list[str], permit_types: list[str]
    ) -> tuple[bool, list[dict[str, str]]]:
        return False, [
            {
                "receiverId": hats_ids[0] if hats_ids else "102334",
                "requirement": "Eclipse",
                "expiry": "2025-07-30",
            }
        ]


class OKHatsAdapter:
    def has_required(
        self, hats_ids: list[str], permit_types: list[str]
    ) -> tuple[bool, list[str]]:
        return True, []


class StubPermitAdapter:
    def __init__(self, permit_types: list[str]) -> None:
        self.permit_types = permit_types

    def fetch_permit(self, workorder_id: str) -> dict[str, list[str] | str]:
        return {"permitTypes": self.permit_types, "status": "active"}


def setup_client(monkeypatch: pytest.MonkeyPatch, hats_adapter: object) -> TestClient:
    monkeypatch.setenv("HATS_FAILCLOSE_CRITICAL", "1")
    monkeypatch.setenv("HATS_WARN_ONLY_MECH", "0")
    monkeypatch.setenv("REQUIRE_EXTERNAL_PERMIT", "1")
    monkeypatch.setenv("RATE_LIMIT_CAPACITY", "100000")
    importlib.reload(constants)
    importlib.reload(work_endpoints)
    importlib.reload(main_module)
    monkeypatch.setattr(work_endpoints, "get_hats_adapter", lambda: hats_adapter)
    monkeypatch.setattr(
        work_endpoints,
        "get_permit_adapter",
        lambda: StubPermitAdapter(["Eclipse"]),
    )
    return TestClient(main_module.app)


def test_missing_receiver(monkeypatch: pytest.MonkeyPatch) -> None:
    wo = demo_data._work_orders_by_id["WO-2"]
    monkeypatch.delitem(wo, "permitReceiversHats", raising=False)
    client = setup_client(monkeypatch, MissingReceiverHatsAdapter())
    resp = client.post(
        "/workorders/WO-2/status",
        json={"status": "INPRG", "currentStatus": "SCHED"},
    )
    assert resp.status_code == 400
    data = resp.json()
    assert data["reason"] == "HATS_CHECK_FAILED"
    assert data["missing"] == ["Permit receiver missing"]


def test_receiver_expired(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(
        demo_data._work_orders_by_id["WO-2"],
        "permitReceiversHats",
        ["102334"],
    )
    client = setup_client(monkeypatch, ExpiredReceiverHatsAdapter())
    resp = client.post(
        "/workorders/WO-2/status",
        json={"status": "INPRG", "currentStatus": "SCHED"},
    )
    assert resp.status_code == 400
    data = resp.json()
    assert data["reason"] == "HATS_CHECK_FAILED"
    assert data["missing"] == ["Receiver 102334: Eclipse expired 2025-07-30"]


def test_all_receivers_current(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(
        demo_data._work_orders_by_id["WO-2"],
        "permitReceiversHats",
        ["102334"],
    )
    client = setup_client(monkeypatch, OKHatsAdapter())
    resp = client.post(
        "/workorders/WO-2/status",
        json={"status": "INPRG", "currentStatus": "SCHED"},
    )
    assert resp.status_code == 200
