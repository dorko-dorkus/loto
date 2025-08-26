import networkx as nx

from loto.models import IsolationPlan, Stimulus
from loto.sim_engine import SimEngine


def build_graph() -> nx.MultiDiGraph:
    g = nx.MultiDiGraph()
    g.add_node("source", is_source=True)
    g.add_node("valve1")
    g.add_node("valve2")
    g.add_node("asset", tag="asset")
    g.add_edge("source", "valve1")
    g.add_edge("valve1", "asset")
    g.add_edge("source", "valve2")
    g.add_edge("valve2", "asset")
    return g


def test_repeated_runs_with_same_seed_are_identical() -> None:
    engine = SimEngine()
    plan = IsolationPlan(plan_id="p1")
    stim = Stimulus(name="REMOTE_OPEN", magnitude=1.0, duration_s=1.0)

    applied1 = engine.apply(plan, {"steam": build_graph()})
    report1 = engine.run_stimuli(applied1, [stim], seed=123)

    applied2 = engine.apply(plan, {"steam": build_graph()})
    report2 = engine.run_stimuli(applied2, [stim], seed=123)

    assert report1.results == report2.results
    assert report1.results[0].paths == report2.results[0].paths
    assert report1.seed == report2.seed == 123
