"""Helpers for assembling schedulable tasks from a work order."""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass, field

from ..inventory import InventoryStatus
from ..models import IsolationPlan
from . import gates
from .des_engine import Task as SchedulerTask

InventoryFn = Callable[[object], InventoryStatus]

DEFAULT_BASELINE_DURATION_MIN = 20
DEFAULT_RESOURCE_BUCKET = "Mechanical"


@dataclass(frozen=True)
class MappedTask:
    """Domain scheduling task mapped from an isolation action."""

    id: str
    action_ref: str
    baseline_duration_min: int
    resources: tuple[str, ...] = (DEFAULT_RESOURCE_BUCKET,)
    dependencies: tuple[str, ...] = ()
    metadata: dict[str, object] = field(default_factory=dict)


def map_plan_tasks(
    plan: IsolationPlan,
    *,
    baseline_duration_min: int = DEFAULT_BASELINE_DURATION_MIN,
    default_resource_bucket: str = DEFAULT_RESOURCE_BUCKET,
) -> list[MappedTask]:
    """Map each isolation action in ``plan`` to a deterministic domain task."""

    mapped: list[MappedTask] = []
    previous_id: str | None = None
    for idx, action in enumerate(plan.actions):
        task_id = f"{plan.plan_id}-{idx}"
        dependencies = (previous_id,) if previous_id is not None else ()
        duration_min = (
            int(math.ceil(action.duration_s / 60))
            if action.duration_s is not None
            else baseline_duration_min
        )
        mapped.append(
            MappedTask(
                id=task_id,
                action_ref=f"{action.method}:{action.component_id}",
                baseline_duration_min=max(1, duration_min),
                resources=(default_resource_bucket,),
                dependencies=dependencies,
                metadata={"action_index": idx},
            )
        )
        previous_id = task_id

    return mapped


def from_work_order(
    work_order: object,
    plan: IsolationPlan,
    check_parts: InventoryFn | None = None,
) -> dict[str, SchedulerTask]:
    """Return schedulable tasks for ``work_order``.

    Each :class:`~loto.models.IsolationAction` in ``plan`` becomes a sequential
    :class:`Task`.  When ``check_parts`` is provided and indicates that parts
    are missing, a :func:`gates.parts_available` predicate is attached to each
    task so execution will wait for parts to arrive.

    Parameters
    ----------
    work_order:
        Object exposing an ``id`` attribute identifying the work order.
    plan:
        Isolation plan describing ordered actions.
    check_parts:
        Optional callable returning an :class:`~loto.inventory.InventoryStatus`
        for ``work_order``.

    Returns
    -------
    dict[str, SchedulerTask]
        Mapping of task identifier to scheduler :class:`~loto.scheduling.des_engine.Task`.
    """

    tasks: dict[str, SchedulerTask] = {}
    for item in map_plan_tasks(plan):
        tasks[item.id] = SchedulerTask(
            duration=item.baseline_duration_min,
            predecessors=item.dependencies,
        )

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
