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

    class Config:
        extra = "forbid"
