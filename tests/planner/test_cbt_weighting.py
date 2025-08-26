import random
from datetime import datetime

import networkx as nx
import pytest

from loto import isolation_planner as ip
from loto.rule_engine import RulePack  # type: ignore[attr-defined]


def test_high_cbt_prefers_fewer_harder_actions(monkeypatch: pytest.MonkeyPatch) -> None:
    random.seed(0)
    monkeypatch.setenv("PLANNER_NODE_SPLIT", "0")
    monkeypatch.setattr(ip, "CB_SCALE", 1000.0)
    monkeypatch.setattr(ip, "RST_SCALE", 10.0)
    monkeypatch.setattr(ip, "ZETA", 0.1)

    g = nx.MultiDiGraph()
    g.add_node("A", is_source=True)
    g.add_node("B", is_source=True)
    g.add_node("U")
    g.add_node("T", tag="asset")

    g.add_edge(
        "A",
        "U",
        is_isolation_point=True,
        op_cost_min=1.0,
        reset_time_min=10.0,
    )
    g.add_edge(
        "B",
        "U",
        is_isolation_point=True,
        op_cost_min=1.0,
        reset_time_min=10.0,
    )
    g.add_edge(
        "U",
        "T",
        is_isolation_point=True,
        op_cost_min=5.0,
        reset_time_min=10.0,
    )

    planner = ip.IsolationPlanner()
    pack = RulePack(risk_policies=None)

    class Adapter0:
        def cbt_minutes(self, craft: str, site: str, when: datetime) -> int:
            return 0

    monkeypatch.setattr(ip, "get_hats_adapter", lambda: Adapter0())
    baseline = planner.compute({"process": g.copy()}, "asset", pack)
    baseline_edges = {
        action.component_id.split(":", 1)[1]
        for action in baseline.actions
        if action.component_id.startswith("process:")
    }

    class Adapter60:
        def cbt_minutes(self, craft: str, site: str, when: datetime) -> int:
            return 60

    monkeypatch.setattr(ip, "get_hats_adapter", lambda: Adapter60())
    adjusted = planner.compute({"process": g.copy()}, "asset", pack)
    adjusted_edges = {
        action.component_id.split(":", 1)[1]
        for action in adjusted.actions
        if action.component_id.startswith("process:")
    }

    assert baseline_edges == {"A->U", "B->U"}
    assert adjusted_edges == {"U->T"}
