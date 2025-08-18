from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List
from uuid import uuid4

from fastapi import FastAPI

from loto.impact_config import load_impact_config
from loto.models import RulePack
from loto.service import plan_and_evaluate

from .schemas import BlueprintRequest, BlueprintResponse, Step

app = FastAPI(title="loto API")


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
        plan, _, impact, _prov = plan_and_evaluate(
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


@app.post("/schedule")
async def post_schedule(payload: dict) -> dict[str, str]:
    """Placeholder for schedule creation."""
    _ = payload  # suppress unused variable warning
    return {"detail": "Not implemented"}


@app.post("/propose")
async def post_propose(payload: dict[str, Any]) -> Dict[str, Any]:
    """Return diff of proposed targets/assignments with an idempotency key."""

    current = {
        "targets": {"asset": "A"},
        "assignments": {"task": "worker"},
    }

    proposed_targets = payload.get("targets", {})
    proposed_assignments = payload.get("assignments", {})

    def diff(
        current_map: Dict[str, Any], proposed_map: Dict[str, Any]
    ) -> Dict[str, Any]:
        added = {k: v for k, v in proposed_map.items() if k not in current_map}
        removed = {k: v for k, v in current_map.items() if k not in proposed_map}
        changed = {
            k: {"from": current_map[k], "to": proposed_map[k]}
            for k in proposed_map
            if k in current_map and current_map[k] != proposed_map[k]
        }
        return {"added": added, "removed": removed, "changed": changed}

    return {
        "idempotency_key": str(uuid4()),
        "target_diff": diff(current["targets"], proposed_targets),
        "assignment_diff": diff(current["assignments"], proposed_assignments),
    }


@app.get("/workorders/{workorder_id}")
async def get_workorder(workorder_id: str) -> dict[str, str]:
    """Mock work order fetch."""
    return {"workorder_id": workorder_id, "status": "mocked"}
