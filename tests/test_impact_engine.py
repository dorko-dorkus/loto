import networkx as nx

from loto.impact import ImpactEngine
from loto.models import IsolationAction, IsolationPlan
from loto.sim_engine import SimEngine


def build_graph() -> nx.MultiDiGraph:
    g = nx.MultiDiGraph()
    g.add_node("source", is_source=True)
    g.add_node("uA", tag="asset")
    g.add_node("uB1", tag="asset")
    g.add_node("uB2", tag="asset")
    g.add_node("local1", tag="asset")

    # edges to assets; some are isolation points
    g.add_edge("source", "uA", is_isolation_point=True)
    g.add_edge("source", "uB1", is_isolation_point=True)
    g.add_edge("source", "uB2", is_isolation_point=True)
    g.add_edge("source", "local1", is_isolation_point=True)
    return g


def test_derates_and_unavailable_sets() -> None:
    original = build_graph()
    plan = IsolationPlan(
        plan_id="p1",
        actions=[
            IsolationAction(
                component_id="steam:source->uA", method="lock", duration_s=0
            ),
            IsolationAction(
                component_id="steam:source->uB1", method="lock", duration_s=0
            ),
            IsolationAction(
                component_id="steam:source->uB2", method="lock", duration_s=0
            ),
            IsolationAction(
                component_id="steam:source->local1", method="lock", duration_s=0
            ),
        ],
    )

    sim = SimEngine()
    applied = sim.apply(plan, {"steam": original})

    engine = ImpactEngine()
    asset_units = {"uA": "UnitA", "uB1": "UnitB", "uB2": "UnitB"}
    unit_data = {
        "UnitA": {"rated": 100.0, "scheme": "SPOF"},
        "UnitB": {"rated": 90.0, "scheme": "N+1"},
    }
    asset_mw = {"uA": 100.0, "uB1": 60.0, "uB2": 40.0}
    asset_groups = {"uA": "gA", "uB1": "gB", "uB2": "gB"}
    group_caps = {"gA": 100.0, "gB": 70.0}
    unit_areas = {"UnitA": "North", "UnitB": "North"}
    penalties = {"local1": 5.0}
    asset_areas = {"local1": "South"}

    result = engine.evaluate(
        applied,
        asset_units=asset_units,
        unit_data=unit_data,
        unit_areas=unit_areas,
        asset_mw=asset_mw,
        asset_groups=asset_groups,
        group_caps=group_caps,
        penalties=penalties,
        asset_areas=asset_areas,
    )

    assert result.unavailable_assets == {"uA", "uB1", "uB2", "local1"}
    assert result.unit_mw_delta == {"UnitA": 100.0, "UnitB": 70.0}
    assert result.area_mw_delta == {"North": 170.0, "South": 5.0}
