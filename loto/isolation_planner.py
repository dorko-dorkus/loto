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

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Set, Tuple

import networkx as nx

from .models import IsolationAction, IsolationPlan, RulePack


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


ALPHA = _env_float("W_ALPHA", 1.0)
BETA = _env_float("W_BETA", 5.0)
GAMMA = _env_float("W_GAMMA", 0.5)
DELTA = _env_float("W_DELTA", 1.0)
EPSILON = _env_float("W_EPSILON", 2.0)
ZETA = _env_float("W_ZETA", 0.5)
CB_SCALE = _env_float("CB_SCALE", 30.0)
CB_MAX = _env_float("CB_MAX", 120.0)
RST_SCALE = _env_float("RST_SCALE", 30.0)


def _split_nodes(graph: nx.MultiDiGraph) -> nx.MultiDiGraph:
    """Split isolatable nodes into ``node_in``/``node_out`` pairs.

    Edges incident to device nodes are rerouted through the new pair with a
    single capacity edge between them representing the device.
    """

    split = nx.MultiDiGraph()

    for node, attrs in graph.nodes(data=True):
        if attrs.get("is_isolation_point"):
            attrs_copy = dict(attrs)
            split.add_node(f"{node}_in", **attrs_copy)
            split.add_node(f"{node}_out", **attrs_copy)
            cap_attrs: Dict[str, Any] = {}
            for _, _, data in graph.in_edges(node, data=True):
                if data.get("is_isolation_point"):
                    cap_attrs = dict(data)
                    break
            if not cap_attrs:
                for _, _, data in graph.out_edges(node, data=True):
                    if data.get("is_isolation_point"):
                        cap_attrs = dict(data)
                        break
            cap_attrs["is_isolation_point"] = True
            split.add_edge(f"{node}_in", f"{node}_out", **cap_attrs)
        else:
            split.add_node(node, **attrs)

    for u, v, data in graph.edges(data=True):
        new_u = f"{u}_out" if graph.nodes[u].get("is_isolation_point") else u
        new_v = f"{v}_in" if graph.nodes[v].get("is_isolation_point") else v
        data_copy = dict(data)
        data_copy["is_isolation_point"] = False
        split.add_edge(new_u, new_v, **data_copy)

    return split


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
        *,
        config: Mapping[str, Any] | None = None,
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

        cbt = float((config or {}).get("callback_time_min", 0))

        node_split = os.getenv("PLANNER_NODE_SPLIT", "1") not in ("0", "")
        work_graphs: Dict[str, nx.MultiDiGraph] = {}

        for domain, base_graph in graphs.items():
            graph = _split_nodes(base_graph) if node_split else base_graph
            work_graphs[domain] = graph
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
                if data.get("is_isolation_point"):
                    op_cost = (
                        data.get("op_cost_min")
                        or graph.nodes[u].get("op_cost_min")
                        or graph.nodes[v].get("op_cost_min")
                        or 0.0
                    )
                    reset_time = (
                        data.get("reset_time_min")
                        or graph.nodes[u].get("reset_time_min")
                        or graph.nodes[v].get("reset_time_min")
                        or 0.0
                    )
                    risk_weight = data.get("risk_weight", 0.0)
                    travel_time = data.get("travel_time_min", 0.0)
                    elevation_penalty = data.get("elevation_penalty", 0.0)
                    outage_penalty = data.get("outage_penalty", 0.0)
                    base = (
                        ALPHA * op_cost
                        + BETA * risk_weight
                        + GAMMA * travel_time
                        + DELTA * elevation_penalty
                        + EPSILON * outage_penalty
                    )
                    if base == 0:
                        base = 1.0
                    mult = 1 + min(cbt, CB_MAX) / CB_SCALE
                    cap = base * mult + ZETA * reset_time * (1 + cbt / RST_SCALE)
                else:
                    cap = float("inf")
                if weighted.has_edge(u, v):
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
                n for n, d in work_graphs[domain].nodes(data=True) if d.get("is_source")
            ]
            targets = [
                n
                for n, d in work_graphs[domain].nodes(data=True)
                if d.get("tag") == asset_tag
            ]
            for component in nx.connected_components(branch_graph):
                branch_label = f"{domain}:{'-'.join(sorted(component))}"
                verifications.append(f"{branch_label} PT=0")
                verifications.append(f"{branch_label} no-movement")

                ddbb_found = False
                for node in component:
                    bleed_edges = [
                        (node, succ)
                        for succ in work_graphs[domain].successors(node)
                        if any(
                            data.get("is_bleed")
                            for data in work_graphs[domain]
                            .get_edge_data(node, succ)
                            .values()
                        )
                    ]
                    if not bleed_edges:
                        continue

                    if not any(
                        nx.has_path(work_graphs[domain], s, node) for s in sources
                    ):
                        continue
                    if not any(
                        nx.has_path(work_graphs[domain], node, t) for t in targets
                    ):
                        continue

                    upstream_iso = [
                        (pred, node)
                        for pred in work_graphs[domain].predecessors(node)
                        if any(
                            data.get("is_isolation_point")
                            for data in work_graphs[domain]
                            .get_edge_data(pred, node)
                            .values()
                        )
                    ]
                    downstream_iso = [
                        (node, succ)
                        for succ in work_graphs[domain].successors(node)
                        if any(
                            data.get("is_isolation_point")
                            for data in work_graphs[domain]
                            .get_edge_data(node, succ)
                            .values()
                        )
                    ]

                    if not upstream_iso or not downstream_iso:
                        continue

                    def set_state(
                        g: nx.MultiDiGraph,
                        edge: Tuple[str, str],
                        state: str,
                        *,
                        bleed_only: bool = False,
                    ) -> None:
                        u, v = edge
                        if not g.has_edge(u, v):
                            return
                        for k, data in g[u][v].items():
                            if bleed_only and not data.get("is_bleed"):
                                continue
                            data["state"] = state

                    def can_reach_safe_sink(g: nx.MultiDiGraph, start: str) -> bool:
                        open_graph = nx.DiGraph()
                        open_graph.add_nodes_from(g.nodes(data=True))
                        for u, v, d in g.edges(data=True):
                            if d.get("state") != "closed":
                                open_graph.add_edge(u, v)
                        sinks = [n for n, d in g.nodes(data=True) if d.get("safe_sink")]
                        return any(nx.has_path(open_graph, start, s) for s in sinks)

                    for ui in upstream_iso:
                        for di in downstream_iso:
                            for bleed in bleed_edges:
                                g = work_graphs[domain].copy()
                                set_state(g, ui, "closed")
                                set_state(g, di, "closed")
                                set_state(g, bleed, "open", bleed_only=True)
                                if shortest_open_path(g) is not None:
                                    continue
                                if not can_reach_safe_sink(g, bleed[0]):
                                    continue
                                redundant = False
                                g_up = g.copy()
                                set_state(g_up, ui, "open")
                                if shortest_open_path(g_up) is None:
                                    redundant = True
                                g_dn = g.copy()
                                set_state(g_dn, di, "open")
                                if shortest_open_path(g_dn) is None:
                                    redundant = True
                                cert = f"{ui[0]}->{ui[1]},{bleed[0]}->{bleed[1]},{di[0]}->{di[1]}"
                                verifications.append(f"{branch_label} DDBB {cert}")
                                if redundant:
                                    verifications.append(
                                        f"{branch_label} redundant DDBB path"
                                    )
                                ddbb_found = True
                                break
                            if ddbb_found:
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
