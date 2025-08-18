import networkx as nx

from loto.isolation_planner import IsolationPlanner
from loto.rule_engine import RulePack
from loto import models

def test_isolationplan_type():
    g = nx.MultiDiGraph()
    g.add_node("S", is_source=True)
    g.add_node("T", tag="asset")
    g.add_edge("S", "T", is_isolation_point=True)

    planner = IsolationPlanner()
    pack = RulePack(version="1", metadata={}, domains={})
    plan = planner.compute({"process": g}, asset_tag="asset", rule_pack=pack)

    assert isinstance(plan, models.IsolationPlan)
