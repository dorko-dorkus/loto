from typing import List, Tuple

from fastapi.testclient import TestClient
from pytest import MonkeyPatch

import apps.api.main as main


def test_commit_gate_enforcement(monkeypatch: MonkeyPatch) -> None:
    records: List[Tuple[str, str]] = []

    def fake_add_record(
        *, user: str, action: str, db_path: object | None = None
    ) -> None:
        records.append((user, action))

    monkeypatch.setattr(main, "add_record", fake_add_record)
    client = TestClient(main.app)

    res = client.post(
        "/commit/WO-1",
        json={"simOk": False, "policies": {"safe": True, "log": True}},
    )
    assert res.status_code == 400
    assert res.json() == {"code": "SIMULATION_RED"}
    assert len(records) == 1

    records.clear()
    res = client.post(
        "/commit/WO-2",
        json={"simOk": True, "policies": {"safe": False, "log": True}},
    )
    assert res.status_code == 400
    assert res.json() == {"code": "POLICY_CHIPS_MISSING"}
    assert len(records) == 1

    records.clear()
    res = client.post(
        "/commit/WO-3",
        json={"simOk": True, "policies": {"safe": True, "log": True}},
    )
    assert res.status_code == 204
    assert len(records) == 1
