"""Helpers for assembling schedulable tasks from a work order."""

from __future__ import annotations

import math
from collections import deque
from collections.abc import Callable, Iterable
from typing import cast

from ..inventory import InventoryStatus
from ..models import IsolationPlan
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
DEFAULT_WORK_TASK_NAME = "work"
LOTO_COMPLETE_TASK_ID = "LOTO_COMPLETE"
WORK_COMPLETE_TASK_ID = "WORK_COMPLETE"
MILESTONE_DURATION_MIN = 1


def _minutes_from_seconds(duration_s: object, fallback_min: int) -> int:
    if isinstance(duration_s, (int, float)):
        return max(1, int(math.ceil(float(duration_s) / 60)))
    return max(1, fallback_min)


def build_isolation_tasks(
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
        duration_min = _minutes_from_seconds(action.duration_s, baseline_duration_min)
        mapped.append(
            PlanningTask(
                task_id=task_id,
                kind="isolation",
                name=f"isolation-{idx}",
                resources={default_resource_bucket: 1},
                duration=DurationSpec(
                    baseline_min=duration_min,
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


def _extract_work_steps(work_order: object) -> list[object]:
    for attr in ("work_tasks", "tasks", "operations", "work", "work_details"):
        value = getattr(work_order, attr, None)
        if isinstance(value, list):
            return value
    if isinstance(work_order, dict):
        for key in ("work_tasks", "tasks", "operations", "work", "work_details"):
            value = work_order.get(key)
            if isinstance(value, list):
                return value
    return []


def _work_item_field(item: object, *names: str) -> object | None:
    if isinstance(item, dict):
        for name in names:
            if name in item:
                return cast(object, item[name])
        return None
    for name in names:
        if hasattr(item, name):
            return cast(object, getattr(item, name))
    return None


def build_work_tasks(
    work_order: object,
    *,
    baseline_duration_min: int = DEFAULT_BASELINE_DURATION_MIN,
    default_resource_bucket: str = DEFAULT_RESOURCE_BUCKET,
    duration_variability_ratio: float = DEFAULT_DURATION_VARIABILITY_RATIO,
) -> list[PlanningTask]:
    """Build work-phase tasks from work-order details.

    Falls back to a single default work task when no details are available.
    """

    wo_id = getattr(work_order, "id", None) or (
        work_order.get("id") if isinstance(work_order, dict) else ""
    )
    prefix = wo_id or "wo"
    work_items = _extract_work_steps(work_order)
    tasks: list[PlanningTask] = []

    for idx, item in enumerate(work_items):
        task_id = f"{prefix}-work-{idx}"
        duration_min = _minutes_from_seconds(
            _work_item_field(item, "duration_s", "duration_sec", "duration_seconds"),
            baseline_duration_min,
        )
        name_value = _work_item_field(item, "name", "description", "title")
        name = str(name_value) if name_value else f"work-{idx}"
        tasks.append(
            PlanningTask(
                task_id=task_id,
                kind="work",
                name=name,
                resources={default_resource_bucket: 1},
                duration=DurationSpec(
                    baseline_min=duration_min,
                    variability_ratio=duration_variability_ratio,
                ),
                meta={"work_item_index": idx},
            )
        )

    if not tasks:
        tasks = [
            PlanningTask(
                task_id=f"{prefix}-work-0",
                kind="work",
                name=DEFAULT_WORK_TASK_NAME,
                resources={default_resource_bucket: 1},
                duration=DurationSpec(
                    baseline_min=max(1, baseline_duration_min),
                    variability_ratio=duration_variability_ratio,
                ),
                meta={"default_work_task": True},
            )
        ]

    ensure_unique_task_ids(tasks)
    return tasks


def build_restoration_tasks(
    plan: IsolationPlan,
    work_order: object,
    *,
    baseline_duration_min: int = DEFAULT_BASELINE_DURATION_MIN,
    default_resource_bucket: str = DEFAULT_RESOURCE_BUCKET,
    duration_variability_ratio: float = DEFAULT_DURATION_VARIABILITY_RATIO,
) -> list[PlanningTask]:
    """Create restoration tasks mirroring isolation actions in reverse order."""

    wo_id = getattr(work_order, "id", None) or (
        work_order.get("id") if isinstance(work_order, dict) else ""
    )
    prefix = wo_id or plan.plan_id
    tasks: list[PlanningTask] = []

    for idx, action in enumerate(reversed(plan.actions)):
        task_id = f"{prefix}-restore-{idx}"
        duration_min = _minutes_from_seconds(action.duration_s, baseline_duration_min)
        tasks.append(
            PlanningTask(
                task_id=task_id,
                kind="restoration",
                name=f"restoration-{idx}",
                resources={default_resource_bucket: 1},
                duration=DurationSpec(
                    baseline_min=duration_min,
                    variability_ratio=duration_variability_ratio,
                ),
                meta={
                    "restoration_action_index": len(plan.actions) - idx - 1,
                    "restoration_method": action.method,
                    "restoration_component_id": action.component_id,
                },
            )
        )

    ensure_unique_task_ids(tasks)
    return tasks


def _chain_within_group(tasks: list[PlanningTask]) -> None:
    previous_id: str | None = None
    for task in tasks:
        task.depends_on[:] = [previous_id] if previous_id is not None else []
        previous_id = task.task_id


def _link_groups(before: Iterable[PlanningTask], after: list[PlanningTask]) -> None:
    if not after:
        return
    before_list = list(before)
    if not before_list:
        return
    after[0].depends_on[:] = [before_list[-1].task_id]


def validate_dag_acyclic(tasks: list[PlanningTask]) -> None:
    """Raise ``ValueError`` when ``tasks`` contain cyclic dependencies."""

    ids = {task.task_id for task in tasks}
    indegree: dict[str, int] = {task.task_id: 0 for task in tasks}
    graph: dict[str, list[str]] = {task.task_id: [] for task in tasks}

    for task in tasks:
        for dep in task.depends_on:
            if dep in ids:
                graph[dep].append(task.task_id)
                indegree[task.task_id] += 1

    queue: deque[str] = deque([tid for tid, degree in indegree.items() if degree == 0])
    visited = 0
    while queue:
        node = queue.popleft()
        visited += 1
        for nxt in graph[node]:
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                queue.append(nxt)

    if visited != len(tasks):
        raise ValueError("planning task graph contains a cycle")


def build_job_dag(
    work_order: object,
    plan: IsolationPlan,
    *,
    baseline_duration_min: int = DEFAULT_BASELINE_DURATION_MIN,
    default_resource_bucket: str = DEFAULT_RESOURCE_BUCKET,
    duration_variability_ratio: float = DEFAULT_DURATION_VARIABILITY_RATIO,
) -> list[PlanningTask]:
    """Build full planning DAG in isolation → work → restoration order."""

    isolation_tasks = build_isolation_tasks(
        plan,
        baseline_duration_min=baseline_duration_min,
        default_resource_bucket=default_resource_bucket,
        duration_variability_ratio=duration_variability_ratio,
    )
    work_tasks = build_work_tasks(
        work_order,
        baseline_duration_min=baseline_duration_min,
        default_resource_bucket=default_resource_bucket,
        duration_variability_ratio=duration_variability_ratio,
    )
    restoration_tasks = build_restoration_tasks(
        plan,
        work_order,
        baseline_duration_min=baseline_duration_min,
        default_resource_bucket=default_resource_bucket,
        duration_variability_ratio=duration_variability_ratio,
    )

    if not isolation_tasks and not restoration_tasks:
        return []

    _chain_within_group(isolation_tasks)
    _chain_within_group(work_tasks)
    _chain_within_group(restoration_tasks)

    loto_complete = PlanningTask(
        task_id=LOTO_COMPLETE_TASK_ID,
        kind="milestone",
        name="LOTO complete",
        resources={},
        duration=DurationSpec(
            baseline_min=MILESTONE_DURATION_MIN, variability_ratio=0.0
        ),
        depends_on=[task.task_id for task in isolation_tasks],
        meta={"milestone": LOTO_COMPLETE_TASK_ID},
    )
    work_complete = PlanningTask(
        task_id=WORK_COMPLETE_TASK_ID,
        kind="milestone",
        name="Work complete",
        resources={},
        duration=DurationSpec(
            baseline_min=MILESTONE_DURATION_MIN, variability_ratio=0.0
        ),
        depends_on=[task.task_id for task in work_tasks],
        meta={"milestone": WORK_COMPLETE_TASK_ID},
    )

    for task in work_tasks:
        task.depends_on[:] = [*task.depends_on, LOTO_COMPLETE_TASK_ID]
    for task in restoration_tasks:
        task.depends_on[:] = [*task.depends_on, WORK_COMPLETE_TASK_ID]

    dag = (
        isolation_tasks
        + [loto_complete]
        + work_tasks
        + [work_complete]
        + restoration_tasks
    )
    ensure_unique_task_ids(dag)
    validate_dag_acyclic(dag)
    return dag


# Backwards-compatible alias for previous API users.
map_plan_tasks = build_isolation_tasks


def planning_to_scheduler_tasks(
    tasks: list[PlanningTask], *, include_resources: bool = False
) -> dict[str, SchedulerTask]:
    """Convert planning-layer tasks into runtime scheduler tasks."""

    ensure_unique_task_ids(tasks)
    return {
        task.task_id: to_scheduler_task(task, include_resources=include_resources)
        for task in tasks
    }
