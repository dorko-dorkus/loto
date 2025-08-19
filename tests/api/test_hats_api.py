from pathlib import Path

from fastapi.testclient import TestClient

from apps.api.main import app
from loto.roster import storage


def _setup_env(monkeypatch, tmp_path: Path) -> tuple[Path, Path]:
    ledger = tmp_path / "ledger.jsonl"
    snapshot = tmp_path / "snapshot.json"
    monkeypatch.setenv("HATS_LEDGER_FILE", str(ledger))
    monkeypatch.setenv("HATS_SNAPSHOT_FILE", str(snapshot))
    return ledger, snapshot


def test_post_kpi(monkeypatch, tmp_path: Path) -> None:
    _setup_env(monkeypatch, tmp_path)
    client = TestClient(app)
    payload = {"wo_id": "1", "hat_id": "hat1", "SA": 0.5, "SP": 0.7}
    res = client.post("/hats/kpi", json=payload)
    assert res.status_code == 200
    assert res.json() == {"rank": 1, "coefficient": 0.6, "band": "A"}


def test_post_kpi_bad_payload(monkeypatch, tmp_path: Path) -> None:
    _setup_env(monkeypatch, tmp_path)
    client = TestClient(app)
    res = client.post("/hats/kpi", json={"wo_id": "1"})
    assert res.status_code == 422


def test_post_kpi_idempotent(monkeypatch, tmp_path: Path) -> None:
    ledger_path, _ = _setup_env(monkeypatch, tmp_path)
    client = TestClient(app)
    payload = {"wo_id": "1", "hat_id": "hat1", "SA": 0.5, "SP": 0.7}
    res1 = client.post("/hats/kpi", json=payload)
    res2 = client.post("/hats/kpi", json=payload)
    assert res1.status_code == res2.status_code == 200
    assert res1.json() == res2.json()
    assert len(storage.read_ledger(ledger_path)) == 1
