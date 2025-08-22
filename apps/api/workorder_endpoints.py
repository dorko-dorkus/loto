from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from loto.integrations.maximo_adapter import MaximoAdapter


class WorkOrderSummary(BaseModel):
    """Simplified work order representation."""

    id: str = Field(..., description="Work order identifier")
    description: str = Field("", description="Work order description")
    asset_id: str = Field("", description="Related asset identifier")

    class Config:
        extra = "forbid"


class KpiItem(BaseModel):
    """Basic KPI item."""

    label: str
    value: int

    class Config:
        extra = "forbid"


class PortfolioResponse(BaseModel):
    """Response model for the portfolio endpoint."""

    kpis: list[KpiItem] = Field(default_factory=list, description="Portfolio KPIs")
    workorders: list[WorkOrderSummary] = Field(
        default_factory=list, description="Open work orders"
    )

    class Config:
        extra = "forbid"


router = APIRouter(tags=["workorders", "LOTO"])


@router.get("/workorders/{workorder_id}", response_model=WorkOrderSummary)
async def get_workorder(workorder_id: str) -> WorkOrderSummary:
    """Fetch a work order from the integration adapter."""

    adapter = MaximoAdapter()
    try:
        data = adapter.get_work_order(workorder_id)
    except Exception as exc:  # pragma: no cover - adapter errors handled generically
        raise HTTPException(
            status_code=502, detail="failed to fetch work order"
        ) from exc
    return WorkOrderSummary(**data)


@router.get("/portfolio", response_model=PortfolioResponse)
async def get_portfolio(window: int = 7) -> PortfolioResponse:
    """List open work orders and basic KPIs."""

    adapter = MaximoAdapter()
    try:
        work_orders = adapter.list_open_work_orders(window)
    except Exception as exc:  # pragma: no cover
        raise HTTPException(
            status_code=502, detail="failed to list work orders"
        ) from exc
    summaries = [WorkOrderSummary(**wo) for wo in work_orders]
    kpis = [KpiItem(label="Open", value=len(summaries))]
    return PortfolioResponse(kpis=kpis, workorders=summaries)
