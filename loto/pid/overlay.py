"""Generate overlay payloads for process diagrams.

This module translates isolation planner and simulation outputs into a
structure understood by the front-end overlay system.  It maps graph node
identifiers to CSS selectors using a ``pid_map.yaml`` file.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Dict, Iterable, List, Set

from ..models import IsolationPlan
from .schema import load_tag_map


def _get_mtime(path: Path) -> float:
    try:
        return path.stat().st_mtime
    except FileNotFoundError:
        return -1.0


@lru_cache(maxsize=32)
def _load_map_cached(path: Path, mtime: float) -> Dict[str, List[str]]:
    tag_map = load_tag_map(path).root
    mapping: Dict[str, List[str]] = {}
    for tag, selectors in tag_map.items():
        mapping[tag] = list(dict.fromkeys(selectors.root))
    return mapping


def _load_map(map_path: Path) -> Dict[str, List[str]]:
    """Return mapping from component tags to CSS selectors."""

    return _load_map_cached(map_path, _get_mtime(map_path))


def _selectors(tag: str, mapping: Dict[str, List[str]]) -> List[str]:
    """Return unique selectors for ``tag`` from ``mapping``."""

    selectors = mapping.get(tag, [])
    # Return a copy to avoid mutating the underlying mapping
    return list(dict.fromkeys(selectors))


def _selectors_from_path(
    path: Iterable[str], mapping: Dict[str, List[str]]
) -> List[str]:
    """Return unique selectors for all nodes in ``path``."""

    selectors: List[str] = []
    seen: Set[str] = set()
    for node in path:
        for sel in _selectors(node, mapping):
            if sel not in seen:
                seen.add(sel)
                selectors.append(sel)
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
    missing: Set[str] = set()
    warnings: List[str] = []

    asset_selectors = _selectors(asset, mapping)
    if asset_selectors:
        for sel in asset_selectors:
            highlight.add(sel)
            badges.append({"selector": sel, "type": "asset"})
    else:
        missing.add(asset)

    for src in sources:
        src_selectors = _selectors(src, mapping)
        if src_selectors:
            for sel in src_selectors:
                highlight.add(sel)
                badges.append({"selector": sel, "type": "source"})
        else:
            missing.add(src)

    for action in plan.actions:
        try:
            edge = action.component_id.split(":", 1)[1]
            u, v = edge.split("->")
        except ValueError:
            continue
        for tag in (u, v):
            sels = _selectors(tag, mapping)
            if sels:
                highlight.update(sels)
            else:
                missing.add(tag)

    for idx, path_nodes in enumerate(sim_fail_paths):
        selectors = _selectors_from_path(path_nodes, mapping)
        if selectors:
            paths.append({"id": f"path{idx}", "selectors": selectors})
            highlight.update(selectors)
        else:
            for node in path_nodes:
                if not _selectors(node, mapping):
                    missing.add(node)

    if missing:
        # If any tag is missing a selector, attach a warning badge to the
        # asset (if available) and surface the missing tags in the warnings
        # list.  This allows the front-end to draw attention to the asset and
        # display an explanatory message to the user.
        if asset_selectors:
            for sel in asset_selectors:
                badges.append({"selector": sel, "type": "warning"})
        for tag in sorted(missing):
            warnings.append(f"missing selector for tag '{tag}'")

    return {
        "highlight": sorted(highlight),
        "badges": badges,
        "paths": paths,
        "warnings": warnings,
    }
