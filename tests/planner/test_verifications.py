import networkx as nx

from loto.isolation_planner import IsolationPlanner, VerificationGate
from loto.rule_engine import RulePack


def simple_graph():
    g = nx.MultiDiGraph()
    g.add_node("s", is_source=True)
    g.add_node("t", tag="asset")
    g.add_edge("s", "t", is_isolation_point=True)
    return g


def ddbb_graph():
    g = nx.MultiDiGraph()
    g.add_node("s", is_source=True)
    g.add_node("v1")
    g.add_node("v2")
    g.add_node("t", tag="asset")
    g.add_node("b")
    g.add_edge("s", "v1", is_isolation_point=True)
    g.add_edge("v1", "v2", is_isolation_point=True)
    g.add_edge("v2", "t")
    g.add_edge("v1", "b", is_bleed=True)
    return g


def test_basic_verifications():
    planner = IsolationPlanner()
    plan = planner.compute(
        {"p": simple_graph()}, asset_tag="asset", rule_pack=RulePack()
    )
    assert len(plan.verifications) == 2
    assert any("PT=0" in v for v in plan.verifications)
    assert any("no-movement" in v for v in plan.verifications)


def test_ddbb_hint():
    planner = IsolationPlanner()
    plan = planner.compute({"p": ddbb_graph()}, asset_tag="asset", rule_pack=RulePack())
    assert len(plan.verifications) == 3
    assert any("PT=0" in v for v in plan.verifications)
    assert any("no-movement" in v for v in plan.verifications)
    assert any("DDBB" in v for v in plan.verifications)


def test_gate_single_user_insufficient():
    gate = VerificationGate()
    gate.approve("user1")
    assert not gate.is_ready


def test_gate_two_distinct_users_required():
    gate = VerificationGate()
    gate.approve("user1")
    gate.approve("user1")
    assert not gate.is_ready
    gate.approve("user2")
    assert gate.is_ready
