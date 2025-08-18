"""Scheduling objective utilities.

This module provides helpers for evaluating a simple scheduling objective.

Two pieces of functionality are provided:

``integrate_mwh``
    Integrate a piecewise linear power curve expressed as ``(time, MW)``
    pairs to obtain an energy measure in megawatt hours (MW·h).

``integrate_cost``
    Integrate a piecewise linear power curve weighted by a price curve to
    obtain an expected cost.

``objective``
    Compute a scalar objective combining makespan, an energy- or cost-based
    integral and an optional late completion penalty::

        J = makespan + \u03bb * integral + \u03c1 * late_penalty

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


def integrate_cost(curve: Sequence[Point], price: Sequence[Point]) -> float:
    """Return the cost integral of ``curve`` weighted by ``price``.

    The supplied ``curve`` and ``price`` are treated as piecewise linear
    functions.  ``curve`` provides power in megawatts while ``price`` supplies
    an associated price (for instance in $/MW·h).  The returned value is the
    integral of the product of these two functions.

    Parameters
    ----------
    curve:
        Ordered sequence of ``(time, MW)`` pairs.
    price:
        Ordered sequence of ``(time, price)`` pairs.
    """

    if len(curve) < 2 or len(price) < 2:
        return 0.0

    def interp(data: Sequence[Point], t: float) -> float:
        # Linear interpolation within ``data``.  Values outside the supplied
        # range use the nearest endpoint.
        for (t0, v0), (t1, v1) in zip(data, data[1:]):
            if t0 <= t <= t1:
                if t1 == t0:
                    return v0
                return v0 + (v1 - v0) * (t - t0) / (t1 - t0)
        return data[0][1] if t < data[0][0] else data[-1][1]

    times = sorted({t for t, _ in curve} | {t for t, _ in price})
    total = 0.0
    for t0, t1 in zip(times, times[1:]):
        p0 = interp(curve, t0)
        p1 = interp(curve, t1)
        q0 = interp(price, t0)
        q1 = interp(price, t1)
        dt = t1 - t0
        dp = (p1 - p0) / dt
        dq = (q1 - q0) / dt
        total += (
            p0 * q0 * dt
            + 0.5 * (p0 * dq + q0 * dp) * dt * dt
            + (1.0 / 3.0) * dp * dq * dt * dt * dt
        )
    return total


def objective(
    makespan: float,
    curve: Sequence[Point],
    lam: float,
    rho: float,
    deadline: float | None = None,
    price: Sequence[Point] | None = None,
) -> float:
    """Return the combined scheduling objective.

    Parameters
    ----------
    makespan:
        Completion time of the schedule.
    curve:
        Power curve used when computing the MW·h integral or cost.
    lam:
        Weight applied to the integral term.
    rho:
        Penalty weight applied if the schedule exceeds ``deadline``.
    deadline:
        Optional deadline for completion.  If provided and ``makespan`` is
        greater than ``deadline`` a unit late penalty is incurred.
    price:
        Optional price curve used to weight ``curve`` when computing an
        expected cost.  When ``None`` the integral is interpreted purely in
        energy terms (MW·h).
    """

    total = integrate_cost(curve, price) if price is not None else integrate_mwh(curve)
    late = 1.0 if (deadline is not None and makespan > deadline) else 0.0
    return float(makespan) + lam * total + rho * late
