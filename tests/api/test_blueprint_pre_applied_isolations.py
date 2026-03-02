from __future__ import annotations

import importlib

import pytest
from fastapi.testclient import TestClient

import apps.api.main as main
from tests.job_utils import wait_for_job


class _StubPermitAdapter:
    def __init__(self, applied_isolations: list[str]) -> None:
        self._applied_isolations = applied_isolations

    def fetch_permit(self, _workorder_id: str) -> dict[str, list[str]]:
        return {"applied_isolations": self._applied_isolations}


def test_blueprint_strict_pre_applied_isolations_returns_400(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reloaded_main = importlib.reload(main)
    monkeypatch.setattr(
        reloaded_main,
        "get_permit_adapter",
        lambda: _StubPermitAdapter(["ISO-1", "steam:V->ASSET"]),
    )

    client = TestClient(reloaded_main.app)
    response = client.post("/blueprint?strict=true", json={"workorder_id": "WO-1"})

    assert response.status_code == 400
    assert "Malformed component_id 'ISO-1'" in response.text


def test_blueprint_non_strict_pre_applied_isolations_ignores_malformed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reloaded_main = importlib.reload(main)
    monkeypatch.setattr(
        reloaded_main,
        "get_permit_adapter",
        lambda: _StubPermitAdapter(["ISO-1", "steam:V->ASSET"]),
    )

    client = TestClient(reloaded_main.app)
    response = client.post("/blueprint", json={"workorder_id": "WO-1"})

    assert response.status_code == 202
    job = wait_for_job(client, response.json()["job_id"])
    assert job["status"] == "done"
    assert job["result"]["steps"] == []
