import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from apps.api.reporting import generate_weekly_report


def test_generate_weekly_report(tmp_path: Path) -> None:
    now = datetime.now(tz=UTC)
    runs = [
        {
            "executed_at": now - timedelta(minutes=i),
            "time_to_pack_delta": float(i % 5),
            "issuer_acceptance": i % 2 == 0,
            "parts_wait_hours": float(i % 7),
        }
        for i in range(200)
    ]

    result = generate_weekly_report(runs, report_dir=tmp_path)
    pdf_path = result["pdf"]
    json_path = result["json"]

    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 10 * 1024

    data = json.loads(json_path.read_text())
    assert set(data) == {
        "run_count",
        "avg_time_to_pack_delta",
        "issuer_acceptance_rate",
        "parts_wait_hours_total",
    }
