"""Planning-layer task model and mapper to runtime scheduler tasks."""

from __future__ import annotations

import random
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Literal, TypeAlias

from .des_engine import DurationDistribution
from .des_engine import Task as SchedulerTask


@dataclass(frozen=True)
class DeterministicDurationSpec:
    """Fixed duration configuration in minutes."""

    kind: Literal["deterministic"] = "deterministic"
    minutes: int = 1


@dataclass(frozen=True)
class TriangularDurationSpec:
    """Triangular duration configuration in minutes."""

    kind: Literal["triangular"] = "triangular"
    min: int = 1
    mode: int = 1
    max: int = 1


DurationSpec: TypeAlias = DeterministicDurationSpec | TriangularDurationSpec


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
    gate: Callable[[Mapping[str, object]], bool] | None = None


def duration_spec_from_baseline_variability(
    baseline_min: int,
    variability_ratio: float = 0.0,
) -> DurationSpec:
    """Create a :class:`DurationSpec` from the legacy baseline/variability form."""

    baseline = max(1, int(baseline_min))
    variability = max(0.0, float(variability_ratio))
    if variability <= 0:
        return DeterministicDurationSpec(minutes=baseline)
    minimum = max(1, int(round(baseline * (1.0 - variability))))
    maximum = max(minimum, int(round(baseline * (1.0 + variability))))
    return TriangularDurationSpec(min=minimum, mode=baseline, max=maximum)


def duration_sampler_from_spec(
    duration: DurationSpec,
) -> tuple[int | Callable[[random.Random], int], int, DurationDistribution]:
    """Convert a planning-layer duration spec into runtime scheduling representation."""

    if duration.kind == "deterministic":
        minutes = max(1, int(duration.minutes))
        return (
            minutes,
            minutes,
            DurationDistribution(kind="fixed"),
        )

    minimum = max(1, int(duration.min))
    mode = max(minimum, int(duration.mode))
    maximum = max(mode, int(duration.max))

    def triangular_sampler(rng: random.Random) -> int:
        sampled = rng.triangular(minimum, maximum, mode)
        return max(1, int(round(sampled)))

    return (
        triangular_sampler,
        mode,
        DurationDistribution(
            kind="triangular",
            low=minimum / mode,
            mode=1.0,
            high=maximum / mode,
        ),
    )


def to_scheduler_task(
    task: PlanningTask, *, include_resources: bool = False
) -> SchedulerTask:
    """Map a planning task into the runtime scheduler primitive."""

    runtime_duration, base_duration, distribution = duration_sampler_from_spec(
        task.duration
    )
    runtime_resources = dict(task.resources) if include_resources else {}
    return SchedulerTask(
        duration=runtime_duration,
        predecessors=tuple(task.depends_on),
        resources=runtime_resources,
        gate=task.gate,
        base_duration=base_duration,
        distribution=distribution,
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
