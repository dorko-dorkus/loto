"""Read-only Maximo CMMS adapter."""

from __future__ import annotations

import os
from typing import Any, Dict, List, TypedDict

import requests  # type: ignore[import-untyped]


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

    # internal helper
    def _get(self, path: str, params: Dict[str, Any] | None = None) -> Dict[str, Any]:
        url = f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"
        headers = {"apikey": self.apikey} if self.apikey else {}
        for attempt in range(2):
            try:
                resp = self._session.get(
                    url, headers=headers, params=params, timeout=self._timeout
                )
                resp.raise_for_status()
                return resp.json()
            except requests.RequestException:
                if attempt == 1:
                    raise
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
        data = self._get(
            f"os/{self.os_workorder}", params={"status": "OPEN", "window": window}
        )
        return [
            {
                "id": item["id"],
                "description": item.get("description", ""),
                "asset_id": item.get("asset_id", ""),
            }
            for item in data.get("members", [])
        ]

    def get_asset(self, asset_id: str) -> Asset:
        """Retrieve asset details by identifier."""
        data = self._get(f"os/{self.os_asset}/{asset_id}")
        return {
            "id": data["id"],
            "description": data.get("description", ""),
            "location": data.get("location", ""),
        }
