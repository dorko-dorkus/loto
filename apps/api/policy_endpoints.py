from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

from loto.sim import FailureModel, compare_policies

router = APIRouter(prefix="/policy", tags=["policy", "LOTO"])


class PolicyRequest(BaseModel):
    tau: float
    reactive_cost: float
    secondary_damage: float
    planned_cost: float
    expedite_cost: float
    price_per_mwh: float
    derate_mw: float
    downtime_hours: float
    cbt_penalty: float
    failure_rate: float
    shape: float | None = None
    distribution: Literal["exponential", "weibull"] = "exponential"
    workorder_id: str | None = None
    permit_id: str | None = None
    permit_verified: bool = False


class PolicyResponse(BaseModel):
    rtf: float
    plan: float
    expedite: float


@router.post("", response_model=PolicyResponse)
async def post_policy(payload: PolicyRequest) -> PolicyResponse:
    model = FailureModel(
        rate=payload.failure_rate, shape=payload.shape, dist=payload.distribution
    )
    costs = compare_policies(
        model,
        tau=payload.tau,
        reactive_cost=payload.reactive_cost,
        secondary_damage=payload.secondary_damage,
        planned_cost=payload.planned_cost,
        expedite_cost=payload.expedite_cost,
        price_per_mwh=payload.price_per_mwh,
        derate_mw=payload.derate_mw,
        downtime_hours=payload.downtime_hours,
        cbt_penalty=payload.cbt_penalty,
        permit_id=payload.permit_id,
        permit_verified=payload.permit_verified,
        workorder_id=payload.workorder_id,
    )
    return PolicyResponse(**costs)
