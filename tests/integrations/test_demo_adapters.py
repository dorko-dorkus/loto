"""Smoke tests for demo integration adapters.

These tests validate the default return shapes and basic error handling of

the demo adapters.  The adapters perform no external calls and only return
fixture data.
"""

from __future__ import annotations

from datetime import datetime

import pytest

from loto.integrations.coupa_adapter import DemoCoupaAdapter
from loto.integrations.stores_adapter import DemoStoresAdapter
from loto.integrations.wapr_adapter import DemoWaprAdapter


def test_wapr_reserve_window_returns_identifier() -> None:
    """A reservation identifier is produced for a valid window."""
    adapter = DemoWaprAdapter()
    start = datetime(2024, 1, 1, 8)
    end = datetime(2024, 1, 1, 9)
    reservation = adapter.reserve_window(start, end)
    assert reservation.startswith("RES-")


def test_wapr_reserve_window_invalid() -> None:
    """Invalid windows raise a ValueError."""
    adapter = DemoWaprAdapter()
    start = datetime(2024, 1, 1, 9)
    end = datetime(2024, 1, 1, 8)
    with pytest.raises(ValueError):
        adapter.reserve_window(start, end)


def test_wapr_list_conflicts_returns_list() -> None:
    """Conflicts are returned as a list of work order identifiers."""
    adapter = DemoWaprAdapter()
    start = datetime(2024, 1, 1, 8)
    end = datetime(2024, 1, 1, 9)
    conflicts = adapter.list_conflicts(start, end)
    assert conflicts and all(isinstance(c, str) for c in conflicts)


def test_wapr_get_price_curve_shape() -> None:
    """Price curves are lists of ``(hour, price)`` pairs."""
    adapter = DemoWaprAdapter()
    curve = adapter.get_price_curve("ASSET-1")
    assert isinstance(curve, list)
    assert curve and isinstance(curve[0], tuple)


def test_wapr_get_price_curve_unknown() -> None:
    """Unknown assets raise a ``KeyError``."""
    adapter = DemoWaprAdapter()
    with pytest.raises(KeyError):
        adapter.get_price_curve("UNKNOWN")


def test_coupa_po_status_fixture() -> None:
    """Fixture purchase order statuses are returned."""
    adapter = DemoCoupaAdapter()
    status = adapter.get_po_status("PO-1")
    assert status in {"OPEN", "CLOSED"}


def test_coupa_po_status_unknown() -> None:
    """Unknown purchase orders raise ``KeyError``."""
    adapter = DemoCoupaAdapter()
    with pytest.raises(KeyError):
        adapter.get_po_status("PO-999")


def test_stores_inventory_status_fixture() -> None:
    """Inventory status includes an ``available`` quantity."""
    adapter = DemoStoresAdapter()
    status = adapter.inventory_status("P-100")
    assert "available" in status


def test_stores_inventory_status_unknown() -> None:
    """Unknown assets raise ``KeyError``."""
    adapter = DemoStoresAdapter()
    with pytest.raises(KeyError):
        adapter.inventory_status("P-999")
