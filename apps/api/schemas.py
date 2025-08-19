from __future__ import annotations

from datetime import datetime
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
    blocked_by_parts: bool = Field(
        False,
        description="Whether execution is blocked due to missing parts",
    )
    rulepack_sha256: str = Field(
        ..., description="SHA-256 digest of the rule pack used"
    )
    rulepack_id: str | None = Field(None, description="Identifier of the rule pack")
    rulepack_version: str | None = Field(None, description="Version of the rule pack")

    class Config:
        extra = "forbid"


class HatKpiRequest(BaseModel):
    """Payload for recording hat KPI metrics."""

    wo_id: str = Field(..., description="Work order identifier")
    hat_id: str = Field(..., description="Hat identifier")
    SA: float = Field(..., description="Safety metric A")
    SP: float = Field(..., description="Safety metric P")
    RQ: float | None = Field(None, description="Optional RQ metric")
    OF: float | None = Field(None, description="Optional OF metric")

    class Config:
        extra = "forbid"


class HatSnapshot(BaseModel):
    """Snapshot of ranking information for a hat."""

    hat_id: str = Field(..., description="Identifier of the hat")
    rank: int = Field(0, description="Rank among hats (1 = best)")
    c_r: float = Field(0.5, description="Ranking coefficient")
    n_samples: int = Field(0, description="Number of KPI events")
    last_event_at: datetime | None = Field(
        None,
        description="Timestamp of the most recent event",
    )

    class Config:
        extra = "forbid"
