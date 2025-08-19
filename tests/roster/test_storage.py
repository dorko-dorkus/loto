from pathlib import Path

import pytest

from loto.roster import storage


def test_duplicate_write_refused(tmp_path: Path) -> None:
    ledger = tmp_path / "ledger.jsonl"
    entry = {"wo_id": "1", "hat_id": "a", "data": 1}
    storage.append_ledger(ledger, entry)
    with pytest.raises(ValueError):
        storage.append_ledger(ledger, entry)


def test_snapshot_equals_recompute(tmp_path: Path) -> None:
    ledger = tmp_path / "ledger.jsonl"
    snapshot_file = tmp_path / "snapshot.json"
    entries: list[dict[str, object]] = [
        {"wo_id": "1", "hat_id": "a", "foo": "bar"},
        {"wo_id": "2", "hat_id": "b", "baz": 3},
    ]
    for e in entries:
        storage.append_ledger(ledger, e)

    recomputed = storage.compute_snapshot(storage.read_ledger(ledger))
    storage.write_snapshot(snapshot_file, recomputed)

    assert storage.read_snapshot(snapshot_file) == recomputed
