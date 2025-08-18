"""Graph builder for the LOTO planner.

This module defines the :class:`GraphBuilder` class which is responsible
for constructing domain-specific connectivity graphs from raw input
files (e.g., CSV exports of line lists, valve registers, and drains).
Graphs are used by the isolation planner to compute minimal cut sets and
simulate isolation states.

Each graph is a directed multigraph where nodes represent equipment
tags, ports, actuators, and other components, and edges represent
connections (pipes, tubes, lines). Graph validation logic ensures
consistency of the input data (e.g., no dangling references or
impossible mediums). Only method signatures are provided.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import networkx as nx  # type: ignore
import pandas as pd


@dataclass
class Issue:
    """Represents a problem detected during graph construction or validation."""

    message: str
    severity: str = "error"  # could also be "warning" or "info"


class GraphBuilder:
    """Build connectivity graphs for each energy domain.

    The resulting graphs are used by the isolation planner to compute
    minimal cut sets. A single GraphBuilder instance can construct
    multiple domain graphs from a set of CSV inputs.
    """

    def from_csvs(
        self,
        line_list_path: str | Path,
        valves_path: str | Path,
        drains_path: str | Path,
        sources_path: Optional[str | Path] = None,
        air_map_path: Optional[str | Path] = None,
    ) -> Dict[str, nx.MultiDiGraph]:
        """Load CSV data and return graphs keyed by domain.

        Parameters
        ----------
        line_list_path: str | Path
            Path to the line list CSV file.
        valves_path: str | Path
            Path to the valve register CSV file.
        drains_path: str | Path
            Path to the drains/vents CSV file.
        sources_path: Optional[str | Path]
            Path to the energy sources CSV file; optional.
        air_map_path: Optional[str | Path]
            Path to the instrument air map CSV file; optional.

        Returns
        -------
        Dict[str, nx.MultiDiGraph]
            A mapping from energy domain names to their corresponding
            directed multigraphs.

        Notes
        -----
        The demo implementation expects very small CSV schemas used in
        the unit tests.  Each CSV must contain a ``domain`` column to
        group records.  The relevant columns are:

        ``line_list``
            ``from_tag`` and ``to_tag`` describing connections.
        ``valves``
            ``tag``, ``fail_state`` and ``kind`` for isolation points.
        ``drains``
            ``tag`` describing drain/vent nodes.
        ``sources`` (optional)
            ``tag`` and ``kind`` marking energy sources.

        Every node in the resulting graphs exposes the following
        attributes with sensible defaults: ``tag``, ``is_source``,
        ``is_isolation_point``, ``fail_state`` and ``kind``.
        """

        def _ensure_node(graph: nx.MultiDiGraph, tag: str) -> None:
            if tag not in graph:
                graph.add_node(
                    tag,
                    tag=tag,
                    is_source=False,
                    is_isolation_point=False,
                    fail_state=None,
                    kind=None,
                )

        graphs: Dict[str, nx.MultiDiGraph] = {}

        line_df = pd.read_csv(line_list_path)
        valve_df = pd.read_csv(valves_path)
        drain_df = pd.read_csv(drains_path)
        source_df = (
            pd.read_csv(sources_path) if sources_path is not None else pd.DataFrame()
        )

        for _, row in line_df.iterrows():
            domain = row["domain"]
            g = graphs.setdefault(domain, nx.MultiDiGraph())
            _ensure_node(g, row["from_tag"])
            _ensure_node(g, row["to_tag"])
            g.add_edge(row["from_tag"], row["to_tag"], line_tag=row.get("line_tag"))

        for _, row in valve_df.iterrows():
            domain = row["domain"]
            g = graphs.setdefault(domain, nx.MultiDiGraph())
            tag = row["tag"]
            _ensure_node(g, tag)
            g.nodes[tag].update(
                {
                    "is_isolation_point": True,
                    "fail_state": row.get("fail_state"),
                    "kind": row.get("kind"),
                }
            )

        for _, row in drain_df.iterrows():
            domain = row["domain"]
            g = graphs.setdefault(domain, nx.MultiDiGraph())
            tag = row["tag"]
            _ensure_node(g, tag)
            if "kind" in row:
                g.nodes[tag]["kind"] = row["kind"]

        if not source_df.empty:
            for _, row in source_df.iterrows():
                domain = row["domain"]
                g = graphs.setdefault(domain, nx.MultiDiGraph())
                tag = row["tag"]
                _ensure_node(g, tag)
                g.nodes[tag].update({"is_source": True, "kind": row.get("kind")})

        return graphs

    def validate(self, graphs: Dict[str, nx.MultiDiGraph]) -> List[Issue]:
        """Validate the constructed graphs.

        Checks include:

        * dangling nodes (no incident edges)
        * graphs with missing domain names
        * edges missing a ``line_tag`` attribute
        * optional cycle detection

        Parameters
        ----------
        graphs: Dict[str, nx.MultiDiGraph]
            The mapping of domain names to graphs to validate.

        Returns
        -------
        List[Issue]
            A list of issues detected during validation. If the list is
            empty, the graphs are considered valid.
        """
        issues: List[Issue] = []

        def _is_missing(value: object) -> bool:
            if value is None:
                return True
            if isinstance(value, float) and pd.isna(value):
                return True
            if isinstance(value, str) and value.strip() == "":
                return True
            return False

        for domain, graph in graphs.items():
            if _is_missing(domain):
                issues.append(Issue("Graph with missing domain"))
            for u, v, data in graph.edges(data=True):
                if _is_missing(data.get("line_tag")):
                    issues.append(
                        Issue(f"Edge {u}->{v} in domain {domain} missing line tag")
                    )
                if _is_missing(u) or _is_missing(v):
                    issues.append(
                        Issue(f"Edge with unknown node in domain {domain}: {u}->{v}")
                    )
            for node in graph.nodes():
                if graph.degree(node) == 0:
                    issues.append(Issue(f"Dangling node {node} in domain {domain}"))
            try:
                if not nx.is_directed_acyclic_graph(graph):
                    issues.append(
                        Issue(f"Cycle detected in domain {domain}", severity="warning")
                    )
            except Exception:
                pass

        return issues
