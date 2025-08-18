"""Procurement workflow utilities."""

from __future__ import annotations

from typing import Iterable

from loto.integrations.coupa_adapter import CoupaAdapter, DemoCoupaAdapter
from loto.integrations.stores_adapter import DemoStoresAdapter, StoresAdapter


def procure_shortages(
    shortages: Iterable[dict[str, int | str]],
    coupa_adapter: CoupaAdapter | None = None,
    stores_adapter: StoresAdapter | None = None,
    dry_run: bool = False,
) -> tuple[list[dict[str, str]], str]:
    """Process shortages via Coupa or Stores adapters.

    Parameters
    ----------
    shortages:
        Iterable of shortage dictionaries with keys ``part_number``,
        ``quantity`` and ``action``.  ``action`` must be either
        ``"purchase"`` to raise an urgent enquiry or ``"issue`` to create a
        pick list.
    coupa_adapter:
        Adapter used when raising urgent enquiries.  If ``None`` or ``dry_run``
        is true, :class:`DemoCoupaAdapter` is used.
    stores_adapter:
        Adapter used when issuing pick lists.  If ``None`` or ``dry_run`` is
        true, :class:`DemoStoresAdapter` is used.
    dry_run:
        When true, demo adapters are used and the returned status will be
        ``"dry-run"``.

    Returns
    -------
    tuple[list[dict[str, str]], str]
        A tuple containing a list of action dictionaries and a status string.
    """
    if dry_run or coupa_adapter is None:
        coupa_adapter = DemoCoupaAdapter()
    if dry_run or stores_adapter is None:
        stores_adapter = DemoStoresAdapter()

    actions: list[dict[str, str]] = []
    for item in shortages:
        part_number = str(item["part_number"])
        quantity = int(item["quantity"])
        action_type = str(item.get("action", "purchase"))
        idempotency_key = f"{action_type}:{part_number}:{quantity}"

        if action_type == "purchase":
            rfq_id = coupa_adapter.raise_urgent_enquiry(part_number, quantity)
            actions.append(
                {
                    "action": "raise_urgent_enquiry",
                    "id": rfq_id,
                    "idempotency_key": idempotency_key,
                }
            )
        else:
            pick_id = stores_adapter.create_pick_list(part_number, quantity)
            actions.append(
                {
                    "action": "create_pick_list",
                    "id": pick_id,
                    "idempotency_key": idempotency_key,
                }
            )

    status = "dry-run" if dry_run else "completed"
    return actions, status
