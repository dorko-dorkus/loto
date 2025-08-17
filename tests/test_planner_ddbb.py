import networkx as nx

from loto.isolation_planner import IsolationPlanner
from loto.rule_engine import RulePack


def build_graph():
    g = nx.MultiDiGraph()
    # Asset node
    g.add_node("asset", type="asset")
    # Block valves with varying health scores
    g.add_node("block1", type="block", health_score=80)
    g.add_node("block2", type="block", health_score=90)
    g.add_node("block3", type="block", health_score=70)
    # Bleed
    g.add_node("bleed1", type="bleed", health_score=50)
    # Drain and vent
    g.add_node("drain1", type="drain", health_score=40)
    g.add_node("vent2", type="vent", health_score=30)
    # Instrumentation for verification
    g.add_node("pt1", type="pt", health_score=20)
    g.add_node("tt1", type="tt", health_score=25)

    edges = [
        ("asset", "block1"), ("block1", "asset"),
        ("asset", "block2"), ("block2", "asset"),
        ("asset", "block3"), ("block3", "asset"),
        ("asset", "bleed1"), ("bleed1", "asset"),
        ("asset", "drain1"), ("drain1", "asset"),
        ("bleed1", "vent2"), ("vent2", "bleed1"),
        ("block1", "pt1"), ("pt1", "block1"),
        ("asset", "tt1"), ("tt1", "asset"),
    ]
    g.add_edges_from(edges)
    return g


def test_ddbb_expansion_ordering():
    planner = IsolationPlanner()
    rule_pack = RulePack(version="1.0", metadata={}, domains={})
    graph = build_graph()

    plan = planner.compute({"steam": graph}, asset_tag="asset", rule_pack=rule_pack)

    # Expected ordering: two blocks, bleed, drain
    assert plan.plan["steam"] == [
        {"component": "block2", "action": "CLOSE"},
        {"component": "block1", "action": "CLOSE"},
        {"component": "bleed1", "action": "OPEN"},
        {"component": "drain1", "action": "OPEN"},
    ]
    # Only the nearest PT/TT is used for verification
    assert plan.verifications == [{"component": "tt1", "action": "VERIFY"}]
