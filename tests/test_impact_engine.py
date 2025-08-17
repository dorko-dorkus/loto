import networkx as nx

from loto.sim_engine import SimEngine
from loto.isolation_planner import IsolationPlan
from loto.impact import ImpactEngine


def build_graph():
    g = nx.MultiDiGraph()
    g.add_node("source", is_source=True)
    g.add_node("uA", tag="asset")
    g.add_node("uB1", tag="asset")
    g.add_node("uB2", tag="asset")
    g.add_node("local1", tag="asset")

    # edges to assets; some are isolation points
    g.add_edge("source", "uA", is_isolation_point=True)
    g.add_edge("source", "uB1", is_isolation_point=True)
    g.add_edge("source", "uB2")
    g.add_edge("source", "local1", is_isolation_point=True)
    return g


def test_derates_and_unavailable_sets():
    original = build_graph()
    plan = IsolationPlan(
        plan={"steam": [("source", "uA"), ("source", "uB1"), ("source", "local1")]},
        verifications=[],
    )

    sim = SimEngine()
    applied = sim.apply(plan, {"steam": original})

    engine = ImpactEngine()
    asset_units = {"uA": "UnitA", "uB1": "UnitB", "uB2": "UnitB"}
    unit_data = {
        "UnitA": {"rated": 100.0, "scheme": "SPOF"},
        "UnitB": {"rated": 90.0, "scheme": "N+1", "nplus": 2},
    }
    unit_areas = {"UnitA": "North", "UnitB": "North"}
    penalties = {"local1": 5.0}
    asset_areas = {"local1": "South"}

    result = engine.evaluate(
        applied,
        asset_units=asset_units,
        unit_data=unit_data,
        unit_areas=unit_areas,
        penalties=penalties,
        asset_areas=asset_areas,
    )

    assert result.unavailable_assets == {"uA", "uB1", "local1"}
    assert result.unit_mw_delta == {"UnitA": 100.0, "UnitB": 45.0}
    assert result.area_mw_delta == {"North": 145.0, "South": 5.0}
