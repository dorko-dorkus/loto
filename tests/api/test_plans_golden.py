from __future__ import annotations

from fastapi.testclient import TestClient

from apps.api.main import app
from apps.api.schemas import ScheduleResponse
from tests.job_utils import wait_for_job


def test_plans_endpoint_returns_schedule() -> None:
    client = TestClient(app)
    res = client.post("/plans", json={"workorder": "WO-1"})
    assert res.status_code == 202
    job = res.json()["job_id"]
    data = wait_for_job(client, job)["result"]
    data = ScheduleResponse.model_validate(data)
    assert data.schedule
