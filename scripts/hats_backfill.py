"""Seed hats ranking with synthetic KPI events.

This script fabricates KPI metrics for a set of historical demo work orders
and writes them to the hats ledger. After backfilling the ledger it logs a
ranking snapshot so that ranks and sample counts can be inspected manually.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, cast

import structlog

logger = structlog.get_logger()

# Allow running the script without installing the package
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from loto.roster import storage, update_ranking  # noqa: E402

# Demo work orders and associated metrics.  Each tuple contains::
# (work order id, hat id, [SA, SP])
_HISTORICAL_WOS: list[tuple[str, str, list[float]]] = [
    ("WO-100", "h1", [0.95, 0.90]),
    ("WO-101", "h2", [0.75, 0.65]),
    ("WO-102", "h3", [0.45, 0.50]),
    ("WO-103", "h1", [0.92, 0.88]),
    ("WO-104", "h2", [0.70, 0.60]),
    ("WO-105", "h3", [0.50, 0.55]),
    ("WO-106", "h1", [0.90, 0.91]),
    ("WO-107", "h2", [0.68, 0.70]),
    ("WO-108", "h1", [0.93, 0.89]),
]


def main() -> None:
    """Backfill ledger and print ranking snapshot."""

    ledger_path = Path(os.getenv("HATS_LEDGER_PATH", "hats_ledger.jsonl"))

    # Start with a fresh ledger so backfill is idempotent.
    if ledger_path.exists():
        ledger_path.unlink()

    base_time = datetime(2024, 1, 1)

    # Write synthetic KPI events to the ledger.
    for idx, (wo_id, hat_id, metrics) in enumerate(_HISTORICAL_WOS):
        entry = {
            "wo_id": wo_id,
            "hat_id": hat_id,
            "metrics": metrics,
            "timestamp": (base_time + timedelta(days=idx)).isoformat(),
        }
        storage.append_ledger(ledger_path, entry)

    # Build ledger mapping and stats for ranking.
    entries = storage.read_ledger(ledger_path)
    ledger: dict[str, list[list[float]]] = {}
    stats: dict[str, dict[str, Any]] = {}
    for entry in entries:
        hat = str(entry["hat_id"])
        metrics_raw: Any = (
            entry.get("metrics")
            or entry.get("values")
            or entry.get("data")
            or entry.get("value")
        )
        if not isinstance(metrics_raw, list):
            metrics_raw = [metrics_raw]
        metrics = [float(m) for m in metrics_raw]
        ledger.setdefault(hat, []).append(metrics)

        stat = stats.setdefault(hat, {"n_samples": 0, "last_event_at": None})
        stat["n_samples"] = int(stat["n_samples"]) + 1
        ts = entry.get("timestamp")
        if ts:
            dt = datetime.fromisoformat(str(ts))
            prev = stat.get("last_event_at")
            if not isinstance(prev, datetime) or dt > prev:
                stat["last_event_at"] = dt

    ranking = update_ranking(ledger)
    snapshots: list[dict[str, Any]] = []
    for hat_id, info in ranking.items():
        stat = stats.get(hat_id, {})
        snapshots.append(
            {
                "hat_id": hat_id,
                "rank": int(cast(Any, info.get("rank", 0))),
                "c_r": float(cast(Any, info.get("coefficient", 0.0))),
                "n_samples": int(stat.get("n_samples", 0)),
                "last_event_at": stat.get("last_event_at"),
            }
        )

    snapshots.sort(key=lambda s: int(s["rank"]))
    logger.info("ranking_snapshot", snapshots=snapshots)


if __name__ == "__main__":  # pragma: no cover - manual script
    main()
