from __future__ import annotations

import os
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

from fastapi import APIRouter, HTTPException

from loto.roster import storage, update_ranking

from .schemas import HatKpiRequest, HatKpiResponse

router = APIRouter(prefix="/hats", tags=["hats"])


def _ledger_path() -> Path:
    return Path(os.getenv("HATS_LEDGER_FILE", "hats_ledger.jsonl"))


def _snapshot_path() -> Path:
    return Path(os.getenv("HATS_SNAPSHOT_FILE", "hats_snapshot.json"))


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

    ledger: Dict[str, List[List[float]]] = defaultdict(list)
    for e in snapshot.values():
        metrics: List[float] = []
        for key in ("SA", "SP", "RQ", "OF"):
            if key in e:
                metrics.append(float(e[key]))
        ledger[str(e["hat_id"])].append(metrics)

    ranking = update_ranking(ledger)
    data = ranking.get(payload.hat_id)
    if data is None:
        raise HTTPException(status_code=500, detail="ranking failed")
    return HatKpiResponse(**data)
