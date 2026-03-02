from __future__ import annotations

import importlib
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

import apps.api.main as main
from tests.job_utils import wait_for_job


def test_blueprint_prefers_pipeline_over_canned(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reloaded_main = importlib.reload(main)

    monkeypatch.setattr(
        reloaded_main.demo_data,
        "get_blueprint",
        lambda _workorder_id: {
            "steps": [{"component_id": "CANNED", "method": "close"}],
        },
    )

    fake_plan = SimpleNamespace(
        actions=[SimpleNamespace(component_id="PIPELINE", method="close")]
    )
    fake_impact = SimpleNamespace(
        unavailable_assets={"ASSET-1"},
        unit_mw_delta={"U1": 1.0},
    )
    fake_provenance = SimpleNamespace(seed=123, rule_hash="f" * 64)

    monkeypatch.setattr(
        reloaded_main,
        "plan_and_evaluate",
        lambda *args, **kwargs: (fake_plan, None, fake_impact, fake_provenance),
    )

    client = TestClient(reloaded_main.app)
    response = client.post("/blueprint", json={"workorder_id": "WO-1"})
    assert response.status_code == 202

    job = wait_for_job(client, response.json()["job_id"])
    assert "result" in job

    component_ids = [step["component_id"] for step in job["result"]["steps"]]
    assert "PIPELINE" in component_ids
    assert "CANNED" not in component_ids
