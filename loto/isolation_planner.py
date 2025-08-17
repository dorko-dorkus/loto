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

from typing import Any, Dict, List

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

        This intentionally tiny implementation focuses on expanding the
        double-block-and-bleed (DDBB) rule for steam networks.  The planner
        searches the provided graph for the two closest block valves, the
        closest bleed, any nearby drains or vents, and a PT/TT node for
        verification.  Actions are returned in the order required by the
        specification: blocks → bleed → drains → verification.

        Parameters
        ----------
        graphs:
            Mapping of domain names to connectivity graphs.  Only the
            ``"steam"`` domain is examined.
        asset_tag:
            Tag of the asset to isolate.  The asset must exist in the graph
            as a node identifier.
        rule_pack:
            Unused placeholder for future rule-based logic.  Present for API
            compatibility.

        Returns
        -------
        IsolationPlan
            Structured list of isolation actions and verification steps.
        """

        # Retrieve the steam domain graph.
        graph = graphs.get("steam")
        if graph is None:
            raise ValueError("steam domain graph is required")

        if asset_tag not in graph:
            raise ValueError(f"asset '{asset_tag}' not present in graph")

        # Compute shortest path lengths from the asset to all other nodes.
        distances = nx.single_source_shortest_path_length(graph, asset_tag)

        def _candidates(types: set[str]) -> List[tuple[int, float, str]]:
            """Return candidate nodes of the given types.

            Each candidate is represented as ``(distance, -health_score, id)`` so
            that sorting yields nearest nodes and, for equal distances, those with
            higher ``health_score`` first.
            """

            out: List[tuple[int, float, str]] = []
            for node, data in graph.nodes(data=True):
                if data.get("type") in types and node in distances:
                    health = float(data.get("health_score", 0.0))
                    out.append((distances[node], -health, node))
            out.sort()
            return out

        # Select two closest block valves with health-score tie break.
        block_nodes = [n for _, _, n in _candidates({"block"})[:2]]

        # Closest bleed valve.
        bleed_nodes = _candidates({"bleed"})
        bleed = bleed_nodes[0][2] if bleed_nodes else None

        # Closest drain or vent.
        drain_nodes = _candidates({"drain", "vent"})
        drain = drain_nodes[0][2] if drain_nodes else None

        # Verification: nearest PT or TT.
        verify_nodes = _candidates({"pt", "tt"})
        verify = verify_nodes[0][2] if verify_nodes else None

        actions: List[Dict[str, str]] = []
        for node in block_nodes:
            actions.append({"component": node, "action": "CLOSE"})
        if bleed:
            actions.append({"component": bleed, "action": "OPEN"})
        if drain:
            actions.append({"component": drain, "action": "OPEN"})

        verifications: List[Dict[str, str]] = []
        if verify:
            verifications.append({"component": verify, "action": "VERIFY"})

        return IsolationPlan(plan={"steam": actions}, verifications=verifications)
