from __future__ import annotations

from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from apps.api.main import app
from apps.api.schemas import ScheduleResponse
from loto.errors import UnisolatablePathError
from tests.job_utils import wait_for_job


def test_plans_endpoint_returns_schedule() -> None:
    client = TestClient(app)
    res = client.post("/plans", json={"workorder": "WO-1"})
    assert res.status_code == 202
    job = res.json()["job_id"]
    data = wait_for_job(client, job)["result"]
    data = ScheduleResponse.model_validate(data)
    assert data.schedule


def test_plans_endpoint_surfaces_unisolatable_path_error(
    monkeypatch: MonkeyPatch,
) -> None:
    def _boom(*args: object, **kwargs: object) -> None:
        raise UnisolatablePathError(
            target_identifier="UA-500",
            reason="no isolation points on any source→target path",
            hint="add an inline valve on each source-to-target path",
        )

    monkeypatch.setattr("apps.api.main.load_work_order_plan", _boom)
    client = TestClient(app)
    res = client.post("/plans", json={"workorder": "WO-1"})
    assert res.status_code == 202
    job_id = res.json()["job_id"]
    job = wait_for_job(client, job_id)
    assert job["status"] == "failed"
    assert job["result"] == {
        "code": "UNISOLATABLE_PATH",
        "message": "unable to isolate target 'UA-500': no isolation points on any source→target path",
        "target": "UA-500",
        "reason": "no isolation points on any source→target path",
        "hint": "add an inline valve on each source-to-target path",
    }
