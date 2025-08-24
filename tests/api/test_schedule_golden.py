from __future__ import annotations

import importlib
import json
from datetime import date
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import apps.api.main as main
from apps.api.schemas import ScheduleResponse


class FixedDate(date):
    @classmethod
    def today(cls) -> "FixedDate":
        return cls(2024, 1, 1)


@pytest.fixture
def golden(request):
    path = Path(request.node.fspath).with_suffix(".golden.json")
    expected = json.loads(path.read_text())

    def check(data: object) -> None:
        assert data == expected

    return check


def test_schedule_golden(monkeypatch, golden):
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
    assert res1.status_code == 200
    data1 = ScheduleResponse.model_validate(res1.json()).model_dump()
    golden(data1)
    res2 = client.post("/schedule", json=payload, headers={"Authorization": "Bearer x"})
    assert res2.status_code == 200
    data2 = ScheduleResponse.model_validate(res2.json()).model_dump()
    assert data2 == data1
