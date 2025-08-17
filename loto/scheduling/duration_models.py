"""Duration distribution helpers for the task scheduler.

This module provides lightweight utilities for generating random durations
for scheduled activities.  Distributions are represented as callables that
accept a random number generator and return a sample in seconds.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from math import exp, sqrt
from typing import Any

Sampler = Callable[[Any], float]


def Triangular(a: float, m: float, b: float) -> Sampler:
    """Return a sampler for the triangular distribution.

    ``a`` is the minimum, ``m`` the mode and ``b`` the maximum.  The returned
    callable expects an RNG exposing a ``random`` method yielding values in
    ``[0, 1)`` and produces a duration measured in seconds.
    """

    c = (m - a) / (b - a)

    def sample(rng: Any) -> float:
        u = rng.random()
        if u < c:
            return a + sqrt(u * (b - a) * (m - a))
        return b - sqrt((1 - u) * (b - a) * (b - m))

    return sample


def Lognormal(mu: float, sigma: float) -> Sampler:
    """Return a sampler for the log-normal distribution.

    ``mu`` and ``sigma`` are the mean and standard deviation of the underlying
    normal distribution.  The returned callable expects an RNG capable of
    producing either log-normal or standard normal variates and yields a
    duration in seconds.
    """

    def sample(rng: Any) -> float:
        if hasattr(rng, "lognormal"):
            return rng.lognormal(mu, sigma)
        if hasattr(rng, "lognormvariate"):
            return rng.lognormvariate(mu, sigma)
        if hasattr(rng, "standard_normal"):
            z = rng.standard_normal()
        elif hasattr(rng, "normal"):
            z = rng.normal(0.0, 1.0)
        elif hasattr(rng, "gauss"):
            z = rng.gauss(0.0, 1.0)
        elif hasattr(rng, "normalvariate"):
            z = rng.normalvariate(0.0, 1.0)
        else:
            raise TypeError("RNG must provide a method to draw normal samples")
        return exp(mu + sigma * z)

    return sample


_DEFAULT_MODELS: Mapping[str, tuple[str, tuple[float, ...]]] = {
    "A": ("triangular", (10.0, 20.0, 30.0)),
    "B": ("lognormal", (3.0, 0.4)),
}


def make_sampler(class_id: str, context: Mapping[str, float]) -> Sampler:
    """Create a duration sampler for ``class_id`` adjusted by ``context``.

    The ``context`` mapping may include ``"health"``, ``"access"`` and
    ``"experience"`` factors.  These factors scale the sampled duration by the
    reciprocal of their product – healthier, more experienced workers with
    better access complete tasks faster.
    """

    model, params = _DEFAULT_MODELS[class_id]
    if model == "triangular":
        sampler = Triangular(*params)
    elif model == "lognormal":
        sampler = Lognormal(*params)
    else:
        raise ValueError(f"unknown model: {model}")

    health = context.get("health", 1.0)
    access = context.get("access", 1.0)
    experience = context.get("experience", 1.0)
    scale = 1.0 / max(health, 1e-9) / max(access, 1e-9) / max(experience, 1e-9)

    def adjusted(rng: Any) -> float:
        return sampler(rng) * scale

    return adjusted
