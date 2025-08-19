from __future__ import annotations

from typing import Dict, List

from pydantic import BaseModel, Field


class BlueprintRequest(BaseModel):
    """Request body for the /blueprint endpoint."""

    workorder_id: str = Field(..., description="Identifier of the work order")

    class Config:
        extra = "forbid"


class Step(BaseModel):
    """Single isolation step in the computed plan."""

    component_id: str = Field(..., description="Component identifier")
    method: str = Field(..., description="Isolation method")

    class Config:
        extra = "forbid"


class BlueprintResponse(BaseModel):
    """Response model for the /blueprint endpoint."""

    steps: List[Step] = Field(
        default_factory=list, description="Ordered isolation steps"
    )
    unavailable_assets: List[str] = Field(
        default_factory=list, description="Assets that became unavailable"
    )
    unit_mw_delta: Dict[str, float] = Field(
        default_factory=dict, description="Lost capacity per unit in MW"
    )
    blocked_by_parts: bool = Field(
        False, description="Whether execution is blocked due to missing parts"
    )
    parts_status: Dict[str, str] = Field(
        default_factory=dict, description="Inventory status per material line"
    )

    class Config:
        extra = "forbid"


class ScheduleRequest(BaseModel):
    """Request body for the /schedule endpoint."""

    workorder: str = Field(..., description="Identifier of the work order")

    class Config:
        extra = "forbid"


class SchedulePoint(BaseModel):
    """Single datapoint in the returned schedule."""

    date: str = Field(..., description="ISO formatted date")
    p10: float = Field(..., description="P10 duration percentile")
    p50: float = Field(..., description="P50 duration percentile")
    p90: float = Field(..., description="P90 duration percentile")
    price: float = Field(..., description="Energy price for the interval")
    hats: int = Field(..., description="Crew size (number of hard hats)")

    class Config:
        extra = "forbid"


class ScheduleResponse(BaseModel):
    """Response model for the /schedule endpoint."""

    schedule: List[SchedulePoint] = Field(
        default_factory=list, description="Synthetic schedule data"
    )
    seed: str = Field(..., description="Seed used for deterministic simulation")
    objective: float = Field(..., description="Objective value for the schedule")

    class Config:
        extra = "forbid"
