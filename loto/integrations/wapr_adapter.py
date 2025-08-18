"""WAPR permit-to-work adapter stubs.

This module defines an abstract interface for retrieving permit data from
WAPR and a demo implementation that serves fixture data for testing and
dry-run scenarios.
"""

from __future__ import annotations

import abc
from typing import Any, Dict, List


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


class DemoWaprAdapter(WaprAdapter):
    """Dry-run WAPR adapter that returns fixture permit data."""

    _FIXTURE_PERMITS: Dict[str, Dict[str, List[str]]] = {
        "WO-100": {"applied_isolations": ["ISO-1", "ISO-2"]},
        "WO-200": {"applied_isolations": ["ISO-3"]},
    }

    def fetch_permit(self, work_order_id: str) -> Dict[str, Any]:
        """Return fixture permit data for the given work order."""
        return self._FIXTURE_PERMITS.get(work_order_id, {"applied_isolations": []})
