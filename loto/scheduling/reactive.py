"""Helpers for selecting hats for reactive work orders."""

from __future__ import annotations

import random
from collections.abc import Mapping, Sequence
from typing import Any


def choose_hats_for_reactive(
    wo: Any,
    candidates: Sequence[str],
    snapshot: Mapping[str, Any],
    policy: Mapping[str, Any],
) -> list[str]:
    """Return a list of chosen hats for a reactive work order.

    Parameters
    ----------
    wo:
        Work order object.  The function is agnostic to its structure and only
        uses it as an opaque handle.
    candidates:
        Iterable of hat identifiers that are currently available.
    snapshot:
        Mapping of hat identifier to an object exposing a ``c_r`` attribute
        representing the ranking coefficient for that hat.
    policy:
        Mapping defining selection policy.  The following keys are recognised:

        ``rotation`` (mapping):
            Number of recent rotations for each hat.  Higher values incur a
            penalty.
        ``rotation_penalty`` (float):
            Amount subtracted from the ranking coefficient for each rotation.
        ``rotation_limit`` (int | None):
            Maximum number of rotations allowed before a hat is excluded.
        ``utilization`` (mapping):
            Current utilization for each hat expressed as a fraction.
        ``utilization_cap`` (float):
            Upper bound on utilization; hats meeting or exceeding this value are
            not considered.
        ``crew_size`` (int):
            Number of hats to select.  Defaults to ``1``.

    Returns
    -------
    list[str]
        Chosen hat identifiers.  The list length will not exceed ``crew_size``.
    """

    rotation = policy.get("rotation", {})
    rotation_limit = policy.get("rotation_limit")
    rotation_penalty = policy.get("rotation_penalty", 0.0)
    utilization = policy.get("utilization", {})
    util_cap = policy.get("utilization_cap", 1.0)
    crew_size = int(policy.get("crew_size", 1))

    eligible: list[str] = []
    weights: list[float] = []
    for hat in candidates:
        snap = snapshot.get(hat)
        if snap is None:
            continue
        if utilization.get(hat, 0.0) >= util_cap:
            continue
        rot = rotation.get(hat, 0)
        if rotation_limit is not None and rot >= rotation_limit:
            continue
        score = float(getattr(snap, "c_r", 0.0)) - rotation_penalty * rot
        if score < 0:
            score = 0.0
        eligible.append(hat)
        weights.append(score)

    if not eligible:
        return []

    weight_seq: Sequence[float] | None = weights
    if all(w == 0 for w in weights):
        weight_seq = None

    k = min(crew_size, len(eligible))
    return random.choices(eligible, weights=weight_seq, k=k)
