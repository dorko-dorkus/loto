from __future__ import annotations

import importlib
import json
from datetime import date
from pathlib import Path
from typing import Callable

from _pytest.fixtures import FixtureRequest
from _pytest.monkeypatch import MonkeyPatch

import pytest
from fastapi.testclient import TestClient

import apps.api.main as main
from apps.api.schemas import ScheduleResponse
from tests.job_utils import wait_for_job


class FixedDate(date):
    @classmethod
    def today(cls) -> "FixedDate":
        return cls(2024, 1, 1)


@pytest.fixture  # type: ignore[misc]
def golden(request: FixtureRequest) -> Callable[[object], None]:
    path = Path(request.node.fspath).with_suffix(".golden.json")
    expected = json.loads(path.read_text())

    def check(data: object) -> None:
        if (
            isinstance(data, dict)
            and isinstance(expected, dict)
            and "rulepack_sha256" in data
            and "rulepack_sha256" in expected
        ):
            assert data["rulepack_sha256"] == main.RULE_PACK_HASH
            adjusted_expected = dict(expected)
            adjusted_expected["rulepack_sha256"] = data["rulepack_sha256"]
            assert data == adjusted_expected
            return
        assert data == expected

    return check


def test_schedule_golden(
    monkeypatch: MonkeyPatch, golden: Callable[[object], None]
) -> None:
    importlib.reload(main)
    monkeypatch.setattr(main, "date", FixedDate)
    client = TestClient(main.app)
    monkeypatch.setattr(
        main,
        "authenticate_user",
        lambda *a, **kw: main.OIDCUser(
            iss="iss",
            sub="sub",
            aud="aud",
            exp=0,
            iat=0,
            roles=["planner"],
        ),
    )
    payload = {"workorder": "WO-1"}
    res1 = client.post("/schedule", json=payload, headers={"Authorization": "Bearer x"})
    assert res1.status_code == 202
    job1 = res1.json()["job_id"]
    job_res1 = wait_for_job(client, job1)
    data1 = ScheduleResponse.model_validate(job_res1["result"]).model_dump()
    golden(data1)
    res2 = client.post("/schedule", json=payload, headers={"Authorization": "Bearer x"})
    assert res2.status_code == 202
    job2 = res2.json()["job_id"]
    job_res2 = wait_for_job(client, job2)
    data2 = ScheduleResponse.model_validate(job_res2["result"]).model_dump()
    assert data2 == data1
