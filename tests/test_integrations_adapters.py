"""Tests for Coupa and Stores adapter stubs."""

from loto.integrations.coupa_adapter import DemoCoupaAdapter
from loto.integrations.stores_adapter import DemoStoresAdapter
from loto.integrations.wapr_adapter import DemoWaprAdapter


def test_coupa_demo_adapter_returns_rfq_id() -> None:
    """Simulate a shortage and ensure an RFQ identifier is produced."""
    available = 0
    needed = 5
    adapter = DemoCoupaAdapter()
    if available < needed:
        rfq_id = adapter.raise_urgent_enquiry("P-100", needed)
    else:
        rfq_id = ""
    assert rfq_id.startswith("RFQ-")


def test_stores_demo_adapter_returns_pick_list_id() -> None:
    """Simulate a shortage and ensure a pick list identifier is produced."""
    available = 0
    needed = 3
    adapter = DemoStoresAdapter()
    if available < needed:
        pick_id = adapter.create_pick_list("P-100", needed)
    else:
        pick_id = ""
    assert pick_id.startswith("PL-")


def test_wapr_demo_adapter_returns_fixture_permit() -> None:
    """Ensure fixture permit data is returned for a work order."""
    adapter = DemoWaprAdapter()
    permit = adapter.fetch_permit("WO-100")
    assert permit == {"applied_isolations": ["ISO-1", "ISO-2"]}
