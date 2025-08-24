"""Coupa procurement adapter stubs.

This module defines an abstract interface for raising urgent enquiries via
Coupa and a demo implementation used for dry runs.  The real implementation
would call the Coupa API to raise a request for quotation (RFQ).
"""

from __future__ import annotations

import abc
import os
import time
import uuid
from typing import Any, Dict, cast

import requests  # type: ignore[import-untyped]

from ._errors import AdapterRequestError


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


class HttpCoupaAdapter(CoupaAdapter):
    """HTTP-based Coupa adapter."""

    def __init__(self, *, session: requests.Session | None = None) -> None:
        self.base_url = os.environ.get("COUPA_BASE_URL", "")
        self.apikey = os.environ.get("COUPA_APIKEY")
        self._session = session or requests.Session()
        self._timeout = (3.05, 10)
        self._retries = 3

    def _get(self, path: str, params: Dict[str, Any] | None = None) -> Dict[str, Any]:
        url = f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"
        headers = {"apikey": self.apikey} if self.apikey else {}
        backoff = 1.0
        for attempt in range(self._retries):
            try:
                resp = self._session.get(
                    url, headers=headers, params=params, timeout=self._timeout
                )
            except requests.RequestException as exc:
                if attempt == self._retries - 1:
                    raise AdapterRequestError(status_code=0, retry_after=None) from exc
                time.sleep(backoff)
                backoff *= 2
                continue

            status = resp.status_code
            if status == 429 or status >= 500:
                retry_after_header = resp.headers.get("Retry-After")
                try:
                    retry_after = (
                        float(retry_after_header) if retry_after_header else None
                    )
                except ValueError:
                    retry_after = None
                if attempt == self._retries - 1:
                    raise AdapterRequestError(
                        status_code=status, retry_after=retry_after
                    )
                time.sleep(retry_after or backoff)
                backoff *= 2
                continue

            if status >= 400:
                raise AdapterRequestError(status_code=status, retry_after=None)

            return cast(Dict[str, Any], resp.json())
        raise RuntimeError("Unreachable")

    def _post(self, path: str, json: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"
        headers = {"apikey": self.apikey} if self.apikey else {}
        backoff = 1.0
        for attempt in range(self._retries):
            try:
                resp = self._session.post(
                    url, headers=headers, json=json, timeout=self._timeout
                )
            except requests.RequestException as exc:
                if attempt == self._retries - 1:
                    raise AdapterRequestError(status_code=0, retry_after=None) from exc
                time.sleep(backoff)
                backoff *= 2
                continue

            status = resp.status_code
            if status == 429 or status >= 500:
                retry_after_header = resp.headers.get("Retry-After")
                try:
                    retry_after = (
                        float(retry_after_header) if retry_after_header else None
                    )
                except ValueError:
                    retry_after = None
                if attempt == self._retries - 1:
                    raise AdapterRequestError(
                        status_code=status, retry_after=retry_after
                    )
                time.sleep(retry_after or backoff)
                backoff *= 2
                continue

            if status >= 400:
                raise AdapterRequestError(status_code=status, retry_after=None)

            return cast(Dict[str, Any], resp.json())
        raise RuntimeError("Unreachable")

    def raise_urgent_enquiry(self, part_number: str, quantity: int) -> str:
        """Raise an urgent enquiry (RFQ) for a part via Coupa."""
        payload = {"part_number": part_number, "quantity": quantity}
        data = self._post("rfqs", json=payload)
        return cast(str, data.get("id", ""))

    def get_po_status(self, po_number: str) -> str:  # pragma: no cover - stub
        data = self._get(f"po/{po_number}")
        return cast(str, data.get("status", ""))


__all__ = ["CoupaAdapter", "DemoCoupaAdapter", "HttpCoupaAdapter"]
