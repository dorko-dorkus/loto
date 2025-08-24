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

import os
import tomllib
from collections.abc import Mapping
from datetime import datetime
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as pkg_version
from io import BytesIO
from pathlib import Path
from subprocess import CalledProcessError, run
from typing import Any, Dict
from zoneinfo import ZoneInfo

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .models import IsolationPlan, SimReport

try:
    APP_VERSION = pkg_version("loto")
except PackageNotFoundError:
    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    APP_VERSION = tomllib.loads(pyproject.read_text())["project"]["version"]


def _git_sha() -> str:
    try:
        result = run(
            ["git", "rev-parse", "--short", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    except (CalledProcessError, FileNotFoundError):
        return "unknown"


GIT_SHA = _git_sha()


class Renderer:
    """Render isolation plans and simulation reports to various formats."""

    def pdf(
        self,
        plan: IsolationPlan,
        sim_report: SimReport,
        rule_hash: str,
        *,
        seed: int | None = None,
        timezone: str = "UTC",
    ) -> bytes:
        """Generate a PDF representation of the plan and simulation report.

        Parameters
        ----------
        plan: IsolationPlan
            The isolation plan to render.
        sim_report: SimReport
            The simulation report to render.
        rule_hash: str
            A hash of the rule pack used, included for traceability.
        seed: int | None
            Optional random seed recorded for determinism.
        timezone: str
            Timezone identifier for provenance information.

        Returns
        -------
        bytes
            A byte string containing the contents of the generated PDF.

        Notes
        -----
        The implementation intentionally keeps layout simple and
        deterministic so tests can reliably parse the output.  A
        minimal set of fields are rendered: a title containing the
        plan identifier, the rule hash for traceability, a table of
        isolation actions and a summary of simulation stimuli.  ReportLab
        is used directly with basic fonts (Helvetica) to avoid any
        environment specific variability.
        """

        buffer = BytesIO()
        # ``SimpleDocTemplate`` provides a deterministic page layout using
        # standard letter size and Helvetica fonts.
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()

        story = [Paragraph(f"Isolation Plan: {plan.plan_id}", styles["Title"])]
        story.append(Paragraph(f"Work Order ID: {plan.plan_id}", styles["Normal"]))
        story.append(Paragraph(f"Rule Hash: {rule_hash}", styles["Normal"]))
        story.append(
            Paragraph(f"Seed: {seed if seed is not None else 'N/A'}", styles["Normal"])
        )
        story.append(Paragraph(f"Timezone: {timezone}", styles["Normal"]))
        timestamp = datetime.now(ZoneInfo(timezone))
        story.append(
            Paragraph(
                f"Generated: {timestamp.strftime('%Y-%m-%d %H:%M %Z')}",
                styles["Normal"],
            )
        )
        story.append(Spacer(1, 12))
        story.append(Paragraph("Legend", styles["Heading2"]))
        story.append(
            Paragraph(
                "Because… footnotes explain why each isolation is required."
                " 'DDBB' denotes double block and bleed.",
                styles["Normal"],
            )
        )
        story.append(Spacer(1, 12))

        if plan.actions:
            action_rows: list[list[str]] = [
                ["Component", "Method", "Duration (s)"],
            ]
            for action in plan.actions:
                duration = "" if action.duration_s is None else f"{action.duration_s:g}"
                action_rows.append([action.component_id, action.method, duration])

            action_table = Table(action_rows, hAlign="LEFT")
            action_table.setStyle(
                TableStyle(
                    [
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ]
                )
            )
            story.append(action_table)
            story.append(Spacer(1, 12))

        if sim_report.results:
            story.append(Paragraph("Simulation Stimuli", styles["Heading2"]))
            stim_rows: list[list[str]] = [["Stimulus", "Success", "Impact"]]
            for item in sim_report.results:
                stim_rows.append(
                    [
                        item.stimulus.name,
                        "yes" if item.success else "no",
                        f"{item.impact:g}",
                    ]
                )

            stim_table = Table(stim_rows, hAlign="LEFT")
            stim_table.setStyle(
                TableStyle(
                    [
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ]
                )
            )
            story.append(stim_table)
            story.append(Spacer(1, 12))

        if plan.hazards:
            story.append(Paragraph("Hazards", styles["Heading2"]))
            for hazard in plan.hazards:
                story.append(Paragraph(hazard, styles["Normal"]))
            story.append(Spacer(1, 12))

        if plan.controls:
            story.append(Paragraph("Controls", styles["Heading2"]))
            for control in plan.controls:
                story.append(Paragraph(control, styles["Normal"]))
            story.append(Spacer(1, 12))

        if plan.verifications:
            story.append(Paragraph("Footnotes", styles["Heading2"]))
            for note in plan.verifications:
                story.append(Paragraph(f"Because {note}", styles["Normal"]))

        env = os.getenv("APP_ENV", "").lower()
        if env == "live":
            env_badge = "PROD"
        elif env == "test":
            env_badge = "TEST"
        else:
            env_badge = "DRY-RUN"

        nz_timestamp = datetime.now(ZoneInfo("Pacific/Auckland"))
        version_str = f"{APP_VERSION} ({GIT_SHA})"
        footer_text = (
            f"WO: {plan.plan_id} | Seed: {seed if seed is not None else 'N/A'} | "
            f"Rule Hash: {rule_hash} | Generated: {nz_timestamp.strftime('%Y-%m-%d %H:%M %Z')} | "
            f"ENV: {env_badge} | Version: {version_str}"
        )

        def _footer(canvas: Any, doc: Any) -> None:
            canvas.saveState()
            canvas.setFont("Helvetica", 8)
            canvas.drawString(doc.leftMargin, 15, footer_text)
            canvas.restoreState()

        doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

    def to_json(
        self,
        plan: IsolationPlan,
        sim_report: SimReport,
        impact: Mapping[str, Any] | None = None,
        bundling_picks: list[str] | None = None,
        bundling_params: Mapping[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """Serialize the plan and simulation report to a JSON-friendly dict.

        Parameters
        ----------
        plan: IsolationPlan
            The isolation plan to serialize.
        sim_report: SimReport
            The simulation report to serialize.
        impact: Mapping[str, Any] | None
            Optional impact information (e.g., unavailable assets, unit
            derates) to include in the JSON output.
        bundling_picks: list[str] | None
            Optional list of bundle pick identifiers. The list is sorted to
            ensure deterministic output.
        bundling_params: Mapping[str, Any] | None
            Optional bundle parameters. Keys are recursively sorted for
            deterministic output.

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

        def _sorted_dict(data: Mapping[str, Any]) -> Dict[str, Any]:
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

        if bundling_picks or bundling_params:
            bundle_payload: Dict[str, Any] = {}
            if bundling_picks:
                bundle_payload["picks"] = sorted(bundling_picks)
            if bundling_params:
                bundle_payload["params"] = _sorted_dict(dict(bundling_params))
            payload["bundling"] = bundle_payload

        return payload
