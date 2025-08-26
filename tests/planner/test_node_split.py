import networkx as nx
import pytest

from loto.isolation_planner import IsolationPlanner
from loto.rule_engine import RulePack  # type: ignore[attr-defined]


def test_node_split_isolates_device_once(monkeypatch: pytest.MonkeyPatch) -> None:
    g = nx.MultiDiGraph()
    g.add_node("S1", is_source=True)
    g.add_node("S2", is_source=True)
    g.add_node("V", is_isolation_point=True)
    g.add_node("t1", tag="asset")
    g.add_node("t2", tag="asset")
    g.add_edge("S1", "V", is_isolation_point=True)
    g.add_edge("S2", "V", is_isolation_point=True)
    g.add_edge("V", "t1", is_isolation_point=True)
    g.add_edge("V", "t2", is_isolation_point=True)

    monkeypatch.setenv("PLANNER_NODE_SPLIT", "1")
    planner = IsolationPlanner()
    pack = RulePack(risk_policies=None)
    plan = planner.compute({"process": g}, asset_tag="asset", rule_pack=pack)

    edges = []
    for action in plan.actions:
        domain, edge = action.component_id.split(":", 1)
        if domain == "process":
            u, v = edge.split("->")
            edges.append((u, v))

    assert edges == [("V_in", "V_out")]
