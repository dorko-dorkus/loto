from pathlib import Path
from typing import Any, Dict, cast

import pytest
import yaml

import loto.integrations.hats_adapter as hats_adapter
from loto.integrations.hats_adapter import (
    DemoHatsAdapter,
    HatsAdapter,
    HttpHatsAdapter,
)


def test_demo_hats_adapter_get_profile_keys() -> None:
    adapter: HatsAdapter = DemoHatsAdapter()
    profile = adapter.get_profile("DEMO-1")
    assert {"inductions", "competencies", "roster"} <= set(profile)


def test_hats_permit_map_loads() -> None:
    cfg = yaml.safe_load(Path("config/hats_permit_map.yaml").read_text())
    assert "ConfinedSpace" in cfg


def test_demo_hats_adapter_has_required() -> None:
    adapter: HatsAdapter = DemoHatsAdapter()
    ok, missing = adapter.has_required(["DEMO-1"], ["Electrical", "HighVoltage"])
    assert ok and not missing
    ok, missing = adapter.has_required(["DEMO-1"], ["ConfinedSpace"])
    assert not ok and missing == ["DEMO-1"]


def test_http_hats_adapter_profile_cache(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0
    fake_time = 1_000.0

    class DummyResp:
        def __init__(self, data: Dict[str, Any]) -> None:
            self._data = data

        def json(self) -> Dict[str, Any]:
            return self._data

        def raise_for_status(self) -> None:  # pragma: no cover - no-op
            return None

    def fake_get(url: str, headers: Dict[str, str], timeout: int) -> DummyResp:
        nonlocal calls
        calls += 1
        return DummyResp({"id": "H1"})

    monkeypatch.setattr(cast(Any, hats_adapter).requests, "get", fake_get)
    monkeypatch.setattr(cast(Any, hats_adapter).time, "time", lambda: fake_time)

    adapter = HttpHatsAdapter("http://example.com")

    adapter.get_profile("H1")
    assert calls == 1

    adapter.get_profile("H1")
    assert calls == 1
    assert adapter.cache_hits == 1

    monkeypatch.setattr(
        cast(Any, hats_adapter).time,
        "time",
        lambda: fake_time + adapter.profile_cache_ttl + 1,
    )

    adapter.get_profile("H1")
    assert calls == 2
