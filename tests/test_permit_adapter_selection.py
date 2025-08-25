"""Tests for permit adapter selection logic."""

from __future__ import annotations

import pytest

from loto.integrations import (
    DemoEllipseAdapter,
    DemoWaprAdapter,
    HttpEllipseAdapter,
    get_permit_adapter,
)


def test_default_returns_demo_ellipse(monkeypatch: pytest.MonkeyPatch) -> None:
    """Demo Ellipse adapter is used by default."""
    monkeypatch.delenv("PERMIT_PROVIDER", raising=False)
    monkeypatch.delenv("ELLIPSE_MODE", raising=False)
    adapter = get_permit_adapter()
    assert isinstance(adapter, DemoEllipseAdapter)


def test_ellipse_http_selected(monkeypatch: pytest.MonkeyPatch) -> None:
    """HTTP Ellipse adapter is returned when configured."""
    monkeypatch.setenv("PERMIT_PROVIDER", "ELLIPSE")
    monkeypatch.setenv("ELLIPSE_MODE", "HTTP")
    monkeypatch.setenv("ELLIPSE_BASE_URL", "https://example")
    monkeypatch.setenv("ELLIPSE_USERNAME", "u")
    monkeypatch.setenv("ELLIPSE_PASSWORD", "p")
    adapter = get_permit_adapter()
    assert isinstance(adapter, HttpEllipseAdapter)


def test_wapr_demo_selected(monkeypatch: pytest.MonkeyPatch) -> None:
    """Demo WAPR adapter is returned when provider=WAPR."""
    monkeypatch.setenv("PERMIT_PROVIDER", "WAPR")
    monkeypatch.setenv("WAPR_MODE", "DEMO")
    adapter = get_permit_adapter()
    assert isinstance(adapter, DemoWaprAdapter)


def test_wapr_http_not_implemented(monkeypatch: pytest.MonkeyPatch) -> None:
    """WAPR HTTP mode currently raises NotImplementedError."""
    monkeypatch.setenv("PERMIT_PROVIDER", "WAPR")
    monkeypatch.setenv("WAPR_MODE", "HTTP")
    with pytest.raises(NotImplementedError):
        get_permit_adapter()
