from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

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
from loto.service import plan_and_evaluate
from loto.service.blueprints import Provenance, inventory_state

from .demo_data import demo_data


@dataclass
class WorkOrder:
    """Minimal work order representation for inventory checks."""

    id: str
    reservations: list[Reservation]


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
            "asset_tag": "uA",
            "impact_cfg": impact_cfg,
        }


def load_work_order_plan(
    workorder_id: str,
    *,
    strict_pre_applied_isolations: bool,
    state: Dict[str, object] | None,
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
    asset_tag = str(ctx["asset_tag"])
    if asset_tag not in impact_cfg.asset_units and impact_cfg.unit_data:
        impact_cfg.asset_units[asset_tag] = sorted(impact_cfg.unit_data)[0]

    permit = get_permit_adapter().fetch_permit(workorder_id) or {}
    cfg: Dict[str, Any] = {"callback_time_min": permit.get("callback_time_min", 0)}
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
