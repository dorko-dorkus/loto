from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Dict, List
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from loto.config import validate_env_vars
from loto.impact_config import load_impact_config
from loto.integrations.stores_adapter import DemoStoresAdapter
from loto.inventory import (
    InventoryStatus,
    Reservation,
    StockItem,
    check_wo_parts_required,
)
from loto.loggers import configure_logging, request_id_var, rule_hash_var, seed_var
from loto.materials.jobpack import DEFAULT_LEAD_DAYS, build_jobpack
from loto.models import RulePack
from loto.rule_engine import RuleEngine
from loto.scheduling.des_engine import Task
from loto.scheduling.monte_carlo import simulate
from loto.service import plan_and_evaluate
from loto.service.blueprints import inventory_state

from .hats_endpoints import router as hats_router  # provides hats KPI endpoints
from .pid_endpoints import router as pid_router
from .schemas import (
    BlueprintRequest,
    BlueprintResponse,
    SchedulePoint,
    ScheduleRequest,
    ScheduleResponse,
    Step,
)
from .workorder_endpoints import router as workorder_router

configure_logging()
validate_env_vars()

_rule_engine = RuleEngine()
_default_rulepack = (
    Path(__file__).resolve().parents[2] / "config" / "hswa_rules_v1.1.yaml"
)
_rulepack_path = Path(os.getenv("RULEPACK_FILE", _default_rulepack))
RULE_PACK = _rule_engine.load(_rulepack_path)
RULE_PACK_HASH = _rule_engine.hash(RULE_PACK)
RULE_PACK_ID = RULE_PACK.metadata.get("id")
RULE_PACK_VERSION = RULE_PACK.metadata.get("version")
logging.info("loaded rulepack %s sha256=%s", _rulepack_path, RULE_PACK_HASH)

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
app.include_router(hats_router)
app.include_router(workorder_router)


AUTH_REQUIRED = os.getenv("AUTH_REQUIRED", "").lower() == "true"
AUTH_TOKEN = os.getenv("AUTH_TOKEN", "")


@app.middleware("http")
async def auth_guard(request: Request, call_next):
    """Enforce bearer token on non-read-only requests when required."""
    if AUTH_REQUIRED and request.method not in {"GET", "HEAD", "OPTIONS"}:
        auth_header = request.headers.get("Authorization")
        if auth_header != f"Bearer {AUTH_TOKEN}":
            resp = Response(status_code=401)
            resp.headers["X-Env"] = ENV_BADGE
            return resp
    return await call_next(request)


@app.middleware("http")
async def log_context(request: Request, call_next):
    req_id = str(uuid4())
    token = request_id_var.set(req_id)
    try:
        response = await call_next(request)
        return response
    finally:
        request_id_var.reset(token)
        seed_var.set(None)
        rule_hash_var.set(None)


@app.exception_handler(HTTPException)
async def _handle_http_exception(request: Request, exc: HTTPException) -> JSONResponse:
    """Return errors in a consistent JSON envelope."""
    return JSONResponse(status_code=exc.status_code, content={"error": str(exc.detail)})


@app.exception_handler(Exception)
async def _handle_exception(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all handler to wrap unexpected exceptions."""
    logging.exception("Unhandled exception: %s", exc)
    return JSONResponse(status_code=500, content={"error": str(exc)})


ENV = os.getenv("APP_ENV", "").lower()
if ENV == "live":
    ENV_BADGE = "PROD"
elif ENV == "test":
    ENV_BADGE = "TEST"
else:
    ENV_BADGE = "DRY-RUN"

RATE_LIMIT_PATHS = {"/pid/overlay", "/schedule"}
RATE_LIMIT_CAPACITY = int(os.getenv("RATE_LIMIT_CAPACITY", "10"))
RATE_LIMIT_INTERVAL = float(os.getenv("RATE_LIMIT_INTERVAL", "60"))
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


@app.get("/healthz", include_in_schema=False, tags=["LOTO"])
async def healthz() -> dict[str, Any]:
    """Health check endpoint including rate limit counters."""
    return {
        "status": "ok",
        "rate_limit": {
            "capacity": RATE_LIMIT_CAPACITY,
            "interval": RATE_LIMIT_INTERVAL,
            "counters": {
                path: state["tokens"] for path, state in _rate_limit_state.items()
            },
        },
    }


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


@app.post("/blueprint", response_model=BlueprintResponse, tags=["LOTO"])
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

    parts_status: Dict[str, str] = {}
    for res in work_order.reservations:
        stock = lookup_stock(res.item_id)
        available = stock.quantity if stock else 0
        if available >= res.quantity:
            parts_status[res.item_id] = "ok"
        elif available > 0:
            parts_status[res.item_id] = "low"
        else:
            parts_status[res.item_id] = "short"

    inv_status = check_parts(work_order)

    global STATE
    STATE = dict(inventory_state(work_order, check_parts, STATE))

    with (
        open(ctx["line_csv"]) as line,
        open(ctx["valve_csv"]) as valve,
        open(ctx["drain_csv"]) as drain,
        open(ctx["source_csv"]) as source,
    ):
        plan, _, impact, prov = plan_and_evaluate(
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
    seed_var.set(prov.seed)
    rule_hash_var.set(prov.rule_hash)
    logging.info("request complete")

    steps: List[Step] = [
        Step(component_id=a.component_id, method=a.method) for a in plan.actions
    ]

    return BlueprintResponse(
        steps=steps,
        unavailable_assets=sorted(impact.unavailable_assets),
        unit_mw_delta=impact.unit_mw_delta,
        blocked_by_parts=inv_status.blocked,
        parts_status=parts_status,
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


@app.post("/propose", response_model=ProposeResponse, tags=["LOTO"])
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


@app.post("/schedule", response_model=ScheduleResponse, tags=["LOTO"])
async def post_schedule(
    payload: ScheduleRequest, strict: bool = False
) -> ScheduleResponse:
    """Return a synthetic schedule for the given work order.

    When ``strict`` is ``True`` and the work order is blocked by missing parts,
    a ``409 Conflict`` response is returned instead of an empty schedule.
    """

    stores = DemoStoresAdapter()
    work_order = WorkOrder(
        id=payload.workorder,
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

    inv_status = check_wo_parts_required(work_order, lookup_stock)

    seed_int = 0
    if inv_status.blocked:
        seed_var.set(seed_int)
        rule_hash_var.set(RULE_PACK_HASH)
        logging.info("request complete")
        missing_parts = [
            {"item_id": res.item_id, "quantity": res.quantity}
            for res in inv_status.missing
        ]
        if strict:
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content={
                    "blocked_by_parts": True,
                    "missing_parts": missing_parts,
                },
            )
        return ScheduleResponse(
            schedule=[],
            seed=str(seed_int),
            objective=0.0,
            blocked_by_parts=True,
            rulepack_sha256=RULE_PACK_HASH,
            rulepack_id=RULE_PACK_ID,
            rulepack_version=RULE_PACK_VERSION,
        )

    # Minimal demo task graph
    tasks = {
        "prep": Task(duration=1),
        "exec": Task(duration=2, predecessors=["prep"]),
    }

    mc_res = simulate(tasks, {}, runs=20)
    today = date.today()
    schedule: List[SchedulePoint] = []
    for i, pct in enumerate(mc_res.task_percentiles.values()):
        schedule.append(
            SchedulePoint(
                date=(today + timedelta(days=i)).isoformat(),
                p10=pct.get("P10", 0.0),
                p50=pct.get("P50", 0.0),
                p90=pct.get("P90", 0.0),
                price=0.0,
                hats=i + 1,
            )
        )

    seed_var.set(seed_int)
    rule_hash_var.set(RULE_PACK_HASH)
    logging.info("request complete")
    return ScheduleResponse(
        schedule=schedule,
        seed=str(seed_int),
        objective=0.0,
        blocked_by_parts=False,
        rulepack_sha256=RULE_PACK_HASH,
        rulepack_id=RULE_PACK_ID,
        rulepack_version=RULE_PACK_VERSION,
    )


@app.get("/workorders/{workorder_id}/jobpack", tags=["LOTO"])
async def get_jobpack(
    workorder_id: str,
    permit_start: date | None = None,
    lead_days: int = DEFAULT_LEAD_DAYS,
) -> dict[str, object]:
    """Return a mock job pack for the given work order."""
    seed_int = 0
    seed_var.set(seed_int)
    rule_hash_var.set(RULE_PACK_HASH)
    return build_jobpack(
        workorder_id,
        permit_start=permit_start,
        lead_days=lead_days,
        rulepack_sha256=RULE_PACK_HASH,
        rulepack_id=RULE_PACK_ID,
        rulepack_version=RULE_PACK_VERSION,
        seed=str(seed_int),
    )
