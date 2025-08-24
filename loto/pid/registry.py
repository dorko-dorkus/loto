"""Schema for P&ID registry definitions.

This module defines light-weight Pydantic models describing available process
and instrumentation diagrams (P&IDs).  A registry associates a unique
identifier with the SVG document and corresponding tag map used by
:func:`loto.pid.overlay.build_overlay`.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from .validator import validate_svg_map


def _get_mtime(path: Path) -> float:
    try:
        return path.stat().st_mtime
    except FileNotFoundError:
        return -1.0


@lru_cache(maxsize=32)
def _load_registry_cached(path: Path, mtime: float) -> PidRegistry:
    with path.open("r") as fh:
        data = yaml.safe_load(fh) or {}
    registry = PidRegistry(**data)

    base = path.parent
    for pid, entry in registry.pids.items():
        tag_map_path = entry.tag_map
        if not tag_map_path.is_absolute():
            tag_map_path = (base / tag_map_path).resolve()
        svg_path = entry.svg
        if not svg_path.is_absolute():
            svg_path = (base / svg_path).resolve()
        try:
            report = validate_svg_map(svg_path, tag_map_path)
        except ValueError as exc:
            raise ValueError(f"{path}: PID '{pid}': {exc}") from None
        entry.tag_map = tag_map_path
        entry.svg = svg_path
        entry.warnings = report.warnings

    return registry


class PidEntry(BaseModel):
    """Metadata for a single P&ID document."""

    svg: Path = Field(..., description="Path to the SVG document")
    tag_map: Path = Field(..., description="Path to YAML map of tags to CSS selectors")
    description: str | None = Field(
        None, description="Optional human readable description"
    )
    warnings: list[str] = Field(
        default_factory=list, description="Validation warnings for this PID"
    )

    class Config:
        extra = "forbid"


class PidRegistry(BaseModel):
    """Registry of available P&ID documents."""

    pids: dict[str, PidEntry] = Field(
        default_factory=dict,
        description="Mapping of PID identifier to registry entry",
    )

    class Config:
        extra = "forbid"


def load_registry(path: str | Path) -> PidRegistry:
    """Load a :class:`PidRegistry` from a YAML file."""

    path = Path(path)
    registry = _load_registry_cached(path, _get_mtime(path))
    # Return a deep copy so callers can mutate without affecting the cache
    return registry.model_copy(deep=True)
