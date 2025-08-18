from __future__ import annotations

from pathlib import Path
from typing import List, Tuple
import csv
from datetime import datetime

Point = Tuple[float, float]


def load_price_curve(path: str | Path) -> List[Point]:
    """Return price curve from ``path`` as ``(hour, price)`` pairs.

    The CSV at ``path`` is expected to contain two columns: a timestamp and
    a price value denominated in $/MWh.  Timestamps are parsed using
    :func:`datetime.fromisoformat` and converted into hours relative to the
    first entry.
    """

    path = Path(path)
    rows: List[Tuple[datetime, float]] = []
    with path.open(newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) < 2:
                continue
            ts_str, price_str = row[0], row[1]
            try:
                ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                price = float(price_str)
            except ValueError:
                # Skip header or malformed lines
                continue
            rows.append((ts, price))

    if not rows:
        return []

    rows.sort(key=lambda x: x[0])
    t0 = rows[0][0]
    curve: List[Point] = [
        ((ts - t0).total_seconds() / 3600.0, price) for ts, price in rows
    ]
    return curve
