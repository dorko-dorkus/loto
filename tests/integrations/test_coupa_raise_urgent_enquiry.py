from __future__ import annotations

import time
from typing import Any, Dict

import pytest
from pytest import MonkeyPatch

from loto.integrations._errors import AdapterRequestError
from loto.integrations.coupa_adapter import HttpCoupaAdapter


class DummyResponse:
    def __init__(
        self,
        status_code: int,
        data: Dict[str, Any] | None = None,
        headers: Dict[str, str] | None = None,
    ):
        self.status_code = status_code
        self._data = data or {}
        self.headers = headers or {}

    def json(self) -> Dict[str, Any]:
        return self._data


def _set_coupa_env(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("COUPA_BASE_URL", "http://coupa.local")
    monkeypatch.setenv("COUPA_APIKEY", "secret")


def test_raise_urgent_enquiry_retry(monkeypatch: MonkeyPatch) -> None:
    _set_coupa_env(monkeypatch)
    adapter = HttpCoupaAdapter()
    calls = {"count": 0}

    def fake_post(
        url: str,
        headers: Dict[str, str] | None = None,
        json: Dict[str, Any] | None = None,
        timeout: tuple[float, float] | None = None,
    ) -> DummyResponse:
        calls["count"] += 1
        if calls["count"] == 1:
            return DummyResponse(429, headers={"Retry-After": "2"})
        assert json == {"part_number": "P-1", "quantity": 5}
        return DummyResponse(201, data={"id": "RFQ-123"})

    monkeypatch.setattr(adapter._session, "post", fake_post)

    sleeps: list[float] = []

    def fake_sleep(s: float) -> None:
        sleeps.append(s)

    monkeypatch.setattr(time, "sleep", fake_sleep)
    rfq_id = adapter.raise_urgent_enquiry("P-1", 5)
    assert rfq_id == "RFQ-123"
    assert sleeps == [2.0]


def test_raise_urgent_enquiry_error(monkeypatch: MonkeyPatch) -> None:
    _set_coupa_env(monkeypatch)
    adapter = HttpCoupaAdapter()

    def fake_post(
        url: str,
        headers: Dict[str, str] | None = None,
        json: Dict[str, Any] | None = None,
        timeout: tuple[float, float] | None = None,
    ) -> DummyResponse:
        return DummyResponse(500)

    monkeypatch.setattr(adapter._session, "post", fake_post)

    def fake_sleep(_: float) -> None:
        return None

    monkeypatch.setattr(time, "sleep", fake_sleep)
    with pytest.raises(AdapterRequestError) as excinfo:
        adapter.raise_urgent_enquiry("P-1", 5)
    err = excinfo.value
    assert err.status_code == 500
    assert err.retry_after is None
