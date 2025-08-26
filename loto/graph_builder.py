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
impossible mediums).

Set the environment variable ``LOTO_STRICT_VALIDATION`` to any truthy
value to enable strict validation. When enabled,
``GraphBuilder.validate`` raises ``ValueError`` for edges referencing
unknown nodes instead of returning an :class:`Issue`.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import IO, Any, Dict, List, Optional, cast

import networkx as nx
import pandas as pd
from pydantic import ValidationError

from .graph_models import DrainRow, LineRow, SourceRow, ValveRow

STRICT_VALIDATION = bool(os.getenv("LOTO_STRICT_VALIDATION"))

NON_RETURN_DEVICE_KINDS: set[str] = {
    "check valve",
    "check-valve",
    "check_valve",
    "nrv",
    "non-return valve",
}


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
        line_list_path: str | Path | IO[str],
        valves_path: str | Path | IO[str],
        drains_path: str | Path | IO[str],
        sources_path: Optional[str | Path | IO[str]] = None,
        air_map_path: Optional[str | Path | IO[str]] = None,
    ) -> Dict[str, nx.MultiDiGraph]:
        """Load CSV data and return graphs keyed by domain.

        Parameters
        ----------
        line_list_path: str | Path | IO[str]
            Path or file-like object for the line list CSV.
        valves_path: str | Path | IO[str]
            Path or file-like object for the valve register CSV.
        drains_path: str | Path | IO[str]
            Path or file-like object for the drains/vents CSV.
        sources_path: Optional[str | Path | IO[str]]
            Path or file-like object for the energy sources CSV; optional.
        air_map_path: Optional[str | Path | IO[str]]
            Path or file-like object for the instrument air map CSV; optional.

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

        errors: List[str] = []

        for idx, row in line_df.iterrows():
            try:
                line_row = LineRow.parse_obj(row.to_dict())
            except ValidationError as e:
                errors.append(f"line_list row {idx}: {e}")
                continue
            domain = line_row.domain.value
            g = graphs.setdefault(domain, nx.MultiDiGraph())
            _ensure_node(g, line_row.from_tag)
            _ensure_node(g, line_row.to_tag)
            cost = (
                line_row.isolation_cost if line_row.isolation_cost is not None else 1.0
            )
            edge_attrs = {
                "line_tag": line_row.line_tag,
                "isolation_cost": float(cost),
            }
            optional_attrs = {
                k: v
                for k, v in {
                    "op_cost_min": line_row.op_cost_min,
                    "reset_time_min": line_row.reset_time_min,
                    "risk_weight": line_row.risk_weight,
                    "travel_time_min": line_row.travel_time_min,
                    "elevation_penalty": line_row.elevation_penalty,
                    "outage_penalty": line_row.outage_penalty,
                }.items()
                if v is not None
            }
            edge_attrs.update(optional_attrs)
            g.add_edge(line_row.from_tag, line_row.to_tag, **edge_attrs)

        for idx, row in valve_df.iterrows():
            try:
                valve_row = ValveRow.parse_obj(row.to_dict())
            except ValidationError as e:
                errors.append(f"valves row {idx}: {e}")
                continue
            domain = valve_row.domain.value
            g = graphs.setdefault(domain, nx.MultiDiGraph())
            tag = valve_row.tag
            _ensure_node(g, tag)
            cost = (
                valve_row.isolation_cost
                if valve_row.isolation_cost is not None
                else 1.0
            )
            node_attrs: Dict[str, Any] = {
                "is_isolation_point": True,
                "fail_state": valve_row.fail_state,
                "kind": valve_row.kind,
            }
            optional_attrs = {
                k: v
                for k, v in {
                    "op_cost_min": valve_row.op_cost_min,
                    "reset_time_min": valve_row.reset_time_min,
                    "risk_weight": valve_row.risk_weight,
                    "travel_time_min": valve_row.travel_time_min,
                    "elevation_penalty": valve_row.elevation_penalty,
                    "outage_penalty": valve_row.outage_penalty,
                }.items()
                if v is not None
            }
            node_attrs.update(optional_attrs)
            node_data = cast(Dict[str, Any], g.nodes[tag])
            node_data.update(node_attrs)
            for u, v, data in list(g.in_edges(tag, data=True)):
                edge_data = cast(Dict[str, Any], data)
                edge_data["is_isolation_point"] = True
                edge_data["isolation_cost"] = float(cost)
                for k, v2 in optional_attrs.items():
                    edge_data[k] = float(v2)
            for u, v, data in list(g.out_edges(tag, data=True)):
                edge_data = cast(Dict[str, Any], data)
                edge_data["is_isolation_point"] = True
                edge_data["isolation_cost"] = float(cost)
                for k, v2 in optional_attrs.items():
                    edge_data[k] = float(v2)

        for idx, row in drain_df.iterrows():
            try:
                drain_row = DrainRow.parse_obj(row.to_dict())
            except ValidationError as e:
                errors.append(f"drains row {idx}: {e}")
                continue
            domain = drain_row.domain.value
            g = graphs.setdefault(domain, nx.MultiDiGraph())
            tag = drain_row.tag
            _ensure_node(g, tag)
            if drain_row.kind is not None:
                g.nodes[tag]["kind"] = drain_row.kind

        if not source_df.empty:
            for idx, row in source_df.iterrows():
                try:
                    source_row = SourceRow.parse_obj(row.to_dict())
                except ValidationError as e:
                    errors.append(f"sources row {idx}: {e}")
                    continue
                domain = source_row.domain.value
                g = graphs.setdefault(domain, nx.MultiDiGraph())
                tag = source_row.tag
                _ensure_node(g, tag)
                g.nodes[tag].update({"is_source": True, "kind": source_row.kind})

        if errors:
            raise ValueError("\n".join(errors))

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
                    msg = f"Edge with unknown node in domain {domain}: {u}->{v}"
                    if STRICT_VALIDATION:
                        raise ValueError(msg)
                    issues.append(Issue(msg))
            for node in graph.nodes():
                if graph.degree(node) == 0:
                    issues.append(Issue(f"Dangling node {node} in domain {domain}"))
            try:
                cycles = list(nx.simple_cycles(graph))
            except Exception:
                cycles = []
            for cycle in cycles:
                edge_pairs = list(zip(cycle, cycle[1:] + [cycle[0]]))
                all_nr_nodes = all(
                    isinstance(graph.nodes[n].get("kind"), str)
                    and graph.nodes[n]["kind"].lower() in NON_RETURN_DEVICE_KINDS
                    for n in cycle
                )
                all_nr_edges = True
                for u, v in edge_pairs:
                    data_dict = graph.get_edge_data(u, v, default={})
                    if not data_dict:
                        all_nr_edges = False
                        break
                    for data in data_dict.values():
                        kind = data.get("kind")
                        if (
                            not isinstance(kind, str)
                            or kind.lower() not in NON_RETURN_DEVICE_KINDS
                        ):
                            all_nr_edges = False
                            break
                    if not all_nr_edges:
                        break
                cycle_str = " -> ".join(map(str, cycle + [cycle[0]]))
                if all_nr_nodes and all_nr_edges:
                    issues.append(
                        Issue(
                            f"Cycle detected in domain {domain}: {cycle_str}",
                            severity="warning",
                        )
                    )
                else:
                    issues.append(
                        Issue(
                            f"Cycle detected in domain {domain}: {cycle_str}",
                            severity="info",
                        )
                    )

        return issues
