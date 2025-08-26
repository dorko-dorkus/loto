import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from apps.api.main import app


def test_post_kpi_and_idempotent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ledger = tmp_path / "ledger.jsonl"
    snapshot = tmp_path / "snapshot.json"
    monkeypatch.setenv("HATS_LEDGER_PATH", str(ledger))
    monkeypatch.setenv("HATS_SNAPSHOT_PATH", str(snapshot))

    client = TestClient(app)
    payload = {"wo_id": "1", "hat_id": "h1", "SA": 0.8, "SP": 0.9}

    res = client.post("/triage/kpi", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["hat_id"] == "h1"
    assert data["rank"] == 84
    assert data["c_r"] == pytest.approx(0.8375)
    assert data["n_samples"] == 1

    # Ledger and snapshot written
    assert ledger.exists() and snapshot.exists()
    assert len(ledger.read_text().strip().splitlines()) == 1
    snap = json.loads(snapshot.read_text())
    assert snap  # not empty

    # Second post is idempotent
    res2 = client.post("/triage/kpi", json=payload)
    assert res2.status_code == 200
    assert res2.json() == data
    assert len(ledger.read_text().strip().splitlines()) == 1


def test_post_kpi_bad_payload(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    ledger = tmp_path / "ledger.jsonl"
    snapshot = tmp_path / "snapshot.json"
    monkeypatch.setenv("HATS_LEDGER_PATH", str(ledger))
    monkeypatch.setenv("HATS_SNAPSHOT_PATH", str(snapshot))

    client = TestClient(app)
    res = client.post("/triage/kpi", json={"wo_id": "1"})
    assert res.status_code == 422
