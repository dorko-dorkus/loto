"""Helpers for assembling schedulable tasks from a work order."""

from __future__ import annotations

import math
from collections.abc import Callable

from ..inventory import InventoryStatus
from ..models import IsolationPlan
from . import gates
from .des_engine import Task as SchedulerTask
from .task_model import (
    DurationSpec,
    PlanningTask,
    ensure_unique_task_ids,
    to_scheduler_task,
)

InventoryFn = Callable[[object], InventoryStatus]

DEFAULT_BASELINE_DURATION_MIN = 20
DEFAULT_RESOURCE_BUCKET = "Mechanical"
DEFAULT_DURATION_VARIABILITY_RATIO = 0.15


def map_plan_tasks(
    plan: IsolationPlan,
    *,
    baseline_duration_min: int = DEFAULT_BASELINE_DURATION_MIN,
    default_resource_bucket: str = DEFAULT_RESOURCE_BUCKET,
    duration_variability_ratio: float = DEFAULT_DURATION_VARIABILITY_RATIO,
) -> list[PlanningTask]:
    """Map each isolation action in ``plan`` to a deterministic planning task."""

    mapped: list[PlanningTask] = []
    previous_id: str | None = None
    for idx, action in enumerate(plan.actions):
        task_id = f"{plan.plan_id}-iso-{idx}"
        dependencies = [previous_id] if previous_id is not None else []
        valve_tag = (
            action.component_id.split(":", 1)[1]
            if ":" in action.component_id
            else action.component_id
        )
        duration_min = (
            int(math.ceil(action.duration_s / 60))
            if action.duration_s is not None
            else baseline_duration_min
        )
        mapped.append(
            PlanningTask(
                task_id=task_id,
                kind="isolation",
                name=f"isolation-{idx}",
                resources={default_resource_bucket: 1},
                duration=DurationSpec(
                    baseline_min=max(1, duration_min),
                    variability_ratio=duration_variability_ratio,
                ),
                depends_on=dependencies,
                meta={
                    "action_index": idx,
                    "method": action.method,
                    "component_id": action.component_id,
                    "valve_tag": valve_tag,
                },
            )
        )
        previous_id = task_id

    ensure_unique_task_ids(mapped)
    return mapped


def planning_to_scheduler_tasks(
    tasks: list[PlanningTask], *, include_resources: bool = False
) -> dict[str, SchedulerTask]:
    """Convert planning-layer tasks into runtime scheduler tasks."""

    ensure_unique_task_ids(tasks)
    return {
        task.task_id: to_scheduler_task(task, include_resources=include_resources)
        for task in tasks
    }


def from_work_order(
    work_order: object,
    plan: IsolationPlan,
    check_parts: InventoryFn | None = None,
    *,
    duration_variability_ratio: float = DEFAULT_DURATION_VARIABILITY_RATIO,
) -> dict[str, SchedulerTask]:
    """Return schedulable tasks for ``work_order``.

    Each :class:`~loto.models.IsolationAction` in ``plan`` becomes a sequential
    :class:`Task`.  When ``check_parts`` is provided and indicates that parts
    are missing, a :func:`gates.parts_available` predicate is attached to each
    task so execution will wait for parts to arrive.
    """

    planning_tasks = map_plan_tasks(
        plan, duration_variability_ratio=duration_variability_ratio
    )
    tasks = planning_to_scheduler_tasks(planning_tasks)

    if check_parts:
        status = check_parts(work_order)
        if status.blocked:
            wo_id = getattr(work_order, "id", "")
            gate = gates.parts_available(wo_id)
            for task in tasks.values():
                task.gate = (
                    gate if task.gate is None else gates.compose_gates(task.gate, gate)
                )

    return tasks
