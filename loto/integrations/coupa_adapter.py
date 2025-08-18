"""Coupa procurement adapter stubs.

This module defines an abstract interface for raising urgent enquiries via
Coupa and a demo implementation used for dry runs.  The real implementation
would call the Coupa API to raise a request for quotation (RFQ).
"""

from __future__ import annotations

import abc
import uuid


class CoupaAdapter(abc.ABC):
    """Abstract interface for Coupa interactions."""

    @abc.abstractmethod
    def raise_urgent_enquiry(self, part_number: str, quantity: int) -> str:
        """Raise an urgent enquiry (RFQ) for a part.

        Parameters
        ----------
        part_number:
            Identifier for the required part.
        quantity:
            Number of units required.

        Returns
        -------
        str
            Identifier of the raised RFQ.
        """

    @abc.abstractmethod
    def get_po_status(self, po_number: str) -> str:
        """Return the status of a purchase order."""


class DemoCoupaAdapter(CoupaAdapter):
    """Dry-run Coupa adapter that fabricates RFQ identifiers."""

    _PO_STATUSES = {
        "PO-1": "OPEN",
        "PO-2": "CLOSED",
    }

    def raise_urgent_enquiry(self, part_number: str, quantity: int) -> str:
        """Simulate raising an RFQ and return its identifier."""
        return f"RFQ-{uuid.uuid4().hex[:8]}"

    def get_po_status(self, po_number: str) -> str:
        """Return a fixture status for the given purchase order."""
        try:
            return self._PO_STATUSES[po_number]
        except KeyError as exc:  # pragma: no cover - simple error path
            raise KeyError(f"Unknown purchase order {po_number}") from exc
