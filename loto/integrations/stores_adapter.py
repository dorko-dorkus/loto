"""Stores warehouse adapter stubs.

This module defines an abstract interface for creating pick lists in the
warehouse and a demo implementation used for dry runs.
"""

from __future__ import annotations

import abc
import uuid


class StoresAdapter(abc.ABC):
    """Abstract interface for warehouse interactions."""

    @abc.abstractmethod
    def create_pick_list(self, part_number: str, quantity: int) -> str:
        """Create a pick list for the requested part.

        Parameters
        ----------
        part_number:
            Identifier for the part to be picked.
        quantity:
            Number of units to pick.

        Returns
        -------
        str
            Identifier of the generated pick list.
        """


class DemoStoresAdapter(StoresAdapter):
    """Dry-run stores adapter that fabricates pick list identifiers."""

    def create_pick_list(self, part_number: str, quantity: int) -> str:
        """Simulate creating a pick list and return its identifier."""
        return f"PL-{uuid.uuid4().hex[:8]}"
