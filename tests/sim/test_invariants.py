import networkx as nx

from loto.models import IsolationAction, IsolationPlan, Stimulus
from loto.sim_engine import SimEngine


def build_graph() -> nx.MultiDiGraph:
    g = nx.MultiDiGraph()
    g.add_node("source", is_source=True)
    g.add_node("valve1")
    g.add_node("asset", tag="asset")
    g.add_edge("source", "valve1", is_isolation_point=True)
    g.add_edge("valve1", "asset")
    g.add_node("bleed", safe_sink=True)
    g.add_edge("asset", "bleed", is_bleed=True)
    return g


def test_invariants_pass_when_isolated() -> None:
    g = build_graph()
    plan = IsolationPlan(
        plan_id="p1",
        actions=[
            IsolationAction(
                component_id="steam:source->valve1", method="lock", duration_s=1.0
            )
        ],
    )
    engine = SimEngine()
    applied = engine.apply(plan, {"steam": g})
    stim = Stimulus(name="REMOTE_OPEN", magnitude=1.0, duration_s=1.0)

    report = engine.run_stimuli(applied, [stim])
    res = report.results[0]
    assert res.success
    assert res.paths == []
    assert res.domain is None


def test_reports_shortest_offending_path_and_domain() -> None:
    g = build_graph()
    plan = IsolationPlan(plan_id="p1", actions=[])
    engine = SimEngine()
    applied = engine.apply(plan, {"steam": g})
    stim = Stimulus(name="REMOTE_OPEN", magnitude=1.0, duration_s=1.0)

    report = engine.run_stimuli(applied, [stim])
    res = report.results[0]
    assert not res.success
    assert res.domain == "steam"
    assert res.paths == [["source", "valve1", "asset"]]
    assert res.hint is not None and "extra isolation" in res.hint


def test_reports_multiple_offending_paths() -> None:
    g = nx.MultiDiGraph()
    g.add_node("source", is_source=True)
    g.add_node("valve1")
    g.add_node("valve2")
    g.add_node("asset", tag="asset")
    g.add_edge("source", "valve1")
    g.add_edge("source", "valve2")
    g.add_edge("valve1", "asset")
    g.add_edge("valve2", "asset")

    plan = IsolationPlan(plan_id="p1", actions=[])
    engine = SimEngine()
    applied = engine.apply(plan, {"steam": g})
    stim = Stimulus(name="REMOTE_OPEN", magnitude=1.0, duration_s=1.0)

    report = engine.run_stimuli(applied, [stim])
    res = report.results[0]
    assert not res.success
    assert res.domain == "steam"
    assert res.paths is not None
    paths = res.paths
    assert len(paths) == 2
    assert ["source", "valve1", "asset"] in paths
    assert ["source", "valve2", "asset"] in paths


def test_trapped_component_without_bleed_fails() -> None:
    g = nx.MultiDiGraph()
    g.add_node("s", is_source=True)
    g.add_node("v")
    g.add_node("t", tag="asset")
    g.add_edge("s", "v", is_isolation_point=True)
    g.add_edge("v", "t")

    plan = IsolationPlan(
        plan_id="p1",
        actions=[
            IsolationAction(component_id="steam:s->v", method="lock", duration_s=1.0)
        ],
    )
    engine = SimEngine()
    applied = engine.apply(plan, {"steam": g})
    stim = Stimulus(name="REMOTE_OPEN", magnitude=1.0, duration_s=1.0)

    report = engine.run_stimuli(applied, [stim])
    res = report.results[0]
    assert not res.success
    assert res.paths is not None and ["t"] in res.paths
    assert res.hint is not None and "bleed" in res.hint


def test_trapped_component_can_bleed_through_check_valve() -> None:
    g = nx.MultiDiGraph()
    g.add_node("s", is_source=True)
    g.add_node("v")
    g.add_node("cv")
    g.add_node("t", tag="asset")
    g.add_node("b", safe_sink=True)
    g.add_edge("s", "v", is_isolation_point=True)
    g.add_edge("v", "cv")
    g.add_edge("cv", "t", kind="check valve")
    g.add_edge("cv", "b", is_bleed=True)

    plan = IsolationPlan(
        plan_id="p1",
        actions=[
            IsolationAction(component_id="steam:s->v", method="lock", duration_s=1.0)
        ],
    )
    engine = SimEngine()
    applied = engine.apply(plan, {"steam": g})
    stim = Stimulus(name="REMOTE_OPEN", magnitude=1.0, duration_s=1.0)

    report = engine.run_stimuli(applied, [stim])
    res = report.results[0]
    assert res.success


def test_check_valve_blocks_reverse_flow() -> None:
    g = nx.MultiDiGraph()
    g.add_node("s", is_source=True)
    g.add_node("cv")
    g.add_node("t", tag="asset")
    g.add_node("b", safe_sink=True)
    g.add_edge("t", "cv", kind="check valve")
    g.add_edge("cv", "s")
    g.add_edge("t", "b", is_bleed=True)

    plan = IsolationPlan(plan_id="p1", actions=[])
    engine = SimEngine()
    applied = engine.apply(plan, {"steam": g})
    stim = Stimulus(name="REMOTE_OPEN", magnitude=1.0, duration_s=1.0)

    report = engine.run_stimuli(applied, [stim])
    res = report.results[0]
    assert res.success
