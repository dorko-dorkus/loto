"""Schema for P&ID registry definitions.

This module defines light-weight Pydantic models describing available process
and instrumentation diagrams (P&IDs).  A registry associates a unique
identifier with the SVG document and corresponding tag map used by
:func:`loto.pid.overlay.build_overlay`.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Dict

import yaml
from pydantic import BaseModel, Field

from .schema import load_tag_map


class PidEntry(BaseModel):
    """Metadata for a single P&ID document."""

    svg: Path = Field(..., description="Path to the SVG document")
    tag_map: Path = Field(..., description="Path to YAML map of tags to CSS selectors")
    description: str | None = Field(
        None, description="Optional human readable description"
    )

    class Config:
        extra = "forbid"


class PidRegistry(BaseModel):
    """Registry of available P&ID documents."""

    pids: Dict[str, PidEntry] = Field(
        default_factory=dict,
        description="Mapping of PID identifier to registry entry",
    )

    class Config:
        extra = "forbid"


@lru_cache(maxsize=32)
def _load_registry_cached(path: str, mtime: float) -> PidRegistry:
    """Internal helper that parses a registry file.

    Parameters
    ----------
    path:
        Absolute path to the registry file.
    mtime:
        Modification time used solely for cache invalidation.
    """

    with Path(path).open("r") as fh:
        data = yaml.safe_load(fh) or {}
    registry = PidRegistry(**data)

    base = Path(path).parent
    for entry in registry.pids.values():
        tag_map_path = entry.tag_map
        if not tag_map_path.is_absolute():
            tag_map_path = (base / tag_map_path).resolve()
        load_tag_map(tag_map_path)
        entry.tag_map = tag_map_path

    return registry


def load_registry(path: str | Path) -> PidRegistry:
    """Load a :class:`PidRegistry` from a YAML file.

    The function validates each referenced tag map against
    :func:`loto.pid.schema.load_tag_map`.
    """

    abs_path = Path(path).resolve()
    mtime = abs_path.stat().st_mtime
    # Return a copy so callers cannot mutate the cached instance
    return _load_registry_cached(str(abs_path), mtime).model_copy()
