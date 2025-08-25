"""Permit readiness utilities and conditional expression management."""

from __future__ import annotations

from typing import Any, Dict, Mapping

from loto.constants import CHECKLIST_HAND_BACK, DOC_CATEGORY


class ConditionalExpressionManager:
    """Simple manager for named conditional expressions.

    Expressions use a limited SQL-like syntax with ``:name`` placeholders.
    Currently supported operations:
    - ``:field IS NOT NULL``
    - ``:field = <literal>`` with integer or quoted string literals
    Expressions may be combined using ``AND``.
    """

    def __init__(self) -> None:
        self._exprs: Dict[str, str] = {}

    def register(self, name: str, expression: str) -> None:
        """Register a new expression under ``name``."""

        self._exprs[name] = expression

    def evaluate(self, name: str, values: Mapping[str, Any]) -> bool:
        """Evaluate expression ``name`` against ``values``."""

        expr = self._exprs[name]
        parts = [p.strip() for p in expr.split("AND")]
        return all(self._eval_part(part, values) for part in parts)

    def _eval_part(self, part: str, values: Mapping[str, Any]) -> bool:
        if part.endswith("IS NOT NULL"):
            field = part.split()[0][1:]
            return values.get(field) is not None
        if "=" in part:
            left, right = [p.strip() for p in part.split("=", 1)]
            field = left[1:] if left.startswith(":") else left
            value: Any
            if right.startswith("'") and right.endswith("'"):
                value = right[1:-1]
            elif right.isdigit():
                value = int(right)
            else:
                value = right
            return bool(values.get(field) == value)
        raise ValueError(f"Unsupported condition: {part}")


_expr_manager = ConditionalExpressionManager()
_expr_manager.register(
    "PERMIT_READY", ":permit_id IS NOT NULL AND :permit_verified = 1"
)


def permit_ready(values: Mapping[str, Any]) -> bool:
    """Return True if the permit is recorded and verified."""

    return _expr_manager.evaluate("PERMIT_READY", values)


class StatusValidationError(RuntimeError):
    """Raised when a status transition is not allowed."""


def validate_status_change(
    workorder: Mapping[str, Any],
    from_status: str,
    to_status: str,
    reason: str | None = None,
) -> None:
    """Validate a work order status change.

    The transition from ``SCHED`` to ``INPRG`` requires the ``PERMIT_READY``
    condition to be satisfied. When moving from ``INPRG`` to ``HOLD`` a
    reason must be supplied.
    """

    if from_status == "INPRG" and to_status == "HOLD":
        if not reason:
            raise StatusValidationError(
                "Hold reason is required when placing work order on hold."
            )
        return

    if from_status == "HOLD" and to_status == "INPRG":
        return

    if from_status == "SCHED" and to_status == "INPRG":
        if not workorder.get("maximo_wo"):
            raise StatusValidationError(
                "WO Number (Maximo) is required before work can start."
            )
        values = {
            "permit_id": workorder.get("permit_id"),
            "permit_verified": int(bool(workorder.get("permit_verified"))),
        }
        if not permit_ready(values):
            raise StatusValidationError(
                "Permit must be recorded and verified before work can start."
            )

    if from_status == "INPRG" and to_status == "COMP":
        attachments = workorder.get("attachments", [])
        checklist = workorder.get("checklist", {})
        has_doc = any(doc.get("category") == DOC_CATEGORY for doc in attachments)
        closed = bool(checklist.get(CHECKLIST_HAND_BACK))
        if not has_doc or not closed:
            raise StatusValidationError(
                "Permit closeout requires permit document upload and checklist confirmation."
            )
