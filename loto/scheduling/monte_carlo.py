"""Monte Carlo wrapper for the discrete-event scheduling engine.

This module provides a thin helper around :mod:`loto.scheduling.des_engine`
that runs the scheduler multiple times and summarises the results.  For each
run the makespan and task completion times are recorded.  Once all runs are
complete percentile statistics and task criticality probabilities are
reported.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, Iterable, Mapping

from .des_engine import RunResult, Task, run


@dataclass
class MonteCarloResult:
    """Summary statistics from a Monte Carlo scheduling simulation."""

    task_percentiles: Dict[str, Dict[str, float]]
    makespan_percentiles: Dict[str, float]
    criticality: Dict[str, float]


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
