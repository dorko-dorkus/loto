from __future__ import annotations

import csv
import hashlib
import io
import json
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, List

DEFAULT_LEAD_DAYS = 2
__all__ = ["build_jobpack", "DEFAULT_LEAD_DAYS"]


def _default_items() -> List[Dict[str, object]]:
    """Fixture reservation lines for demo job packs."""

    return [
        {"part_number": "P-100", "quantity": 1, "storeroom": "WH1", "bin": "A1"},
        {"part_number": "P-200", "quantity": 1, "storeroom": "WH1", "bin": "B2"},
    ]


def build_jobpack(
    workorder_id: str,
    *,
    permit_start: date | None = None,
    lead_days: int = DEFAULT_LEAD_DAYS,
    rulepack_sha256: str | None = None,
    rulepack_id: str | None = None,
    rulepack_version: str | None = None,
    seed: str | None = None,
) -> Dict[str, object]:
    """Construct a mock job pack for ``workorder_id``.

    Parameters
    ----------
    workorder_id:
        Identifier of the work order.
    permit_start:
        Optional start date for the permit. If omitted, a date five days in the
        future is used.
    lead_days:
        Number of days prior to ``permit_start`` that materials should be picked.
    rulepack_sha256:
        Optional SHA-256 hash of the rule pack used to generate the job pack.
    rulepack_id:
        Optional identifier of the rule pack.
    rulepack_version:
        Optional version string of the rule pack.
    seed:
        Optional random seed recorded for determinism.
    """

    permit_start = permit_start or (date.today() + timedelta(days=5))
    pick_by = permit_start - timedelta(days=lead_days)
    items = _default_items()
    payload = {
        "workorder": workorder_id,
        "permit_start": permit_start.isoformat(),
        "pick_by": pick_by.isoformat(),
        "items": items,
    }
    if rulepack_sha256:
        payload["rulepack_sha256"] = rulepack_sha256
    if rulepack_id:
        payload["rulepack_id"] = rulepack_id
    if rulepack_version:
        payload["rulepack_version"] = rulepack_version
    if seed is not None:
        payload["seed"] = seed

    out_dir = Path("out/jobpacks") / f"WO-{workorder_id}"
    out_dir.mkdir(parents=True, exist_ok=True)

    json_bytes = json.dumps(payload, sort_keys=True).encode()
    json_hash = hashlib.sha256(json_bytes).hexdigest()
    json_name = f"{json_hash}.json"
    (out_dir / json_name).write_bytes(json_bytes)

    csv_buffer = io.StringIO()
    fieldnames = ["part_number", "quantity", "storeroom", "bin", "pick_by"]
    writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames)
    writer.writeheader()
    for line in items:
        row = dict(line)
        row["pick_by"] = pick_by.isoformat()
        writer.writerow(row)
    csv_content = csv_buffer.getvalue()
    csv_hash = hashlib.sha256(csv_content.encode()).hexdigest()
    csv_name = f"{csv_hash}.csv"
    (out_dir / csv_name).write_text(csv_content)

    result: Dict[str, object] = {
        "json": {"filename": json_name, "content": payload},
        "csv": {"filename": csv_name, "content": csv_content},
    }
    if rulepack_sha256 is not None:
        result["rulepack_sha256"] = rulepack_sha256
    if rulepack_id is not None:
        result["rulepack_id"] = rulepack_id
    if rulepack_version is not None:
        result["rulepack_version"] = rulepack_version
    if seed is not None:
        result["seed"] = seed
    return result
