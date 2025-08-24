from __future__ import annotations

from dataclasses import dataclass

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from loto.integrations.stores_adapter import DemoStoresAdapter
from loto.inventory import Reservation, StockItem, check_wo_parts_required

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
    blocked_by_parts: bool = Field(
        False, description="True if scheduling is blocked due to parts"
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

    return WorkOrderSummary(**data, blocked_by_parts=inv_status.blocked)


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
        summaries.append(WorkOrderSummary(**wo, blocked_by_parts=inv_status.blocked))
    kpis = [KpiItem(label="Open", value=len(summaries))]
    return PortfolioResponse(kpis=kpis, workOrders=summaries)
