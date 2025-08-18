"""Pure wrappers chaining graph building, planning, simulation and impact."""

from __future__ import annotations

from pathlib import Path
from typing import IO, Dict, Iterable, Mapping, Tuple

from ..graph_builder import GraphBuilder
from ..impact import ImpactEngine, ImpactResult
from ..isolation_planner import IsolationPlanner
from ..models import IsolationPlan, RulePack, SimReport, Stimulus
from ..scheduling import gates
from ..scheduling.assemble import InventoryFn
from ..sim_engine import SimEngine


def plan_and_evaluate(
    line_csv: str | Path | IO[str],
    valve_csv: str | Path | IO[str],
    drain_csv: str | Path | IO[str],
    source_csv: str | Path | IO[str] | None = None,
    *,
    asset_tag: str,
    rule_pack: RulePack,
    stimuli: Iterable[Stimulus],
    asset_units: Dict[str, str],
    unit_data: Dict[str, Dict[str, float]],
    unit_areas: Dict[str, str],
    penalties: Dict[str, float] | None = None,
    asset_areas: Dict[str, str] | None = None,
) -> Tuple[IsolationPlan, SimReport, ImpactResult]:
    """Run builder → planner → simulator → impact evaluation pipeline.

    All parameters are in-memory objects to keep this function free of any
    I/O side effects.  CSV inputs may therefore be file-like objects such as
    :class:`io.StringIO` instances.
    """

    builder = GraphBuilder()
    graphs = builder.from_csvs(line_csv, valve_csv, drain_csv, source_csv)

    # Mark edges leaving isolation points so the planner can identify them.
    for g in graphs.values():
        for u, v, data in g.edges(data=True):
            if g.nodes[u].get("is_isolation_point"):
                data["is_isolation_point"] = True

    planner = IsolationPlanner()
    plan = planner.compute(graphs, asset_tag=asset_tag, rule_pack=rule_pack)

    sim = SimEngine()
    applied = sim.apply(plan, graphs)
    report = sim.run_stimuli(applied, list(stimuli), rule_pack)

    impact = ImpactEngine().evaluate(
        applied,
        asset_units=asset_units,
        unit_data=unit_data,
        unit_areas=unit_areas,
        penalties=penalties,
        asset_areas=asset_areas,
    )

    return plan, report, impact


def inventory_state(
    work_order: object,
    check_parts: InventoryFn | None,
    state: Mapping[str, object] | None = None,
) -> Mapping[str, object]:
    """Return scheduler state seeded with parts availability.

    Parameters
    ----------
    work_order:
        Object exposing an ``id`` attribute identifying the work order.
    check_parts:
        Optional callable returning an :class:`~loto.inventory.InventoryStatus`.
    state:
        Optional existing state mapping to update.

    Returns
    -------
    dict[str, object]
        New state mapping including the work order's parts readiness.
    """

    state = dict(state or {})
    if check_parts:
        status = check_parts(work_order)
        wo_id = getattr(work_order, "id", "")
        state = dict(gates.feed_parts_state(state, wo_id, status.ready))
    return state
