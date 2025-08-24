from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import apps.api.main as main
from apps.api.schemas import BlueprintResponse
from tests.job_utils import wait_for_job


@pytest.fixture
def golden(request):
    path = Path(request.node.fspath).with_suffix(".golden.json")
    expected = json.loads(path.read_text())

    def check(data: object) -> None:
        assert data == expected

    return check


def test_blueprint_golden(golden):
    importlib.reload(main)
    client = TestClient(main.app)
    payload = {"workorder_id": "WO-1"}
    res1 = client.post("/blueprint", json=payload)
    assert res1.status_code == 202
    job1 = res1.json()["job_id"]
    job_res1 = wait_for_job(client, job1)
    data1 = BlueprintResponse.model_validate(job_res1["result"]).model_dump()
    golden(data1)

    res2 = client.post("/blueprint", json=payload)
    assert res2.status_code == 202
    job2 = res2.json()["job_id"]
    job_res2 = wait_for_job(client, job2)
    data2 = BlueprintResponse.model_validate(job_res2["result"]).model_dump()
    assert data2 == data1
