import networkx as nx

from loto.models import IsolationAction, IsolationPlan
from loto.sim_engine import SimEngine


def build_graph():
    g = nx.MultiDiGraph()
    g.add_node("source", is_source=True)
    g.add_node("valve1")
    g.add_node("target", tag="asset")
    g.add_node("drain")
    g.add_node("vent")
    g.add_node("bypass")

    # Isolation edge to be removed
    g.add_edge("source", "valve1", is_isolation_point=True, fail_state="FC")
    # Edge with fail-open default
    g.add_edge("valve1", "target", fail_state="FO")
    # Drain and vent edges
    g.add_edge("target", "drain", kind="drain")
    g.add_edge("target", "vent", kind="vent")
    # Edge to test fail-closed default
    g.add_edge("source", "bypass", fail_state="FC")
    return g


def test_apply_removes_edges_and_sets_states():
    original = build_graph()
    plan = IsolationPlan(
        plan_id="demo",
        actions=[IsolationAction(component_id="source->valve1", method="isolate")],
    )

    engine = SimEngine()
    applied = engine.apply(plan, {"steam": original})

    # Original graph is untouched
    assert original.has_edge("source", "valve1")
    assert "state" not in original.get_edge_data("valve1", "target")[0]
    assert "state" not in original.get_edge_data("source", "bypass")[0]

    g = applied["steam"]

    # Isolation edge removed
    assert not g.has_edge("source", "valve1")
    assert g.number_of_edges() == original.number_of_edges() - 1

    # Drains and vents are opened
    assert g.get_edge_data("target", "drain")[0]["state"] == "open"
    assert g.get_edge_data("target", "vent")[0]["state"] == "open"

    # FO/FC defaults applied
    assert g.get_edge_data("valve1", "target")[0]["state"] == "open"
    assert g.get_edge_data("source", "bypass")[0]["state"] == "closed"

    # Graph validity: nodes preserved
    assert set(g.nodes()) == set(original.nodes())
