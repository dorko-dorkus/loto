"""Simple assignment helper.

This module provides minimal functionality for allocating tasks to hats
based on skill and availability gates with an optional rank bias.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence


class RankBias(Protocol):
    """Protocol describing a rank bias helper."""

    def duration_with_rank(self, duration_s: float, rank: int) -> float:
        """Return objective duration adjusted for ``rank``."""


@dataclass(frozen=True)
class Hat:
    """Representation of a worker hat in the scheduler."""

    id: str
    skills: set[str]
    calendar: set[int]
    rank: int


@dataclass(frozen=True)
class Task:
    """Representation of a schedulable task."""

    skill: str
    start: int
    duration_s: float = 0.0


def simulate(task: Task, hats: Sequence[Hat], rank_bias: RankBias) -> Hat | None:
    """Return the best hat candidate for ``task``.

    Hats are filtered by skill and calendar availability.  Among the
    eligible candidates the one with the lowest adjusted duration
    according to ``rank_bias`` is returned.  ``None`` is returned when no
    candidate satisfies the gating criteria.
    """

    candidates: list[tuple[float, Hat]] = []
    for hat in hats:
        if task.skill not in hat.skills:
            continue
        if task.start not in hat.calendar:
            continue
        objective = rank_bias.duration_with_rank(task.duration_s, hat.rank)
        candidates.append((objective, hat))

    if not candidates:
        return None

    candidates.sort(key=lambda pair: pair[0])
    return candidates[0][1]
