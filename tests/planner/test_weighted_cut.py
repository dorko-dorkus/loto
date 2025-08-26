import networkx as nx

from loto.isolation_planner import IsolationPlanner
from loto.rule_engine import RulePack  # type: ignore[attr-defined]


def test_weighted_cut_prefers_cheapest() -> None:
    g = nx.MultiDiGraph()
    g.add_node("S", is_source=True)
    g.add_node("N")
    g.add_node("T", tag="asset")

    g.add_edge("S", "N", is_isolation_point=True, op_cost_min=5.0)
    g.add_edge("N", "T", is_isolation_point=True, op_cost_min=1.0)

    planner = IsolationPlanner()
    pack = RulePack(risk_policies=None)
    plan = planner.compute({"process": g}, asset_tag="asset", rule_pack=pack)

    edges = []
    for action in plan.actions:
        domain, edge = action.component_id.split(":", 1)
        if domain == "process":
            u, v = edge.split("->")
            edges.append((u, v))

    assert edges == [("N", "T")]
