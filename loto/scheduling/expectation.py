"""Expectation estimation utilities for scheduling simulations.

This module provides a simple Monte Carlo estimator for the expectation of a
scalar objective ``J``.  Samples of ``J`` are drawn repeatedly from a provided
callable until either a desired confidence interval (CI) width is achieved or a
maximum number of samples is reached.  Percentile targets of the sampled
values may also be computed.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, Dict, Iterable, Sequence

import statistics


@dataclass
class ExpectationResult:
    """Summary of expectation estimation."""

    mean: float
    ci_width: float
    samples: int
    stopped_early: bool
    percentiles: Dict[str, float]


def _quantiles(values: Iterable[float], p_targets: Sequence[float]) -> Dict[str, float]:
    """Return percentile values for the supplied probabilities.

    Percentiles are computed using linear interpolation between closest ranks.
    Returned dictionary keys follow the ``"PXX"`` convention where ``XX`` is the
    percentile expressed as an integer percentage.
    """

    data = sorted(values)
    n = len(data)
    if n == 0:
        return {f"P{int(p*100)}": 0.0 for p in p_targets}

    result: Dict[str, float] = {}
    for p in p_targets:
        k = (n - 1) * p
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            v = data[int(k)]
        else:
            v = data[f] + (data[c] - data[f]) * (k - f)
        result[f"P{int(round(p * 100))}"] = float(v)
    return result


def estimate(
    sampler: Callable[[int], float],
    max_runs: int,
    ci_threshold: float,
    p_targets: Sequence[float] | None = None,
) -> ExpectationResult:
    """Estimate ``E[J]`` using Monte Carlo sampling.

    Parameters
    ----------
    sampler:
        Callable producing a sample of ``J``.  It receives an integer seed which
        may be used to seed any internal random number generators to ensure
        reproducibility.
    max_runs:
        Maximum number of samples to draw.
    ci_threshold:
        Desired maximum width of the 95% confidence interval.  Sampling stops
        early once the estimated CI width drops below this value.  Use a
        non-positive threshold to disable early stopping.
    p_targets:
        Optional sequence of probabilities for which to compute percentiles of
        the sampled values.
    """

    samples: list[float] = []
    ci_width = math.inf
    stopped = False

    for i in range(1, max_runs + 1):
        samples.append(float(sampler(i - 1)))
        if i > 1:
            mean = statistics.fmean(samples)
            sd = statistics.stdev(samples)
            ci_width = 2.0 * 1.96 * sd / math.sqrt(i)
            if ci_threshold > 0 and ci_width < ci_threshold:
                stopped = True
                break

    mean = statistics.fmean(samples) if samples else 0.0
    if len(samples) > 1:
        sd = statistics.stdev(samples)
        ci_width = 2.0 * 1.96 * sd / math.sqrt(len(samples))
    else:
        ci_width = 0.0

    percentiles = _quantiles(samples, p_targets) if p_targets is not None else {}

    return ExpectationResult(mean, ci_width, len(samples), stopped, percentiles)
