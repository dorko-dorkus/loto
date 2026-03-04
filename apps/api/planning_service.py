from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import structlog

from loto.impact import ImpactResult
from loto.impact_config import load_impact_config
from loto.integrations import get_permit_adapter
from loto.integrations.stores_adapter import DemoStoresAdapter
from loto.inventory import (
    InventoryStatus,
    Reservation,
    StockItem,
    check_wo_parts_required,
)
from loto.models import IsolationPlan, RulePack
from loto.normalization import (
    canonicalize_exposure_mode,
    canonicalize_graph_tag,
    canonicalize_hazard_class,
    canonicalize_work_type,
)
from loto.service import plan_and_evaluate
from loto.service.blueprints import Provenance, inventory_state
from loto.work_scope import infer_exposure_mode

from .demo_data import demo_data

logger = structlog.get_logger()


@dataclass
class WorkOrder:
    """Minimal work order representation for inventory checks."""

    id: str
    reservations: list[Reservation]
    description: str | None = None
    trade: str | None = None
    job_steps: list[dict[str, Any]] | None = None


@dataclass
class WorkOrderPlanBundle:
    """Shared work-order context and planning result for API endpoints."""

    work_order: WorkOrder
    inv_status: InventoryStatus
    parts_status: Dict[str, str]
    missing_part_details: list[Dict[str, Any]]
    plan: IsolationPlan
    impact: ImpactResult
    provenance: Provenance

    @property
    def plan_version(self) -> str:
        digest = hashlib.sha256(
            "|".join(f"{a.component_id}:{a.method}" for a in self.plan.actions).encode()
        ).hexdigest()
        return digest[:12]

    @property
    def plan_action_set(self) -> list[str]:
        return [f"{a.component_id}:{a.method}" for a in self.plan.actions]


class DemoMaximoAdapter:
    """Tiny Maximo adapter serving demo data from the repository."""

    def load_context(self, workorder_id: str) -> Dict[str, Any]:
        base = Path(__file__).resolve().parents[2] / "demo"
        impact_cfg = load_impact_config(
            base / "unit_map.yaml", base / "redundancy_map.yaml"
        )
        return {
            "line_csv": base / "line_list.csv",
            "valve_csv": base / "valves.csv",
            "drain_csv": base / "drains.csv",
            "source_csv": base / "sources.csv",
            "asset_tag": canonicalize_graph_tag("uA"),
            "impact_cfg": impact_cfg,
        }


def load_work_order_plan(
    workorder_id: str,
    *,
    strict_pre_applied_isolations: bool,
    state: Dict[str, object] | None,
    work_type: str | None = None,
    hazard_class: str | list[str] | None = None,
    exposure_mode: str | None = None,
) -> tuple[WorkOrderPlanBundle, Dict[str, object]]:
    """Load work-order context and run the shared planner entrypoint."""

    stores = DemoStoresAdapter()
    bom = demo_data.get_bom(workorder_id)
    work_order = WorkOrder(
        id=workorder_id,
        reservations=[
            Reservation(
                item_id=line["item_id"],
                quantity=line["quantity"],
                critical=line.get("critical", False),
            )
            for line in bom
        ],
    )

    def lookup_stock(item_id: str) -> StockItem | None:
        try:
            status = stores.inventory_status(item_id)
        except KeyError:
            return None
        return StockItem(
            item_id=item_id,
            quantity=status.get("available", 0),
            reorder_point=status.get("reorder_point", 0),
        )

    inv_status = check_wo_parts_required(work_order, lookup_stock)
    parts_status: Dict[str, str] = {}
    missing_part_details: list[Dict[str, Any]] = []
    for res in work_order.reservations:
        stock = lookup_stock(res.item_id)
        available = stock.quantity if stock else 0
        reorder = stock.reorder_point if stock else 0
        if available < res.quantity:
            parts_status[res.item_id] = "short"
            missing_part_details.append(
                {
                    "item": res.item_id,
                    "required": res.quantity,
                    "available": available,
                    "shortfall": res.quantity - available,
                    "reason": "insufficient_available",
                }
            )
        elif res.critical and available <= reorder:
            parts_status[res.item_id] = "low"
            missing_part_details.append(
                {
                    "item": res.item_id,
                    "required": res.quantity,
                    "available": available,
                    "shortfall": 0,
                    "reason": "critical_at_or_below_reorder_point",
                }
            )
        else:
            parts_status[res.item_id] = "ok"

    adapter = DemoMaximoAdapter()
    ctx = adapter.load_context(workorder_id)
    impact_cfg = ctx["impact_cfg"]
    asset_tag = str(canonicalize_graph_tag(ctx["asset_tag"]))
    if asset_tag not in impact_cfg.asset_units and impact_cfg.unit_data:
        impact_cfg.asset_units[asset_tag] = sorted(impact_cfg.unit_data)[0]

    permit = get_permit_adapter().fetch_permit(workorder_id) or {}
    description = str(permit.get("description") or work_order.description or "")

    def infer_work_type() -> str:
        permit_work_type = canonicalize_work_type(permit.get("work_type"))
        if isinstance(permit_work_type, str) and permit_work_type:
            return permit_work_type
        lowered = description.lower()
        if "hot" in lowered and "work" in lowered:
            return "hot_work"
        if "inspect" in lowered:
            return "inspection_external"
        if "calib" in lowered:
            return "instrument_calibration"
        return "intrusive_mech"

    def infer_hazard_class() -> list[str]:
        permit_hazard = permit.get("hazard_class") or permit.get("hazard_classes")
        raw_values = (
            permit_hazard if isinstance(permit_hazard, list) else [permit_hazard]
        )
        values = [
            canonicalize_hazard_class(item)
            for item in raw_values
            if isinstance(item, str) and item.strip()
        ]
        if values:
            return values
        lowered = description.lower()
        inferred: list[str] = []
        if "pressure" in lowered:
            inferred.append("pressure")
        if "elect" in lowered:
            inferred.append("electrical")
        if "chem" in lowered:
            inferred.append("chemical")
        if "temp" in lowered or "thermal" in lowered:
            inferred.append("temperature")
        return inferred or ["mechanical"]

    def fallback_exposure_mode(normalized_hazards: list[str]) -> str:
        permit_exposure = canonicalize_exposure_mode(permit.get("exposure_mode"))
        if isinstance(permit_exposure, str) and permit_exposure:
            return permit_exposure
        lowered = description.lower()
        if "ignition" in lowered or "spark" in lowered or "hot work" in lowered:
            return "ignition_possible"
        if any(h in {"pressure", "chemical"} for h in normalized_hazards):
            return "release_possible"
        if any(h == "temperature" for h in normalized_hazards):
            return "thermal_only"
        return "none"

    provided_work_type = canonicalize_work_type(work_type)
    normalized_work_type = provided_work_type or infer_work_type()
    normalized_hazard_class: list[str]
    if isinstance(hazard_class, list):
        normalized_hazard_class = [
            canonicalize_hazard_class(item)
            for item in hazard_class
            if isinstance(item, str) and item.strip()
        ]
    elif isinstance(hazard_class, str):
        normalized_hazard_class = [canonicalize_hazard_class(hazard_class)]
    else:
        normalized_hazard_class = []
    if not normalized_hazard_class:
        normalized_hazard_class = infer_hazard_class()
    provided_exposure_mode = canonicalize_exposure_mode(exposure_mode)
    scope_inference = infer_exposure_mode(description, permit=permit)
    inferred_exposure_mode = scope_inference.exposure_mode or fallback_exposure_mode(
        normalized_hazard_class
    )
    normalized_exposure_mode = provided_exposure_mode or inferred_exposure_mode

    escalation_applied = (
        scope_inference.escalate_to_intrusive_mech
        and not provided_work_type
        and normalized_work_type != "intrusive_mech"
    )
    if escalation_applied:
        normalized_work_type = "intrusive_mech"

    inference_meta = {
        "exposure_mode": {
            "provided": provided_exposure_mode,
            "inferred": inferred_exposure_mode,
            "final": normalized_exposure_mode,
            "source": "request" if provided_exposure_mode else "inferred",
            "matched_terms": list(scope_inference.matched_terms),
        },
        "work_type": {
            "provided": provided_work_type,
            "final": normalized_work_type,
            "escalated_to_intrusive_mech": escalation_applied,
        },
    }
    logger.info("work_scope_inference", **inference_meta)

    cfg: Dict[str, Any] = {
        "callback_time_min": permit.get("callback_time_min", 0),
        "work_type": normalized_work_type,
        "hazard_class": normalized_hazard_class,
        "exposure_mode": normalized_exposure_mode,
    }
    pre_applied = permit.get("applied_isolations") or []

    def check_parts(wo: object) -> InventoryStatus:
        assert isinstance(wo, WorkOrder)
        return check_wo_parts_required(wo, lookup_stock)

    next_state = dict(inventory_state(work_order, check_parts, state))

    with (
        Path(ctx["line_csv"]).open() as line,
        Path(ctx["valve_csv"]).open() as valve,
        Path(ctx["drain_csv"]).open() as drain,
        Path(ctx["source_csv"]).open() as source,
    ):
        plan, _, impact, provenance = plan_and_evaluate(
            line,
            valve,
            drain,
            source,
            asset_tag=asset_tag,
            rule_pack=RulePack(risk_policies=None),
            stimuli=[],
            asset_units=impact_cfg.asset_units,
            unit_data=impact_cfg.unit_data,
            unit_areas=impact_cfg.unit_areas,
            penalties=impact_cfg.penalties,
            asset_areas=impact_cfg.asset_areas,
            config=cfg,
            pre_applied_isolations=pre_applied,
            strict_pre_applied_isolations=strict_pre_applied_isolations,
            work_type=normalized_work_type,
            hazard_class=normalized_hazard_class,
            exposure_mode=normalized_exposure_mode,
        )

    provenance = Provenance(
        seed=provenance.seed,
        rule_hash=provenance.rule_hash,
        context=inference_meta,
    )

    return (
        WorkOrderPlanBundle(
            work_order=work_order,
            inv_status=inv_status,
            parts_status=parts_status,
            missing_part_details=missing_part_details,
            plan=plan,
            impact=impact,
            provenance=provenance,
        ),
        next_state,
    )
