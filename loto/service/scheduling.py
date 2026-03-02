"""Wrappers around the scheduling utilities."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import TypedDict

from ..inventory import InventoryStatus
from ..models import IsolationPlan
from ..scheduling import assemble, des_engine, monte_carlo
from ..scheduling.des_engine import RunResult, Task
from ..scheduling.monte_carlo import MonteCarloResult
from .blueprints import validate_fk_integrity


class MissingPart(TypedDict):
    """Structured representation of missing inventory requirements."""

    item_id: str
    quantity: int


class VerificationInfo(TypedDict):
    """Metadata for optional conditional scheduling tasks."""

    ddbb_candidates: list[str]
    applied_verification_tasks: list[str]


class AssembledTasks(TypedDict):
    """Structured output returned by :func:`assemble_tasks`."""

    tasks: dict[str, Task]
    parts_gate: dict[str, object]
    missing_parts: list[MissingPart]
    conditional: VerificationInfo


VerificationTaskBuilder = Callable[
    [object, IsolationPlan, Mapping[str, Task]], Mapping[str, Task]
]


def assemble_tasks(
    work_order: object,
    plan: IsolationPlan,
    check_parts: assemble.InventoryFn | None = None,
    verification_task_builder: VerificationTaskBuilder | None = None,
) -> AssembledTasks:
    """Return mapped tasks and inventory gate evaluation for a work order."""
    validate_fk_integrity(
        getattr(work_order, "asset_id", None), getattr(work_order, "location", None)
    )
    status = check_parts(work_order) if check_parts else InventoryStatus(blocked=False)

    def cached_status(_: object) -> InventoryStatus:
        return status

    tasks = assemble.from_work_order(
        work_order,
        plan,
        cached_status if check_parts is not None else None,
    )

    extra_tasks: Mapping[str, Task] = {}
    if verification_task_builder is not None:
        extra_tasks = verification_task_builder(work_order, plan, tasks)
        tasks.update(dict(extra_tasks))

    return {
        "tasks": tasks,
        "parts_gate": {
            "blocked": status.blocked,
            "status": "blocked_by_parts" if status.blocked else "feasible",
        },
        "missing_parts": [
            {"item_id": item.item_id, "quantity": item.quantity}
            for item in status.missing
        ],
        "conditional": {
            "ddbb_candidates": [
                check for check in plan.verifications if "DDBB" in check
            ],
            "applied_verification_tasks": sorted(extra_tasks),
        },
    }


def run_schedule(
    tasks: Mapping[str, Task],
    resource_caps: Mapping[str, int],
    *,
    state: Mapping[str, object] | None = None,
    seed: int | None = None,
) -> RunResult:
    """Execute the discrete-event scheduler."""

    return des_engine.run(tasks, resource_caps, state=state, seed=seed)


def monte_carlo_schedule(
    tasks: Mapping[str, Task],
    resource_caps: Mapping[str, int],
    runs: int,
    *,
    state: Mapping[str, object] | None = None,
    seed: int = 0,
) -> MonteCarloResult:
    """Run Monte Carlo simulations of the scheduler."""

    return monte_carlo.simulate(
        tasks,
        resource_caps,
        runs=runs,
        state=state,
        seed=seed,
    )
