"""Impact analysis engine for the LOTO planner.

This module provides a small utility to quantify the impact of an
isolation on generating units and geographical areas.  After an
isolation plan has been applied to the domain graphs (see
:mod:`loto.sim_engine`), the :class:`ImpactEngine` can be used to
identify which asset nodes have become unavailable and to translate
those outages into megawatt (MW) derates for the affected units and
areas.

The implementation intentionally focuses on a minimal, pure-python
approach suitable for unit testing.  Real deployments may wish to
extend the data structures or integrate with external asset
management systems.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, Set

import networkx as nx  # type: ignore


@dataclass
class ImpactResult:
    """Container returned by :meth:`ImpactEngine.evaluate`.

    Attributes
    ----------
    unavailable_assets:
        Set of asset identifiers that became unreachable after
        isolation actions were applied.
    unit_mw_delta:
        Mapping of unit name to lost capacity (in MW).
    area_mw_delta:
        Mapping of area name to lost capacity (in MW).  Area deltas
        include unit derates and any local penalties associated with
        assets that are not part of a unit.
    """

    unavailable_assets: Set[str]
    unit_mw_delta: Dict[str, float]
    area_mw_delta: Dict[str, float]


class ImpactEngine:
    """Compute asset availability and capacity derates."""

    def evaluate(
        self,
        applied_graphs: Dict[str, nx.MultiDiGraph],
        asset_units: Dict[str, str],
        unit_data: Dict[str, Dict[str, Any]],
        unit_areas: Dict[str, str],
        penalties: Dict[str, float] | None = None,
        asset_areas: Dict[str, str] | None = None,
    ) -> ImpactResult:
        """Evaluate the impact of isolation on units and areas.

        Parameters
        ----------
        applied_graphs:
            Graphs with isolation actions already applied.
        asset_units:
            Mapping from asset node identifier to the name of the unit it
            belongs to.
        unit_data:
            Information about each unit.  Expected keys per unit::

                {
                    'rated': <MW rating>,
                    'scheme': 'SPOF' | 'N+1',
                    'nplus': <total redundant elements (for N+1)>
                }

        unit_areas:
            Mapping from unit name to area name.
        penalties:
            Optional mapping of asset identifier to additional MW derates
            that apply when the asset is unavailable.
        asset_areas:
            Mapping from asset identifier to area for assets that do not
            belong to a unit.  This is typically used for local penalty
            assets.

        Returns
        -------
        ImpactResult
            Structured result containing unavailable assets and MW
            deltas for units and areas.
        """

        penalties = penalties or {}
        asset_areas = asset_areas or {}

        # ------------------------------------------------------------------
        # Determine which asset nodes are no longer reachable from any
        # source node.  Unreachable assets are considered unavailable.
        # ------------------------------------------------------------------
        unavailable: Set[str] = set()
        for g in applied_graphs.values():
            # Gather reachable nodes by traversing edges that are not closed.
            sources = [n for n, d in g.nodes(data=True) if d.get("is_source")]
            open_graph = nx.DiGraph()
            open_graph.add_nodes_from(g.nodes())
            for u, v, data in g.edges(data=True):
                if data.get("state") != "closed":
                    open_graph.add_edge(u, v)

            reachable: Set[str] = set()
            for s in sources:
                for node in nx.descendants(open_graph, s) | {s}:
                    reachable.add(node)

            assets = {n for n, d in g.nodes(data=True) if d.get("tag") == "asset"}
            unavailable.update(assets - reachable)

        # ------------------------------------------------------------------
        # Map unavailable assets to units and compute MW derates.
        # ------------------------------------------------------------------
        unit_unavail: Dict[str, Set[str]] = {}
        for asset in unavailable:
            unit = asset_units.get(asset)
            if unit is not None:
                unit_unavail.setdefault(unit, set()).add(asset)

        unit_delta: Dict[str, float] = {}
        for unit, info in unit_data.items():
            rated = float(info.get("rated", 0.0))
            scheme = str(info.get("scheme", "SPOF")).upper()
            nplus = int(info.get("nplus", 1))
            offline_assets = len(unit_unavail.get(unit, set()))
            delta = 0.0

            if scheme == "SPOF":
                if offline_assets > 0:
                    delta = rated
            elif scheme == "N+1":
                delta = min(rated, offline_assets * rated / max(nplus, 1))

            # Apply asset-specific penalties for this unit
            for asset in unit_unavail.get(unit, set()):
                delta += penalties.get(asset, 0.0)

            if delta > 0:
                unit_delta[unit] = delta

        # ------------------------------------------------------------------
        # Aggregate MW deltas by area.  Unit deltas roll up to their
        # respective areas and standalone penalty assets contribute
        # directly via ``asset_areas``.
        # ------------------------------------------------------------------
        area_delta: Dict[str, float] = {}
        for unit, delta in unit_delta.items():
            area = unit_areas.get(unit)
            if area is not None:
                area_delta[area] = area_delta.get(area, 0.0) + delta

        # Local penalty assets not tied to a unit
        for asset in unavailable:
            if asset not in asset_units:
                area = asset_areas.get(asset)
                if area is not None:
                    area_delta[area] = area_delta.get(area, 0.0) + penalties.get(asset, 0.0)

        return ImpactResult(
            unavailable_assets=unavailable,
            unit_mw_delta=unit_delta,
            area_mw_delta=area_delta,
        )
