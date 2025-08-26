from __future__ import annotations

import importlib

import pytest
from fastapi.testclient import TestClient

import apps.api.workorder_endpoints as work_endpoints
import loto.constants as constants
from apps.api import main as main_module


class StubHatsAdapter:
    def has_required(
        self, hats_ids: list[str], permit_types: list[str]
    ) -> tuple[bool, list[dict[str, str]]]:
        return False, [
            {
                "receiverId": "102334",
                "name": "J.SMITH",
                "requirement": "Confined Space",
                "expiry": "2025-07-30",
            }
        ]


class StubPermitAdapter:
    def __init__(self, permit_types: list[str]) -> None:
        self.permit_types = permit_types

    def fetch_permit(self, workorder_id: str) -> dict[str, list[str]]:
        return {"permitTypes": self.permit_types}


def setup_client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("HATS_FAILCLOSE_CRITICAL", "1")
    monkeypatch.setenv("HATS_WARN_ONLY_MECH", "0")
    monkeypatch.setenv("RATE_LIMIT_CAPACITY", "100000")
    importlib.reload(constants)
    importlib.reload(work_endpoints)
    importlib.reload(main_module)
    monkeypatch.setattr(work_endpoints, "get_hats_adapter", lambda: StubHatsAdapter())
    monkeypatch.setattr(
        work_endpoints,
        "get_permit_adapter",
        lambda: StubPermitAdapter(["ConfinedSpace"]),
    )
    return TestClient(main_module.app)


def test_hats_failure_messages(monkeypatch: pytest.MonkeyPatch) -> None:
    client = setup_client(monkeypatch)
    resp = client.post(
        "/workorders/WO-2/status",
        json={"status": "INPRG", "currentStatus": "SCHED"},
    )
    assert resp.status_code == 400
    data = resp.json()
    assert data["reason"] == "HATS_CHECK_FAILED"
    assert data["missing"] == [
        "Receiver 102334 (J.SMITH): Confined Space expired 2025-07-30"
    ]
