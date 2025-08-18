"""Discrete-event scheduling engine."""

from __future__ import annotations

import heapq
import random
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, Mapping


@dataclass
class Task:
    """Represents a schedulable task.

    Parameters
    ----------
    duration:
        Either a constant duration in time units or a callable accepting
        ``random.Random`` and returning the duration.  Durations are
        interpreted as integer time units.
    predecessors:
        IDs of tasks that must complete before this task may start.
    resources:
        Mapping of resource names to the quantity required.
    calendar:
        Optional predicate returning ``True`` when work may be performed at
        a given time.
    gate:
        Optional predicate that must evaluate to ``True`` for the task to
        start.  Gates receive the global ``state`` mapping supplied to
        :func:`run`.
    """

    duration: int | Callable[[random.Random], int]
    predecessors: Iterable[str] = field(default_factory=list)
    resources: Mapping[str, int] = field(default_factory=dict)
    calendar: Callable[[int], bool] | None = None
    gate: Callable[[Mapping[str, Any]], bool] | None = None


@dataclass
class RunResult:
    """Result of a scheduling run."""

    starts: Dict[str, int]
    ends: Dict[str, int]
    queues: Dict[str, list[str]]
    violations: list[str]
    seed: int


def _duration(task: Task, rng: random.Random) -> int:
    dur = task.duration
    if callable(dur):
        return int(dur(rng))
    return int(dur)


def run(
    tasks: Mapping[str, Task],
    resource_caps: Mapping[str, int],
    state: Mapping[str, Any] | None = None,
    *,
    resource_calendars: Mapping[str, Callable[[int], bool]] | None = None,
    seed: int | None = None,
    max_time: int | None = None,
) -> RunResult:
    """Run a simple discrete-event schedule.

    Parameters
    ----------
    tasks:
        Mapping of task ID to :class:`Task` specification.
    resource_caps:
        Mapping of resource name to available capacity.
    state:
        Optional state mapping consulted by task gate predicates.
    seed:
        Optional seed for duration sampling.
    """

    rng = random.Random(seed)
    seed = seed if seed is not None else 0
    state = state or {}
    resource_calendars = resource_calendars or {}
    max_time = 10_000 if max_time is None else max_time

    time = 0
    starts: Dict[str, int] = {}
    ends: Dict[str, int] = {}
    remaining = set(tasks.keys())
    running: list[tuple[int, str]] = []  # heap of (end_time, task_id)
    available = dict(resource_caps)
    queues: dict[str, list[str]] = defaultdict(list)
    violations: list[str] = []
    durations: Dict[str, int] = {}

    while remaining or running:
        started: list[str] = []
        violated: list[str] = []
        for tid in sorted(remaining):
            task = tasks[tid]
            dur = durations.setdefault(tid, _duration(task, rng))
            if any(pred not in ends for pred in task.predecessors):
                continue
            if task.gate and not task.gate(state):
                continue
            if task.calendar and not all(task.calendar(time + dt) for dt in range(dur)):
                continue

            over_cap = [
                res
                for res, req in task.resources.items()
                if req > resource_caps.get(res, 0)
            ]
            if over_cap:
                violations.append(tid)
                violated.append(tid)
                continue

            blocked = False
            for res in task.resources:
                cal = resource_calendars.get(res)
                if cal and not all(cal(time + dt) for dt in range(dur)):
                    blocked = True
                    break
            if blocked:
                continue

            missing = [
                res
                for res, req in task.resources.items()
                if available.get(res, 0) < req
            ]
            if missing:
                for res in missing:
                    if tid not in queues[res]:
                        queues[res].append(tid)
                continue

            starts[tid] = time
            end_time = time + dur
            heapq.heappush(running, (end_time, tid))
            for res, req in task.resources.items():
                available[res] = available.get(res, 0) - req
            started.append(tid)

        for tid in started + violated:
            remaining.remove(tid)

        if running:
            next_time, tid = heapq.heappop(running)
            time = next_time
            ends[tid] = time
            task = tasks[tid]
            for res, req in task.resources.items():
                available[res] = available.get(res, 0) + req
            # handle other tasks completing at same time
            while running and running[0][0] == time:
                next_time, tid = heapq.heappop(running)
                ends[tid] = time
                task = tasks[tid]
                for res, req in task.resources.items():
                    available[res] = available.get(res, 0) + req
        elif remaining:
            # No tasks running; advance time.  If all tasks are gated, stop.
            if time >= max_time:
                violations.extend(sorted(remaining))
                break
            gated: list[str] = []
            for tid in remaining:
                gate = tasks[tid].gate
                if gate and not gate(state):
                    gated.append(tid)
            if len(gated) == len(remaining):
                violations.extend(sorted(gated))
                break
            # otherwise advance to next integer time until calendars open
            time += 1

    return RunResult(starts, ends, dict(queues), violations, seed)
