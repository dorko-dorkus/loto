"""Tests for integration adapter selection logic."""

from __future__ import annotations

from loto.integrations import (
    DemoIntegrationAdapter,
    MaximoAdapter,
    get_integration_adapter,
)


def test_returns_demo_adapter_when_maximo_env_missing(monkeypatch) -> None:
    """Demo adapter is used when any MAXIMO_* variable is missing."""
    for var in [
        "MAXIMO_BASE_URL",
        "MAXIMO_APIKEY",
        "MAXIMO_OS_WORKORDER",
        "MAXIMO_OS_ASSET",
    ]:
        monkeypatch.delenv(var, raising=False)
    adapter = get_integration_adapter()
    assert isinstance(adapter, DemoIntegrationAdapter)


def test_returns_maximo_adapter_when_env_present(monkeypatch) -> None:
    """Real adapter is returned when all MAXIMO_* variables are set."""
    monkeypatch.setenv("MAXIMO_BASE_URL", "https://example")
    monkeypatch.setenv("MAXIMO_APIKEY", "token")
    monkeypatch.setenv("MAXIMO_OS_WORKORDER", "WORKORDER")
    monkeypatch.setenv("MAXIMO_OS_ASSET", "ASSET")
    adapter = get_integration_adapter()
    assert isinstance(adapter, MaximoAdapter)
