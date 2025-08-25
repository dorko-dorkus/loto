"""Ellipse/Eclipse permit and work order adapter stubs.

This module defines an abstract interface for interacting with the
Ellipse/Eclipse system and simple demo and HTTP implementations. The real
implementation would authenticate with Ellipse and call its APIs to retrieve
work order and permit information.
"""

from __future__ import annotations

import abc
import os
import time
from typing import Any, Dict, cast

import requests  # type: ignore[import-untyped]

from ._errors import AdapterRequestError


class EllipseAdapter(abc.ABC):
    """Abstract interface for Ellipse/Eclipse interactions."""

    @abc.abstractmethod
    def fetch_work_order(self, work_order_id: str) -> Dict[str, Any]:
        """Return minimal information about a work order."""

    @abc.abstractmethod
    def fetch_permit(self, work_order_id: str) -> Dict[str, Any]:
        """Return permit data associated with ``work_order_id``."""


class DemoEllipseAdapter(EllipseAdapter):
    """Dry-run Ellipse adapter that returns fixture data."""

    _WORK_ORDERS: Dict[str, Dict[str, str]] = {
        "WO-1": {"id": "WO-1", "description": "Demo WO", "asset_id": "ASSET-1"},
        "WO-2": {"id": "WO-2", "description": "Demo WO", "asset_id": "ASSET-2"},
    }
    _PERMITS: Dict[str, Dict[str, Any]] = {
        "WO-1": {
            "id": "PRM-1",
            "status": "Active",
            "applied_isolations": ["ISO-1", "ISO-2"],
        },
        "WO-2": {
            "id": "PRM-2",
            "status": "Authorised",
            "applied_isolations": ["ISO-3"],
        },
    }

    def fetch_work_order(self, work_order_id: str) -> Dict[str, Any]:
        """Return fixture work order details."""
        return self._WORK_ORDERS.get(
            work_order_id,
            {"id": work_order_id, "description": "", "asset_id": ""},
        )

    def fetch_permit(self, work_order_id: str) -> Dict[str, Any]:
        """Return fixture permit data for the work order."""
        return self._PERMITS.get(
            work_order_id,
            {"id": None, "status": "Unknown", "applied_isolations": []},
        )


class HttpEllipseAdapter(EllipseAdapter):
    """HTTP-based Ellipse adapter with basic token authentication."""

    def __init__(self, *, session: requests.Session | None = None) -> None:
        self.base_url = os.environ.get("ELLIPSE_BASE_URL", "")
        self.username = os.environ.get("ELLIPSE_USERNAME")
        self.password = os.environ.get("ELLIPSE_PASSWORD")
        self._session = session or requests.Session()
        self._timeout = (3.05, 10)
        self._retries = 3
        self._token: str | None = None

    def _authenticate(self) -> None:
        if self._token:
            return
        payload = {"username": self.username, "password": self.password}
        resp = self._session.post(
            f"{self.base_url.rstrip('/')}/auth/login",
            json=payload,
            timeout=self._timeout,
        )
        resp.raise_for_status()
        data = cast(Dict[str, Any], resp.json())
        self._token = cast(str, data.get("token", ""))

    def _get(self, path: str, params: Dict[str, Any] | None = None) -> Dict[str, Any]:
        self._authenticate()
        url = f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"
        headers = {"Authorization": f"Bearer {self._token}"} if self._token else {}
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

    def fetch_work_order(self, work_order_id: str) -> Dict[str, Any]:
        """Fetch work order details via the Ellipse API."""
        return self._get(f"workorders/{work_order_id}")

    def fetch_permit(self, work_order_id: str) -> Dict[str, Any]:
        """Fetch permit data for ``work_order_id`` via the Ellipse API."""
        return self._get(f"permits/{work_order_id}")


__all__ = ["EllipseAdapter", "DemoEllipseAdapter", "HttpEllipseAdapter"]
