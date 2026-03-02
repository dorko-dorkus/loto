"""Monte Carlo scheduling utilities.

This module provides two layers:

* a richer simulation-input model that captures explicit task/dependency,
  capacity, calendar and run-configuration data.
* a compatibility wrapper (:func:`simulate`) that keeps existing callers of the
  original task-map interface working.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Dict, Iterable, Literal, Mapping

from .des_engine import RunResult, Task, run


@dataclass
class MonteCarloResult:
    """Summary statistics from a Monte Carlo scheduling simulation."""

    task_percentiles: Dict[str, Dict[str, float]]
    makespan_percentiles: Dict[str, float]
    criticality: Dict[str, float]


@dataclass(frozen=True)
class CalendarSpec:
    """Calendar availability model.

    ``kind='always_on'`` is the MVP behaviour and allows work at all times.
    """

    kind: Literal["always_on"] = "always_on"


@dataclass(frozen=True)
class DurationDistribution:
    """Task duration sampling distribution."""

    kind: Literal["fixed", "uniform"] = "fixed"
    low: float = 1.0
    high: float = 1.0


@dataclass(frozen=True)
class SimulationTaskInput:
    """Serializable task model for simulation input."""

    base_duration: int
    predecessors: tuple[str, ...] = ()
    resources: Mapping[str, int] = field(default_factory=dict)
    calendar: str = "always_on"
    distribution: DurationDistribution = DurationDistribution()
    cost_per_time: float | None = None


@dataclass(frozen=True)
class RunConfig:
    """Configuration for a Monte Carlo campaign."""

    N: int = 300
    seed: int = 0


@dataclass(frozen=True)
class SimulationInput:
    """Top-level input model for Monte Carlo scheduling."""

    tasks: Mapping[str, SimulationTaskInput]
    resource_capacities: Mapping[str, int]
    calendars: Mapping[str, CalendarSpec]
    run_config: RunConfig


@dataclass
class RunMetrics:
    """Per-run completion metrics captured during simulation."""

    run_index: int
    makespan: int
    completion_times: Dict[str, int]
    total_cost: float | None


@dataclass
class SimulationSummary:
    """Aggregated outputs for the new simulation-input model."""

    p10: float
    p50: float
    p90: float
    expected_makespan: float
    expected_cost: float | None
    run_metrics: list[RunMetrics]
    provenance: Dict[str, str]


def _percentiles(samples: Iterable[int]) -> Dict[str, float]:
    """Return P10/P50/P80/P90 percentiles of *samples*.

    Percentiles are computed using linear interpolation between closest ranks.
    """

    values = sorted(samples)
    if not values:
        return {"P10": 0.0, "P50": 0.0, "P80": 0.0, "P90": 0.0}

    def pct(p: float) -> float:
        k = (len(values) - 1) * p
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return float(values[int(k)])
        return float(values[f] + (values[c] - values[f]) * (k - f))

    return {
        "P10": pct(0.10),
        "P50": pct(0.50),
        "P80": pct(0.80),
        "P90": pct(0.90),
    }


def _topo_order(tasks: Mapping[str, Task]) -> list[str]:
    """Return tasks in topological order based on predecessor links."""

    remaining: Dict[str, set[str]] = {
        tid: set(task.predecessors) for tid, task in tasks.items()
    }
    order: list[str] = []
    ready = sorted([tid for tid, preds in remaining.items() if not preds])
    while ready:
        tid = ready.pop(0)
        order.append(tid)
        for sid, preds in list(remaining.items()):
            if tid in preds:
                preds.remove(tid)
                if not preds:
                    ready.append(sid)
                    ready.sort()
        remaining.pop(tid, None)
    if remaining:
        raise ValueError("Task graph contains a cycle")
    return order


def _critical_tasks(tasks: Mapping[str, Task], result: RunResult) -> set[str]:
    """Identify tasks on the critical path for a single run."""

    starts = result.starts
    ends = result.ends
    durations = {tid: ends[tid] - starts[tid] for tid in starts}

    succs: Dict[str, list[str]] = {tid: [] for tid in tasks}
    for tid, task in tasks.items():
        for pred in task.predecessors:
            succs[pred].append(tid)

    order = _topo_order(tasks)
    makespan = max(ends.values()) if ends else 0
    latest_finish: Dict[str, int] = {tid: makespan for tid in tasks}
    latest_start: Dict[str, int] = {}
    for tid in reversed(order):
        if succs[tid]:
            latest_finish[tid] = min(latest_start[s] for s in succs[tid])
        latest_start[tid] = latest_finish[tid] - durations.get(tid, 0)

    critical: set[str] = set()
    for tid in starts:
        slack = latest_start[tid] - starts[tid]
        if slack == 0:
            critical.add(tid)
    return critical


def simulate(
    tasks: Mapping[str, Task],
    resource_caps: Mapping[str, int],
    runs: int,
    state: Mapping[str, object] | None = None,
) -> MonteCarloResult:
    """Run *runs* Monte Carlo simulations of the scheduler.

    Parameters
    ----------
    tasks:
        Mapping of task ID to :class:`Task` specification.
    resource_caps:
        Resource capacity constraints passed to the scheduler.
    runs:
        Number of independent simulations to perform.
    state:
        Optional global state forwarded to task gate predicates.
    """

    end_samples: Dict[str, list[int]] = {tid: [] for tid in tasks}
    makespans: list[int] = []
    crit_counts: Dict[str, int] = {tid: 0 for tid in tasks}

    for i in range(runs):
        result = run(tasks, resource_caps, state=state, seed=i)
        for tid, end in result.ends.items():
            end_samples[tid].append(end)
        makespan = max(result.ends.values()) if result.ends else 0
        makespans.append(makespan)
        for tid in _critical_tasks(tasks, result):
            crit_counts[tid] += 1

    task_percentiles = {
        tid: _percentiles(samples) for tid, samples in end_samples.items()
    }
    makespan_percentiles = _percentiles(makespans)
    criticality = {tid: crit_counts[tid] / runs for tid in tasks}

    return MonteCarloResult(task_percentiles, makespan_percentiles, criticality)


def _sample_duration(
    base_duration: int, distribution: DurationDistribution, rng: random.Random
) -> int:
    if distribution.kind == "fixed":
        return max(1, int(base_duration))
    if distribution.kind == "uniform":
        sampled = base_duration * rng.uniform(distribution.low, distribution.high)
        return max(1, int(round(sampled)))
    raise ValueError(f"unsupported distribution kind: {distribution.kind}")


def simulate_input_model(sim_input: SimulationInput) -> SimulationSummary:
    """Run Monte Carlo using the explicit simulation-input model."""

    makespans: list[int] = []
    costs: list[float] = []
    run_metrics: list[RunMetrics] = []
    base_seed = sim_input.run_config.seed

    for run_idx in range(sim_input.run_config.N):
        rng = random.Random(base_seed + run_idx)
        sampled_tasks: dict[str, Task] = {}
        for task_id, task in sim_input.tasks.items():
            calendar = sim_input.calendars.get(task.calendar, CalendarSpec())
            if calendar.kind != "always_on":
                raise ValueError(f"unsupported calendar kind: {calendar.kind}")
            sampled_tasks[task_id] = Task(
                duration=_sample_duration(task.base_duration, task.distribution, rng),
                predecessors=task.predecessors,
                resources=task.resources,
                calendar=lambda _t: True,
            )

        result = run(
            sampled_tasks,
            sim_input.resource_capacities,
            seed=base_seed + run_idx,
        )
        makespan = max(result.ends.values()) if result.ends else 0
        makespans.append(makespan)

        total_cost = 0.0
        has_cost = False
        for task_id, task in sim_input.tasks.items():
            if task.cost_per_time is not None and task_id in result.ends:
                start = result.starts[task_id]
                end = result.ends[task_id]
                total_cost += (end - start) * task.cost_per_time
                has_cost = True
        if has_cost:
            costs.append(total_cost)

        run_metrics.append(
            RunMetrics(
                run_index=run_idx,
                makespan=makespan,
                completion_times=dict(result.ends),
                total_cost=total_cost if has_cost else None,
            )
        )

    pct = _percentiles(makespans)
    expected_cost = sum(costs) / len(costs) if costs else None
    return SimulationSummary(
        p10=pct["P10"],
        p50=pct["P50"],
        p90=pct["P90"],
        expected_makespan=sum(makespans) / len(makespans) if makespans else 0.0,
        expected_cost=expected_cost,
        run_metrics=run_metrics,
        provenance={
            "random_seed": str(base_seed),
            "sample_count": str(sim_input.run_config.N),
            "seed_strategy": "deterministic",
            "distribution": ",".join(
                sorted({task.distribution.kind for task in sim_input.tasks.values()})
            ),
        },
    )
