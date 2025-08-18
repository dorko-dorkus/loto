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

from dataclasses import dataclass
from typing import Any, Dict, List

import networkx as nx  # type: ignore

from .isolation_planner import IsolationPlan
from .rule_engine import RulePack


@dataclass
class Stimulus:
    """Represents a stimulus applied during simulation testing.

    Attributes
    ----------
    id: str
        A unique identifier for the stimulus (e.g., 'REMOTE_OPEN').
    parameters: Dict[str, Any]
        Optional parameters required for the stimulus (e.g., which
        actuator to toggle). The structure is currently undefined.
    """

    id: str
    parameters: Dict[str, Any] | None = None


@dataclass
class StimulusResult:
    """Holds the result of applying a stimulus during simulation."""

    stimulus_id: str
    result: str  # expected values: 'PASS' or 'FAIL'
    details: Dict[str, Any] | None = None


class SimReport:
    """Represents the outcome of a simulation run."""

    def __init__(self, results: List[StimulusResult], unknowns: List[str]):
        self.results = results
        self.unknowns = unknowns


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

        for domain, graph in graphs.items():
            # ``nx.Graph.copy`` performs a shallow copy where the adjacency
            # structure and attribute dictionaries are duplicated.  Mutating
            # the returned graph therefore leaves ``graph`` untouched, which
            # keeps ``apply`` a pure function.
            g = graph.copy()

            # Remove edges specified in the isolation plan.  Each entry can
            # either specify an explicit key (u, v, k) or an edge pair (u, v)
            # in which case all multi-edges between the nodes are removed.
            for edge in plan.plan.get(domain, []):
                u, v, *rest = edge  # type: ignore[misc]
                if rest:  # A specific key is provided
                    k = rest[0]
                    if g.has_edge(u, v, k):
                        g.remove_edge(u, v, k)
                elif g.has_edge(u, v):
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
            The simulation report containing results per stimulus and
            a list of unknowns encountered during the process.

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

        results: List[StimulusResult] = []
        unknowns: List[str] = []

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

        for stim in stimuli:
            if stim.id not in supported:
                unknowns.append(stim.id)
                continue

            offending: List[str] | None = None
            for graph in applied_graphs.values():
                path = shortest_path(graph)
                if path is not None:
                    if offending is None or len(path) < len(offending):
                        offending = path

            if offending:
                details = {
                    "path": offending,
                    "suggestion": "Apply extra isolation",
                }
                results.append(
                    StimulusResult(stimulus_id=stim.id, result="FAIL", details=details)
                )
            else:
                results.append(StimulusResult(stimulus_id=stim.id, result="PASS"))

        return SimReport(results, unknowns)
