from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Iterable, List, Optional


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
