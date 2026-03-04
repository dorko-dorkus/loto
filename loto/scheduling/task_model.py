"""Planning-layer task model and mapper to runtime scheduler tasks."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from .des_engine import DurationDistribution
from .des_engine import Task as SchedulerTask


@dataclass(frozen=True)
class DurationSpec:
    """Duration configuration used before mapping to runtime tasks."""

    baseline_min: int
    variability_ratio: float = 0.0


@dataclass(frozen=True)
class PlanningTask:
    """Scheduling task representation used at the planning layer."""

    task_id: str
    kind: Literal["isolation", "work", "restoration", "milestone"]
    name: str
    resources: dict[str, int]
    duration: DurationSpec
    depends_on: list[str] = field(default_factory=list)
    meta: dict[str, object] = field(default_factory=dict)


def to_scheduler_task(
    task: PlanningTask, *, include_resources: bool = False
) -> SchedulerTask:
    """Map a planning task into the runtime scheduler primitive."""

    variability = max(0.0, float(task.duration.variability_ratio))
    baseline = max(1, int(task.duration.baseline_min))
    runtime_resources = dict(task.resources) if include_resources else {}
    return SchedulerTask(
        duration=baseline,
        predecessors=tuple(task.depends_on),
        resources=runtime_resources,
        base_duration=baseline,
        distribution=DurationDistribution(
            kind="uniform" if variability > 0 else "fixed",
            low=max(0.0, 1.0 - variability),
            high=max(1.0 - variability, 1.0 + variability),
        ),
    )


def ensure_unique_task_ids(tasks: list[PlanningTask]) -> None:
    """Validate that planning tasks have unique IDs."""

    seen: set[str] = set()
    duplicates: set[str] = set()
    for task in tasks:
        if task.task_id in seen:
            duplicates.add(task.task_id)
        seen.add(task.task_id)

    if duplicates:
        dup = ", ".join(sorted(duplicates))
        raise ValueError(f"duplicate planning task IDs: {dup}")
