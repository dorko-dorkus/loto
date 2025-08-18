"""Simulation engine for the LOTO planner.

The simulation engine applies an isolation plan to domain graphs and
executes predefined stimuli (remote commands, local toggles, air
restores, etc.) to verify that isolated assets remain de-energized.
It also checks invariants such as unreachable energy paths and can be
extended to evaluate simple cause & effect logic.

This module defines basic class stubs; real implementations must be
provided by developers. The simulation engine should be deterministic
and must not control real hardware.
"""

from __future__ import annotations

from typing import Dict, List

import networkx as nx  # type: ignore

from .models import IsolationPlan, SimReport, SimResultItem, Stimulus
from .rule_engine import RulePack


class SimEngine:
    """Apply isolation plans and run stimulus tests."""

    def apply(
        self, plan: IsolationPlan, graphs: Dict[str, nx.MultiDiGraph]
    ) -> Dict[str, nx.MultiDiGraph]:
        """Return isolated copies of each domain graph.

        The method performs a pure transformation of ``graphs`` by cloning
        each :class:`~networkx.MultiDiGraph` and applying the actions from the
        isolation ``plan``.  Edges listed in the plan are removed, drains and
        vents are opened, and components with a fail-open (``FO``) or
        fail-closed (``FC``) designation have their default ``state`` set
        accordingly.  The original ``graphs`` are not modified.

        Parameters
        ----------
        plan:
            The isolation plan produced by the planner.
        graphs:
            Mapping of domain names to their connectivity graphs.

        Returns
        -------
        Dict[str, nx.MultiDiGraph]
            New graphs with isolation actions applied.
        """

        isolated: Dict[str, nx.MultiDiGraph] = {}

        # Build mapping from domain to edge tuples encoded in the plan actions
        plan_edges: Dict[str, List[tuple[str, str]]] = {}
        for action in plan.actions:
            try:
                domain, edge = action.component_id.split(":", 1)
                u, v = edge.split("->")
            except ValueError:
                continue
            plan_edges.setdefault(domain, []).append((u, v))

        for domain, graph in graphs.items():
            # ``nx.Graph.copy`` performs a shallow copy where the adjacency
            # structure and attribute dictionaries are duplicated.  Mutating
            # the returned graph therefore leaves ``graph`` untouched, which
            # keeps ``apply`` a pure function.
            g = graph.copy()

            # Remove edges specified in the isolation plan
            for u, v in plan_edges.get(domain, []):
                if g.has_edge(u, v):
                    g.remove_edges_from([(u, v, k) for k in list(g[u][v])])

            # Set states for edges and nodes.  Drains and vents are always
            # opened while other components fall back to their fail state if
            # one is supplied.
            for _, _, _, data in g.edges(data=True, keys=True):
                if data.get("kind") in {"drain", "vent"}:
                    data["state"] = "open"
                elif "state" not in data:
                    fail = data.get("fail_state")
                    if fail == "FO":
                        data["state"] = "open"
                    elif fail == "FC":
                        data["state"] = "closed"

            for _, data in g.nodes(data=True):
                if data.get("kind") in {"drain", "vent"}:
                    data["state"] = "open"
                elif "state" not in data:
                    fail = data.get("fail_state")
                    if fail == "FO":
                        data["state"] = "open"
                    elif fail == "FC":
                        data["state"] = "closed"

            isolated[domain] = g

        return isolated

    def run_stimuli(
        self,
        applied_graphs: Dict[str, nx.MultiDiGraph],
        stimuli: List[Stimulus],
        rule_pack: "RulePack" | None = None,
    ) -> SimReport:
        """Run stimuli on the isolated graphs and check invariants.

        Parameters
        ----------
        applied_graphs: Dict[str, nx.MultiDiGraph]
            The graphs after isolation actions have been applied.
        stimuli: List[Stimulus]
            A list of stimuli to apply (remote commands, local toggles, etc.).
        rule_pack: RulePack | None
            Optional rule pack for domain-specific behaviour; may not be
            necessary for simple reachability checks.

        Returns
        -------
        SimReport
            The simulation report containing results for each processed stimulus.

        Notes
        -----
        This stub does not implement any simulation logic. Developers
        should add reachability checks and, optionally, simple cause &
        effect evaluation.
        """
        supported = {
            "REMOTE_OPEN",
            "LOCAL_OPEN",
            "AIR_RETURN",
            "ESD_RESET",
            "PUMP_START",
        }

        results: List[SimResultItem] = []

        def shortest_path(g: nx.MultiDiGraph) -> List[str] | None:
            """Return shortest open path from any source to an asset."""

            # Build graph of traversable edges (state != 'closed')
            open_graph = nx.DiGraph()
            open_graph.add_nodes_from(g.nodes())
            for u, v, data in g.edges(data=True):
                if data.get("state") != "closed":
                    open_graph.add_edge(u, v)

            sources = [n for n, d in g.nodes(data=True) if d.get("is_source")]
            targets = [n for n, d in g.nodes(data=True) if d.get("tag") == "asset"]

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

        total_time = 0.0
        for stim in stimuli:
            if stim.name not in supported:
                continue

            offending_domain: str | None = None
            offending_path: List[str] | None = None
            for domain, graph in applied_graphs.items():
                path = shortest_path(graph)
                if path is not None:
                    offending_domain = domain
                    offending_path = path
                    break

            success = offending_path is None
            impact = 0.0 if success else 1.0
            hint = None if success else "extra isolation required"
            results.append(
                SimResultItem(
                    stimulus=stim,
                    success=success,
                    impact=impact,
                    domain=offending_domain,
                    path=offending_path,
                    hint=hint,
                )
            )
            total_time += getattr(stim, "duration_s", 0.0)

        return SimReport(results=results, total_time_s=total_time)
