"""Wrappers around the scheduling utilities."""

from __future__ import annotations

from typing import Mapping

from ..models import IsolationPlan
from ..scheduling import assemble, des_engine, monte_carlo
from ..scheduling.des_engine import RunResult, Task
from ..scheduling.monte_carlo import MonteCarloResult


def assemble_tasks(
    work_order: object, plan: IsolationPlan, check_parts: assemble.InventoryFn | None = None
) -> dict[str, Task]:
    """Return tasks assembled from a work order and plan."""

    return assemble.from_work_order(work_order, plan, check_parts)


def run_schedule(
    tasks: Mapping[str, Task],
    resource_caps: Mapping[str, int],
    *,
    state: Mapping[str, object] | None = None,
    seed: int | None = None,
) -> RunResult:
    """Execute the discrete-event scheduler."""

    return des_engine.run(tasks, resource_caps, state=state, seed=seed)


def monte_carlo_schedule(
    tasks: Mapping[str, Task],
    resource_caps: Mapping[str, int],
    runs: int,
    *,
    state: Mapping[str, object] | None = None,
) -> MonteCarloResult:
    """Run Monte Carlo simulations of the scheduler."""

    return monte_carlo.simulate(tasks, resource_caps, runs=runs, state=state)
