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

import logging
import random
from typing import Dict, List

import networkx as nx

from .models import IsolationPlan, RulePack, SimReport, SimResultItem, Stimulus

logger = logging.getLogger(__name__)


class SimEngine:
    """Apply isolation plans and run stimulus tests."""

    def __init__(self, seed: int | None = None) -> None:
        """Create a new simulation engine.

        Parameters
        ----------
        seed: int | None
            Optional random seed used for deterministic behaviour when
            running stimuli.
        """

        self.seed = seed

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
        seed: int | None = None,
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
        seed: int | None
            Optional random seed used for tie-breaking when enumerating
            paths.  When omitted, the engine's seed from the constructor is
            used.

        Returns
        -------
        SimReport
            The simulation report containing results for each processed
            stimulus and the seed used for reproducibility.

        Notes
        -----
        This stub does not implement any simulation logic. Developers
        should add reachability checks and, optionally, simple cause &
        effect evaluation.
        """
        rng_seed = seed if seed is not None else self.seed
        rng = random.Random(rng_seed)
        logger.info("run_stimuli_seed", extra={"seed": rng_seed})

        results: List[SimResultItem] = []

        def _open_by_control(control: str) -> None:
            for graph in applied_graphs.values():
                for _, _, data in graph.edges(data=True):
                    if data.get("control") == control:
                        data["state"] = "open"
                for _, data in graph.nodes(data=True):
                    if data.get("control") == control:
                        data["state"] = "open"

        def _open_by_kind(kind: str, state: str = "open") -> None:
            for graph in applied_graphs.values():
                for _, _, data in graph.edges(data=True):
                    if data.get("kind") == kind:
                        data["state"] = state
                for _, data in graph.nodes(data=True):
                    if data.get("kind") == kind:
                        data["state"] = state

        def _handle_remote_open() -> None:
            _open_by_control("remote")

        def _handle_local_open() -> None:
            _open_by_control("local")

        def _handle_air_return() -> None:
            _open_by_kind("air_return")

        def _handle_esd_reset() -> None:
            _open_by_kind("esd")

        def _handle_pump_start() -> None:
            for graph in applied_graphs.values():
                for _, data in graph.nodes(data=True):
                    if data.get("kind") == "pump":
                        data["state"] = "on"

        dispatch = {
            "REMOTE_OPEN": _handle_remote_open,
            "LOCAL_OPEN": _handle_local_open,
            "AIR_RETURN": _handle_air_return,
            "ESD_RESET": _handle_esd_reset,
            "PUMP_START": _handle_pump_start,
        }

        def k_shortest_paths(g: nx.MultiDiGraph, k: int) -> List[List[str]]:
            """Return up to ``k`` open paths from any source to an asset.

            A path is considered "open" if all of its edges are not in the
            ``closed`` state. Paths are returned in order of increasing length.
            """

            # Build graph of traversable edges (state != 'closed')
            open_graph = nx.DiGraph()
            open_graph.add_nodes_from(g.nodes())
            for u, v, data in g.edges(data=True):
                if data.get("state") != "closed":
                    open_graph.add_edge(u, v)

            sources = [n for n, d in g.nodes(data=True) if d.get("is_source")]
            targets = [n for n, d in g.nodes(data=True) if d.get("tag") == "asset"]

            paths: List[List[str]] = []
            for s in sources:
                for t in targets:
                    try:
                        gen = nx.shortest_simple_paths(open_graph, s, t)
                        for path in gen:
                            paths.append(list(path))
                            if len(paths) >= k:
                                break
                    except nx.NetworkXNoPath:
                        continue
                    if len(paths) >= k:
                        break
                if len(paths) >= k:
                    break

            paths.sort(key=lambda p: (len(p), rng.random()))
            return paths[:k]

        total_time = 0.0
        for stim in stimuli:
            handler = dispatch.get(stim.name)
            if handler is None:
                continue

            handler()

            offending_domain: str | None = None
            offending_paths: List[List[str]] = []
            for domain, graph in applied_graphs.items():
                paths = k_shortest_paths(graph, k=5)
                if paths:
                    offending_domain = domain
                    offending_paths = paths
                    break

            success = not offending_paths
            impact = 0.0 if success else 1.0
            hint = None if success else "extra isolation required"
            results.append(
                SimResultItem(
                    stimulus=stim,
                    success=success,
                    impact=impact,
                    domain=offending_domain,
                    paths=offending_paths,
                    hint=hint,
                )
            )
            total_time += getattr(stim, "duration_s", 0.0)

        return SimReport(results=results, total_time_s=total_time, seed=rng_seed)
