from __future__ import annotations

from dataclasses import dataclass, field, replace
from functools import lru_cache
from pathlib import Path
from typing import Callable, Iterable, List, Mapping, Optional

import yaml


@dataclass
class StockItem:
    """Represents an item held in inventory."""

    item_id: str
    quantity: int


@dataclass
class Reservation:
    """Represents a quantity of a stock item required for a work order."""

    item_id: str
    quantity: int


@dataclass
class InventoryStatus:
    """Result of checking whether a work order can proceed based on stock levels."""

    blocked: bool
    missing: List[Reservation] = field(default_factory=list)

    @property
    def ready(self) -> bool:  # pragma: no cover - trivial property
        return not self.blocked


@dataclass
class InventoryRecord:
    """Detailed representation of an inventory row.

    These records are intentionally lightweight and primarily used by helper
    utilities that normalise unit descriptions and flag low stock.  The fields
    mirror the common columns present in scraped CSV exports.
    """

    description: str
    unit: str
    qty_onhand: int
    reorder_point: int
    site: str | None = None
    bin: str | None = None


_UNIT_MAP_PATH = Path(__file__).resolve().parents[1] / "config" / "inventory_units.yaml"


@lru_cache
def _load_unit_map() -> dict[str, str]:
    try:
        with _UNIT_MAP_PATH.open() as fh:
            data = yaml.safe_load(fh) or {}
    except FileNotFoundError:
        data = {}
    return {k.lower(): v for k, v in data.items()}


def ingest_inventory(records: Iterable[InventoryRecord]) -> list[InventoryRecord]:
    """Normalise units on ``records`` using configured mappings."""
    unit_map = _load_unit_map()
    normalised: list[InventoryRecord] = []
    for rec in records:
        unit = unit_map.get(rec.unit.lower(), rec.unit)
        normalised.append(replace(rec, unit=unit))
    return normalised


def normalize_units(
    records: Iterable[InventoryRecord], unit_map: Mapping[str, str]
) -> list[InventoryRecord]:
    """Return ``records`` with units normalised via ``unit_map``.

    Parameters
    ----------
    records:
        Inventory rows whose units may be inconsistent across sites or bins.
    unit_map:
        Mapping of item description to canonical unit string.
    """

    normalised: list[InventoryRecord] = []
    for rec in records:
        unit = unit_map.get(rec.description, rec.unit)
        normalised.append(replace(rec, unit=unit))
    return normalised


def reorder_flags(records: Iterable[InventoryRecord]) -> list[InventoryRecord]:
    """Return records at or below their reorder point."""

    return [rec for rec in records if rec.qty_onhand <= rec.reorder_point]


def check_wo_parts_required(
    work_order: object,
    lookup_stock: Callable[[str], Optional[StockItem]],
) -> InventoryStatus:
    """Determine if a work order has the required parts available.

    Parameters
    ----------
    work_order:
        Object containing a ``reservations`` attribute iterable of :class:`Reservation`.
    lookup_stock:
        Function returning a :class:`StockItem` given an item id.  Should return ``None``
        when the item is unknown.

    Returns
    -------
    InventoryStatus
        Status indicating whether execution is blocked due to missing parts.
    """

    reservations: Iterable[Reservation] = getattr(work_order, "reservations", [])
    missing: List[Reservation] = []

    for res in reservations:
        stock = lookup_stock(res.item_id)
        available = stock.quantity if stock else 0
        if available < res.quantity:
            missing.append(res)

    return InventoryStatus(blocked=bool(missing), missing=missing)
