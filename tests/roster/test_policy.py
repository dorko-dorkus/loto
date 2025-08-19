from __future__ import annotations

import random
from dataclasses import dataclass
from pathlib import Path

import yaml

from loto.roster import policy, ranking
from loto.scheduling import choose_hats_for_reactive


@dataclass
class Snap:
    c_r: float


def test_yaml_affects_ranking(tmp_path: Path) -> None:
    cfg_path = tmp_path / "hats_policy.yaml"
    cfg_path.write_text(
        yaml.safe_dump(
            {
                "weights": [1, 0],
                "half_life": 1,
                "pseudo_count": 0.0,
                "incident_cap": 10,
                "rotation_window": 1,
                "daily_utilization_cap": 1.0,
            }
        )
    )

    ledger = {"h1": [(1.0, 0.0)], "h2": [(0.0, 1.0)]}
    pol = policy.load_policy(cfg_path)
    snap = ranking.update_ranking(ledger, pol)
    assert snap["h1"]["rank"] == 1

    cfg = yaml.safe_load(cfg_path.read_text())
    cfg["weights"] = [0, 1]
    cfg_path.write_text(yaml.safe_dump(cfg))
    pol = policy.load_policy(cfg_path)
    snap = ranking.update_ranking(ledger, pol)
    assert snap["h1"]["rank"] == 2


def test_yaml_affects_chooser(tmp_path: Path) -> None:
    cfg_path = tmp_path / "hats_policy.yaml"
    cfg = {
        "weights": [0.5, 0.5],
        "half_life": 1,
        "pseudo_count": 0.0,
        "incident_cap": 10,
        "rotation_window": 1,
        "daily_utilization_cap": 1.0,
    }
    cfg_path.write_text(yaml.safe_dump(cfg))

    wo = object()
    candidates = ["h1", "h2"]
    snapshot = {"h1": Snap(0.9), "h2": Snap(0.5)}

    pol = policy.load_policy(cfg_path)
    pol["rotation"] = {"h1": 1}
    pol["utilization"] = {}
    random.seed(123)
    chosen = choose_hats_for_reactive(wo, candidates, snapshot, pol)
    assert chosen == ["h2"]

    cfg["rotation_window"] = 2
    cfg_path.write_text(yaml.safe_dump(cfg))
    pol = policy.load_policy(cfg_path)
    pol["rotation"] = {"h1": 1}
    pol["utilization"] = {}
    random.seed(123)
    chosen = choose_hats_for_reactive(wo, candidates, snapshot, pol)
    assert chosen == ["h1"]

    cfg["daily_utilization_cap"] = 0.8
    cfg_path.write_text(yaml.safe_dump(cfg))
    pol = policy.load_policy(cfg_path)
    pol["rotation"] = {}
    pol["utilization"] = {"h1": 0.9}
    random.seed(123)
    chosen = choose_hats_for_reactive(wo, candidates, snapshot, pol)
    assert chosen == ["h2"]
