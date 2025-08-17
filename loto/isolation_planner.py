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

from typing import Any, Dict, List, Tuple

import networkx as nx  # type: ignore

from .rule_engine import RulePack


class IsolationPlan:
    """Represents the output of the isolation planner.

    Parameters
    ----------
    plan:
        Mapping of energy domain to a list of isolation actions.  For this
        simplified implementation the actions are represented by component
        identifiers.
    verifications:
        Verification steps to confirm an isolation is effective.
    notes:
        Human readable notes describing why particular components were chosen.
    """

    def __init__(self, plan: Dict[str, List[Any]], verifications: List[Any], notes: List[str]):
        self.plan = plan
        self.verifications = verifications
        self.notes = notes


class IsolationPlanner:
    """Compute isolation plans from domain graphs and rule packs.

    The real project will eventually implement full minimal cut-set
    computation.  For the purposes of the exercises in this repository the
    planner focuses on a couple of behaviours that are easy to test:

    * If a path from an energy source to the asset uses a component that is
      part of a ``bypass_group`` then *all* members of that group must be
      included in the resulting isolation set.
    * When multiple alternative paths exist, prefer those that contain more
      lockable devices and, where tied, devices with healthier status
      (numerically larger ``health`` attribute).
    * Selections are recorded in ``notes`` so test cases can assert why a
      particular path was chosen.
    """

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

        """
        plan: Dict[str, List[Any]] = {}
        notes: List[str] = []

        for domain, graph in graphs.items():
            if asset_tag not in graph:
                continue

            # determine all source nodes
            sources = [n for n, d in graph.nodes(data=True) if d.get("source")]
            if not sources:
                continue

            best_devices: List[str] | None = None
            best_score: Tuple[int, int] = (-1, -1)
            best_notes: List[str] = []

            for src in sources:
                try:
                    paths = nx.all_simple_paths(graph, src, asset_tag)
                except nx.NetworkXNoPath:  # pragma: no cover - safety
                    continue
                for path in paths:
                    devices: List[str] = []
                    path_notes: List[str] = []

                    # skip first and last node (source and asset)
                    for node in path[1:-1]:
                        data = graph.nodes[node]
                        group = data.get("bypass_group")
                        if group:
                            members = [
                                n
                                for n, d in graph.nodes(data=True)
                                if d.get("bypass_group") == group
                            ]
                            for member in members:
                                if member not in devices:
                                    devices.append(member)
                            # choose the best member for explanation purposes
                            best_member = max(
                                members,
                                key=lambda m: (
                                    bool(graph.nodes[m].get("lockable")),
                                    graph.nodes[m].get("health", 0),
                                ),
                            )
                            path_notes.append(
                                f"Bypass group {group}: selected {best_member}"
                            )
                        else:
                            if node not in devices:
                                devices.append(node)

                    lockable_count = sum(
                        1 for n in devices if graph.nodes[n].get("lockable")
                    )
                    health_total = sum(
                        graph.nodes[n].get("health", 0) for n in devices
                    )
                    score = (lockable_count, health_total)
                    if score > best_score:
                        best_score = score
                        best_devices = devices
                        best_notes = path_notes

            if best_devices is None:
                raise ValueError(
                    f"No path found from sources to {asset_tag} in domain {domain}"
                )

            plan[domain] = best_devices
            notes.extend(best_notes)
            if best_devices:
                notes.append(
                    f"Selected path in {domain} using components: {', '.join(best_devices)}"
                )

        return IsolationPlan(plan=plan, verifications=[], notes=notes)
