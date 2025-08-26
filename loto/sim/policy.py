"""Expected cost comparison for maintenance policies."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

from loto.impact import unit_derate_curve
from loto.integrations import get_permit_adapter
from loto.permits import permit_ready


@dataclass
class FailureModel:
    """Failure-time distribution model."""

    rate: float
    shape: float | None = None
    dist: Literal["exponential", "weibull"] = "exponential"

    def survival(self, t: float) -> float:
        """Return survival probability ``P(T > t)``."""

        if self.dist == "exponential":
            return math.exp(-self.rate * t)
        if self.shape is None:
            raise ValueError("shape required for weibull distribution")
        return math.exp(-((t / self.rate) ** self.shape))


def _downtime_cost(mw: float, hours: float, price_per_mwh: float) -> float:
    """Return cost of a derate ``mw`` for ``hours`` at ``price_per_mwh``."""

    curve = unit_derate_curve(0.0, hours, mw)
    loss = 0.0
    for (t1, m1), (t2, _) in zip(curve, curve[1:]):
        loss += (t2 - t1) * m1
    return loss * price_per_mwh


def compare_policies(
    model: FailureModel,
    *,
    tau: float,
    reactive_cost: float,
    secondary_damage: float,
    planned_cost: float,
    expedite_cost: float,
    price_per_mwh: float,
    derate_mw: float,
    downtime_hours: float,
    cbt_penalty: float,
    permit_id: str | None = None,
    permit_verified: bool = False,
    workorder_id: str | None = None,
) -> dict[str, float]:
    """Compare expected costs of RTF, plan-at-τ and expedite policies."""

    permit_delay = 0.0
    if not permit_ready(
        {"permit_id": permit_id, "permit_verified": int(permit_verified)}
    ):
        permit_delay = 24.0

    callback_min = 0.0
    if workorder_id:
        try:
            adapter = get_permit_adapter()
            permit = adapter.fetch_permit(workorder_id)
            callback_min = float(permit.get("callback_time_min", 0))
        except Exception:
            callback_min = 0.0

    rtf_hours = downtime_hours + permit_delay + callback_min / 60.0
    rtf_downtime = _downtime_cost(derate_mw, rtf_hours, price_per_mwh)
    rtf = reactive_cost + secondary_damage + rtf_downtime + cbt_penalty

    planned_hours = downtime_hours
    planned_downtime = _downtime_cost(derate_mw, planned_hours, price_per_mwh)
    planned_base = planned_cost + planned_downtime
    survive = model.survival(tau)
    plan = (1.0 - survive) * rtf + survive * planned_base

    exp_hours = downtime_hours
    exp_downtime = _downtime_cost(derate_mw, exp_hours, price_per_mwh)
    expedite = expedite_cost + exp_downtime

    return {"rtf": rtf, "plan": plan, "expedite": expedite}
