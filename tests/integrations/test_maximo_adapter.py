from typing import Any, Dict

import requests  # type: ignore[import-untyped]

from loto.integrations.maximo_adapter import MaximoAdapter


class DummyResponse:
    def __init__(self, data: Dict[str, Any], status_code: int = 200):
        self._data = data
        self.status_code = status_code
        self.headers: Dict[str, str] = {}

    def json(self) -> Dict[str, Any]:
        return self._data


def _set_env(monkeypatch) -> None:
    monkeypatch.setenv("MAXIMO_BASE_URL", "http://maximo.local")
    monkeypatch.setenv("MAXIMO_APIKEY", "secret")
    monkeypatch.setenv("MAXIMO_OS_WORKORDER", "WORKORDER")
    monkeypatch.setenv("MAXIMO_OS_ASSET", "ASSET")


def test_get_work_order(monkeypatch) -> None:
    _set_env(monkeypatch)

    def fake_get(url, headers=None, params=None, timeout=None):
        assert url == "http://maximo.local/os/WORKORDER/WO-1"
        assert headers == {"apikey": "secret"}
        assert timeout == (3.05, 10)
        return DummyResponse(
            {"id": "WO-1", "description": "Fix pump", "asset_id": "A-1"}
        )

    adapter = MaximoAdapter()
    monkeypatch.setattr(adapter._session, "get", fake_get)
    work_order = adapter.get_work_order("WO-1")
    assert work_order == {"id": "WO-1", "description": "Fix pump", "asset_id": "A-1"}


def test_list_open_work_orders(monkeypatch) -> None:
    _set_env(monkeypatch)

    def fake_get(url, headers=None, params=None, timeout=None):
        assert url == "http://maximo.local/os/WORKORDER"
        assert params == {"status": "OPEN", "window": 7}
        assert timeout == (3.05, 10)
        data = {
            "members": [
                {"id": "WO-1", "description": "A", "asset_id": "A-1"},
                {"id": "WO-2", "description": "B", "asset_id": "A-2"},
            ]
        }
        return DummyResponse(data)

    adapter = MaximoAdapter()
    monkeypatch.setattr(adapter._session, "get", fake_get)
    work_orders = adapter.list_open_work_orders(7)
    assert work_orders == [
        {"id": "WO-1", "description": "A", "asset_id": "A-1"},
        {"id": "WO-2", "description": "B", "asset_id": "A-2"},
    ]


def test_get_asset(monkeypatch) -> None:
    _set_env(monkeypatch)

    def fake_get(url, headers=None, params=None, timeout=None):
        assert url == "http://maximo.local/os/ASSET/A-1"
        assert timeout == (3.05, 10)
        return DummyResponse({"id": "A-1", "description": "Pump", "location": "LOC-1"})


def test_get_asset_timeout_retry(monkeypatch) -> None:
    _set_env(monkeypatch)

    calls: Dict[str, int] = {"count": 0}

    def fake_get(url, headers=None, params=None, timeout=None):
        calls["count"] += 1
        assert timeout == (3.05, 10)
        if calls["count"] == 1:
            raise requests.exceptions.ReadTimeout()
        assert url == "http://maximo.local/os/ASSET/A-1"
        return DummyResponse({"id": "A-1", "description": "Pump", "location": "LOC-1"})

    adapter = MaximoAdapter()
    monkeypatch.setattr(adapter._session, "get", fake_get)
    asset = adapter.get_asset("A-1")
    assert asset == {"id": "A-1", "description": "Pump", "location": "LOC-1"}
    assert calls["count"] == 2
