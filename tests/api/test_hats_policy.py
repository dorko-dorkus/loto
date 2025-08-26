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
    ) -> tuple[bool, list[str]]:
        return False, ["MISSING"]


class StubPermitAdapter:
    def __init__(self, permit_types: list[str]) -> None:
        self.permit_types = permit_types

    def fetch_permit(
        self, workorder_id: str
    ) -> dict[str, list[str]]:  # pragma: no cover - simple stub
        return {"permitTypes": self.permit_types}


def setup_client(
    monkeypatch: pytest.MonkeyPatch,
    permit_types: list[str],
    *,
    failclose: bool = True,
    warn_only_mech: bool = False,
) -> TestClient:
    monkeypatch.setenv("HATS_FAILCLOSE_CRITICAL", "1" if failclose else "0")
    monkeypatch.setenv("HATS_WARN_ONLY_MECH", "1" if warn_only_mech else "0")
    monkeypatch.setenv("RATE_LIMIT_CAPACITY", "100000")
    importlib.reload(constants)
    importlib.reload(work_endpoints)
    importlib.reload(main_module)
    monkeypatch.setattr(work_endpoints, "get_hats_adapter", lambda: StubHatsAdapter())
    monkeypatch.setattr(
        work_endpoints, "get_permit_adapter", lambda: StubPermitAdapter(permit_types)
    )
    return TestClient(main_module.app)


@pytest.mark.parametrize("failclose,expected", [(True, 400), (False, 200)])  # type: ignore[misc]
def test_hats_failclose_critical(
    monkeypatch: pytest.MonkeyPatch, failclose: bool, expected: int
) -> None:
    client = setup_client(monkeypatch, ["Electrical"], failclose=failclose)
    resp = client.post(
        "/workorders/WO-2/status", json={"status": "INPRG", "currentStatus": "SCHED"}
    )
    assert resp.status_code == expected


@pytest.mark.parametrize("warn_only,expected", [(False, 400), (True, 200)])  # type: ignore[misc]
def test_hats_warn_only_mech(
    monkeypatch: pytest.MonkeyPatch, warn_only: bool, expected: int
) -> None:
    client = setup_client(monkeypatch, ["Mechanical"], warn_only_mech=warn_only)
    resp = client.post(
        "/workorders/WO-2/status", json={"status": "INPRG", "currentStatus": "SCHED"}
    )
    assert resp.status_code == expected
