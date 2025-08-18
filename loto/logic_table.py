"""Utility functions for parsing and evaluating simple logic tables.

This module provides helpers to read a CSV "truth table" describing
simple cause & effect relationships. Only a very small subset of
behaviour is implemented: detection of actuator coils energising under
isolation.  The expected CSV format is::

    isolation,actuator_coil
    0,0
    1,0
    1,1

Columns are interpreted as integers (0 or 1).  When the ``isolation``
column has value ``1`` (meaning isolation is active) the coil may not
transition from ``0`` to ``1``.  Violations are reported by returning the
1-indexed row numbers where the transition occurred.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import csv
from typing import List


@dataclass
class LogicRow:
    """Represents one row from the logic table."""

    isolation: int
    actuator_coil: int


def parse_csv(path: str | Path) -> List[LogicRow]:
    """Parse a CSV logic table into a list of :class:`LogicRow`.

    Parameters
    ----------
    path:
        Path to the CSV file.
    """

    rows: List[LogicRow] = []
    with open(path, newline="") as fh:
        reader = csv.DictReader(fh)
        for raw in reader:
            rows.append(
                LogicRow(
                    isolation=int(raw.get("isolation", 0)),
                    actuator_coil=int(raw.get("actuator_coil", 0)),
                )
            )
    return rows


def find_coil_violations(rows: List[LogicRow]) -> List[int]:
    """Return row numbers where coil transitions 0→1 while isolated.

    Parameters
    ----------
    rows:
        Parsed logic table rows.

    Returns
    -------
    List[int]
        1-indexed row numbers where a violation was detected.
    """

    violations: List[int] = []
    if not rows:
        return violations

    previous = rows[0].actuator_coil
    for idx, row in enumerate(rows[1:], start=2):
        if row.isolation == 1 and previous == 0 and row.actuator_coil == 1:
            violations.append(idx)
        previous = row.actuator_coil
    return violations
