import networkx as nx

from loto.isolation_planner import IsolationPlanner, VerificationGate
from loto.models import RulePack


def simple_graph() -> nx.MultiDiGraph:
    g = nx.MultiDiGraph()
    g.add_node("s", is_source=True)
    g.add_node("t", tag="asset")
    g.add_edge("s", "t", is_isolation_point=True)
    return g


def ddbb_graph() -> nx.MultiDiGraph:
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


def ddbb_with_bypass_graph() -> nx.MultiDiGraph:
    g = ddbb_graph()
    g.add_node("x")
    g.add_edge("s", "x")
    g.add_edge("x", "t", is_isolation_point=True)
    return g


def test_basic_verifications() -> None:
    planner = IsolationPlanner()
    plan = planner.compute(
        {"p": simple_graph()}, asset_tag="asset", rule_pack=RulePack(risk_policies=None)
    )
    assert len(plan.verifications) == 2
    assert any("PT=0" in v for v in plan.verifications)
    assert any("no-movement" in v for v in plan.verifications)


def test_ddbb_valid() -> None:
    planner = IsolationPlanner()
    plan = planner.compute(
        {"p": ddbb_graph()}, asset_tag="asset", rule_pack=RulePack(risk_policies=None)
    )
    assert any("PT=0" in v for v in plan.verifications)
    assert any("no-movement" in v for v in plan.verifications)
    assert any("DDBB" in v for v in plan.verifications)


def test_ddbb_bypass_not_flagged() -> None:
    planner = IsolationPlanner()
    plan = planner.compute(
        {"p": ddbb_with_bypass_graph()},
        asset_tag="asset",
        rule_pack=RulePack(risk_policies=None),
    )
    assert any("PT=0" in v for v in plan.verifications)
    assert any("no-movement" in v for v in plan.verifications)
    assert not any("DDBB" in v for v in plan.verifications)


def test_gate_single_user_insufficient() -> None:
    gate = VerificationGate()
    gate.approve("user1")
    assert not gate.is_ready


def test_gate_two_distinct_users_required() -> None:
    gate = VerificationGate()
    gate.approve("user1")
    gate.approve("user1")
    assert not gate.is_ready
    gate.approve("user2")
    assert gate.is_ready
