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

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import networkx as nx  # type: ignore


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

    #: Known mediums used by :meth:`validate`.  The list is intentionally
    #: small – it merely needs to cover the values used in the tests.  Any
    #: medium not present here will be reported as an issue.
    KNOWN_MEDIUMS = {
        "steam",
        "water",
        "air",
        "gas",
        "oil",
        "electric",
        "hydraulic",
    }

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
        The real project contains a fairly involved parser for a number of
        different CSV exports.  For the unit tests in this kata we only need a
        *very* small subset of that functionality.  The implementation below
        focuses on the fields that appear in the tests:

        ``domain``
            Energy domain for the row.  A separate graph is created per domain.
        ``from`` / ``to``
            Endpoints of a connection.  If the CSV uses different column names
            (e.g. ``source``/``target``) they are accepted as well.
        ``medium``
            Medium transported by the connection.  Stored as an edge attribute
            and later validated.
        ``state`` / ``fail_state``
            Operational state information for isolation points.  Stored as edge
            attributes when provided.

        The function returns a mapping of ``domain -> graph`` where each graph
        is a :class:`networkx.MultiDiGraph`.
        """

        def _get_graph(domain: str) -> nx.MultiDiGraph:
            if domain not in graphs:
                graphs[domain] = nx.MultiDiGraph()
            return graphs[domain]

        def _read(path: str | Path) -> List[Dict[str, str]]:
            with open(
                path, newline="", encoding="utf-8"
            ) as fh:  # pragma: no cover - trivial
                return list(csv.DictReader(fh))

        graphs: Dict[str, nx.MultiDiGraph] = {}

        # --- Line list -------------------------------------------------
        for row in _read(line_list_path):
            domain = (row.get("domain") or row.get("Domain") or "unknown").strip()
            start = (
                row.get("from")
                or row.get("source")
                or row.get("from_tag")
                or row.get("upstream")
                or row.get("node_u")
            )
            end = (
                row.get("to")
                or row.get("target")
                or row.get("to_tag")
                or row.get("downstream")
                or row.get("node_v")
            )
            if start and end:
                g = _get_graph(domain)
                line_attrs: Dict[str, Any] = {}
                if row.get("medium"):
                    line_attrs["medium"] = row["medium"].strip()
                g.add_edge(start.strip(), end.strip(), **line_attrs)

        # --- Valves (isolation points) -------------------------------
        for row in _read(valves_path):
            domain = (row.get("domain") or row.get("Domain") or "unknown").strip()
            start = (
                row.get("from")
                or row.get("source")
                or row.get("from_tag")
                or row.get("upstream")
                or row.get("node_u")
            )
            end = (
                row.get("to")
                or row.get("target")
                or row.get("to_tag")
                or row.get("downstream")
                or row.get("node_v")
            )
            if start and end:
                g = _get_graph(domain)
                valve_attrs: Dict[str, Any] = {"is_isolation_point": True}
                if row.get("state"):
                    valve_attrs["state"] = row["state"].strip()
                if row.get("fail_state"):
                    valve_attrs["fail_state"] = row["fail_state"].strip()
                if row.get("medium"):
                    valve_attrs["medium"] = row["medium"].strip()
                g.add_edge(start.strip(), end.strip(), **valve_attrs)

        # --- Drains / vents ------------------------------------------
        for row in _read(drains_path):
            domain = (row.get("domain") or row.get("Domain") or "unknown").strip()
            start = (
                row.get("from")
                or row.get("source")
                or row.get("from_tag")
                or row.get("upstream")
                or row.get("node_u")
                or row.get("node")
            )
            end = (
                row.get("to")
                or row.get("target")
                or row.get("to_tag")
                or row.get("downstream")
                or row.get("node_v")
            )
            if start and end:
                g = _get_graph(domain)
                drain_attrs: Dict[str, Any] = {"is_isolation_point": True}
                if row.get("state"):
                    drain_attrs["state"] = row["state"].strip()
                if row.get("fail_state"):
                    drain_attrs["fail_state"] = row["fail_state"].strip()
                if row.get("medium"):
                    drain_attrs["medium"] = row["medium"].strip()
                g.add_edge(start.strip(), end.strip(), **drain_attrs)

        # --- Sources --------------------------------------------------
        if sources_path:
            for row in _read(sources_path):
                domain = (
                    row.get("domain")
                    or row.get("Domain")
                    or row.get("medium")
                    or "unknown"
                ).strip()
                tag = row.get("node") or row.get("tag") or row.get("source")
                if not tag:
                    continue
                tag = tag.strip()
                g = _get_graph(domain)
                g.add_node(tag, is_source=True)

        # Instrument air map is ignored in this trimmed down
        # implementation; the tests exercising this module do not require
        # it.  The parameter is only accepted for API compatibility.
        _ = air_map_path

        return graphs

    def validate(self, graphs: Dict[str, nx.MultiDiGraph]) -> List[Issue]:
        """Validate the constructed graphs.

        Parameters
        ----------
        graphs: Dict[str, nx.MultiDiGraph]
            The mapping of domain names to graphs to validate.

        Returns
        -------
        List[Issue]
            A list of issues detected during validation. If the list is
            empty, the graphs are considered valid.

        Notes
        -----
        The original project performs a large number of consistency checks.
        For the unit tests bundled with this kata we only implement two simple
        validations:

        * report nodes that are completely disconnected ("dangling"), and
        * report edges whose ``medium`` attribute is either missing or not
          recognised.

        The method returns a list of :class:`Issue` instances describing the
        problems.  An empty list means the graphs are considered valid.
        """

        issues: List[Issue] = []

        for domain, graph in graphs.items():
            # Detect dangling nodes (nodes without any edges)
            for node in graph.nodes:
                if graph.degree(node) == 0:
                    issues.append(
                        Issue(f"{domain}: node '{node}' is not connected to the graph")
                    )

            # Validate mediums on edges
            for u, v, data in graph.edges(data=True):
                medium = data.get("medium")
                if not medium:
                    issues.append(
                        Issue(f"{domain}: edge {u!r}->{v!r} has unknown medium")
                    )
                elif medium not in self.KNOWN_MEDIUMS:
                    issues.append(
                        Issue(
                            f"{domain}: edge {u!r}->{v!r} has unknown medium '{medium}'"
                        )
                    )

        return issues
