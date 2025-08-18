"""Utilities for selecting candidate work bundles.

This module implements a simple 0/1 knapsack style selector used to pick
maintenance candidates that maximise saved future derate subject to two
resource constraints: readiness and SIMOPs (simultaneous operations).

The function :func:`select_candidates` returns both the chosen subset and
human readable reasons for why each candidate was or was not selected.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence


@dataclass(frozen=True)
class Candidate:
    """A potential maintenance task to be considered for bundling."""

    name: str
    saved_future_derate: float
    readiness_cost: int
    simops_cost: int
    ready: bool = True


ReasonMap = dict[str, str]


def _knapsack(
    candidates: Sequence[Candidate], max_readiness: int, max_simops: int
) -> set[int]:
    """Return indices of the optimal candidate subset.

    A dynamic programming approach is used to solve a two dimensional
    knapsack problem where readiness and SIMOPs represent the capacity
    constraints.
    """

    # dp[r][s] -> (value, set_of_indices)
    dp: list[list[tuple[float, set[int]]]] = [
        [(0.0, set()) for _ in range(max_simops + 1)] for _ in range(max_readiness + 1)
    ]

    for idx, c in enumerate(candidates):
        for r in range(max_readiness, c.readiness_cost - 1, -1):
            for s in range(max_simops, c.simops_cost - 1, -1):
                prev_val, prev_set = dp[r - c.readiness_cost][s - c.simops_cost]
                new_val = prev_val + c.saved_future_derate
                if new_val > dp[r][s][0]:
                    dp[r][s] = (new_val, prev_set | {idx})

    return dp[max_readiness][max_simops][1]


def select_candidates(
    candidates: Iterable[Candidate],
    max_readiness: int,
    max_simops: int,
) -> tuple[list[Candidate], ReasonMap]:
    """Select candidates that maximise saved future derate.

    Parameters
    ----------
    candidates:
        Iterable of :class:`Candidate` objects to consider.
    max_readiness:
        Maximum total readiness cost available.
    max_simops:
        Maximum total SIMOPs cost allowed.

    Returns
    -------
    tuple[list[Candidate], dict[str, str]]
        The chosen subset of candidates and a mapping from candidate name
        to a human readable reason for inclusion or exclusion.
    """

    candidates = list(candidates)
    reasons: ReasonMap = {}

    # Filter out candidates that are not ready
    ready_candidates: list[Candidate] = []
    for c in candidates:
        if not c.ready:
            reasons[c.name] = "not ready"
        else:
            ready_candidates.append(c)

    chosen_indices = _knapsack(ready_candidates, max_readiness, max_simops)
    selected: list[Candidate] = []
    for idx, c in enumerate(ready_candidates):
        if idx in chosen_indices:
            selected.append(c)
            reasons[c.name] = f"selected ({c.saved_future_derate} MW saved)"

    # Any remaining ready candidate was excluded due to constraints
    for c in ready_candidates:
        if c.name not in reasons:
            if c.readiness_cost > max_readiness or c.simops_cost > max_simops:
                reasons[c.name] = "exceeds individual constraints"
            else:
                reasons[c.name] = "excluded to respect readiness/SIMOPs constraints"

    return selected, reasons
