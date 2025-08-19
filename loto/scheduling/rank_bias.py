"""Utilities for adjusting durations based on hat rank.

This module exposes :func:`duration_with_rank` which applies a simple
multiplier to a base duration according to a hat's rank.  The multiplier grows
linearly with the rank and is capped to avoid extreme values.
"""

from __future__ import annotations

__all__ = ["duration_with_rank"]

_CR = 1.5  # maximum allowed multiplier
_C = 1.0  # baseline multiplier for rank 1
_R = 0.1  # incremental multiplier per additional rank


def duration_with_rank(base_dur: float, hat_rank: int) -> float:
    """Return the biased duration for a task.

    Parameters
    ----------
    base_dur:
        The nominal duration of the task.
    hat_rank:
        Rank of the hat performing the task (1 = best).

    Returns
    -------
    float
        Duration after applying rank bias.
    """

    multiplier = min(_CR, _C + (hat_rank - 1) * _R)
    return base_dur * multiplier
