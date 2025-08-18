import networkx as nx

from loto.isolation_planner import IsolationPlanner
from loto.rule_engine import RulePack


def test_min_cut_blocks_targets():
    g = nx.MultiDiGraph()
    g.add_node('S1', is_source=True)
    g.add_node('S2', is_source=True)
    g.add_node('A')
    g.add_node('t1', tag='asset')
    g.add_node('t2', tag='asset')

    g.add_edge('S1', 'A')
    g.add_edge('S2', 'A')
    g.add_edge('A', 't1', is_isolation_point=True)
    g.add_edge('A', 't2', is_isolation_point=True)

    planner = IsolationPlanner()
    pack = RulePack(version='1', metadata={}, domains={})
    plan = planner.compute({'process': g}, asset_tag='asset', rule_pack=pack)

    edges = {tuple(a.component_id.split('->')) for a in plan.actions}
    assert edges == {('A', 't1'), ('A', 't2')}

    g_cut = g.copy()
    for a in plan.actions:
        u, v = a.component_id.split('->')
        if g_cut.has_edge(u, v):
            g_cut.remove_edges_from([(u, v, k) for k in list(g_cut[u][v])])

    sources = [n for n, data in g_cut.nodes(data=True) if data.get('is_source')]
    targets = [n for n, data in g_cut.nodes(data=True) if data.get('tag') == 'asset']

    for s in sources:
        for t in targets:
            assert not nx.has_path(g_cut, s, t)
