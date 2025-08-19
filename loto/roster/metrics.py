"""Utility models and helpers for ranking field operations.

This module defines small Pydantic models used by the roster portion of the
project as well as a couple of metric helpers.  The goal is to keep the code
lightweight and dependency free while still exercising a few common statistical
patterns: exponentially weighted moving averages, Bayesian shrinkage and
threshold based ranking.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Sequence, Tuple

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class KpiEvent(BaseModel):
    """Represents a single KPI measurement.

    Attributes
    ----------
    timestamp:
        When the event occurred.
    incidents:
        Number of incidents observed.
    total:
        Total population for the KPI (denominator for a rate).
    """

    timestamp: datetime = Field(..., description="When the KPI was measured")
    incidents: int = Field(0, ge=0, description="Number of incidents")
    total: int = Field(1, ge=1, description="Population for the KPI")

    class Config:
        extra = "forbid"


class HatScore(BaseModel):
    """Score associated with a hat ranking system."""

    value: float = Field(..., ge=0.0, le=1.0, description="Score between 0 and 1")
    incidents: int = Field(0, ge=0)
    total: int = Field(0, ge=0)

    class Config:
        extra = "forbid"


class HatRank(BaseModel):
    """Represents the discrete band a score falls into."""

    band: Literal["green", "amber", "red"]
    score: float = Field(..., ge=0.0, le=1.0)

    class Config:
        extra = "forbid"


# ---------------------------------------------------------------------------
# Metric helpers
# ---------------------------------------------------------------------------


def ewma(previous: float, observation: float, dt: float, half_life: float) -> float:
    """Update an exponentially weighted moving average.

    Parameters
    ----------
    previous:
        The previous average value.
    observation:
        The new observation to incorporate.
    dt:
        Time since the last observation in the same units as ``half_life``.
    half_life:
        The period over which the influence of ``previous`` decays by half.

    Returns
    -------
    float
        The updated moving average.
    """

    if half_life <= 0:
        raise ValueError("half_life must be positive")

    # Convert the half-life to an exponential smoothing factor.
    alpha = 1 - 0.5 ** (dt / half_life)
    return (1 - alpha) * previous + alpha * observation


def shrink(
    incidents: int,
    total: int,
    *,
    prior: float = 0.5,
    weight: float = 1.0,
    cap: int | None = None,
) -> float:
    """Bayesian shrinkage of an incident rate.

    A simple Beta prior centred on ``prior`` is blended with the observed
    incident rate.  ``weight`` controls the strength of the prior and ``cap``
    places an upper bound on the number of incidents considered.
    """

    if total < 0:
        raise ValueError("total must be non-negative")
    if incidents < 0:
        raise ValueError("incidents must be non-negative")
    if cap is not None:
        incidents = min(incidents, cap)

    numerator = incidents + prior * weight
    denominator = total + weight
    return numerator / denominator if denominator else prior


def rank_bands(score: float, bands: Sequence[Tuple[float, str]]) -> str:
    """Return the rank band name for ``score``.

    ``bands`` should be an iterable of ``(threshold, name)`` pairs ordered from
    highest to lowest threshold.  The first band whose threshold is less than or
    equal to ``score`` is returned.
    """

    for threshold, name in bands:
        if score >= threshold:
            return name
    # Fall back to the lowest band name if nothing matches
    return bands[-1][1]
