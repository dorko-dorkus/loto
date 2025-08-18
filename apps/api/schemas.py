from __future__ import annotations

from typing import Dict, List, Tuple

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


class TaskSpec(BaseModel):
    """Specification for a schedulable task."""

    duration: int = Field(..., description="Task duration in arbitrary units")
    predecessors: List[str] = Field(
        default_factory=list, description="IDs of prerequisite tasks"
    )

    class Config:
        extra = "forbid"


class ScheduleRequest(BaseModel):
    """Request body for the /schedule endpoint."""

    tasks: Dict[str, TaskSpec] = Field(
        default_factory=dict, description="Mapping of task ID to specification"
    )
    resource_caps: Dict[str, int] = Field(
        default_factory=dict, description="Resource capacity constraints"
    )
    runs: int = Field(10, description="Number of Monte Carlo simulations")
    seed: int | None = Field(None, description="Random seed for deterministic run")
    power_curve: List[Tuple[float, float]] | None = Field(
        default=None,
        description="Power curve as (time, MW) pairs for cost evaluation",
    )
    price_curve: List[Tuple[float, float]] | None = Field(
        default=None,
        description="Price curve as (time, price) pairs for cost evaluation",
    )

    class Config:
        extra = "forbid"


class ScheduleResponse(BaseModel):
    """Response model for the /schedule endpoint."""

    p10: float = Field(..., description="P10 percentile of makespan")
    p50: float = Field(..., description="P50 percentile of makespan")
    p90: float = Field(..., description="P90 percentile of makespan")
    expected_cost: float = Field(..., description="Expected cost of the schedule")
    violations: List[str] = Field(
        default_factory=list, description="List of violated task IDs"
    )
    seed: int = Field(..., description="Seed used for deterministic run")

    class Config:
        extra = "forbid"
