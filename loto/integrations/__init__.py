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

from .coupa_adapter import CoupaAdapter, DemoCoupaAdapter, HttpCoupaAdapter
from .ellipse_adapter import DemoEllipseAdapter, EllipseAdapter, HttpEllipseAdapter
from .hats_adapter import DemoHatsAdapter, HatsAdapter, HttpHatsAdapter
from .maximo_adapter import MaximoAdapter
from .stores_adapter import DemoStoresAdapter, StoresAdapter
from .wapr_adapter import DemoWaprAdapter, WaprAdapter

if TYPE_CHECKING:  # pragma: no cover - imported for type checking only
    from ..models import IsolationPlan, SimReport


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


def get_integration_adapter() -> IntegrationAdapter | MaximoAdapter:
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
    if all(os.environ.get(var) for var in required):
        return MaximoAdapter()
    return DemoIntegrationAdapter()


def get_permit_adapter() -> EllipseAdapter | WaprAdapter:
    """Select a permit adapter based on environment configuration.

    ``PERMIT_PROVIDER`` controls which system to target and may be set to
    ``ELLIPSE``, ``WAPR`` or ``DEMO`` (the default). For the Ellipse provider,
    ``ELLIPSE_MODE`` determines whether the demo or HTTP adapter is used. When
    ``ELLIPSE_MODE=HTTP``, the variables ``ELLIPSE_BASE_URL``,
    ``ELLIPSE_USERNAME`` and ``ELLIPSE_PASSWORD`` must also be provided.

    The WAPR provider currently only supports ``WAPR_MODE=DEMO``; selecting
    ``HTTP`` will raise :class:`NotImplementedError`.
    """

    provider = os.getenv("PERMIT_PROVIDER", "DEMO").upper()
    if provider == "ELLIPSE":
        mode = os.getenv("ELLIPSE_MODE", "DEMO").upper()
        if mode == "HTTP":
            return HttpEllipseAdapter()
        return DemoEllipseAdapter()
    if provider == "WAPR":
        mode = os.getenv("WAPR_MODE", "DEMO").upper()
        if mode == "HTTP":
            raise NotImplementedError("HTTP WAPR adapter not implemented")
        return DemoWaprAdapter()
    return DemoEllipseAdapter()


def get_hats_adapter() -> HatsAdapter:
    """Return a HATS adapter based on environment configuration."""

    base_url = os.getenv("HATS_BASE_URL")
    if base_url:
        return HttpHatsAdapter(base_url, os.getenv("HATS_API_KEY"))
    return DemoHatsAdapter()


__all__ = [
    "IntegrationAdapter",
    "DemoIntegrationAdapter",
    "get_integration_adapter",
    "get_permit_adapter",
    "get_hats_adapter",
    "CoupaAdapter",
    "DemoCoupaAdapter",
    "HttpCoupaAdapter",
    "StoresAdapter",
    "DemoStoresAdapter",
    "WaprAdapter",
    "DemoWaprAdapter",
    "EllipseAdapter",
    "DemoEllipseAdapter",
    "HttpEllipseAdapter",
    "HatsAdapter",
    "DemoHatsAdapter",
    "HttpHatsAdapter",
    "MaximoAdapter",
]
