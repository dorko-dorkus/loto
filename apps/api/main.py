from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List
from uuid import uuid4

from fastapi import FastAPI
from pydantic import BaseModel, Field

from loto.impact_config import load_impact_config
from loto.models import RulePack
from loto.service import plan_and_evaluate

from .pid_endpoints import router as pid_router
from .schemas import BlueprintRequest, BlueprintResponse, Step

app = FastAPI(title="loto API")
app.include_router(pid_router)


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


@app.post("/schedule")
async def post_schedule(payload: dict) -> dict[str, str]:
    """Placeholder for schedule creation."""
    _ = payload  # suppress unused variable warning
    return {"detail": "Not implemented"}


@app.get("/workorders/{workorder_id}")
async def get_workorder(workorder_id: str) -> dict[str, str]:
    """Mock work order fetch."""
    return {"workorder_id": workorder_id, "status": "mocked"}
