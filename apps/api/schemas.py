from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal

from pydantic import BaseModel, ConfigDict, Field


class BlueprintRequest(BaseModel):
    """Request body for the /blueprint endpoint."""

    workorder_id: str = Field(..., description="Identifier of the work order")

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": {"workorder_id": "WO-1001"}},
    )


class Step(BaseModel):
    """Single isolation step in the computed plan."""

    component_id: str = Field(..., description="Component identifier")
    method: str = Field(..., description="Isolation method")

    model_config = ConfigDict(extra="forbid")


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

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "steps": [
                    {"component_id": "VALVE-1", "method": "lock"},
                    {"component_id": "BREAKER-2", "method": "tag"},
                ],
                "unavailable_assets": ["GENERATOR-3"],
                "unit_mw_delta": {"UNIT-1": -1.5},
                "blocked_by_parts": False,
                "parts_status": {"MAT-1": "available"},
            }
        },
    )


class CommitRequest(BaseModel):
    """Request body for the /commit endpoint."""

    sim_ok: bool = Field(..., alias="simOk", description="Simulation run is green")
    policies: Dict[str, bool] = Field(
        default_factory=dict, description="Policy chip acknowledgements"
    )

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class ScheduleRequest(BaseModel):
    """Request body for the /schedule endpoint."""

    workorder: str = Field(..., description="Identifier of the work order")

    model_config = ConfigDict(
        extra="forbid", json_schema_extra={"example": {"workorder": "WO-1001"}}
    )


class SchedulePoint(BaseModel):
    """Single datapoint in the returned schedule."""

    date: str = Field(..., description="ISO formatted date")
    p10: float = Field(..., description="P10 duration percentile")
    p50: float = Field(..., description="P50 duration percentile")
    p90: float = Field(..., description="P90 duration percentile")
    price: float = Field(..., description="Energy price for the interval")
    hats: int = Field(..., description="Crew size (number of hard hats)")

    model_config = ConfigDict(extra="forbid")


class ScheduleResponse(BaseModel):
    """Response model for the /schedule endpoint."""

    schedule: List[SchedulePoint] = Field(
        default_factory=list, description="Synthetic schedule data"
    )
    seed: str = Field(..., description="Seed used for deterministic simulation")
    objective: float = Field(..., description="Objective value for the schedule")
    blocked_by_parts: bool = Field(
        False, description="Whether execution is blocked due to missing parts"
    )
    rulepack_sha256: str = Field(
        ..., description="SHA-256 digest of the rule pack used"
    )
    rulepack_id: str | None = Field(None, description="Identifier of the rule pack")
    rulepack_version: str | None = Field(None, description="Version of the rule pack")

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "schedule": [
                    {
                        "date": "2024-05-01",
                        "p10": 1.0,
                        "p50": 2.0,
                        "p90": 3.0,
                        "price": 100.0,
                        "hats": 2,
                    }
                ],
                "seed": "12345",
                "objective": 50.0,
                "blocked_by_parts": False,
                "rulepack_sha256": "abc123",
                "rulepack_id": "default",
                "rulepack_version": "1.0.0",
            }
        },
    )


class JobInfo(BaseModel):
    """Response returned when a job is enqueued."""

    job_id: str = Field(..., description="Identifier for the submitted job")

    model_config = ConfigDict(extra="forbid")


class JobStatus(BaseModel):
    """Status information for a background job."""

    status: Literal["queued", "running", "done", "failed"] = Field(
        ..., description="Current state of the job"
    )
    result: Dict[str, Any] | None = Field(
        None, description="Result payload when the job has completed"
    )
    error: str | None = Field(None, description="Error message if the job failed")

    model_config = ConfigDict(extra="forbid")


class HatKpiRequest(BaseModel):
    """Payload for recording hat KPI metrics."""

    wo_id: str = Field(..., description="Work order identifier")
    hat_id: str = Field(..., description="Hat identifier")
    SA: float = Field(..., description="Safety metric A")
    SP: float = Field(..., description="Safety metric P")
    RQ: float | None = Field(None, description="Optional RQ metric")
    OF: float | None = Field(None, description="Optional OF metric")

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "wo_id": "WO-1001",
                "hat_id": "HAT-7",
                "SA": 0.9,
                "SP": 0.8,
                "RQ": 0.7,
                "OF": 0.6,
            }
        },
    )


class HatSnapshot(BaseModel):
    """Snapshot of ranking information for a hat."""

    hat_id: str = Field(..., description="Identifier of the hat")
    rank: int = Field(0, description="Rank among hats (1 = best)")
    c_r: float = Field(0.5, description="Ranking coefficient")
    n_samples: int = Field(0, description="Number of KPI events")
    last_event_at: datetime | None = Field(
        None, description="Timestamp of the most recent event"
    )

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "hat_id": "HAT-7",
                "rank": 1,
                "c_r": 0.75,
                "n_samples": 10,
                "last_event_at": "2024-05-01T12:00:00Z",
            }
        },
    )
