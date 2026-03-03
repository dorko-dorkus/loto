from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


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
    runs: int = Field(
        200,
        ge=1,
        strict=True,
        description="Number of Monte Carlo runs to execute",
    )
    resource_caps: Dict[str, int] = Field(
        default_factory=lambda: {"mech": 2},
        description="Resource capacity profile used for scheduling",
    )
    seed: int = Field(
        0,
        ge=0,
        strict=True,
        description="Deterministic random seed",
    )

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "workorder": "WO-1001",
                "runs": 200,
                "resource_caps": {"mech": 2},
                "seed": 0,
            }
        },
    )

    @model_validator(mode="after")
    def validate_resource_caps(self) -> "ScheduleRequest":
        if not self.resource_caps:
            raise ValueError("resource_caps must not be empty")
        if any(not key for key in self.resource_caps):
            raise ValueError("resource_caps keys must be non-empty")
        if any(
            not isinstance(value, int) or value < 1
            for value in self.resource_caps.values()
        ):
            raise ValueError("resource_caps values must be integers >= 1")
        return self


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

    status: Literal["feasible", "blocked_by_parts", "failed"] = Field(
        ..., description="Outcome status of the schedule request"
    )
    provenance: Dict[str, str] = Field(
        ...,
        description=(
            "Execution provenance including plan_id, simulation_config_id, "
            "simulation_config_version, and random_seed or seed_strategy"
        ),
    )
    schedule: List[SchedulePoint] = Field(
        default_factory=list, description="Synthetic schedule data"
    )
    p10: float | None = Field(None, description="P10 duration percentile")
    p50: float | None = Field(None, description="P50 duration percentile")
    p90: float | None = Field(None, description="P90 duration percentile")
    expected_makespan: float | None = Field(None, description="Expected total makespan")
    expected_cost: float | None = Field(None, description="Expected schedule cost")
    objective: float | None = Field(
        None, description="Objective value for the schedule"
    )
    missing_parts: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Machine-readable parts gate details (`item`, `required`, `available`, `shortfall`, `reason`)",
    )
    gating_reason: str | None = Field(
        None, description="Human-readable summary of the gating condition"
    )
    percentiles_conditional: bool = Field(
        False,
        description=(
            "Whether p10/p50/p90 values are conditional estimates that assume "
            "missing parts are resolved"
        ),
    )
    conditional_basis: str | None = Field(
        None,
        description=(
            "Machine-readable marker describing what assumptions were applied "
            "to conditional scheduling outputs"
        ),
    )
    error_code: str | None = Field(None, description="Machine-readable failure code")
    error_message: str | None = Field(
        None, description="Human-readable failure message"
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
                "status": "feasible",
                "provenance": {
                    "plan_id": "WO-1001",
                    "simulation_config_id": "default-des-montecarlo",
                    "simulation_config_version": "1.0",
                    "random_seed": "12345",
                    "seed_strategy": "deterministic",
                },
                "p10": 1.0,
                "p50": 2.0,
                "p90": 3.0,
                "expected_makespan": 2.0,
                "objective": 50.0,
                "rulepack_sha256": "abc123",
                "rulepack_id": "default",
                "rulepack_version": "1.0.0",
            }
        },
    )

    @model_validator(mode="after")
    def validate_status_contract(self) -> "ScheduleResponse":
        if self.status == "feasible":
            required = [self.p10, self.p50, self.p90, self.expected_makespan]
            if any(value is None for value in required):
                raise ValueError(
                    "feasible responses require p10, p50, p90, and expected_makespan"
                )
        if self.status == "blocked_by_parts" and not (
            self.missing_parts or self.gating_reason
        ):
            raise ValueError(
                "blocked_by_parts responses require missing_parts or gating_reason"
            )
        if (
            self.status == "blocked_by_parts"
            and any(value is not None for value in (self.p10, self.p50, self.p90))
            and not self.percentiles_conditional
        ):
            raise ValueError(
                "blocked_by_parts responses with percentiles must set percentiles_conditional=true"
            )
        if self.status == "failed" and not (self.error_code and self.error_message):
            raise ValueError("failed responses require error_code and error_message")
        required_provenance = {
            "plan_id",
            "simulation_config_id",
            "simulation_config_version",
        }
        if not required_provenance.issubset(self.provenance.keys()):
            raise ValueError(
                "provenance requires plan_id, simulation_config_id, and simulation_config_version"
            )
        if not ("random_seed" in self.provenance or "seed_strategy" in self.provenance):
            raise ValueError("provenance requires random_seed or seed_strategy")
        return self


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
    error: Dict[str, Any] | str | None = Field(
        None, description="Structured error payload if the job failed"
    )

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
