"""WAPR permit-to-work adapter stubs.

This module defines an abstract interface for retrieving permit data from
WAPR and a demo implementation that serves fixture data for testing and
dry-run scenarios.
"""

from __future__ import annotations

import abc
import uuid
from datetime import datetime
from typing import Any, Dict, List, Tuple


class WaprAdapter(abc.ABC):
    """Abstract interface for WAPR interactions."""

    @abc.abstractmethod
    def fetch_permit(self, work_order_id: str) -> Dict[str, Any]:
        """Fetch permit data for a work order.

        Parameters
        ----------
        work_order_id:
            Identifier of the work order whose permit is requested.

        Returns
        -------
        Dict[str, Any]
            A dictionary of permit details including applied isolations.
        """

    @abc.abstractmethod
    def reserve_window(self, start: datetime, end: datetime) -> str:
        """Reserve a maintenance window and return its identifier.

        Parameters
        ----------
        start:
            Beginning of the desired maintenance window.
        end:
            End of the desired maintenance window. ``end`` must be after
            ``start``.
        """

    @abc.abstractmethod
    def list_conflicts(self, start: datetime, end: datetime) -> List[str]:
        """List work order identifiers that conflict with the window."""

    @abc.abstractmethod
    def get_price_curve(self, asset: str) -> List[Tuple[int, float]]:
        """Return a simple price curve for ``asset`` as ``(hour, price)`` pairs."""


class DemoWaprAdapter(WaprAdapter):
    """Dry-run WAPR adapter that returns fixture permit data."""

    _FIXTURE_PERMITS: Dict[str, Dict[str, List[str]]] = {
        "WO-100": {"applied_isolations": ["ISO-1", "ISO-2"]},
        "WO-200": {"applied_isolations": ["ISO-3"]},
    }
    _FIXTURE_CURVES: Dict[str, List[Tuple[int, float]]] = {
        "ASSET-1": [(0, 100.0), (1, 110.0)],
    }

    def fetch_permit(self, work_order_id: str) -> Dict[str, Any]:
        """Return fixture permit data for the given work order."""
        return self._FIXTURE_PERMITS.get(work_order_id, {"applied_isolations": []})

    def reserve_window(self, start: datetime, end: datetime) -> str:
        """Return a fabricated reservation identifier for the window."""
        if end <= start:
            raise ValueError("end must be after start")
        return f"RES-{uuid.uuid4().hex[:8]}"

    def list_conflicts(self, start: datetime, end: datetime) -> List[str]:
        """Return fixture conflicting work order identifiers."""
        if end <= start:
            raise ValueError("end must be after start")
        return ["WO-300", "WO-400"]

    def get_price_curve(self, asset: str) -> List[Tuple[int, float]]:
        """Return a fixture price curve for the asset."""
        try:
            return self._FIXTURE_CURVES[asset]
        except KeyError as exc:  # pragma: no cover - simple error path
            raise KeyError(f"No price curve for {asset}") from exc
