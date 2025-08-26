"""Isolation planner for the LOTO system.

The :class:`IsolationPlanner` computes minimal cut sets for isolating
energy sources from target assets based on domain graphs produced by
the :class:`loto.graph_builder.GraphBuilder` and rules loaded by
the :class:`loto.rule_engine.RuleEngine`. The planner also applies
domain-specific constraints such as double-block-and-bleed requirements
and bypass handling.

Method bodies in this stub are intentionally left unimplemented. Use
these signatures as a starting point for a full implementation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple

import networkx as nx

from .models import IsolationAction, IsolationPlan, RulePack


@dataclass
class VerificationGate:
    """Require approvals from two distinct users before energization."""

    approved_by: Set[str] = field(default_factory=set)

    def approve(self, user: str) -> bool:
        """Record approval by ``user`` and return readiness state."""

        self.approved_by.add(user)
        return self.is_ready

    @property
    def is_ready(self) -> bool:
        """Whether energization can proceed."""

        return len(self.approved_by) >= 2


class IsolationPlanner:
    """Compute isolation plans from domain graphs and rule packs."""

    def compute(
        self,
        graphs: Dict[str, nx.MultiDiGraph],
        asset_tag: str,
        rule_pack: RulePack,
    ) -> IsolationPlan:
        """Compute a minimal cut-set isolation plan for the given asset.

        Parameters
        ----------
        graphs: Dict[str, nx.MultiDiGraph]
            Mapping of domain names to connectivity graphs.
        asset_tag: str
            The tag of the asset to isolate.
        rule_pack: RulePack
            The rule pack containing domain-specific isolation rules.

        Returns
        -------
        IsolationPlan
            The computed isolation plan including isolation actions and
            verification steps.

        Notes
        -----
        This implementation performs a basic minimum cut computation.  For
        each domain graph it identifies all source nodes (``is_source``) and
        target nodes whose ``tag`` matches ``asset_tag``.  Candidate edges are
        those marked with ``is_isolation_point``.  A min-cut is computed between
        a super source aggregating all sources and each target individually with
        unit capacity on candidate edges and infinite capacity elsewhere.  The
        union of all edges in these cut sets forms the raw isolation plan for
        that domain.
        """

        plan: Dict[str, List[Tuple[str, str]]] = {}

        for domain, graph in graphs.items():
            sources = [n for n, data in graph.nodes(data=True) if data.get("is_source")]
            targets = [
                n for n, data in graph.nodes(data=True) if data.get("tag") == asset_tag
            ]

            if not sources or not targets:
                plan[domain] = []
                continue

            # Build weighted graph for min-cut computations
            weighted = nx.DiGraph()
            for u, v, data in graph.edges(data=True):
                cap = (
                    data.get("isolation_cost", 1.0)
                    if data.get("is_isolation_point")
                    else float("inf")
                )
                if weighted.has_edge(u, v):
                    # Keep the lowest capacity if multiple edges exist
                    weighted[u][v]["capacity"] = min(weighted[u][v]["capacity"], cap)
                else:
                    weighted.add_edge(u, v, capacity=cap)

            super_source = "__super_source__"
            super_sink = "__super_sink__"
            weighted.add_node(super_source)
            weighted.add_node(super_sink)
            for s in sources:
                weighted.add_edge(super_source, s, capacity=float("inf"))
            for t in targets:
                weighted.add_edge(t, super_sink, capacity=float("inf"))

            _, (reachable, non_reachable) = nx.minimum_cut(
                weighted, super_source, super_sink, capacity="capacity"
            )

            cut_edges: Set[Tuple[str, str]] = set()
            for u in reachable:
                if u == super_source:
                    continue
                for v in graph.successors(u):
                    if v in non_reachable:
                        edge_data = graph.get_edge_data(u, v)
                        for attrs in edge_data.values():
                            if attrs.get("is_isolation_point"):
                                cut_edges.add((u, v))
                                break

            plan[domain] = list(cut_edges)

        actions: List[IsolationAction] = []
        for domain, edges in plan.items():
            for u, v in edges:
                actions.append(
                    IsolationAction(
                        component_id=f"{domain}:{u}->{v}",
                        method="lock",
                        duration_s=0.0,
                    )
                )
        verifications: List[str] = []
        hazards: List[str] = []
        controls: List[str] = []

        def shortest_open_path(g: nx.MultiDiGraph) -> List[str] | None:
            """Return shortest path from any source to the target using open edges."""

            open_graph = nx.DiGraph()
            open_graph.add_nodes_from(g.nodes())
            for u, v, data in g.edges(data=True):
                if data.get("state") != "closed":
                    open_graph.add_edge(u, v)

            sources = [n for n, d in g.nodes(data=True) if d.get("is_source")]
            targets = [n for n, d in g.nodes(data=True) if d.get("tag") == asset_tag]

            best: List[str] | None = None
            for s in sources:
                for t in targets:
                    try:
                        path = nx.shortest_path(open_graph, s, t)
                    except nx.NetworkXNoPath:
                        continue
                    if best is None or len(path) < len(best):
                        best = path
            return best

        for domain, edges in plan.items():
            if not edges:
                continue
            branch_graph = nx.Graph()
            branch_graph.add_edges_from(edges)
            sources = [
                n for n, d in graphs[domain].nodes(data=True) if d.get("is_source")
            ]
            targets = [
                n
                for n, d in graphs[domain].nodes(data=True)
                if d.get("tag") == asset_tag
            ]
            for component in nx.connected_components(branch_graph):
                branch_label = f"{domain}:{'-'.join(sorted(component))}"
                verifications.append(f"{branch_label} PT=0")
                verifications.append(f"{branch_label} no-movement")

                ddbb_found = False
                for node in component:
                    bleed_present = any(
                        data.get("is_bleed")
                        for _, _, data in graphs[domain].out_edges(node, data=True)
                    )
                    if not bleed_present:
                        continue

                    if not any(nx.has_path(graphs[domain], s, node) for s in sources):
                        continue
                    if not any(nx.has_path(graphs[domain], node, t) for t in targets):
                        continue

                    upstream_iso = [
                        (pred, node)
                        for pred in graphs[domain].predecessors(node)
                        if any(
                            data.get("is_isolation_point")
                            for data in graphs[domain]
                            .get_edge_data(pred, node)
                            .values()
                        )
                    ]
                    downstream_iso = [
                        (node, succ)
                        for succ in graphs[domain].successors(node)
                        if any(
                            data.get("is_isolation_point")
                            for data in graphs[domain]
                            .get_edge_data(node, succ)
                            .values()
                        )
                    ]

                    if not upstream_iso or not downstream_iso:
                        continue

                    for ui in upstream_iso:
                        for di in downstream_iso:
                            g = graphs[domain].copy()
                            if g.has_edge(*ui):
                                g.remove_edges_from(
                                    [(ui[0], ui[1], k) for k in list(g[ui[0]][ui[1]])]
                                )
                            if g.has_edge(*di):
                                g.remove_edges_from(
                                    [(di[0], di[1], k) for k in list(g[di[0]][di[1]])]
                                )
                            if shortest_open_path(g) is None:
                                verifications.append(f"{branch_label} DDBB")
                                ddbb_found = True
                                break
                        if ddbb_found:
                            break
                    if ddbb_found:
                        break
                if ddbb_found:
                    continue

        return IsolationPlan(
            plan_id=asset_tag,
            actions=actions,
            verifications=verifications,
            hazards=hazards,
            controls=controls,
        )
