"""Seed demo data via API endpoints or direct database insertion.

Reads CSV files from the repository's ``demo`` directory and posts each row to
API endpoints.  The base API URL defaults to ``http://localhost:8000`` but can
be overridden with ``--base-url``.
"""

from __future__ import annotations

import argparse
import csv
import logging
from pathlib import Path

import requests  # type: ignore[import-untyped]


def _post_csv(path: Path, endpoint: str, base_url: str) -> int:
    """Send each row in ``path`` to ``base_url/endpoint``.

    Parameters
    ----------
    path:
        Path to the CSV file.
    endpoint:
        Endpoint relative to ``base_url``.
    base_url:
        Base URL of the API server.

    Returns
    -------
    int
        Number of rows successfully posted.
    """

    count = 0
    with path.open(newline="") as fh:
        for row in csv.DictReader(fh):
            resp = requests.post(
                f"{base_url.rstrip('/')}/{endpoint}", json=row, timeout=10
            )
            resp.raise_for_status()
            count += 1
    return count


def main() -> None:
    """Import demo CSVs and report a summary."""

    parser = argparse.ArgumentParser(description="Seed demo dataset")
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="Base URL for API requests",
    )
    parser.add_argument(
        "--demo-dir",
        default=str(Path(__file__).resolve().parents[1] / "demo"),
        help="Directory containing demo CSV files",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    demo_dir = Path(args.demo_dir)
    base_url = args.base_url.rstrip("/")

    valves = _post_csv(demo_dir / "valves.csv", "valves", base_url)
    lines = _post_csv(demo_dir / "line_list.csv", "lines", base_url)
    work_orders = _post_csv(demo_dir / "work_orders.csv", "workorders", base_url)

    logging.info(
        "Imported %s valves, %s lines, %s work orders", valves, lines, work_orders
    )


if __name__ == "__main__":  # pragma: no cover - manual script
    main()
