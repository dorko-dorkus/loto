"""Pure wrappers chaining graph building, planning, simulation and impact."""

from __future__ import annotations

import hashlib
import os
import random
import time
from dataclasses import dataclass
from pathlib import Path
from typing import IO, Dict, Iterable, Mapping, Tuple

import structlog

from ..graph_builder import GraphBuilder
from ..impact import ImpactEngine, ImpactResult
from ..integrations import MaximoAdapter
from ..integrations._errors import AdapterRequestError
from ..isolation_planner import IsolationPlanner
from ..models import IsolationPlan, RulePack, SimReport, Stimulus
from ..scheduling import gates
from ..scheduling.assemble import InventoryFn
from ..sim_engine import SimEngine

logger = structlog.get_logger()


@dataclass(frozen=True)
class Provenance:
    """Record of deterministic inputs influencing planning."""

    seed: int | None
    rule_hash: str


def validate_fk_integrity(
    asset_id: str | None,
    location_id: str | None,
    *,
    adapter: MaximoAdapter | None = None,
) -> None:
    """Validate that asset and location identifiers exist in Maximo.

    Parameters
    ----------
    asset_id:
        Asset identifier to check.
    location_id:
        Location identifier to check.
    adapter:
        Optional :class:`~loto.integrations.maximo_adapter.MaximoAdapter`
        instance. A new one is created when omitted.

    Raises
    ------
    ValueError
        If the asset or location cannot be found.
    """

    adapter = adapter or MaximoAdapter()
    if not getattr(adapter, "base_url", None):
        return
    if asset_id:
        try:
            adapter.get_asset(asset_id)
        except AdapterRequestError as exc:  # pragma: no cover - sanity
            raise ValueError(f"Unknown asset '{asset_id}'") from exc
    if location_id:
        os_location = os.environ.get("MAXIMO_OS_LOCATION", "LOCATION")
        try:
            adapter._get(f"os/{os_location}/{location_id}")
        except AdapterRequestError as exc:  # pragma: no cover - sanity
            raise ValueError(f"Unknown location '{location_id}'") from exc


def plan_and_evaluate(
    line_csv: str | Path | IO[str],
    valve_csv: str | Path | IO[str],
    drain_csv: str | Path | IO[str],
    source_csv: str | Path | IO[str] | None = None,
    *,
    asset_tag: str,
    location_id: str | None = None,
    rule_pack: RulePack,
    stimuli: Iterable[Stimulus],
    asset_units: Dict[str, str],
    unit_data: Dict[str, Dict[str, float]],
    unit_areas: Dict[str, str],
    penalties: Dict[str, float] | None = None,
    asset_areas: Dict[str, str] | None = None,
    seed: int | None = None,
) -> Tuple[IsolationPlan, SimReport, ImpactResult, Provenance]:
    """Run builder → planner → simulator → impact evaluation pipeline.

    All parameters are in-memory objects to keep this function free of any
    I/O side effects.  CSV inputs may therefore be file-like objects such as
    :class:`io.StringIO` instances.  When ``seed`` is provided the random
    module is seeded to ensure deterministic output.  The returned
    :class:`Provenance` captures the seed and a hash of the rule pack used.
    """

    if seed is not None:
        random.seed(seed)

    validate_fk_integrity(asset_tag, location_id)

    builder = GraphBuilder()
    graphs = builder.from_csvs(line_csv, valve_csv, drain_csv, source_csv)
    summary = {
        name: {"nodes": g.number_of_nodes(), "edges": g.number_of_edges()}
        for name, g in graphs.items()
    }
    logger.info("ingest_complete", graphs=summary)

    # Mark edges leaving isolation points so the planner can identify them.
    for g in graphs.values():
        for u, v, data in g.edges(data=True):
            if g.nodes[u].get("is_isolation_point"):
                data["is_isolation_point"] = True

    planner = IsolationPlanner()
    start = time.perf_counter()
    plan = planner.compute(graphs, asset_tag=asset_tag, rule_pack=rule_pack)
    duration = time.perf_counter() - start
    logger.info("plan_generated", duration=duration)

    sim = SimEngine(seed=seed)
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

    rule_hash = hashlib.sha256(rule_pack.model_dump_json().encode()).hexdigest()
    provenance = Provenance(seed=seed, rule_hash=rule_hash)

    return plan, report, impact, provenance


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
