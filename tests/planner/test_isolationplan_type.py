import networkx as nx

from loto.isolation_planner import IsolationPlanner
from loto.rule_engine import RulePack
from loto.models import IsolationPlan


def test_planner_returns_models_isolationplan():
    g = nx.MultiDiGraph()
    g.add_node("s", is_source=True)
    g.add_node("t", tag="asset")
    g.add_edge("s", "t", is_isolation_point=True)

    planner = IsolationPlanner()
    pack = RulePack()
    result = planner.compute({"process": g}, asset_tag="asset", rule_pack=pack)

    assert isinstance(result, IsolationPlan)
