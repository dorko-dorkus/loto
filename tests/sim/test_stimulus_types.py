from typing import Any

import networkx as nx
import pytest

from loto.models import (
    IsolationAction,
    IsolationPlan,
    SimReport,
    SimResultItem,
    Stimulus,
)
from loto.sim_engine import SimEngine


def build_graph() -> nx.MultiDiGraph:
    g = nx.MultiDiGraph()
    g.add_node("source", is_source=True)
    g.add_node("valve1")
    g.add_node("asset", tag="asset")
    g.add_edge("source", "valve1", is_isolation_point=True)
    g.add_edge("valve1", "asset")
    return g


def test_accepts_model_stimulus() -> None:
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

    assert isinstance(report, SimReport)
    assert all(isinstance(r, SimResultItem) for r in report.results)


def test_invalid_stimulus_type_raises() -> None:
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

    invalid_stimuli: Any = [
        {"name": "REMOTE_OPEN", "magnitude": 1.0, "duration_s": 1.0}
    ]
    with pytest.raises(AttributeError):
        engine.run_stimuli(applied, invalid_stimuli)


@pytest.mark.parametrize(
    "stim_name, edge_data, node_data, expected",
    [
        ("REMOTE_OPEN", {"control": "remote", "state": "closed"}, None, "open"),
        ("LOCAL_OPEN", {"control": "local", "state": "closed"}, None, "open"),
        ("AIR_RETURN", None, {"kind": "air_return", "state": "closed"}, "open"),
        ("ESD_RESET", None, {"kind": "esd", "state": "closed"}, "open"),
        ("PUMP_START", None, {"kind": "pump", "state": "off"}, "on"),
    ],
)  # type: ignore[misc]
def test_handlers_mutate_state(
    stim_name: str,
    edge_data: dict[str, str] | None,
    node_data: dict[str, str] | None,
    expected: str,
) -> None:
    g = nx.MultiDiGraph()
    if edge_data is not None:
        g.add_node("u", is_source=True)
        g.add_node("v")
        g.add_edge("u", "v", **edge_data)
    if node_data is not None:
        g.add_node("n", **node_data)

    plan = IsolationPlan(plan_id="p1", actions=[])
    engine = SimEngine()
    applied = engine.apply(plan, {"steam": g})
    stim = Stimulus(name=stim_name, magnitude=1.0, duration_s=1.0)

    engine.run_stimuli(applied, [stim])

    if edge_data is not None:
        assert applied["steam"].edges["u", "v", 0]["state"] == expected
    if node_data is not None:
        assert applied["steam"].nodes["n"]["state"] == expected
