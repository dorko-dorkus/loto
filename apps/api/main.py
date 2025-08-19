from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List
from uuid import uuid4

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from loto.impact_config import load_impact_config
from loto.integrations.stores_adapter import DemoStoresAdapter
from loto.inventory import (
    InventoryStatus,
    Reservation,
    StockItem,
    check_wo_parts_required,
)
from loto.models import RulePack
from loto.scheduling.des_engine import Task
from loto.scheduling.objective import integrate_cost
from loto.service import monte_carlo_schedule, plan_and_evaluate, run_schedule
from loto.service.blueprints import inventory_state

from .pid_endpoints import router as pid_router
from .schemas import (
    BlueprintRequest,
    BlueprintResponse,
    ScheduleRequest,
    ScheduleResponse,
    Step,
)

app = FastAPI(title="loto API")

origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]
if origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(pid_router)

ENV = os.getenv("APP_ENV", "").lower()
if ENV == "live":
    ENV_BADGE = "PROD"
elif ENV == "test":
    ENV_BADGE = "TEST"
else:
    ENV_BADGE = "DRY-RUN"

RATE_LIMIT_PATHS = {"/pid/overlay", "/schedule"}
RATE_LIMIT_CAPACITY = 10
RATE_LIMIT_INTERVAL = 60.0
_rate_limit_state = {
    path: {"tokens": RATE_LIMIT_CAPACITY, "ts": time.monotonic()}
    for path in RATE_LIMIT_PATHS
}


@app.middleware("http")
async def add_env_and_rate_limit(request: Request, call_next):
    path = request.url.path
    if path in _rate_limit_state:
        bucket = _rate_limit_state[path]
        now = time.monotonic()
        elapsed = now - bucket["ts"]
        if elapsed > RATE_LIMIT_INTERVAL:
            bucket["tokens"] = RATE_LIMIT_CAPACITY
            bucket["ts"] = now
        if bucket["tokens"] <= 0:
            response = Response(status_code=429)
            response.headers["X-Env"] = ENV_BADGE
            return response
        bucket["tokens"] -= 1
    response = await call_next(request)
    response.headers["X-Env"] = ENV_BADGE
    return response


STATE: Dict[str, Any] = {}


@dataclass
class WorkOrder:
    """Minimal work order representation for demo inventory checks."""

    id: str
    reservations: List[Reservation]


class ProposeRequest(BaseModel):
    """Payload for proposing plan and schedule updates."""

    plan: Dict[str, Any] = Field(default_factory=dict, description="Proposed targets")
    schedule: Dict[str, Any] = Field(
        default_factory=dict, description="Proposed assignments"
    )

    class Config:
        extra = "forbid"


class ProposeResponse(BaseModel):
    """Response highlighting differences from current state."""

    diff: Dict[str, Dict[str, Dict[str, Any]]] = Field(
        default_factory=dict, description="Differences vs current targets/assignments"
    )
    idempotency_key: str

    class Config:
        extra = "forbid"


@app.get("/healthz", include_in_schema=False)
async def healthz() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


class DemoMaximoAdapter:
    """Tiny Maximo adapter serving demo data from the repository."""

    def load_context(self, workorder_id: str) -> Dict[str, Any]:
        """Return file paths and metadata for the given work order."""

        base = Path(__file__).resolve().parents[2] / "demo"
        impact_cfg = load_impact_config(
            base / "unit_map.yaml", base / "redundancy_map.yaml"
        )
        return {
            "line_csv": base / "line_list.csv",
            "valve_csv": base / "valves.csv",
            "drain_csv": base / "drains.csv",
            "source_csv": base / "sources.csv",
            "asset_tag": "A",  # arbitrary asset tag for demo data
            "impact_cfg": impact_cfg,
        }


@app.post("/blueprint", response_model=BlueprintResponse)
async def post_blueprint(payload: BlueprintRequest) -> BlueprintResponse:
    """Plan isolations for a work order and return impact metrics."""

    adapter = DemoMaximoAdapter()
    ctx = adapter.load_context(payload.workorder_id)
    impact_cfg = ctx["impact_cfg"]

    stores = DemoStoresAdapter()
    work_order = WorkOrder(
        id=payload.workorder_id,
        reservations=[
            Reservation(item_id="P-100", quantity=1),
            Reservation(item_id="P-200", quantity=1),
        ],
    )

    def lookup_stock(item_id: str) -> StockItem | None:
        try:
            status = stores.inventory_status(item_id)
        except KeyError:
            return None
        return StockItem(item_id=item_id, quantity=status.get("available", 0))

    def check_parts(wo: object) -> InventoryStatus:
        assert isinstance(wo, WorkOrder)
        return check_wo_parts_required(wo, lookup_stock)

    inv_status = check_parts(work_order)

    global STATE
    STATE = dict(inventory_state(work_order, check_parts, STATE))

    with (
        open(ctx["line_csv"]) as line,
        open(ctx["valve_csv"]) as valve,
        open(ctx["drain_csv"]) as drain,
        open(ctx["source_csv"]) as source,
    ):
        plan, _, impact, _ = plan_and_evaluate(
            line,
            valve,
            drain,
            source,
            asset_tag=str(ctx["asset_tag"]),
            rule_pack=RulePack(),
            stimuli=[],
            asset_units=impact_cfg.asset_units,
            unit_data=impact_cfg.unit_data,
            unit_areas=impact_cfg.unit_areas,
            penalties=impact_cfg.penalties,
            asset_areas=impact_cfg.asset_areas,
        )

    steps: List[Step] = [
        Step(component_id=a.component_id, method=a.method) for a in plan.actions
    ]

    return BlueprintResponse(
        steps=steps,
        unavailable_assets=sorted(impact.unavailable_assets),
        unit_mw_delta=impact.unit_mw_delta,
        blocked_by_parts=inv_status.blocked,
    )


def _diff(
    current: Dict[str, Any], proposed: Dict[str, Any]
) -> Dict[str, Dict[str, Any]]:
    """Return key-wise difference between two mappings."""

    delta: Dict[str, Dict[str, Any]] = {}
    for key in set(current) | set(proposed):
        cur = current.get(key)
        prop = proposed.get(key)
        if cur != prop:
            delta[key] = {"current": cur, "proposed": prop}
    return delta


@app.post("/propose", response_model=ProposeResponse)
async def post_propose(payload: ProposeRequest) -> ProposeResponse:
    """Return diffs between proposed plan/schedule and current state."""

    current: Dict[str, Dict[str, Any]] = {
        "targets": {"A": 1},
        "assignments": {"A": "crew-1"},
    }

    diff = {
        "targets": _diff(current["targets"], payload.plan),
        "assignments": _diff(current["assignments"], payload.schedule),
    }

    return ProposeResponse(diff=diff, idempotency_key=str(uuid4()))


@app.post("/schedule", response_model=ScheduleResponse)
async def post_schedule(payload: ScheduleRequest) -> ScheduleResponse:
    """Run scheduling simulations and return summary statistics."""

    tasks = {
        tid: Task(duration=spec.duration, predecessors=spec.predecessors)
        for tid, spec in payload.tasks.items()
    }
    run_res = run_schedule(tasks, payload.resource_caps, seed=payload.seed)
    mc_res = monte_carlo_schedule(tasks, payload.resource_caps, runs=payload.runs)
    cost = 0.0
    if payload.power_curve and payload.price_curve:
        cost = integrate_cost(payload.power_curve, payload.price_curve)

    return ScheduleResponse(
        p10=mc_res.makespan_percentiles.get("P10", 0.0),
        p50=mc_res.makespan_percentiles.get("P50", 0.0),
        p90=mc_res.makespan_percentiles.get("P90", 0.0),
        expected_cost=cost,
        violations=run_res.violations,
        seed=run_res.seed,
    )


@app.get("/workorders/{workorder_id}")
async def get_workorder(workorder_id: str) -> dict[str, str]:
    """Mock work order fetch."""
    return {"workorder_id": workorder_id, "status": "mocked"}
