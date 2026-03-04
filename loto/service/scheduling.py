"""Wrappers around the scheduling utilities."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import replace
from typing import TypedDict

from ..inventory import InventoryStatus
from ..models import IsolationPlan
from ..scheduling import assemble, des_engine, gates, monte_carlo
from ..scheduling.des_engine import DurationDistribution, RunResult, Task
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
    task_meta: dict[str, dict[str, object]]
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
    *,
    duration_variability_ratio: float = assemble.DEFAULT_DURATION_VARIABILITY_RATIO,
) -> AssembledTasks:
    """Return mapped tasks and inventory gate evaluation for a work order."""
    validate_fk_integrity(
        getattr(work_order, "asset_id", None), getattr(work_order, "location", None)
    )
    status = check_parts(work_order) if check_parts else InventoryStatus(blocked=False)

    planning_tasks = assemble.build_job_dag(
        work_order,
        plan,
        duration_variability_ratio=duration_variability_ratio,
    )

    if check_parts is not None and status.blocked:
        wo_id = getattr(work_order, "id", "")
        gate = gates.parts_available(wo_id)
        for idx, task in enumerate(planning_tasks):
            planning_tasks[idx] = replace(
                task,
                gate=(
                    gate if task.gate is None else gates.compose_gates(task.gate, gate)
                ),
            )

    tasks = assemble.planning_to_scheduler_tasks(planning_tasks)

    extra_tasks: Mapping[str, Task] = {}
    if verification_task_builder is not None:
        extra_tasks = verification_task_builder(work_order, plan, tasks)
        tasks.update(dict(extra_tasks))

    return {
        "tasks": tasks,
        "task_meta": {task.task_id: dict(task.meta) for task in planning_tasks},
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


def apply_duration_variability(
    tasks: Mapping[str, Task], spread_ratio: float = 0.15
) -> dict[str, Task]:
    """Return tasks with duration distribution metadata attached."""

    normalized_ratio = max(0.0, float(spread_ratio))
    wrapped: dict[str, Task] = {}
    for task_id, task in tasks.items():
        if task.distribution is not None and task.base_duration is not None:
            wrapped[task_id] = task
            continue

        if callable(task.duration):
            wrapped[task_id] = task
            continue

        base_duration = max(1, int(task.duration))
        wrapped[task_id] = Task(
            duration=base_duration,
            predecessors=task.predecessors,
            resources=task.resources,
            calendar=task.calendar,
            gate=task.gate,
            base_duration=base_duration,
            distribution=DurationDistribution(
                kind="uniform" if normalized_ratio > 0 else "fixed",
                low=max(0.0, 1.0 - normalized_ratio),
                high=max(1.0 - normalized_ratio, 1.0 + normalized_ratio),
            ),
        )

    return wrapped


def monte_carlo_schedule(
    tasks: Mapping[str, Task],
    resource_caps: Mapping[str, int],
    runs: int,
    *,
    state: Mapping[str, object] | None = None,
    seed: int | None = 0,
) -> MonteCarloResult:
    """Run Monte Carlo simulations of the scheduler."""

    return monte_carlo.simulate(
        tasks,
        resource_caps,
        runs=runs,
        state=state,
        seed=seed,
    )
