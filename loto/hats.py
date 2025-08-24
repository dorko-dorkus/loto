from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Mapping, Sequence

_CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "hats.json"


@lru_cache()
def load_weights(path: str | Path = _CONFIG_PATH) -> List[float]:
    """Return normalised KPI weights from *path*.

    The configuration file must contain JSON of the form::

        {"weights": [0.5, 0.3, 0.2]}

    Weights are normalised so the returned list sums to 1.0.
    """

    data = json.loads(Path(path).read_text())
    weights = data.get("weights")
    if not isinstance(weights, list) or not weights:
        raise ValueError("weights must be a non-empty list")
    floats = [float(w) for w in weights]
    total = sum(floats)
    if total <= 0:
        raise ValueError("weights must sum to a positive value")
    return [w / total for w in floats]


def aggregate_ledger(
    ledger: Mapping[str, Sequence[Sequence[float]]],
) -> Dict[str, List[float]]:
    """Aggregate ``ledger`` into mean KPI values per hat.

    Parameters
    ----------
    ledger:
        Mapping of hat identifier to an ordered sequence of KPI observations. Each
        observation is a sequence of metric values.

    Returns
    -------
    dict
        Mapping of hat identifier to a list containing the mean of each metric.
    """

    aggregated: Dict[str, List[float]] = {}
    for hat_id, observations in ledger.items():
        obs_list = [list(map(float, obs)) for obs in observations]
        if not obs_list:
            continue
        width = max(len(obs) for obs in obs_list)
        sums = [0.0] * width
        for obs in obs_list:
            for idx, value in enumerate(obs):
                sums[idx] += value
        n = len(obs_list)
        aggregated[hat_id] = [s / n for s in sums]
    return aggregated


def compute_ranking(
    ledger: Mapping[str, Sequence[Sequence[float]]],
    weights: Sequence[float] | None = None,
) -> Dict[str, Dict[str, float | int]]:
    """Return rank and coefficient per hat for the given ``ledger``.

    ``weights`` may be provided to override the configuration file. The returned
    mapping is keyed by hat identifier with each value containing ``rank`` and
    ``coefficient`` entries.
    """

    weight_list = list(weights) if weights is not None else load_weights()
    aggregated = aggregate_ledger(ledger)
    ranking: Dict[str, Dict[str, float | int]] = {}
    for hat_id, metrics in aggregated.items():
        used_weights = weight_list[: len(metrics)]
        total_w = sum(used_weights)
        coeff = (
            sum(w * m for w, m in zip(used_weights, metrics)) / total_w
            if total_w
            else 0.0
        )
        coeff = max(0.0, min(1.0, coeff))
        rank = round(coeff * 100)
        if any(m < 0.4 for m in metrics[: len(used_weights)]):
            rank = min(rank, 20)
        ranking[hat_id] = {"rank": int(rank), "coefficient": coeff}
    return ranking
