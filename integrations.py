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

from typing import List, Dict, Any

from .isolation_planner import IsolationPlan
from .sim_engine import SimReport


class IntegrationAdapter:
    """Base class for integration adapters.

    Subclasses should implement the methods defined here to read
    necessary data from external systems and write back the outputs
    produced by the LOTO planner.
    """

    def fetch_work_order(self, work_order_id: str) -> Dict[str, Any]:
        """Retrieve minimal information about a work order.

        Parameters
        ----------
        work_order_id: str
            Identifier of the work order to fetch.

        Returns
        -------
        Dict[str, Any]
            A dictionary containing fields needed by the planner (e.g.,
            asset tags, location, description). The exact schema is
            implementation-specific.
        """
        raise NotImplementedError("fetch_work_order is not implemented yet")

    def create_child_work_orders(
        self,
        parent_work_order_id: str,
        plan: IsolationPlan,
    ) -> List[str]:
        """Create child work orders for each isolation action and verification.

        Parameters
        ----------
        parent_work_order_id: str
            The parent work order to which the child work orders will be
            linked.
        plan: IsolationPlan
            The computed isolation plan.

        Returns
        -------
        List[str]
            A list of identifiers for the newly created child work orders.
        """
        raise NotImplementedError("create_child_work_orders is not implemented yet")

    def attach_artifacts(
        self,
        parent_object_id: str,
        plan: IsolationPlan,
        sim_report: SimReport,
        as_json: Dict[str, Any],
        pdf_bytes: bytes,
    ) -> None:
        """Attach JSON and PDF artifacts to a work order or permit.

        Parameters
        ----------
        parent_object_id: str
            Identifier of the object (work order or permit) to attach the
            artifacts to.
        plan: IsolationPlan
            The isolation plan.
        sim_report: SimReport
            The simulation report.
        as_json: Dict[str, Any]
            A JSON-serializable representation of the plan and report.
        pdf_bytes: bytes
            A PDF rendering of the plan and report.

        Notes
        -----
        This method should upload attachments via the appropriate API
        (e.g., Maximo's doclinks) or write them to disk in demo mode.
        """
        raise NotImplementedError("attach_artifacts is not implemented yet")