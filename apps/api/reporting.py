from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Sequence

from weasyprint import HTML


def generate_weekly_report(
    runs: Sequence[dict[str, Any]], report_dir: Path | str = Path("reports")
) -> dict[str, Any]:
    """Generate a weekly KPI report and emit JSON and PDF files.

    Parameters
    ----------
    runs:
        Iterable of run dictionaries with keys ``executed_at`` (``datetime``),
        ``time_to_pack_delta`` (``float``), ``issuer_acceptance`` (``bool``), and
        ``parts_wait_hours`` (``float``).
    report_dir:
        Directory to place ``weekly.json`` and ``weekly.pdf``.
    """
    report_path = Path(report_dir)
    cutoff = datetime.now(tz=UTC) - timedelta(days=7)
    recent = [r for r in runs if r["executed_at"] >= cutoff]

    run_count = len(recent)
    avg_time_to_pack_delta = (
        sum(r["time_to_pack_delta"] for r in recent) / run_count if run_count else 0.0
    )
    issuer_acceptance_rate = (
        sum(1 for r in recent if r["issuer_acceptance"]) / run_count
        if run_count
        else 0.0
    )
    parts_wait_hours_total = sum(r["parts_wait_hours"] for r in recent)

    data = {
        "run_count": run_count,
        "avg_time_to_pack_delta": avg_time_to_pack_delta,
        "issuer_acceptance_rate": issuer_acceptance_rate,
        "parts_wait_hours_total": parts_wait_hours_total,
    }

    report_path.mkdir(parents=True, exist_ok=True)

    json_path = report_path / "weekly.json"
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    rows = "".join(
        f"<tr><td>{r['executed_at'].isoformat()}</td><td>{r['time_to_pack_delta']}</td>"
        f"<td>{'yes' if r['issuer_acceptance'] else 'no'}</td><td>{r['parts_wait_hours']}</td></tr>"
        for r in recent
    )
    html = f"""
    <html>
    <body>
        <h1>Weekly KPI Report</h1>
        <ul>
            <li>Run count: {run_count}</li>
            <li>Avg time-to-pack delta: {avg_time_to_pack_delta:.2f}</li>
            <li>Issuer acceptance rate: {issuer_acceptance_rate:.2%}</li>
            <li>Total parts-wait hours: {parts_wait_hours_total:.2f}</li>
        </ul>
        <table border="1">
            <thead>
                <tr><th>Executed At</th><th>Time-to-Pack Δ</th><th>Issuer Accepted</th><th>Parts Wait (h)</th></tr>
            </thead>
            <tbody>{rows}</tbody>
        </table>
    </body>
    </html>
    """
    pdf_path = report_path / "weekly.pdf"
    HTML(string=html).write_pdf(str(pdf_path))

    return {"json": json_path, "pdf": pdf_path, "data": data}


def _mock_runs(n: int) -> list[dict[str, Any]]:
    now = datetime.now(tz=UTC)
    return [
        {
            "executed_at": now - timedelta(minutes=i),
            "time_to_pack_delta": float(i % 5),
            "issuer_acceptance": i % 2 == 0,
            "parts_wait_hours": float(i % 7),
        }
        for i in range(n)
    ]


def main() -> None:  # pragma: no cover - convenience entrypoint
    runs = _mock_runs(200)
    generate_weekly_report(runs)


if __name__ == "__main__":  # pragma: no cover
    main()
