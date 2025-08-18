"""Document renderer for the LOTO planner.

This module contains the :class:`Renderer` class which is responsible
for producing human‐readable outputs, such as PDF isolation sheets and
JSON summaries suitable for machine consumption. Rendering operations
should be deterministic and avoid side effects beyond file generation.

Only class and method stubs are provided here. An actual implementation
would use a PDF generation library (e.g., ReportLab or python-pptx) and
serialize plan data to JSON.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Dict

from .isolation_planner import IsolationPlan
from .models import SimReport


class Renderer:
    """Render isolation plans and simulation reports to various formats."""

    def pdf(self, plan: IsolationPlan, sim_report: SimReport, rule_hash: str) -> bytes:
        """Generate a PDF representation of the plan and simulation report.

        Parameters
        ----------
        plan: IsolationPlan
            The isolation plan to render.
        sim_report: SimReport
            The simulation report to render.
        rule_hash: str
            A hash of the rule pack used, included for traceability.

        Returns
        -------
        bytes
            A byte string containing the contents of the generated PDF.

        Notes
        -----
        This stub does not implement PDF generation; it simply raises
        NotImplementedError. A real implementation should lay out the
        plan details in tables, embed QR codes, and include the
        simulation results.
        """
        raise NotImplementedError("Renderer.pdf() is not implemented yet")

    def to_json(
        self,
        plan: IsolationPlan,
        sim_report: SimReport,
        impact: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """Serialize the plan and simulation report to a JSON-friendly dict.

        Parameters
        ----------
        plan: IsolationPlan
            The isolation plan to serialize.
        sim_report: SimReport
            The simulation report to serialize.
        impact: Dict[str, Any] | None
            Optional impact information (e.g., unavailable assets, unit
            derates) to include in the JSON output.

        Returns
        -------
        Dict[str, Any]
            A dictionary ready for JSON serialization.

        Notes
        -----
        The returned dictionary is deliberately simple and deterministic.  All
        Pydantic models are converted using ``dict()`` with ``exclude_none`` so
        optional ``None`` values do not appear in the output.  ``impact`` is
        included only when provided and its keys are sorted to maintain a
        stable order for snapshot tests.
        """

        def _sorted_dict(data: Dict[str, Any]) -> Dict[str, Any]:
            """Recursively sort dictionary keys for deterministic output."""

            items: list[tuple[str, Any]] = []
            for key, value in sorted(data.items()):
                if isinstance(value, Mapping):
                    items.append((key, _sorted_dict(dict(value))))
                else:
                    items.append((key, value))
            return {k: v for k, v in items}

        payload: Dict[str, Any] = {
            "plan": plan.dict(exclude_none=True),
            "simulation": sim_report.dict(exclude_none=True),
        }

        if impact:
            payload["impact"] = _sorted_dict(dict(impact))

        return payload
