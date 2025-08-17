import networkx as nx

from loto.sim_engine import SimEngine, Stimulus
from loto.isolation_planner import IsolationPlan



def build_graph():
    g = nx.MultiDiGraph()
    g.add_node("source", is_source=True)
    g.add_node("valve1")
    g.add_node("asset", tag="asset")
    g.add_edge("source", "valve1", is_isolation_point=True)
    g.add_edge("valve1", "asset")
    return g


def make_stimuli():
    ids = ["REMOTE_OPEN", "LOCAL_OPEN", "AIR_RETURN", "ESD_RESET", "PUMP_START"]
    return [Stimulus(id=s) for s in ids]


def test_valid_plan_pass():
    g = build_graph()
    plan = IsolationPlan(plan={"steam": [("source", "valve1")]}, verifications=[])
    engine = SimEngine()
    applied = engine.apply(plan, {"steam": g})

    report = engine.run_stimuli(applied, make_stimuli())

    assert report.unknowns == []
    assert all(r.result == "PASS" for r in report.results)


def test_tampered_plan_fail():
    g = build_graph()
    plan = IsolationPlan(plan={"steam": []}, verifications=[])
    engine = SimEngine()
    applied = engine.apply(plan, {"steam": g})

    report = engine.run_stimuli(applied, make_stimuli())

    assert all(r.result == "FAIL" for r in report.results)
    for r in report.results:
        assert r.details["path"] == ["source", "valve1", "asset"]
        assert "extra isolation" in r.details["suggestion"].lower()
