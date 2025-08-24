from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Any, Dict, Mapping, Sequence, Tuple

from .des_engine import Task, run
from .objective import integrate_cost

Point = Tuple[float, float]


@dataclass
class BandResult:
    """Summary statistics from Monte Carlo schedule sampling."""

    finish_times: Dict[str, float]
    expected_cost: float


def _wrap_duration(duration: Any) -> Any:
    """Return a duration callable for ``run`` from ``duration`` spec.

    ``duration`` may be a constant, a callable already compatible with
    :func:`~loto.scheduling.des_engine.run` or a ``(mean, sigma)`` tuple which
    is interpreted as a normal distribution rounded to the nearest integer.
    """

    if isinstance(duration, tuple) and len(duration) == 2:
        mean, sigma = duration

        def sampler(
            rng: random.Random, mean: float = mean, sigma: float = sigma
        ) -> float:
            return max(0.0, rng.normalvariate(mean, sigma))

        return sampler
    return duration


def _percentiles(samples: Sequence[float]) -> Dict[str, float]:
    values = sorted(samples)
    if not values:
        return {"P10": 0.0, "P50": 0.0, "P90": 0.0}

    def pct(p: float) -> float:
        k = (len(values) - 1) * p
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return float(values[int(k)])
        return float(values[f] + (values[c] - values[f]) * (k - f))

    return {"P10": pct(0.10), "P50": pct(0.50), "P90": pct(0.90)}


def bands(
    tasks: Mapping[str, Task],
    resource_caps: Mapping[str, int],
    runs: int,
    price_curve: Sequence[Point],
    state: Mapping[str, object] | None = None,
    seed: int = 0,
) -> BandResult:
    """Run Monte Carlo samples and return finish time bands and expected cost."""

    wrapped: Dict[str, Task] = {
        tid: Task(
            duration=_wrap_duration(task.duration),
            predecessors=task.predecessors,
            resources=task.resources,
            calendar=task.calendar,
            gate=task.gate,
        )
        for tid, task in tasks.items()
    }

    makespans: list[float] = []
    costs: list[float] = []
    for i in range(runs):
        result = run(wrapped, resource_caps, state=state, seed=seed + i)
        makespan = max(result.ends.values()) if result.ends else 0
        makespans.append(float(makespan))
        curve = [(0.0, 1.0), (float(makespan), 1.0)]
        costs.append(integrate_cost(curve, price_curve))

    finish = _percentiles(makespans)
    expected_cost = sum(costs) / len(costs) if costs else 0.0
    return BandResult(finish, expected_cost)
