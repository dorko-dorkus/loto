from __future__ import annotations

import time
from typing import Any, Dict

import pytest

from loto.integrations._errors import AdapterRequestError
from loto.integrations.coupa_adapter import HttpCoupaAdapter
from loto.integrations.maximo_adapter import MaximoAdapter


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


def _set_maximo_env(monkeypatch) -> None:
    monkeypatch.setenv("MAXIMO_BASE_URL", "http://maximo.local")
    monkeypatch.setenv("MAXIMO_APIKEY", "secret")
    monkeypatch.setenv("MAXIMO_OS_WORKORDER", "WORKORDER")
    monkeypatch.setenv("MAXIMO_OS_ASSET", "ASSET")


def _set_coupa_env(monkeypatch) -> None:
    monkeypatch.setenv("COUPA_BASE_URL", "http://coupa.local")
    monkeypatch.setenv("COUPA_APIKEY", "secret")


def test_maximo_retry_on_429(monkeypatch) -> None:
    _set_maximo_env(monkeypatch)
    adapter = MaximoAdapter()
    calls = {"count": 0}

    def fake_get(url, headers=None, params=None, timeout=None):
        calls["count"] += 1
        if calls["count"] == 1:
            return DummyResponse(429, headers={"Retry-After": "1"})
        return DummyResponse(200, data={"ok": True})

    monkeypatch.setattr(adapter._session, "get", fake_get)
    sleeps: list[float] = []
    monkeypatch.setattr(time, "sleep", lambda s: sleeps.append(s))
    data = adapter._get("/foo")
    assert data == {"ok": True}
    assert sleeps == [1.0]


def test_maximo_structured_error_on_500(monkeypatch) -> None:
    _set_maximo_env(monkeypatch)
    adapter = MaximoAdapter()

    def fake_get(url, headers=None, params=None, timeout=None):
        return DummyResponse(500)

    monkeypatch.setattr(adapter._session, "get", fake_get)
    monkeypatch.setattr(time, "sleep", lambda s: None)
    with pytest.raises(AdapterRequestError) as excinfo:
        adapter._get("/foo")
    err = excinfo.value
    assert err.status_code == 500
    assert err.retry_after is None


def test_coupa_retry_on_429(monkeypatch) -> None:
    _set_coupa_env(monkeypatch)
    adapter = HttpCoupaAdapter()
    calls = {"count": 0}

    def fake_get(url, headers=None, params=None, timeout=None):
        calls["count"] += 1
        if calls["count"] == 1:
            return DummyResponse(429, headers={"Retry-After": "2"})
        return DummyResponse(200, data={"ok": True})

    monkeypatch.setattr(adapter._session, "get", fake_get)
    sleeps: list[float] = []
    monkeypatch.setattr(time, "sleep", lambda s: sleeps.append(s))
    data = adapter._get("/foo")
    assert data == {"ok": True}
    assert sleeps == [2.0]


def test_coupa_structured_error_on_500(monkeypatch) -> None:
    _set_coupa_env(monkeypatch)
    adapter = HttpCoupaAdapter()

    def fake_get(url, headers=None, params=None, timeout=None):
        return DummyResponse(500)

    monkeypatch.setattr(adapter._session, "get", fake_get)
    monkeypatch.setattr(time, "sleep", lambda s: None)
    with pytest.raises(AdapterRequestError) as excinfo:
        adapter._get("/foo")
    err = excinfo.value
    assert err.status_code == 500
    assert err.retry_after is None
