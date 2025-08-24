from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, cast


def _entry_hash(wo_id: str, hat_id: str) -> str:
    """Return a deterministic hash for the given work order and hat IDs."""
    data = f"{wo_id}:{hat_id}".encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def read_ledger(path: Path) -> List[Dict[str, Any]]:
    """Return all ledger entries stored at ``path``.

    The ledger is stored as a JSON Lines (JSONL) file where each line is a
    JSON object representing a single entry. Missing files yield an empty
    list.
    """
    if not path.exists():
        return []
    entries: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


def append_ledger(path: Path, entry: Mapping[str, Any]) -> Dict[str, Any]:
    """Append ``entry`` to the ledger at ``path``.

    The ledger is append-only. If an entry with the same ``wo_id`` and
    ``hat_id`` already exists the write is refused and :class:`ValueError`
    is raised.
    """
    wo_id = str(entry["wo_id"])
    hat_id = str(entry["hat_id"])
    key = _entry_hash(wo_id, hat_id)
    for existing in read_ledger(path):
        existing_key = _entry_hash(str(existing["wo_id"]), str(existing["hat_id"]))
        if existing_key == key:
            raise ValueError("duplicate ledger entry")
    path.parent.mkdir(parents=True, exist_ok=True)
    to_write: Dict[str, Any] = dict(entry)
    to_write["_id"] = key
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(to_write) + "\n")
    return to_write


def compute_snapshot(entries: Iterable[Mapping[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Compute a snapshot from ledger ``entries``.

    The snapshot is a dictionary keyed by the hash derived from ``wo_id``
    and ``hat_id``. The latest occurrence of a key wins.
    """
    snapshot: Dict[str, Dict[str, Any]] = {}
    for entry in entries:
        key = _entry_hash(str(entry["wo_id"]), str(entry["hat_id"]))
        snapshot[key] = dict(entry)
    return snapshot


def write_snapshot(path: Path, snapshot: Dict[str, Dict[str, Any]]) -> None:
    """Write ``snapshot`` to ``path`` as JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(snapshot, fh)


def read_snapshot(path: Path) -> Dict[str, Dict[str, Any]]:
    """Read snapshot data from ``path``.

    Missing files or empty contents yield an empty dictionary.
    """
    if not path.exists():
        return {}
    content = path.read_text(encoding="utf-8").strip()
    if not content:
        return {}
    return cast(Dict[str, Dict[str, Any]], json.loads(content))
