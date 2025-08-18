"""Integration adapters for external systems.

This module defines abstract adapter interfaces for interacting with
external systems such as Maximo (CMMS), WAPR (permit-to-work), and
Coupa (procurement). Concrete implementations will be selected at
runtime based on environment variables and may perform actions such as
creating child work orders, attaching documents, or raising purchase
requisitions.

Only method signatures are provided here, to be fleshed out later.
"""

from __future__ import annotations

import abc
import os
from typing import TYPE_CHECKING, Any, Dict, List

from .coupa_adapter import CoupaAdapter, DemoCoupaAdapter
from .maximo_adapter import MaximoAdapter
from .stores_adapter import DemoStoresAdapter, StoresAdapter
from .wapr_adapter import DemoWaprAdapter, WaprAdapter

if TYPE_CHECKING:  # pragma: no cover - imported for type checking only
    from ..isolation_planner import IsolationPlan
    from ..models import SimReport


class IntegrationAdapter(abc.ABC):
    """Base class for integration adapters.

    Subclasses should implement the methods defined here to read
    necessary data from external systems and write back the outputs
    produced by the LOTO planner.
    """

    @abc.abstractmethod
    def fetch_work_order(self, work_order_id: str) -> Dict[str, Any]:
        """Retrieve minimal information about a work order."""

    @abc.abstractmethod
    def create_child_work_orders(
        self,
        parent_work_order_id: str,
        plan: IsolationPlan,
    ) -> List[str]:
        """Create child work orders for each isolation action and verification."""

    @abc.abstractmethod
    def attach_artifacts(
        self,
        parent_object_id: str,
        plan: IsolationPlan,
        sim_report: SimReport,
        as_json: Dict[str, Any],
        pdf_bytes: bytes,
    ) -> None:
        """Attach JSON and PDF artifacts to a work order or permit."""


from .demo_adapter import DemoIntegrationAdapter  # noqa: E402


def get_integration_adapter() -> IntegrationAdapter:
    """Return an adapter instance based on environment configuration.

    If required environment variables are missing, a
    :class:`DemoIntegrationAdapter` is returned.
    """

    required = [
        "MAXIMO_BASE_URL",
        "MAXIMO_APIKEY",
        "MAXIMO_OS_WORKORDER",
        "MAXIMO_OS_ASSET",
    ]

    if not all(os.environ.get(var) for var in required):
        return DemoIntegrationAdapter()

    # Placeholder: return demo adapter until a real one is available
    return DemoIntegrationAdapter()


__all__ = [
    "IntegrationAdapter",
    "DemoIntegrationAdapter",
    "get_integration_adapter",
    "CoupaAdapter",
    "DemoCoupaAdapter",
    "StoresAdapter",
    "DemoStoresAdapter",
    "WaprAdapter",
    "DemoWaprAdapter",
    "MaximoAdapter",
]
