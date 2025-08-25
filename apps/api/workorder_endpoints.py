from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from loto.integrations import get_permit_adapter
from loto.integrations.stores_adapter import DemoStoresAdapter
from loto.inventory import Reservation, StockItem, check_wo_parts_required
from loto.permits import StatusValidationError, validate_status_change

from .demo_data import demo_data


class WorkOrderSummary(BaseModel):
    """Simplified work order representation."""

    id: str = Field(..., description="Work order identifier")
    description: str = Field("", description="Work order description")
    status: str = Field("", description="Work order status")
    owner: str | None = Field(None, description="Work order owner")
    planned_start: str | None = Field(
        None, alias="plannedStart", description="Planned start date"
    )
    planned_finish: str | None = Field(
        None, alias="plannedFinish", description="Planned finish date"
    )
    assetnum: str | None = Field(None, description="Associated asset identifier")
    location: str | None = Field(None, description="Associated location identifier")
    maximo_wo: str | None = Field(
        None,
        alias="maximoWo",
        description="WO Number (Maximo)",
    )
    permit_id: str | None = Field(
        None,
        alias="permitId",
        description="Permit identifier",
        max_length=40,
    )
    permit_verified: bool | None = Field(
        False, alias="permitVerified", description="Permit has been verified"
    )
    permit_required: bool = Field(
        True, alias="permitRequired", description="Permit is required"
    )
    isolation_ref: str | None = Field(
        None,
        alias="isolationRef",
        description="Reference to isolation procedure",
        max_length=80,
    )
    blocked_by_parts: bool = Field(
        False, description="True if scheduling is blocked due to parts"
    )
    hold_reason: str | None = Field(
        None,
        alias="holdReason",
        description="Reason work order was placed on hold",
    )

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


def _summary_from_data(data: dict[str, Any], **extra: Any) -> WorkOrderSummary:
    """Create ``WorkOrderSummary`` from raw work order data."""

    clean = {k: v for k, v in data.items() if k not in {"attachments", "checklist"}}
    return WorkOrderSummary(**clean, **extra)


class StatusChangeRequest(BaseModel):
    """Payload for updating a work order's status."""

    new_status: str = Field(..., alias="status", description="New status value")
    current_status: str = Field(
        ..., alias="currentStatus", description="Current status value"
    )
    reason: str | None = Field(
        None, description="Reason for status change when applicable"
    )

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class KpiItem(BaseModel):
    """Basic KPI item."""

    label: str
    value: int

    model_config = ConfigDict(extra="forbid")


class PortfolioResponse(BaseModel):
    """Response model for the portfolio endpoint."""

    kpis: list[KpiItem] = Field(default_factory=list, description="Portfolio KPIs")
    work_orders: list[WorkOrderSummary] = Field(
        default_factory=list, alias="workOrders", description="Open work orders"
    )

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


router = APIRouter(tags=["workorders", "LOTO"])


@dataclass
class _WorkOrder:
    reservations: list[Reservation]


@router.get("/workorders/{workorder_id}", response_model=WorkOrderSummary)
async def get_workorder(workorder_id: str) -> WorkOrderSummary:
    """Fetch a work order from the integration adapter."""

    try:
        data = demo_data.get_work_order(workorder_id)
    except KeyError as exc:  # pragma: no cover - simple error path
        raise HTTPException(status_code=404, detail="work order not found") from exc
    asset = data.get("assetnum")
    if not asset or asset not in demo_data.asset_ids:
        raise HTTPException(status_code=400, detail=f"unknown asset: {asset}")
    loc = data.get("location")
    if not loc or loc not in demo_data.location_ids:
        raise HTTPException(status_code=400, detail=f"unknown location: {loc}")

    bom = demo_data.get_bom(workorder_id)
    work_order = _WorkOrder(
        reservations=[
            Reservation(
                item_id=line["item_id"],
                quantity=line["quantity"],
                critical=line.get("critical", False),
            )
            for line in bom
        ]
    )
    stores = DemoStoresAdapter()

    def lookup_stock(item_id: str) -> StockItem | None:
        try:
            status = stores.inventory_status(item_id)
        except KeyError:
            return None
        return StockItem(
            item_id=item_id,
            quantity=status.get("available", 0),
            reorder_point=status.get("reorder_point", 0),
        )

    inv_status = check_wo_parts_required(work_order, lookup_stock)

    return _summary_from_data(data, blocked_by_parts=inv_status.blocked)


@router.post(
    "/workorders/{workorder_id}/status",
    response_model=WorkOrderSummary,
)
async def update_workorder_status(
    workorder_id: str, payload: StatusChangeRequest
) -> WorkOrderSummary:
    """Update the status of a work order after validation."""

    try:
        data = demo_data.get_work_order(workorder_id)
    except KeyError as exc:  # pragma: no cover - simple error path
        raise HTTPException(status_code=404, detail="work order not found") from exc

    wo = {
        "permit_id": data.get("permitId"),
        "permit_verified": data.get("permitVerified"),
        "attachments": data.get("attachments", []),
        "id": workorder_id,
        "checklist": data.get("checklist", {}),
        "maximo_wo": data.get("maximoWo"),
    }
    # If configured, hard-check Ellipse before validation (gives better 4xx)
    if (
        os.getenv("REQUIRE_EXTERNAL_PERMIT", "0") in ("1", "true", "TRUE")
        and payload.new_status == "INPRG"
    ):
        adapter = get_permit_adapter()
        fetched = adapter.fetch_permit(workorder_id)
        if str(fetched.get("status", "")).lower() not in {
            "active",
            "authorised",
            "authorized",
            "issued",
        }:
            raise HTTPException(
                status_code=400, detail="External permit not active/authorised."
            )
    try:
        validate_status_change(
            wo, payload.current_status, payload.new_status, payload.reason
        )
    except StatusValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    data = dict(data)
    data["status"] = payload.new_status
    if payload.new_status == "HOLD":
        data["holdReason"] = payload.reason
    elif payload.new_status == "INPRG":
        data.pop("holdReason", None)
    return _summary_from_data(data)


@router.get("/portfolio", response_model=PortfolioResponse)
async def get_portfolio(window: int = 7) -> PortfolioResponse:
    """List open work orders and basic KPIs."""

    work_orders = demo_data.list_work_orders()
    summaries = []
    stores = DemoStoresAdapter()
    for wo in work_orders:
        bom = demo_data.get_bom(wo["id"])
        work_order = _WorkOrder(
            reservations=[
                Reservation(
                    item_id=line["item_id"],
                    quantity=line["quantity"],
                    critical=line.get("critical", False),
                )
                for line in bom
            ]
        )

        def lookup_stock(item_id: str) -> StockItem | None:
            try:
                status = stores.inventory_status(item_id)
            except KeyError:
                return None
            return StockItem(
                item_id=item_id,
                quantity=status.get("available", 0),
                reorder_point=status.get("reorder_point", 0),
            )

        inv_status = check_wo_parts_required(work_order, lookup_stock)
        summaries.append(_summary_from_data(wo, blocked_by_parts=inv_status.blocked))
    kpis = [KpiItem(label="Open", value=len(summaries))]
    return PortfolioResponse(kpis=kpis, workOrders=summaries)
