from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

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

    class Config:
        extra = "forbid"
        allow_population_by_field_name = True


class KpiItem(BaseModel):
    """Basic KPI item."""

    label: str
    value: int

    class Config:
        extra = "forbid"


class PortfolioResponse(BaseModel):
    """Response model for the portfolio endpoint."""

    kpis: list[KpiItem] = Field(default_factory=list, description="Portfolio KPIs")
    work_orders: list[WorkOrderSummary] = Field(
        default_factory=list, alias="workOrders", description="Open work orders"
    )

    class Config:
        extra = "forbid"
        allow_population_by_field_name = True


router = APIRouter(tags=["workorders", "LOTO"])


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
    return WorkOrderSummary(**data)


@router.get("/portfolio", response_model=PortfolioResponse)
async def get_portfolio(window: int = 7) -> PortfolioResponse:
    """List open work orders and basic KPIs."""

    work_orders = demo_data.list_work_orders()
    summaries = [WorkOrderSummary(**wo) for wo in work_orders]
    kpis = [KpiItem(label="Open", value=len(summaries))]
    return PortfolioResponse(kpis=kpis, work_orders=summaries)
