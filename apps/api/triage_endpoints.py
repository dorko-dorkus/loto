from __future__ import annotations

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple, cast

from fastapi import APIRouter

from loto.roster import storage
from loto.triage_score import compute_ranking

from .schemas import HatKpiRequest, HatSnapshot

router = APIRouter(prefix="/triage", tags=["triage", "LOTO"])


def _ledger_path() -> Path:
    return Path(os.getenv("TRIAGE_LEDGER_PATH", "triage_ledger.jsonl"))


def _snapshot_path() -> Path:
    return Path(os.getenv("TRIAGE_SNAPSHOT_PATH", "triage_snapshot.json"))


def _read_ledger() -> Tuple[Dict[str, List[List[float]]], Dict[str, Dict[str, Any]]]:
    path = _ledger_path()
    entries = storage.read_ledger(path)
    ledger: Dict[str, List[List[float]]] = {}
    stats: Dict[str, Dict[str, Any]] = {}
    for entry in entries:
        hat_id = str(entry.get("hat_id"))
        metrics_raw = (
            entry.get("metrics")
            or entry.get("values")
            or entry.get("data")
            or entry.get("value")
        )
        if metrics_raw is None:
            continue
        if not isinstance(metrics_raw, (list, tuple)):
            metrics_raw = [metrics_raw]
        metrics = [float(m) for m in metrics_raw]
        ledger.setdefault(hat_id, []).append(metrics)

        stat = stats.setdefault(hat_id, {"n_samples": 0, "last_event_at": None})
        stat["n_samples"] += 1
        ts = entry.get("timestamp") or entry.get("ts")
        if ts:
            dt = datetime.fromisoformat(str(ts))
            prev = stat["last_event_at"]
            if prev is None or dt > prev:
                stat["last_event_at"] = dt
    return ledger, stats


def _neutral_snapshot(hat_id: str, stats: Dict[str, Any] | None = None) -> HatSnapshot:
    stats = stats or {}
    return HatSnapshot(
        hat_id=hat_id,
        rank=0,
        c_r=0.5,
        n_samples=int(stats.get("n_samples", 0)),
        last_event_at=stats.get("last_event_at"),
    )


@router.get("", response_model=list[HatSnapshot])
async def list_hats() -> list[HatSnapshot]:
    """Return ranking snapshots for all hats."""

    ledger, stats = _read_ledger()
    if not ledger:
        return []
    ranking = compute_ranking(ledger)
    snapshots: list[HatSnapshot] = []
    for hat_id, info in ranking.items():
        stat = stats.get(hat_id)
        rank = cast(int, info.get("rank", 0))
        coef = cast(float, info.get("coefficient", 0.5))
        snapshots.append(
            HatSnapshot(
                hat_id=hat_id,
                rank=rank,
                c_r=coef,
                n_samples=int(stat["n_samples"]) if stat else 0,
                last_event_at=stat.get("last_event_at") if stat else None,
            )
        )
    return sorted(snapshots, key=lambda s: s.rank)


@router.get("/{hat_id}", response_model=HatSnapshot)
async def get_hat(hat_id: str) -> HatSnapshot:
    """Return ranking snapshot for a single hat."""

    ledger, stats = _read_ledger()
    if not ledger:
        return _neutral_snapshot(hat_id)
    ranking = compute_ranking(ledger)
    info = ranking.get(hat_id)
    stat = stats.get(hat_id)
    if not info:
        return _neutral_snapshot(hat_id, stat)
    rank = cast(int, info.get("rank", 0))
    coef = cast(float, info.get("coefficient", 0.5))
    return HatSnapshot(
        hat_id=hat_id,
        rank=rank,
        c_r=coef,
        n_samples=int(stat.get("n_samples", 0)) if stat else 0,
        last_event_at=stat.get("last_event_at") if stat else None,
    )


@router.post("/kpi", response_model=HatSnapshot)
async def post_hat_kpi(event: HatKpiRequest) -> HatSnapshot:
    """Record KPI metrics for a hat and return updated snapshot."""

    ledger_path = _ledger_path()
    snapshot_path = _snapshot_path()
    metrics: List[float] = [event.SA, event.SP]
    if event.RQ is not None:
        metrics.append(event.RQ)
    if event.OF is not None:
        metrics.append(event.OF)
    entry = {
        "wo_id": event.wo_id,
        "hat_id": event.hat_id,
        "metrics": metrics,
        "timestamp": datetime.utcnow().isoformat(),
    }
    try:
        storage.append_ledger(ledger_path, entry)
    except ValueError:
        logging.debug("failed to append ledger entry", exc_info=True)

    entries = storage.read_ledger(ledger_path)
    snapshot = storage.compute_snapshot(entries)
    storage.write_snapshot(snapshot_path, snapshot)

    ledger, stats = _read_ledger()
    ranking = compute_ranking(ledger) if ledger else {}
    info = ranking.get(event.hat_id)
    stat = stats.get(event.hat_id)
    if not info:
        return _neutral_snapshot(event.hat_id, stat)
    rank = cast(int, info.get("rank", 0))
    coef = cast(float, info.get("coefficient", 0.5))
    return HatSnapshot(
        hat_id=event.hat_id,
        rank=rank,
        c_r=coef,
        n_samples=int(stat.get("n_samples", 0)) if stat else 0,
        last_event_at=stat.get("last_event_at") if stat else None,
    )
