from __future__ import annotations

import os
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple, cast

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from loto.roster import storage, update_ranking

from .schemas import HatKpiRequest, HatKpiResponse

router = APIRouter(prefix="/hats", tags=["hats"])


class HatSnapshot(BaseModel):
    """Snapshot of ranking information for a hat."""

    hat_id: str = Field(..., description="Identifier of the hat")
    rank: int = Field(0, description="Rank among hats (1 = best)")
    c_r: float = Field(0.5, description="Ranking coefficient")
    n_samples: int = Field(0, description="Number of KPI events")
    last_event_at: datetime | None = Field(
        None, description="Timestamp of the most recent event"
    )

    class Config:
        extra = "forbid"


def _ledger_path() -> Path:
    return Path(
        os.getenv(
            "HATS_LEDGER_PATH",
            os.getenv("HATS_LEDGER_FILE", "hats_ledger.jsonl"),
        )
    )


def _snapshot_path() -> Path:
    return Path(
        os.getenv(
            "HATS_SNAPSHOT_PATH",
            os.getenv("HATS_SNAPSHOT_FILE", "hats_snapshot.json"),
        )
    )


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
            metrics_raw = [
                float(entry[k]) for k in ("SA", "SP", "RQ", "OF") if k in entry
            ]
        if not metrics_raw:
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
    ranking = update_ranking(ledger)
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
    ranking = update_ranking(ledger)
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


@router.post("/kpi", response_model=HatKpiResponse)
async def post_kpi(payload: HatKpiRequest) -> HatKpiResponse:
    """Record KPI metrics for a hat and return updated ranking."""

    entry = payload.dict(exclude_none=True)
    ledger_path = _ledger_path()
    snapshot_path = _snapshot_path()
    try:
        storage.append_ledger(ledger_path, entry)
    except ValueError:
        # Duplicate entry – idempotent behaviour
        pass

    entries = storage.read_ledger(ledger_path)
    snapshot = storage.compute_snapshot(entries)
    storage.write_snapshot(snapshot_path, snapshot)

    ranking_ledger: Dict[str, List[List[float]]] = defaultdict(list)
    for e in snapshot.values():
        metrics: List[float] = []
        for key in ("SA", "SP", "RQ", "OF"):
            if key in e:
                metrics.append(float(e[key]))
        ranking_ledger[str(e["hat_id"])].append(metrics)

    ranking = update_ranking(ranking_ledger)
    data = ranking.get(payload.hat_id)
    if data is None:
        raise HTTPException(status_code=500, detail="ranking failed")
    return HatKpiResponse(**data)
