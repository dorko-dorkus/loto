import random
from dataclasses import dataclass

from loto.scheduling import choose_hats_for_reactive


@dataclass
class Snap:
    hat_id: str
    rank: int
    c_r: float


def test_choose_hats_prefers_higher_rank():
    wo = object()
    candidates = ["h1", "h2"]
    snapshot = {
        "h1": Snap("h1", 1, 0.9),
        "h2": Snap("h2", 2, 0.5),
    }
    policy = {
        "rotation": {},
        "rotation_penalty": 0.1,
        "rotation_limit": 2,
        "utilization": {},
        "utilization_cap": 1.0,
    }

    random.seed(123)
    chosen = choose_hats_for_reactive(wo, candidates, snapshot, policy)
    assert chosen == ["h1"]

    policy["rotation"] = {"h1": 2}
    random.seed(123)
    chosen = choose_hats_for_reactive(wo, candidates, snapshot, policy)
    assert chosen == ["h2"]
