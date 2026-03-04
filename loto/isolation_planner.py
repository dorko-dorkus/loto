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

import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Mapping, Sequence, Set, Tuple

import networkx as nx

from loto.integrations import get_hats_adapter

from .errors import AssetTagNotFoundError, UnisolatablePathError
from .models import (
    ExposureMode,
    IsolationAction,
    IsolationPlan,
    RequiredActions,
    RulePack,
    WorkType,
)


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


ALPHA = _env_float("W_ALPHA", 1.0)
BETA = _env_float("W_BETA", 5.0)
GAMMA = _env_float("W_GAMMA", 0.5)
DELTA = _env_float("W_DELTA", 1.0)
EPSILON = _env_float("W_EPSILON", 2.0)
ZETA = _env_float("W_ZETA", 0.5)
CB_SCALE = _env_float("CB_SCALE", 30.0)
CB_MAX = _env_float("CB_MAX", 120.0)
RST_SCALE = _env_float("RST_SCALE", 30.0)


def _split_nodes(graph: nx.MultiDiGraph) -> nx.MultiDiGraph:
    """Split isolatable nodes into ``node_in``/``node_out`` pairs.

    Edges incident to device nodes are rerouted through the new pair with a
    single capacity edge between them representing the device.
    """

    split = nx.MultiDiGraph()

    for node, attrs in graph.nodes(data=True):
        if attrs.get("is_isolation_point"):
            attrs_copy = dict(attrs)
            split.add_node(f"{node}_in", **attrs_copy)
            split.add_node(f"{node}_out", **attrs_copy)
            cap_attrs: Dict[str, Any] = {}
            for _, _, data in graph.in_edges(node, data=True):
                if data.get("is_isolation_point"):
                    cap_attrs = dict(data)
                    break
            if not cap_attrs:
                for _, _, data in graph.out_edges(node, data=True):
                    if data.get("is_isolation_point"):
                        cap_attrs = dict(data)
                        break
            cap_attrs["is_isolation_point"] = True
            split.add_edge(f"{node}_in", f"{node}_out", **cap_attrs)
        else:
            split.add_node(node, **attrs)

    for u, v, data in graph.edges(data=True):
        new_u = f"{u}_out" if graph.nodes[u].get("is_isolation_point") else u
        new_v = f"{v}_in" if graph.nodes[v].get("is_isolation_point") else v
        data_copy = dict(data)
        data_copy["is_isolation_point"] = False
        split.add_edge(new_u, new_v, **data_copy)

    return split


@dataclass
class VerificationGate:
    """Require approvals from two distinct users before energization."""

    approved_by: Set[str] = field(default_factory=set)

    def approve(self, user: str) -> bool:
        """Record approval by ``user`` and return readiness state."""

        self.approved_by.add(user)
        return self.is_ready

    @property
    def is_ready(self) -> bool:
        """Whether energization can proceed."""

        return len(self.approved_by) >= 2


class IsolationPlanner:
    """Compute isolation plans from domain graphs and rule packs."""

    @staticmethod
    def _resolve_required_actions(
        *,
        rule_pack: RulePack,
        work_type: str | None,
        hazard_classes: Sequence[str],
        exposure_mode: str | None,
    ) -> RequiredActions:
        """Resolve policy requirements for the planning request context."""

        if not work_type and not hazard_classes and not exposure_mode:
            return RequiredActions(block_sources=True, prove_zero=True)

        matrix = rule_pack.effective_isolation_policy_matrix()
        resolved_work_type = (
            WorkType(work_type) if work_type else WorkType.INTRUSIVE_MECH
        )

        hazard_list = [h for h in hazard_classes if h]
        if not hazard_list:
            hazard_list = ["pressure"]

        resolved_exposure = ExposureMode(exposure_mode) if exposure_mode else None

        aggregated = RequiredActions(
            block_sources=False,
            depressurize_to_sink=False,
            drain_to_sink=False,
            prove_zero=False,
            add_barriers=False,
            require_ddbb=False,
        )
        for hazard in hazard_list:
            entry = getattr(matrix[resolved_work_type], hazard)
            row = entry.default
            if (
                resolved_exposure is not None
                and resolved_exposure in entry.exposure_overrides
            ):
                row = entry.exposure_overrides[resolved_exposure]
            aggregated.block_sources = aggregated.block_sources or row.block_sources
            aggregated.depressurize_to_sink = (
                aggregated.depressurize_to_sink or row.depressurize_to_sink
            )
            aggregated.drain_to_sink = aggregated.drain_to_sink or row.drain_to_sink
            aggregated.prove_zero = aggregated.prove_zero or row.prove_zero
            aggregated.add_barriers = aggregated.add_barriers or row.add_barriers
            aggregated.require_ddbb = aggregated.require_ddbb or row.require_ddbb
        return aggregated

    @staticmethod
    def _edge_distance_to_targets(
        graph: nx.MultiDiGraph,
        targets: Sequence[str],
        edge: Tuple[str, str],
    ) -> float:
        """Return shortest distance from edge downstream node to any target."""

        _, downstream = edge
        best = float("inf")
        for target in targets:
            try:
                distance = nx.shortest_path_length(graph, downstream, target)
            except nx.NetworkXNoPath:
                continue
            if distance < best:
                best = float(distance)
        return best

    def compute(
        self,
        graphs: Dict[str, nx.MultiDiGraph],
        asset_tag: str,
        rule_pack: RulePack,
        *,
        config: Mapping[str, Any] | None = None,
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

        normalized_tag = str(asset_tag).strip().upper()
        if not normalized_tag:
            normalized_tag = str(asset_tag).upper()

        candidate_tags = sorted(
            {
                str(data.get("tag")).strip().upper()
                for graph in graphs.values()
                for _, data in graph.nodes(data=True)
                if data.get("tag") is not None and str(data.get("tag")).strip()
            }
        )
        has_legacy_u_alias = (
            normalized_tag.startswith("U")
            and len(normalized_tag) > 1
            and normalized_tag[1:] in candidate_tags
        )
        if normalized_tag not in candidate_tags and not has_legacy_u_alias:
            total_nodes = sum(graph.number_of_nodes() for graph in graphs.values())
            raise AssetTagNotFoundError(
                normalized_tag, hint=f"graph contains {total_nodes} nodes"
            )

        plan: Dict[str, List[Tuple[str, str]]] = {}

        cfg = dict(config or {})
        work_type = str(cfg.get("work_type") or "").strip().lower() or None
        raw_hazard = cfg.get("hazard_class")
        if isinstance(raw_hazard, str):
            hazard_classes = [raw_hazard.strip().lower()] if raw_hazard.strip() else []
        elif isinstance(raw_hazard, Sequence):
            hazard_classes = [
                str(item).strip().lower() for item in raw_hazard if str(item).strip()
            ]
        else:
            hazard_classes = []
        exposure_mode = str(cfg.get("exposure_mode") or "").strip().lower() or None

        required_actions = self._resolve_required_actions(
            rule_pack=rule_pack,
            work_type=work_type,
            hazard_classes=hazard_classes,
            exposure_mode=exposure_mode,
        )

        primary_craft = cfg.get("primary_craft") or ""
        site = cfg.get("site") or ""
        window_start = cfg.get("window_start") or datetime.utcnow()
        cbt = (
            get_hats_adapter().cbt_minutes(primary_craft, site, window_start)
            or cfg.get("callback_time_min")
            or 0
        )
        cbt = float(cbt)

        node_split = os.getenv("PLANNER_NODE_SPLIT", "1") not in ("0", "")
        work_graphs: Dict[str, nx.MultiDiGraph] = {}

        for domain, base_graph in graphs.items():
            graph = _split_nodes(base_graph) if node_split else base_graph
            work_graphs[domain] = graph
            sources = [n for n, data in graph.nodes(data=True) if data.get("is_source")]
            targets = [
                n
                for n, data in graph.nodes(data=True)
                if str(data.get("tag", "")).strip().upper() == normalized_tag
            ]

            if not sources or not targets:
                plan[domain] = []
                continue

            # Build weighted graph for min-cut computations
            weighted = nx.DiGraph()
            targets_set = set(targets)
            for u, v, data in graph.edges(data=True):
                if data.get("is_isolation_point"):
                    op_cost = (
                        data.get("op_cost_min")
                        or graph.nodes[u].get("op_cost_min")
                        or graph.nodes[v].get("op_cost_min")
                        or 0.0
                    )
                    reset_time = (
                        data.get("reset_time_min")
                        or graph.nodes[u].get("reset_time_min")
                        or graph.nodes[v].get("reset_time_min")
                        or 0.0
                    )
                    risk_weight = data.get("risk_weight", 0.0)
                    travel_time = data.get("travel_time_min", 0.0)
                    elevation_penalty = data.get("elevation_penalty", 0.0)
                    outage_penalty = data.get("outage_penalty", 0.0)
                    base = (
                        ALPHA * op_cost
                        + BETA * risk_weight
                        + GAMMA * travel_time
                        + DELTA * elevation_penalty
                        + EPSILON * outage_penalty
                    )
                    if base == 0:
                        base = 1.0
                    mult = 1 + min(cbt, CB_MAX) / CB_SCALE
                    cap = base * mult + ZETA * reset_time * (1 + cbt / RST_SCALE)
                    if (
                        work_type == WorkType.EXTERNAL_MAINTENANCE.value
                        and not required_actions.require_ddbb
                    ):
                        edge_dist = self._edge_distance_to_targets(
                            graph, list(targets_set), (u, v)
                        )
                        if edge_dist != float("inf"):
                            cap *= 1 + (0.2 * edge_dist)
                else:
                    cap = float("inf")
                if weighted.has_edge(u, v):
                    weighted[u][v]["capacity"] = min(weighted[u][v]["capacity"], cap)
                else:
                    weighted.add_edge(u, v, capacity=cap)

            super_source = "__super_source__"
            super_sink = "__super_sink__"
            weighted.add_node(super_source)
            weighted.add_node(super_sink)
            for s in sources:
                weighted.add_edge(super_source, s, capacity=float("inf"))
            for t in targets:
                weighted.add_edge(t, super_sink, capacity=float("inf"))

            try:
                _, (reachable, non_reachable) = nx.minimum_cut(
                    weighted, super_source, super_sink, capacity="capacity"
                )
            except nx.NetworkXUnbounded as exc:
                raise UnisolatablePathError(
                    target_identifier=normalized_tag,
                    reason="no isolation points on any source→target path",
                    hint=(
                        "add at least one inline isolation point (for example, "
                        "a valve) on each source-to-target path"
                    ),
                ) from exc

            cut_edges: Set[Tuple[str, str]] = set()
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

        verifications: List[str] = []
        hazards = [f"hazard_class:{hazard}" for hazard in hazard_classes]
        controls: List[str] = []
        actions: List[IsolationAction] = []

        def shortest_open_path(g: nx.MultiDiGraph) -> List[str] | None:
            """Return shortest path from any source to the target using open edges."""

            open_graph = nx.DiGraph()
            open_graph.add_nodes_from(g.nodes())
            for u, v, data in g.edges(data=True):
                if data.get("state") != "closed":
                    open_graph.add_edge(u, v)

            sources = [n for n, d in g.nodes(data=True) if d.get("is_source")]
            targets = [
                n
                for n, d in g.nodes(data=True)
                if str(d.get("tag", "")).strip().upper() == normalized_tag
            ]

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

        for domain, edges in plan.items():
            if required_actions.block_sources:
                for u, v in edges:
                    actions.append(
                        IsolationAction(
                            component_id=f"{domain}:{u}->{v}",
                            method="lock",
                            duration_s=0.0,
                        )
                    )

            if not edges:
                continue
            branch_graph = nx.Graph()
            branch_graph.add_edges_from(edges)
            sources = [
                n for n, d in work_graphs[domain].nodes(data=True) if d.get("is_source")
            ]
            targets = [
                n
                for n, d in work_graphs[domain].nodes(data=True)
                if str(d.get("tag", "")).strip().upper() == normalized_tag
            ]
            domain_ddbb_found = False
            for component in nx.connected_components(branch_graph):
                branch_label = f"{domain}:{'-'.join(sorted(component))}"
                if required_actions.prove_zero:
                    verifications.append(f"{branch_label} PT=0")
                    verifications.append(f"{branch_label} no-movement")

                if required_actions.depressurize_to_sink:
                    verifications.append(
                        f"{branch_label} depressurize_to_sink verified"
                    )
                    controls.append(
                        f"{branch_label} pressure relief routed to safe sink"
                    )
                if required_actions.drain_to_sink:
                    verifications.append(f"{branch_label} drain_to_sink verified")
                    controls.append(f"{branch_label} fluids drained to designated sink")
                if required_actions.add_barriers:
                    controls.append(f"{branch_label} temporary barriers installed")

                ddbb_found = False
                for node in component:
                    bleed_edges = [
                        (node, succ)
                        for succ in work_graphs[domain].successors(node)
                        if any(
                            data.get("is_bleed")
                            for data in work_graphs[domain]
                            .get_edge_data(node, succ)
                            .values()
                        )
                    ]
                    if not bleed_edges:
                        continue

                    if not any(
                        nx.has_path(work_graphs[domain], s, node) for s in sources
                    ):
                        continue
                    if not any(
                        nx.has_path(work_graphs[domain], node, t) for t in targets
                    ):
                        continue

                    upstream_iso = [
                        (pred, node)
                        for pred in work_graphs[domain].predecessors(node)
                        if any(
                            data.get("is_isolation_point")
                            for data in work_graphs[domain]
                            .get_edge_data(pred, node)
                            .values()
                        )
                    ]
                    downstream_iso = [
                        (node, succ)
                        for succ in work_graphs[domain].successors(node)
                        if any(
                            data.get("is_isolation_point")
                            for data in work_graphs[domain]
                            .get_edge_data(node, succ)
                            .values()
                        )
                    ]

                    if not upstream_iso or not downstream_iso:
                        continue

                    def set_state(
                        g: nx.MultiDiGraph,
                        edge: Tuple[str, str],
                        state: str,
                        *,
                        bleed_only: bool = False,
                    ) -> None:
                        u, v = edge
                        if not g.has_edge(u, v):
                            return
                        for k, data in g[u][v].items():
                            if bleed_only and not data.get("is_bleed"):
                                continue
                            data["state"] = state

                    def can_reach_safe_sink(g: nx.MultiDiGraph, start: str) -> bool:
                        open_graph = nx.DiGraph()
                        open_graph.add_nodes_from(g.nodes(data=True))
                        for u, v, d in g.edges(data=True):
                            if d.get("state") != "closed":
                                open_graph.add_edge(u, v)
                        sinks = [n for n, d in g.nodes(data=True) if d.get("safe_sink")]
                        return any(nx.has_path(open_graph, start, s) for s in sinks)

                    for ui in upstream_iso:
                        for di in downstream_iso:
                            for bleed in bleed_edges:
                                g = work_graphs[domain].copy()
                                set_state(g, ui, "closed")
                                set_state(g, di, "closed")
                                set_state(g, bleed, "open", bleed_only=True)
                                if (
                                    required_actions.block_sources
                                    and shortest_open_path(g) is not None
                                ):
                                    continue
                                sink_ok = can_reach_safe_sink(g, bleed[0])
                                if (
                                    required_actions.depressurize_to_sink
                                    or required_actions.drain_to_sink
                                ) and not sink_ok:
                                    continue
                                redundant = False
                                g_up = g.copy()
                                set_state(g_up, ui, "open")
                                if shortest_open_path(g_up) is None:
                                    redundant = True
                                g_dn = g.copy()
                                set_state(g_dn, di, "open")
                                if shortest_open_path(g_dn) is None:
                                    redundant = True
                                cert = f"{ui[0]}->{ui[1]},{bleed[0]}->{bleed[1]},{di[0]}->{di[1]}"
                                verifications.append(f"{branch_label} DDBB {cert}")
                                if redundant:
                                    verifications.append(
                                        f"{branch_label} redundant DDBB path"
                                    )
                                ddbb_found = True
                                domain_ddbb_found = True
                                break
                            if ddbb_found:
                                break
                        if ddbb_found:
                            break
                    if ddbb_found:
                        break
            if required_actions.require_ddbb and not domain_ddbb_found:
                raise UnisolatablePathError(
                    target_identifier=normalized_tag,
                    reason="mandatory DDBB branch unavailable",
                    hint=(
                        "policy requires a double-block-and-bleed branch with a "
                        "reachable safe sink"
                    ),
                )

        if required_actions.depressurize_to_sink:
            verifications.append("path-check: depressurization path to safe sink")
        if required_actions.drain_to_sink:
            verifications.append("path-check: drain path to safe sink")

        return IsolationPlan(
            plan_id=asset_tag,
            actions=actions,
            verifications=verifications,
            hazards=hazards,
            controls=controls,
        )
