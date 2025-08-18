"""Utilities for reading hat availability rosters.

This module parses a simple CSV describing when a particular hat (resource) is
available to work.  Each row in the CSV describes a shift:

```
hat,start,stop,breaks,ot
crew,5,10,"7-8",false
```

`start` and `stop` are integer time units where the hat is available.  The
optional ``breaks`` column may contain one or more ``start-stop`` pairs separated
by semicolons.  Break periods are removed from the availability windows.

The primary entry points are :func:`read_hat_roster` which returns availability
windows for each hat and :func:`calendar_adapter` which converts those windows
into a predicate suitable for :class:`des_engine.Task`'s ``calendar`` field.
"""

from __future__ import annotations

from collections import defaultdict
import csv
from typing import Callable, Iterable, Mapping, Sequence


Interval = tuple[int, int]


def _parse_breaks(spec: str | None) -> list[Interval]:
    """Parse a ``breaks`` specification into intervals.

    ``spec`` should contain semicolon separated ``start-stop`` pairs.
    Empty or ``None`` values return an empty list.
    """

    if not spec:
        return []
    breaks: list[Interval] = []
    for part in spec.split(";"):
        part = part.strip()
        if not part:
            continue
        start_s, stop_s = part.split("-")
        breaks.append((int(start_s), int(stop_s)))
    return breaks


def _subtract_breaks(interval: Interval, breaks: Sequence[Interval]) -> list[Interval]:
    """Remove ``breaks`` from ``interval`` returning availability windows."""

    start, stop = interval
    result: list[Interval] = []
    cursor = start
    for bstart, bstop in sorted(breaks):
        if bstop <= cursor or bstart >= stop:
            continue
        if bstart > cursor:
            result.append((cursor, bstart))
        cursor = max(cursor, bstop)
    if cursor < stop:
        result.append((cursor, stop))
    return result


def read_hat_roster(path: str) -> dict[str, list[Interval]]:
    """Read a hat availability CSV.

    Parameters
    ----------
    path:
        File path to CSV containing columns ``hat``, ``start``, ``stop`` and
        optional ``breaks`` and ``ot``.  ``start``/``stop`` are interpreted as
        integer time units.
    """

    availability: dict[str, list[Interval]] = defaultdict(list)
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            hat = row["hat"]
            start = int(row["start"])
            stop = int(row["stop"])
            breaks = _parse_breaks(row.get("breaks"))
            windows = _subtract_breaks((start, stop), breaks)
            availability[hat].extend(windows)
    return dict(availability)


def resource_caps_timeline(
    roster: Mapping[str, Iterable[Interval]],
) -> dict[int, dict[str, int]]:
    """Construct a time-indexed resource capacity timeline.

    The returned mapping associates each integer time with a mapping of hat name
    to the number of available workers wearing that hat.
    """

    timeline: dict[int, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for hat, intervals in roster.items():
        for start, stop in intervals:
            for t in range(start, stop):
                timeline[t][hat] = timeline[t].get(hat, 0) + 1
    # convert nested defaultdicts to normal dicts
    return {t: dict(caps) for t, caps in timeline.items()}


def calendar_adapter(intervals: Iterable[Interval]) -> Callable[[int], bool]:
    """Return a ``Task.calendar`` predicate for the given intervals."""

    windows = list(intervals)

    def _calendar(t: int) -> bool:
        for start, stop in windows:
            if start <= t < stop:
                return True
        return False

    return _calendar
