"""Simple assignment helper.

This module provides minimal functionality for allocating tasks to hats
based on skill and availability gates with an optional rank bias.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from typing import Protocol, cast


class RankBias(Protocol):
    """Protocol describing a rank bias helper."""

    def duration_with_rank(self, duration_s: float, rank: int) -> float:
        """Return objective duration adjusted for ``rank``."""


def coalesce_slots(slots: Iterable[int]) -> list[tuple[int, int]]:
    """Return inclusive ranges covering consecutive ``slots``."""

    ordered = sorted(set(slots))
    if not ordered:
        return []

    ranges: list[tuple[int, int]] = []
    start = prev = ordered[0]
    for slot in ordered[1:]:
        if slot == prev + 1:
            prev = slot
        else:
            ranges.append((start, prev))
            start = prev = slot
    ranges.append((start, prev))
    return ranges


def is_available(time: int, ranges: Sequence[tuple[int, int]]) -> bool:
    """Return ``True`` if ``time`` falls within any of ``ranges``."""

    for start, end in ranges:
        if start <= time <= end:
            return True
    return False


@dataclass(frozen=True)
class Hat:
    """Representation of a worker hat in the scheduler."""

    id: str
    skills: set[str]
    calendar: list[tuple[int, int]] = field(init=False)
    rank: int

    def __init__(
        self,
        id: str,
        skills: set[str],
        calendar: Iterable[int] | Sequence[tuple[int, int]],
        rank: int,
    ) -> None:
        object.__setattr__(self, "id", id)
        object.__setattr__(self, "skills", skills)
        object.__setattr__(self, "rank", rank)
        cal = list(calendar)
        if cal and isinstance(cal[0], tuple):
            ranges = cast(list[tuple[int, int]], cal)
        else:
            ranges = coalesce_slots(cast(Iterable[int], cal))
        object.__setattr__(self, "calendar", ranges)


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
        if not is_available(task.start, hat.calendar):
            continue
        objective = rank_bias.duration_with_rank(task.duration_s, hat.rank)
        candidates.append((objective, hat))

    if not candidates:
        return None

    candidates.sort(key=lambda pair: pair[0])
    return candidates[0][1]
