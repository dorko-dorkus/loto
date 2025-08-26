import networkx as nx

from loto.isolation_planner import IsolationPlanner
from loto.rule_engine import RulePack  # type: ignore[attr-defined]


def test_min_cut_blocks_targets() -> None:
    g = nx.MultiDiGraph()
    g.add_node("S1", is_source=True)
    g.add_node("S2", is_source=True)
    g.add_node("A")
    g.add_node("t1", tag="asset")
    g.add_node("t2", tag="asset")

    g.add_edge("S1", "A")
    g.add_edge("S2", "A")
    g.add_edge("A", "t1", is_isolation_point=True)
    g.add_edge("A", "t2", is_isolation_point=True)

    planner = IsolationPlanner()
    pack = RulePack(risk_policies=None)
    plan = planner.compute({"process": g}, asset_tag="asset", rule_pack=pack)

    edges = []
    for action in plan.actions:
        domain, edge = action.component_id.split(":", 1)
        if domain == "process":
            u, v = edge.split("->")
            edges.append((u, v))

    assert set(edges) == {("A", "t1"), ("A", "t2")}

    g_cut = g.copy()
    g_cut.remove_edges_from(edges)

    sources = [n for n, data in g_cut.nodes(data=True) if data.get("is_source")]
    targets = [n for n, data in g_cut.nodes(data=True) if data.get("tag") == "asset"]

    for s in sources:
        for t in targets:
            assert not nx.has_path(g_cut, s, t)


def test_global_cut_smaller_than_union() -> None:
    g = nx.MultiDiGraph()
    g.add_node("S", is_source=True)
    g.add_node("A")
    g.add_node("B")
    g.add_node("t1", tag="asset")
    g.add_node("t2", tag="asset")

    g.add_edge("S", "A")
    g.add_edge("A", "B", is_isolation_point=True)
    g.add_edge("B", "t1", is_isolation_point=True)
    g.add_edge("B", "t2", is_isolation_point=True)

    planner = IsolationPlanner()
    pack = RulePack(risk_policies=None)
    plan = planner.compute({"process": g}, asset_tag="asset", rule_pack=pack)

    cut_edges = []
    for action in plan.actions:
        domain, edge = action.component_id.split(":", 1)
        if domain == "process":
            u, v = edge.split("->")
            cut_edges.append((u, v))

    assert set(cut_edges) == {("A", "B")}

    # Per-target min cuts would select two downstream edges
    sources = [n for n, data in g.nodes(data=True) if data.get("is_source")]
    targets = [n for n, data in g.nodes(data=True) if data.get("tag") == "asset"]

    weighted = nx.DiGraph()
    for u, v, data in g.edges(data=True):
        cap = 1.0 if data.get("is_isolation_point") else float("inf")
        if weighted.has_edge(u, v):
            weighted[u][v]["capacity"] = min(weighted[u][v]["capacity"], cap)
        else:
            weighted.add_edge(u, v, capacity=cap)

    super_source = "__super_source__"
    weighted.add_node(super_source)
    for s in sources:
        weighted.add_edge(super_source, s, capacity=float("inf"))

    union_edges = set()
    for target in targets:
        _, (reachable, non_reachable) = nx.minimum_cut(
            weighted, super_source, target, capacity="capacity"
        )
        for u in reachable:
            if u == super_source:
                continue
            for v in g.successors(u):
                if v in non_reachable:
                    edge_data = g.get_edge_data(u, v)
                    for attrs in edge_data.values():
                        if attrs.get("is_isolation_point"):
                            union_edges.add((u, v))
                            break

    assert union_edges == {("B", "t1"), ("B", "t2")}
    assert len(cut_edges) < len(union_edges)

    g_cut = g.copy()
    g_cut.remove_edges_from(cut_edges)
    for s in sources:
        for t in targets:
            assert not nx.has_path(g_cut, s, t)
