import networkx as nx
from loto.sim_engine import SimEngine
from loto.models import IsolationAction, IsolationPlan, Stimulus


def build_graph():
    g = nx.MultiDiGraph()
    g.add_node("source", is_source=True)
    g.add_node("valve1")
    g.add_node("asset", tag="asset")
    g.add_edge("source", "valve1", is_isolation_point=True)
    g.add_edge("valve1", "asset")
    return g


def test_invariants_pass_when_isolated():
    g = build_graph()
    plan = IsolationPlan(
        plan_id="p1",
        actions=[IsolationAction(component_id="steam:source->valve1", method="lock")],
    )
    engine = SimEngine()
    applied = engine.apply(plan, {"steam": g})
    stim = Stimulus(name="REMOTE_OPEN", magnitude=1.0, duration_s=1.0)

    report = engine.run_stimuli(applied, [stim])
    res = report.results[0]
    assert res.success
    assert res.path is None
    assert res.domain is None


def test_reports_shortest_offending_path_and_domain():
    g = build_graph()
    plan = IsolationPlan(plan_id="p1", actions=[])
    engine = SimEngine()
    applied = engine.apply(plan, {"steam": g})
    stim = Stimulus(name="REMOTE_OPEN", magnitude=1.0, duration_s=1.0)

    report = engine.run_stimuli(applied, [stim])
    res = report.results[0]
    assert not res.success
    assert res.domain == "steam"
    assert res.path == ["source", "valve1", "asset"]
    assert "extra isolation" in res.hint
