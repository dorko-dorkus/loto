"""Scheduling objective utilities.

This module provides helpers for evaluating a simple scheduling objective.

Two pieces of functionality are provided:

``integrate_mwh``
    Integrate a piecewise linear power curve expressed as ``(time, MW)``
    pairs to obtain an energy measure in megawatt hours (MW·h).

``objective``
    Compute a scalar objective combining makespan, the MW·h integral and an
    optional late completion penalty::

        J = makespan + \u03bb * MW_h + \u03c1 * late_penalty

    where ``late_penalty`` is ``1`` when the supplied ``deadline`` is exceeded
    and ``0`` otherwise.
"""

from __future__ import annotations

from typing import Sequence, Tuple


Point = Tuple[float, float]


def integrate_mwh(curve: Sequence[Point]) -> float:
    """Return the integral of ``curve`` in megawatt hours (MW·h).

    Parameters
    ----------
    curve:
        Ordered sequence of ``(time, MW)`` pairs.  The curve is treated as a
        piecewise linear function where ``time`` is measured in hours and
        ``MW`` in megawatts.
    """

    total = 0.0
    if len(curve) < 2:
        return total
    for (t0, v0), (t1, v1) in zip(curve, curve[1:]):
        dt = t1 - t0
        total += (v0 + v1) * dt / 2.0
    return total


def objective(
    makespan: float,
    curve: Sequence[Point],
    lam: float,
    rho: float,
    deadline: float | None = None,
) -> float:
    """Return the combined scheduling objective.

    Parameters
    ----------
    makespan:
        Completion time of the schedule.
    curve:
        Power curve used when computing the MW·h integral.
    lam:
        Weight applied to the MW·h term.
    rho:
        Penalty weight applied if the schedule exceeds ``deadline``.
    deadline:
        Optional deadline for completion.  If provided and ``makespan`` is
        greater than ``deadline`` a unit late penalty is incurred.
    """

    mwh = integrate_mwh(curve)
    late = 1.0 if (deadline is not None and makespan > deadline) else 0.0
    return float(makespan) + lam * mwh + rho * late
