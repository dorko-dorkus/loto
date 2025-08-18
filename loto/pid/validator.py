from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Mapping, Set

from .schema import load_tag_map


@dataclass
class ValidationReport:
    """Report from validating selectors against an SVG document."""

    missing_selectors: List[str]


def _flatten_selectors(mapping: Mapping[str, Iterable[str]]) -> Set[str]:
    selectors: Set[str] = set()
    for values in mapping.values():
        selectors.update(values)
    return selectors


def validate_svg_map(svg_path: str | Path, map_path: str | Path) -> ValidationReport:
    """Validate selectors in ``map_path`` exist in the SVG at ``svg_path``."""

    svg_path = Path(svg_path)
    map_path = Path(map_path)

    raw_map = load_tag_map(map_path).root
    tag_map: dict[str, List[str]] = {k: list(v.root) for k, v in raw_map.items()}
    selectors = _flatten_selectors(tag_map)

    try:
        root = ET.parse(svg_path).getroot()
    except FileNotFoundError:
        return ValidationReport(sorted(selectors))

    missing: List[str] = []
    for sel in selectors:
        if sel.startswith("#"):
            if root.find(f".//*[@id='{sel[1:]}']") is None:
                missing.append(sel)
        elif sel.startswith("."):
            class_name = sel[1:]
            found = False
            for elem in root.findall(".//*[@class]"):
                classes = elem.get("class", "").split()
                if class_name in classes:
                    found = True
                    break
            if not found:
                missing.append(sel)
        else:
            if not root.findall(f".//{sel}"):
                missing.append(sel)

    return ValidationReport(sorted(missing))
