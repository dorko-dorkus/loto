"""HATS compliance system adapter interface and implementations."""

from __future__ import annotations

import abc
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple, cast

import requests

DATA_PATH = (
    Path(__file__).resolve().parents[2]
    / "apps"
    / "api"
    / "demo_data"
    / "hats_profiles.json"
)


class HatsAdapter(abc.ABC):
    """Abstract interface for the HATS personnel system."""

    @abc.abstractmethod
    def get_profile(self, hats_id: str) -> Dict[str, Any]:
        """Return the profile information for ``hats_id``."""

    @abc.abstractmethod
    def has_required(
        self, hats_ids: List[str], permit_types: List[str]
    ) -> Tuple[bool, List[str]]:
        """Return whether ``hats_ids`` have the necessary ``permit_types``.

        Returns ``(True, [])`` when all identifiers have the required permits,
        otherwise ``(False, missing)`` where ``missing`` contains the IDs
        that failed validation.
        """

    @abc.abstractmethod
    def cbt_minutes(self, craft: str, site: str, when: datetime) -> int:
        """Return CBT minutes for ``craft`` at ``site`` on ``when``."""


class DemoHatsAdapter(HatsAdapter):
    """Dry-run HATS adapter that serves fixture data from disk."""

    def __init__(self) -> None:
        if DATA_PATH.exists():
            self._profiles: Dict[str, Dict[str, Any]] = json.loads(
                DATA_PATH.read_text()
            )
        else:  # pragma: no cover - fixture missing
            self._profiles = {}

    def get_profile(self, hats_id: str) -> Dict[str, Any]:
        return self._profiles[hats_id]

    def has_required(
        self, hats_ids: List[str], permit_types: List[str]
    ) -> Tuple[bool, List[str]]:
        missing = [hid for hid in hats_ids if hid not in self._profiles]
        return not missing, missing

    def cbt_minutes(self, craft: str, site: str, when: datetime) -> int:
        return 0


class HttpHatsAdapter(HatsAdapter):
    """HTTP implementation of the HATS adapter."""

    def __init__(
        self, base_url: str, api_key: str | None = None, timeout: int = 30
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def _headers(self) -> Dict[str, str]:
        headers = {"Accept": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def get_profile(self, hats_id: str) -> Dict[str, Any]:
        resp = requests.get(
            f"{self.base_url}/profiles/{hats_id}",
            headers=self._headers(),
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return cast(Dict[str, Any], resp.json())

    def has_required(
        self, hats_ids: List[str], permit_types: List[str]
    ) -> Tuple[bool, List[str]]:
        payload = {"hats_ids": hats_ids, "permit_types": permit_types}
        resp = requests.post(
            f"{self.base_url}/required",
            json=payload,
            headers=self._headers(),
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        return bool(data.get("ok")), data.get("missing", [])

    def cbt_minutes(self, craft: str, site: str, when: datetime) -> int:
        payload = {"craft": craft, "site": site, "when": when.isoformat()}
        resp = requests.post(
            f"{self.base_url}/cbt",
            json=payload,
            headers=self._headers(),
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        return int(data.get("minutes", 0))


__all__ = ["HatsAdapter", "DemoHatsAdapter", "HttpHatsAdapter"]
