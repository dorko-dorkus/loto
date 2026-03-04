"""Work-scope inference helpers used by planning entrypoints."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class ExposureInference:
    """Inference output for exposure mode and related escalation hints."""

    exposure_mode: str | None
    escalate_to_intrusive_mech: bool
    matched_terms: tuple[str, ...]


_RELEASE_POSSIBLE_TERMS = (
    "packing leak",
    "gland",
    "clamp",
    "actuator swap",
)
_THERMAL_ONLY_TERMS = (
    "support",
    "insulation",
)
_BOUNDARY_OPEN_TERMS = (
    "boundary open",
    "boundary-open",
    "open boundary",
    "line break",
    "break containment",
    "open line",
    "flange break",
)


def _permit_hints_text(permit: Mapping[str, Any] | None) -> str:
    if not permit:
        return ""
    fields = (
        "scope_hint",
        "scope_hints",
        "work_scope",
        "workscope",
        "job_scope",
        "permit_hints",
    )
    parts: list[str] = []
    for key in fields:
        value = permit.get(key)
        if isinstance(value, str) and value.strip():
            parts.append(value)
        elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            parts.extend(str(item) for item in value if str(item).strip())
    return " ".join(parts)


def infer_exposure_mode(
    description: str | None,
    *,
    permit: Mapping[str, Any] | None = None,
) -> ExposureInference:
    """Infer exposure mode from description and permit hints.

    Boundary-open terms force escalation to ``intrusive_mech``.
    """

    source = f"{description or ''} {_permit_hints_text(permit)}".lower()

    matched_boundary = tuple(term for term in _BOUNDARY_OPEN_TERMS if term in source)
    if matched_boundary:
        return ExposureInference(
            exposure_mode="release_possible",
            escalate_to_intrusive_mech=True,
            matched_terms=matched_boundary,
        )

    matched_release = tuple(term for term in _RELEASE_POSSIBLE_TERMS if term in source)
    if matched_release:
        return ExposureInference(
            exposure_mode="release_possible",
            escalate_to_intrusive_mech=False,
            matched_terms=matched_release,
        )

    matched_thermal = tuple(term for term in _THERMAL_ONLY_TERMS if term in source)
    if matched_thermal:
        return ExposureInference(
            exposure_mode="thermal_only",
            escalate_to_intrusive_mech=False,
            matched_terms=matched_thermal,
        )

    return ExposureInference(
        exposure_mode=None,
        escalate_to_intrusive_mech=False,
        matched_terms=(),
    )
