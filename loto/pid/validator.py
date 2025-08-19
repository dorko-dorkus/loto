"""Utilities for validating PID tag maps against SVG diagrams."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Set

from .schema import load_tag_map


@dataclass
class ValidationReport:
    """Result of validating a PID map against an SVG."""

    warnings: List[str]


def _flatten_selectors(mapping: Mapping[str, Iterable[str]]) -> Dict[str, List[str]]:
    """Return mapping of selector to tags using it."""

    selector_map: Dict[str, List[str]] = {}
    for tag, values in mapping.items():
        for sel in values:
            selector_map.setdefault(sel, []).append(tag)
    return selector_map


def _svg_selectors(root: ET.Element) -> Set[str]:
    selectors: Set[str] = set()
    for elem in root.iter():
        elem_id = elem.get("id")
        if elem_id:
            selectors.add(f"#{elem_id}")
        class_attr = elem.get("class")
        if class_attr:
            selectors.update(f".{c}" for c in class_attr.split())
    return selectors


def validate_svg_map(svg_path: str | Path, map_path: str | Path) -> ValidationReport:
    """Validate selectors in ``map_path`` against the SVG at ``svg_path``."""

    svg_path = Path(svg_path)
    map_path = Path(map_path)

    raw_map = load_tag_map(map_path).root
    tag_map: dict[str, List[str]] = {k: list(v.root) for k, v in raw_map.items()}
    selector_map = _flatten_selectors(tag_map)

    warnings: List[str] = []

    # Warn on selectors mapped to multiple tags
    for sel, tags in selector_map.items():
        if len(tags) > 1:
            joined = ", ".join(sorted(tags))
            warnings.append(f"duplicate tag '{sel}' mapped from: {joined}")

    try:
        root = ET.parse(svg_path).getroot()
    except FileNotFoundError:
        # If SVG missing, report the asset and mark all selectors missing
        warnings.append(f"missing svg '{svg_path}'")
        for sel in selector_map:
            warnings.append(f"missing selector '{sel}'")
        return ValidationReport(sorted(warnings))

    svg_selectors = _svg_selectors(root)
    map_selectors = set(selector_map)

    missing = sorted(map_selectors - svg_selectors)
    for sel in missing:
        warnings.append(f"missing selector '{sel}'")

    unmapped = sorted(svg_selectors - map_selectors)
    for sel in unmapped:
        warnings.append(f"unmapped tag '{sel}'")

    return ValidationReport(sorted(warnings))
