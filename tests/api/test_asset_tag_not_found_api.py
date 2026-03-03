from __future__ import annotations

import importlib
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi.testclient import TestClient

import apps.api.main as main
from apps.api.planning_service import DemoMaximoAdapter
from tests.job_utils import wait_for_job


ORIGINAL_LOAD_CONTEXT = DemoMaximoAdapter.load_context


def _with_unknown_asset_tag(self: Any, workorder_id: str) -> dict[str, Any]:
    ctx = ORIGINAL_LOAD_CONTEXT(self, workorder_id)
    ctx["asset_tag"] = "  UA-404  "
    return ctx


def test_blueprint_unknown_asset_tag_returns_structured_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reloaded_main = importlib.reload(main)
    monkeypatch.setattr(DemoMaximoAdapter, "load_context", _with_unknown_asset_tag)

    client = TestClient(reloaded_main.app)
    response = client.post("/blueprint", json={"workorder_id": "WO-1"})
    assert response.status_code == 202

    job = wait_for_job(client, response.json()["job_id"])
    assert job["status"] == "failed"
    assert job["result"] == {
        "code": "ASSET_TAG_NOT_FOUND",
        "message": "asset_tag 'UA-404' not found in graph",
        "hint": "graph contains 4 nodes",
    }
    assert job["error"] == job["result"]


def test_schedule_unknown_asset_tag_preserves_structured_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reloaded_main = importlib.reload(main)
    monkeypatch.setattr(
        reloaded_main,
        "authenticate_user",
        lambda *a, **kw: SimpleNamespace(
            roles=["planner"], email="planner@example.com"
        ),
    )
    monkeypatch.setattr(DemoMaximoAdapter, "load_context", _with_unknown_asset_tag)

    client = TestClient(reloaded_main.app)
    response = client.post(
        "/schedule",
        json={"workorder": "WO-1"},
        headers={"Authorization": "Bearer x"},
    )
    assert response.status_code == 202

    job = wait_for_job(client, response.json()["job_id"])
    assert job["status"] == "failed"
    assert job["result"] == {
        "code": "ASSET_TAG_NOT_FOUND",
        "message": "asset_tag 'UA-404' not found in graph",
        "hint": "graph contains 4 nodes",
    }
    assert job["error"] == job["result"]
