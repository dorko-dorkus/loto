"""Helpers for assembling schedulable tasks from a work order."""

from __future__ import annotations

from collections.abc import Callable

from ..inventory import InventoryStatus
from ..models import IsolationPlan
from . import gates
from .des_engine import Task

InventoryFn = Callable[[object], InventoryStatus]


def from_work_order(
    work_order: object,
    plan: IsolationPlan,
    check_parts: InventoryFn | None = None,
) -> dict[str, Task]:
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
    dict[str, Task]
        Mapping of task identifier to :class:`Task`.
    """

    tasks: dict[str, Task] = {}
    prev: str | None = None
    for idx, action in enumerate(plan.actions):
        tid = f"{plan.plan_id}-{idx}"
        predecessors = [prev] if prev else []
        dur = int(action.duration_s or 1)
        tasks[tid] = Task(duration=dur, predecessors=predecessors)
        prev = tid

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
