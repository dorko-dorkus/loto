from __future__ import annotations

import math
from typing import Any


def canonicalize_graph_tag(value: Any) -> Any:
    """Apply canonical graph tag normalisation semantics.

    Mirrors existing graph ingestion behaviour by trimming whitespace,
    converting hyphens to underscores, and upper-casing values.
    """

    if value is None:
        return value
    if isinstance(value, float) and math.isnan(value):
        return None
    if isinstance(value, str):
        return value.strip().replace("-", "_").upper()
    return value


def canonicalize_graph_domain(value: Any) -> Any:
    """Canonicalize graph domains with the same ingestion semantics."""

    if isinstance(value, str):
        return value.strip().replace("-", "_").lower()
    return value


def canonicalize_work_type(value: Any) -> Any:
    """Canonicalize work-type values for policy/config lookups."""

    if isinstance(value, str):
        return value.strip().replace("-", "_").lower()
    return value


def canonicalize_hazard_class(value: Any) -> Any:
    """Canonicalize hazard class values for stable downstream matching."""

    if isinstance(value, str):
        return value.strip().replace("-", "_").lower()
    return value


def canonicalize_exposure_mode(value: Any) -> Any:
    """Canonicalize exposure mode values for stable policy overrides."""

    if isinstance(value, str):
        return value.strip().replace("-", "_").lower()
    return value
