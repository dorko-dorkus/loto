import networkx as nx
import pytest

from loto.sim_engine import SimEngine
from loto.models import IsolationAction, IsolationPlan, SimReport, SimResultItem, Stimulus


def build_graph():
    g = nx.MultiDiGraph()
    g.add_node("source", is_source=True)
    g.add_node("valve1")
    g.add_node("asset", tag="asset")
    g.add_edge("source", "valve1", is_isolation_point=True)
    g.add_edge("valve1", "asset")
    return g


def test_accepts_model_stimulus():
    g = build_graph()
    plan = IsolationPlan(
        plan_id="p1",
        actions=[IsolationAction(component_id="steam:source->valve1", method="lock")],
    )
    engine = SimEngine()
    applied = engine.apply(plan, {"steam": g})
    stim = Stimulus(name="REMOTE_OPEN", magnitude=1.0, duration_s=1.0)

    report = engine.run_stimuli(applied, [stim])

    assert isinstance(report, SimReport)
    assert all(isinstance(r, SimResultItem) for r in report.results)


def test_invalid_stimulus_type_raises():
    g = build_graph()
    plan = IsolationPlan(
        plan_id="p1",
        actions=[IsolationAction(component_id="steam:source->valve1", method="lock")],
    )
    engine = SimEngine()
    applied = engine.apply(plan, {"steam": g})

    with pytest.raises(AttributeError):
        engine.run_stimuli(applied, [{"name": "REMOTE_OPEN", "magnitude": 1.0, "duration_s": 1.0}])

