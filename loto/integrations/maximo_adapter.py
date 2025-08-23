"""Read-only Maximo CMMS adapter."""

from __future__ import annotations

import os
import time
from typing import Any, Dict, List, TypedDict

import requests  # type: ignore[import-untyped]

from ._errors import AdapterRequestError


class WorkOrder(TypedDict):
    """Shape of a work order returned by the adapter."""

    id: str
    description: str
    asset_id: str


class Asset(TypedDict):
    """Shape of an asset returned by the adapter."""

    id: str
    description: str
    location: str


class MaximoAdapter:
    """HTTP-based adapter for retrieving data from Maximo.

    The adapter uses environment variables for configuration:
    - ``MAXIMO_BASE_URL``: base URL of the Maximo REST API.
    - ``MAXIMO_APIKEY``: API key for authentication (optional).
    - ``MAXIMO_OS_WORKORDER``: object structure name for work orders.
    - ``MAXIMO_OS_ASSET``: object structure name for assets.
    """

    def __init__(self, *, session: requests.Session | None = None) -> None:
        self.base_url = os.environ.get("MAXIMO_BASE_URL", "")
        self.apikey = os.environ.get("MAXIMO_APIKEY")
        self.os_workorder = os.environ.get("MAXIMO_OS_WORKORDER", "WORKORDER")
        self.os_asset = os.environ.get("MAXIMO_OS_ASSET", "ASSET")
        self._session = session or requests.Session()
        self._timeout = (3.05, 10)
        self._retries = 3

    # internal helper
    def _get(self, path: str, params: Dict[str, Any] | None = None) -> Dict[str, Any]:
        if path.startswith("http://") or path.startswith("https://"):
            url = path
        else:
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
                    raise AdapterRequestError(
                        status_code=502, retry_after=None
                    ) from exc
                time.sleep(backoff)
                backoff *= 2
                continue

            status = resp.status_code
            if status == 429:
                retry_after_header = resp.headers.get("Retry-After")
                try:
                    retry_after = (
                        float(retry_after_header) if retry_after_header else None
                    )
                except ValueError:
                    retry_after = None
                if attempt == self._retries - 1:
                    raise AdapterRequestError(status_code=429, retry_after=retry_after)
                time.sleep(retry_after or backoff)
                backoff *= 2
                continue

            if 500 <= status:
                retry_after_header = resp.headers.get("Retry-After")
                try:
                    retry_after = (
                        float(retry_after_header) if retry_after_header else None
                    )
                except ValueError:
                    retry_after = None
                if attempt == self._retries - 1:
                    raise AdapterRequestError(status_code=502, retry_after=retry_after)
                time.sleep(retry_after or backoff)
                backoff *= 2
                continue

            if status >= 400:
                raise AdapterRequestError(status_code=status, retry_after=None)

            return resp.json()
        raise RuntimeError("Unreachable")

    def get_work_order(self, work_order_id: str) -> WorkOrder:
        """Retrieve a single work order by identifier."""
        data = self._get(f"os/{self.os_workorder}/{work_order_id}")
        return {
            "id": data["id"],
            "description": data.get("description", ""),
            "asset_id": data.get("asset_id", ""),
        }

    def list_open_work_orders(self, window: int) -> List[WorkOrder]:
        """List open work orders within the specified window."""
        path = f"os/{self.os_workorder}"
        params: Dict[str, Any] | None = {"status": "OPEN", "window": window}
        work_orders: List[WorkOrder] = []
        while True:
            data = self._get(path, params=params)
            work_orders.extend(
                {
                    "id": item["id"],
                    "description": item.get("description", ""),
                    "asset_id": item.get("asset_id", ""),
                }
                for item in data.get("members", [])
            )
            next_path = data.get("next")
            if not next_path:
                break
            if next_path.startswith(self.base_url):
                next_path = next_path[len(self.base_url) :]
            path = next_path.lstrip("/")
            params = None
        return work_orders

    def get_asset(self, asset_id: str) -> Asset:
        """Retrieve asset details by identifier."""
        data = self._get(f"os/{self.os_asset}/{asset_id}")
        return {
            "id": data["id"],
            "description": data.get("description", ""),
            "location": data.get("location", ""),
        }
