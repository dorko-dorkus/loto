import networkx as nx

from loto.sim_engine import SimEngine
from loto.isolation_planner import IsolationPlan


def build_graph():
    g = nx.MultiDiGraph()
    g.add_node("source", is_source=True)
    g.add_node("valve1")
    g.add_node("asset", tag="asset")
    g.add_edge("source", "valve1", is_isolation_point=True)
    g.add_edge("valve1", "asset")
    return g


def test_coil_violation_detected(tmp_path):
    table = tmp_path / "logic.csv"
    table.write_text("isolation,actuator_coil\n0,0\n1,0\n1,1\n")

    engine = SimEngine()
    plan = IsolationPlan(plan={"steam": [("source", "valve1")]}, verifications=[])
    applied = engine.apply(plan, {"steam": build_graph()})
    report = engine.run_stimuli(applied, [], logic_table_path=str(table), enable_logic=True)

    logic = [r for r in report.results if r.stimulus_id == "LOGIC_TABLE"]
    assert logic and logic[0].result == "FAIL"
    assert 3 in logic[0].details["rows"]


def test_skip_without_table(tmp_path):
    engine = SimEngine()
    plan = IsolationPlan(plan={"steam": [("source", "valve1")]}, verifications=[])
    applied = engine.apply(plan, {"steam": build_graph()})
    report = engine.run_stimuli(applied, [], logic_table_path=None, enable_logic=True)

    assert all(r.stimulus_id != "LOGIC_TABLE" for r in report.results)


def test_flag_off_by_default(tmp_path):
    table = tmp_path / "logic.csv"
    table.write_text("isolation,actuator_coil\n0,0\n1,0\n1,1\n")

    engine = SimEngine()
    plan = IsolationPlan(plan={"steam": [("source", "valve1")]}, verifications=[])
    applied = engine.apply(plan, {"steam": build_graph()})
    report = engine.run_stimuli(applied, [], logic_table_path=str(table))

    assert all(r.stimulus_id != "LOGIC_TABLE" for r in report.results)
