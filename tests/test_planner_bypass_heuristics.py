import networkx as nx

from loto.isolation_planner import IsolationPlanner
from loto.models import RulePack


def test_bypass_group_included():
    g = nx.MultiDiGraph()
    g.add_node('S', source=True)
    g.add_node('A')
    g.add_node('V1', lockable=True, health=80, bypass_group='G')
    g.add_node('V2', lockable=True, health=70, bypass_group='G')
    g.add_edge('S', 'V1')
    g.add_edge('V1', 'A')

    planner = IsolationPlanner()
    plan = planner.compute({'process': g}, 'A', RulePack())

    assert set(plan.plan['process']) == {'V1', 'V2'}
    assert any('Bypass group G' in note for note in plan.notes)


def test_prefers_lockable_and_healthier_devices():
    g = nx.MultiDiGraph()
    g.add_node('S', source=True)
    g.add_node('A')
    g.add_node('V1', lockable=False, health=90)
    g.add_node('V2', lockable=True, health=70)
    g.add_node('V3', lockable=True, health=60)
    g.add_edge('S', 'V1')
    g.add_edge('V1', 'A')
    g.add_edge('S', 'V2')
    g.add_edge('V2', 'A')
    g.add_edge('S', 'V3')
    g.add_edge('V3', 'A')

    planner = IsolationPlanner()
    plan = planner.compute({'process': g}, 'A', RulePack())

    assert plan.plan['process'] == ['V2']
    assert any('V2' in note for note in plan.notes)
