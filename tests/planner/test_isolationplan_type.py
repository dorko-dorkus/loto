import networkx as nx
import pytest

from loto.isolation_planner import IsolationPlanner
from loto.rule_engine import RulePack  # type: ignore[attr-defined]
from loto.models import IsolationPlan


def test_planner_returns_models_isolationplan(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PLANNER_NODE_SPLIT", "0")
    g = nx.MultiDiGraph()
    g.add_node("s", is_source=True)
    g.add_node("t", tag="asset")
    g.add_edge("s", "t", is_isolation_point=True)

    planner = IsolationPlanner()
    pack = RulePack(risk_policies=None)
    result = planner.compute({"process": g}, asset_tag="asset", rule_pack=pack)

    assert isinstance(result, IsolationPlan)
