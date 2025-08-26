from dataclasses import dataclass
from typing import Any

from loto.scheduling import choose_hats_for_reactive


@dataclass
class Snap:
    c_r: float


def test_round_robin_rotation_without_replacement() -> None:
    wo = object()
    candidates = ["h1", "h2", "h3"]
    snapshot = {hat: Snap(0.0) for hat in candidates}
    policy: dict[str, Any] = {
        "rotation": {},
        "rotation_penalty": 0.0,
        "rotation_limit": None,
        "utilization": {},
        "utilization_cap": 1.0,
        "crew_size": 2,
        "round_robin": {"next": 0},
    }

    chosen = choose_hats_for_reactive(wo, candidates, snapshot, policy)
    assert chosen == ["h1", "h2"]
    assert policy["round_robin"]["next"] == 2

    chosen = choose_hats_for_reactive(wo, candidates, snapshot, policy)
    assert chosen == ["h3", "h1"]
    assert policy["round_robin"]["next"] == 1
