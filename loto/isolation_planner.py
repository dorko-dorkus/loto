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

from typing import Any, Dict, List, Set, Tuple

import networkx as nx  # type: ignore

from .rule_engine import RulePack


class IsolationPlan:
    """Represents the output of the isolation planner.

    Attributes
    ----------
    plan: Dict[str, List[Any]]
        A mapping from energy domain to the list of isolation actions
        (e.g., valves to close, drains to open). The structure of each
        action should be defined in future iterations.
    verifications: List[Any]
        A list of verification steps (pressure checks, test-before-touch,
        etc.) required to confirm that the isolation is effective.
    """

    def __init__(self, plan: Dict[str, List[Any]], verifications: List[Any]):
        self.plan = plan
        self.verifications = verifications


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
            targets = [n for n, data in graph.nodes(data=True) if data.get("tag") == asset_tag]

            if not sources or not targets:
                plan[domain] = []
                continue

            # Build weighted graph for min-cut computations
            weighted = nx.DiGraph()
            for u, v, data in graph.edges(data=True):
                cap = 1.0 if data.get("is_isolation_point") else float("inf")
                if weighted.has_edge(u, v):
                    # Keep the lowest capacity if multiple edges exist
                    weighted[u][v]["capacity"] = min(weighted[u][v]["capacity"], cap)
                else:
                    weighted.add_edge(u, v, capacity=cap)

            super_source = "__super_source__"
            weighted.add_node(super_source)
            for s in sources:
                weighted.add_edge(super_source, s, capacity=float("inf"))

            cut_edges: Set[Tuple[str, str]] = set()

            for target in targets:
                _, (reachable, non_reachable) = nx.minimum_cut(
                    weighted, super_source, target, capacity="capacity"
                )

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

        return IsolationPlan(plan=plan, verifications=[])
