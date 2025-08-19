"""Ranking algorithms for roster metrics.

This module exposes :func:`update_ranking` which consumes a *ledger* – a
mapping of entity identifiers to an ordered sequence of metric tuples – and
returns a snapshot containing the rank and coefficient for each entity.

The calculation demonstrates a few statistical techniques:

* **Composite** – multiple metrics for a single observation are combined into
  a single score by averaging them.
* **EWMA** – the sequence of composite scores is reduced to a single value via
  an exponential weighted moving average.
* **Shrinkage** – each EWMA value is pulled slightly towards the global mean to
  temper extreme outliers.
* **Bands** – the final coefficient is categorised into a band (``S`` through
  ``C``) based on simple thresholds.
* **Caps** – coefficients are clipped into a fixed range to keep them
  well‑behaved.

The function is intentionally small and self contained so it can serve as a
teaching example for statistical style ranking pipelines.
"""

from __future__ import annotations

from typing import Dict, Mapping, Sequence

_ALPHA = 0.5
_SHRINKAGE = 0.1
_THRESHOLDS = (0.75, 0.5, 0.25)  # S, A, B, else C
_CAPS = (0.0, 1.0)


def _composite(observation: Sequence[float]) -> float:
    """Combine multiple metrics into a single score.

    A simple arithmetic mean is used which is sufficient for the tests and keeps
    the function intentionally straightforward.
    """

    if not observation:
        return 0.0
    return float(sum(observation) / len(observation))


def _ewma(values: Sequence[float], alpha: float = _ALPHA) -> float:
    """Compute the exponential weighted moving average for *values*."""

    iterator = iter(values)
    try:
        acc = float(next(iterator))
    except StopIteration:
        return 0.0
    for value in iterator:
        acc = alpha * float(value) + (1.0 - alpha) * acc
    return acc


def _apply_shrinkage(value: float, mean: float, factor: float = _SHRINKAGE) -> float:
    """Pull *value* towards *mean* by ``factor``."""

    return (1.0 - factor) * value + factor * mean


def _band(value: float) -> str:
    """Return the categorical band for *value*."""

    t_s, t_a, t_b = _THRESHOLDS
    if value >= t_s:
        return "S"
    if value >= t_a:
        return "A"
    if value >= t_b:
        return "B"
    return "C"


def update_ranking(
    ledger: Mapping[str, Sequence[Sequence[float]]],
) -> Dict[str, Dict[str, object]]:
    """Return a ranking snapshot for the given *ledger*.

    Parameters
    ----------
    ledger:
        Mapping of entity identifiers to an ordered sequence of observations.
        Each observation may contain one or more metrics.  Each metric tuple is
        collapsed into a single composite value prior to further calculations.

    Returns
    -------
    dict
        A mapping of entity identifier to a dictionary containing ``rank``,
        ``coefficient`` and ``band`` entries.
    """

    # Step 1 – build composite score history for each entity.
    histories: Dict[str, list[float]] = {
        name: [_composite(obs) for obs in observations]
        for name, observations in ledger.items()
    }

    # Step 2 – compute EWMA for each entity.
    ewmas: Dict[str, float] = {name: _ewma(vals) for name, vals in histories.items()}

    # Step 3 – shrink towards global mean to reduce variance.
    global_mean = sum(ewmas.values()) / len(ewmas) if ewmas else 0.0
    coefficients: Dict[str, float] = {
        name: _apply_shrinkage(value, global_mean) for name, value in ewmas.items()
    }

    # Step 4 – apply caps.
    cap_min, cap_max = _CAPS
    coefficients = {
        name: min(max(coeff, cap_min), cap_max) for name, coeff in coefficients.items()
    }

    # Step 5 – assign bands and ranks.
    ranked_names = sorted(coefficients, key=lambda n: coefficients[n], reverse=True)
    snapshot: Dict[str, Dict[str, object]] = {}
    for position, name in enumerate(ranked_names, start=1):
        coeff = round(coefficients[name], 4)
        snapshot[name] = {
            "rank": position,
            "coefficient": coeff,
            "band": _band(coeff),
        }

    return snapshot
