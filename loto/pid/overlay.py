"""Generate overlay payloads for process diagrams.

This module translates isolation planner and simulation outputs into a
structure understood by the front-end overlay system.  It maps graph node
identifiers to CSS selectors using a ``pid_map.yaml`` file.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Dict, Iterable, List, Set

import yaml

from ..models import IsolationPlan

_MAP_PARSES = 0


def _parse_map(path: str) -> Dict[str, List[str]]:
    """Read and normalize the raw YAML map."""

    global _MAP_PARSES
    _MAP_PARSES += 1

    with Path(path).open("r") as fh:
        raw = yaml.safe_load(fh) or {}

    mapping: Dict[str, List[str]] = {}
    for tag, selector in raw.items():
        if isinstance(selector, str):
            mapping[tag] = [selector]
        elif isinstance(selector, Iterable):
            mapping[tag] = [s for s in selector if isinstance(s, str)]
    return mapping


@lru_cache(maxsize=32)
def _load_map_cached(path: str, mtime: float) -> Dict[str, List[str]]:
    """LRU cached loader keyed by path and modification time."""

    return _parse_map(path)


def _load_map(map_path: Path) -> Dict[str, List[str]]:
    """Return mapping from component tags to CSS selectors."""

    abs_path = Path(map_path).resolve()
    mtime = abs_path.stat().st_mtime
    return _load_map_cached(str(abs_path), mtime)


def _selectors(tag: str, mapping: Dict[str, List[str]]) -> List[str]:
    return list(mapping.get(tag, []))


def _selectors_from_path(
    path: Iterable[str], mapping: Dict[str, List[str]]
) -> List[str]:
    selectors: List[str] = []
    for node in path:
        selectors.extend(_selectors(node, mapping))
    return selectors


def build_overlay(
    sources: Iterable[str],
    asset: str,
    plan: IsolationPlan,
    sim_fail_paths: List[Iterable[str]],
    map_path: str | Path = "pid_map.yaml",
) -> Dict[str, object]:
    """Build overlay payload.

    Parameters
    ----------
    sources:
        Iterable of energy source tags.
    asset:
        Tag of the asset under isolation.
    plan:
        Isolation plan produced by the planner.
    sim_fail_paths:
        Paths that still allow energy flow after simulation.
    map_path:
        Location of ``pid_map.yaml`` mapping tags to CSS selectors.
    """

    mapping = _load_map(Path(map_path))

    highlight: Set[str] = set()
    badges: List[Dict[str, str]] = []
    paths: List[Dict[str, object]] = []

    # Asset badge
    for sel in _selectors(asset, mapping):
        highlight.add(sel)
        badges.append({"selector": sel, "type": "asset"})

    # Source badges
    for src in sources:
        for sel in _selectors(src, mapping):
            highlight.add(sel)
            badges.append({"selector": sel, "type": "source"})

    # Isolation actions highlight
    for action in plan.actions:
        try:
            edge = action.component_id.split(":", 1)[1]
            u, v = edge.split("->")
        except ValueError:
            continue
        for tag in (u, v):
            highlight.update(_selectors(tag, mapping))

    # Simulation failing paths
    for idx, path_nodes in enumerate(sim_fail_paths):
        selectors = _selectors_from_path(path_nodes, mapping)
        if selectors:
            paths.append({"id": f"path{idx}", "selectors": selectors})
            highlight.update(selectors)

    return {
        "highlight": sorted(highlight),
        "badges": badges,
        "paths": paths,
    }
