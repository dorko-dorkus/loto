"""PID registry data structures and helpers.

This module defines a small schema for describing P&ID (piping and
instrumentation diagram) files and the tags they contain.  The
schema mirrors the structure of ``demo/pids/pid_map.yaml`` which maps
P&ID identifiers to the SVG file containing the diagram and a list of
tags present on that diagram.

The YAML structure is expected to look like::

    PID-001:
      file: pid-001.svg
      tags:
        - tag: P-101
          description: Main cooling pump
        - tag: V-201
          description: Isolation valve

The :func:`load_registry` function reads such a file and returns a
mapping of P&ID identifiers to :class:`RegistryEntry` instances.  A
convenience :func:`build_tag_map` helper inverts this mapping to allow
looking up which diagram a particular tag appears on.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Mapping, MutableMapping

import yaml


@dataclass
class Tag:
    """Representation of a single tag located on a P&ID diagram."""

    tag: str
    description: str | None = None


@dataclass
class RegistryEntry:
    """Entry describing a single P&ID and its tag collection."""

    pid: str
    file: str | None = None
    tags: List[Tag] = field(default_factory=list)


Registry = Dict[str, RegistryEntry]


def load_registry(path: Path | str) -> Registry:
    """Load a P&ID registry from a YAML file.

    Parameters
    ----------
    path:
        Location of the YAML registry file.

    Returns
    -------
    Registry
        Mapping of P&ID identifiers to registry entries.
    """

    with open(path, "r", encoding="utf8") as fh:
        data: Mapping[str, MutableMapping[str, object]] = yaml.safe_load(fh) or {}

    registry: Registry = {}
    for pid, entry in data.items():
        tags_data = entry.get("tags", []) if isinstance(entry, MutableMapping) else []
        tags: List[Tag] = []
        for t in tags_data:
            if isinstance(t, MutableMapping):
                tags.append(
                    Tag(tag=str(t.get("tag")), description=t.get("description"))
                )
            else:
                tags.append(Tag(tag=str(t)))
        registry[pid] = RegistryEntry(
            pid=pid,
            file=entry.get("file") if isinstance(entry, MutableMapping) else None,
            tags=tags,
        )
    return registry


def build_tag_map(registry: Registry) -> Dict[str, RegistryEntry]:
    """Return a mapping of tag name to the registry entry containing it."""

    tag_map: Dict[str, RegistryEntry] = {}
    for entry in registry.values():
        for tag in entry.tags:
            tag_map[tag.tag] = entry
    return tag_map


__all__ = [
    "Tag",
    "RegistryEntry",
    "Registry",
    "load_registry",
    "build_tag_map",
]
