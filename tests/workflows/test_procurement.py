"""Tests for the procurement workflow."""

from loto.workflows.procurement import procure_shortages


def test_procurement_branches_and_status() -> None:
    """Ensure shortages route to the correct adapter."""
    shortages: list[dict[str, int | str]] = [
        {"part_number": "P-1", "quantity": 5, "action": "purchase"},
        {"part_number": "P-2", "quantity": 3, "action": "issue"},
    ]
    actions, status = procure_shortages(shortages, dry_run=True)
    assert actions[0]["action"] == "raise_urgent_enquiry"
    assert actions[0]["id"].startswith("RFQ-")
    assert actions[1]["action"] == "create_pick_list"
    assert actions[1]["id"].startswith("PL-")
    assert status == "dry-run"


def test_procurement_idempotency_key() -> None:
    """Verify idempotency key combines action, part and quantity."""
    shortages: list[dict[str, int | str]] = [
        {"part_number": "P-3", "quantity": 2, "action": "issue"}
    ]
    actions, _ = procure_shortages(shortages, dry_run=True)
    assert actions[0]["idempotency_key"] == "issue:P-3:2"
