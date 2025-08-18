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


def make_stimuli():
    names = ["REMOTE_OPEN", "LOCAL_OPEN", "AIR_RETURN", "ESD_RESET", "PUMP_START"]
    return [Stimulus(name=n, magnitude=1.0, duration_s=1.0) for n in names]


def test_valid_plan_pass():
    g = build_graph()
    plan = IsolationPlan(
        plan_id="p1",
        actions=[IsolationAction(component_id="steam:source->valve1", method="lock")],
    )
    engine = SimEngine()
    applied = engine.apply(plan, {"steam": g})

    report = engine.run_stimuli(applied, make_stimuli())

    assert all(r.success for r in report.results)


def test_tampered_plan_fail():
    g = build_graph()
    plan = IsolationPlan(plan_id="p1", actions=[])
    engine = SimEngine()
    applied = engine.apply(plan, {"steam": g})

    report = engine.run_stimuli(applied, make_stimuli())

    assert all(not r.success for r in report.results)
