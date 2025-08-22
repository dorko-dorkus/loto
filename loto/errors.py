"""Custom error hierarchy for the LOTO package.

This module defines a small hierarchy of exceptions used throughout the
project.  Each error exposes two pieces of information:

``code``
    A short machine readable error code.  The tests exercise that this code
    is preserved and surfaced in the string representation of the
    exception.
``hint``
    A human readable explanation of the problem or a hint to the user.

The base :class:`LotoError` stores these attributes and formats them into the
exception message.  The various subclasses simply provide semantic meaning
for the type of failure that occurred (configuration, rules processing,
graph building, planning, integrations and rendering).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class LotoError(Exception):
    """Base class for package specific errors.

    Parameters
    ----------
    code:
        Short error code that identifies the failure.
    hint:
        Human readable message to help diagnose the issue.
    """

    code: str
    hint: str

    def __post_init__(self) -> None:  # pragma: no cover - simple assignment
        # Exception expects to be initialised with a message.  We include the
        # error code in the message so that ``str(exc)`` exposes it directly.
        msg = f"[{self.code}] {self.hint}"
        super().__init__(msg)

    def __str__(self) -> str:  # pragma: no cover - trivial
        # Ensures the formatted message always contains the error code.
        return f"[{self.code}] {self.hint}"


class ConfigError(LotoError):
    """Problems with configuration files or environment."""


class RulesError(LotoError):
    """Errors related to rule packs or rule evaluation."""


class GraphError(LotoError):
    """Failures when building or manipulating graphs."""


class PlanError(LotoError):
    """Issues arising during isolation plan computation."""


class IntegrationError(LotoError):
    """Errors when communicating with external systems."""


class RenderError(LotoError):
    """Failures while rendering documents or reports."""


class ValidationError(LotoError):
    """Input failed validation."""

    code = "VALIDATION_ERROR"

    def __init__(self, hint: str):
        super().__init__(self.code, hint)


class ImportError(LotoError):  # noqa: A001 - intended name clash with builtin
    """Importing external data failed."""

    code = "IMPORT_ERROR"

    def __init__(self, hint: str):
        super().__init__(self.code, hint)


class GenerationError(LotoError):
    """Generating output failed."""

    code = "GENERATION_ERROR"

    def __init__(self, hint: str):
        super().__init__(self.code, hint)


__all__ = [
    "LotoError",
    "ConfigError",
    "RulesError",
    "GraphError",
    "PlanError",
    "IntegrationError",
    "RenderError",
    "ValidationError",
    "ImportError",
    "GenerationError",
]
