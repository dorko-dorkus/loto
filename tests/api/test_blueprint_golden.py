from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from apps.api.main import app
from apps.api.schemas import BlueprintResponse


@pytest.fixture
def golden(request):
    path = Path(request.node.fspath).with_suffix(".golden.json")
    expected = json.loads(path.read_text())

    def check(data: object) -> None:
        assert data == expected

    return check


def test_blueprint_golden(golden):
    client = TestClient(app)
    payload = {"workorder_id": "WO-1"}
    res1 = client.post("/blueprint", json=payload)
    assert res1.status_code == 200
    data1 = BlueprintResponse.model_validate(res1.json()).model_dump()
    golden(data1)

    res2 = client.post("/blueprint", json=payload)
    assert res2.status_code == 200
    data2 = BlueprintResponse.model_validate(res2.json()).model_dump()
    assert data2 == data1
