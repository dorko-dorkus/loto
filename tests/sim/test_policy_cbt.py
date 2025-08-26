from datetime import datetime

import pytest

import loto.sim.policy as policy


class AdapterFast:
    def cbt_minutes(self, craft: str, site: str, when: datetime) -> int:
        return 0


class AdapterSlow:
    def __init__(self, t_fail: datetime) -> None:
        self.t_fail = t_fail

    def cbt_minutes(self, craft: str, site: str, when: datetime) -> int:
        return 60 if when == self.t_fail else 0


def test_high_reactive_cbt_discourages_rtf(monkeypatch: pytest.MonkeyPatch) -> None:
    t_fail = datetime(2024, 1, 1)
    model = policy.FailureModel(rate=0.001)

    monkeypatch.setattr(policy, "get_hats_adapter", lambda: AdapterFast())
    costs = policy.compare_policies(
        model,
        tau=1.0,
        reactive_cost=0.0,
        secondary_damage=0.0,
        planned_cost=0.5,
        expedite_cost=5.0,
        price_per_mwh=1.0,
        derate_mw=1.0,
        downtime_hours=1.0,
        cbt_penalty=0.0,
        craft="ELEC",
        site="SITE-A",
        t_fail=t_fail,
        permit_id="p1",
        permit_verified=True,
    )
    assert min(costs, key=lambda k: costs[k]) == "rtf"

    monkeypatch.setattr(policy, "get_hats_adapter", lambda: AdapterSlow(t_fail))
    costs = policy.compare_policies(
        model,
        tau=1.0,
        reactive_cost=0.0,
        secondary_damage=0.0,
        planned_cost=0.5,
        expedite_cost=5.0,
        price_per_mwh=1.0,
        derate_mw=1.0,
        downtime_hours=1.0,
        cbt_penalty=0.0,
        craft="ELEC",
        site="SITE-A",
        t_fail=t_fail,
        permit_id="p1",
        permit_verified=True,
    )
    assert min(costs, key=lambda k: costs[k]) == "plan"
