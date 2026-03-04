import importlib
from typing import Any

import pytest
from _pytest.monkeypatch import MonkeyPatch
from fastapi.testclient import TestClient

import apps.api.main as main
from apps.api.planning_service import WorkOrder, WorkOrderPlanBundle
from apps.api.schemas import ScheduleResponse
from loto.impact import ImpactResult
from loto.integrations.stores_adapter import DemoStoresAdapter
from loto.inventory import InventoryStatus, Reservation
from loto.models import IsolationAction, IsolationPlan
from loto.scheduling.des_engine import Task
from loto.service.blueprints import Provenance
from loto.service.scheduling import apply_duration_variability, monte_carlo_schedule
from tests.job_utils import wait_for_job


def _planner() -> main.OIDCUser:
    return main.OIDCUser(
        iss="iss", sub="sub", aud="aud", exp=0, iat=0, roles=["planner"]
    )


@pytest.fixture  # type: ignore[misc]
def planner_stub_bundle() -> WorkOrderPlanBundle:
    """Small deterministic 3-action bundle returned by the planner stub."""

    return WorkOrderPlanBundle(
        work_order=WorkOrder(
            id="WO-STUB",
            reservations=[Reservation(item_id="P-200", quantity=1, critical=True)],
        ),
        inv_status=InventoryStatus(blocked=False),
        parts_status={"P-200": "ok"},
        missing_part_details=[],
        plan=IsolationPlan(
            plan_id="stub-plan-3a",
            actions=[
                IsolationAction(
                    component_id="steam:S1->V1", method="lock", duration_s=1.0
                ),
                IsolationAction(
                    component_id="steam:V1->D1", method="lock", duration_s=1.0
                ),
                IsolationAction(
                    component_id="steam:D1->sink", method="tag", duration_s=1.0
                ),
            ],
        ),
        impact=ImpactResult(
            unavailable_assets=set(), unit_mw_delta={}, area_mw_delta={}
        ),
        provenance=Provenance(seed=7, rule_hash="f" * 64),
    )


@pytest.fixture  # type: ignore[misc]
def constrained_duration_tasks() -> dict[str, Task]:
    """Task graph with fixed integer durations and a tight shared resource."""

    return {
        "prep": Task(duration=9, resources={"crew": 1}),
        "isolate": Task(duration=11, resources={"crew": 1}),
        "verify": Task(
            duration=7,
            predecessors=["prep", "isolate"],
            resources={"crew": 1},
        ),
    }


def test_schedule_endpoint(monkeypatch: MonkeyPatch) -> None:
    importlib.reload(main)
    client = TestClient(main.app)
    monkeypatch.setattr(main, "authenticate_user", lambda *a, **kw: _planner())
    payload = {"workorder": "WO-1"}
    res = client.post("/schedule", json=payload, headers={"Authorization": "Bearer x"})
    assert res.status_code == 202
    job = res.json()["job_id"]
    data = wait_for_job(client, job)["result"]
    assert "schedule" in data
    assert len(data["schedule"]) > 0
    first = data["schedule"][0]
    assert {"date", "p10", "p50", "p90", "price", "hats"} <= first.keys()
    assert data["status"] == "feasible"
    assert data["provenance"]["plan_id"] == "UA"
    assert "plan_version" in data["provenance"]
    assert "plan_actions" in data["provenance"]
    assert data["provenance"]["random_seed"] == "0"
    assert (
        data["p10"] is not None and data["p50"] is not None and data["p90"] is not None
    )
    assert data["expected_makespan"] is not None
    assert data["rulepack_sha256"] == main.RULE_PACK_HASH


def test_schedule_not_blocked_with_stubbed_parts_check(
    monkeypatch: MonkeyPatch,
    planner_stub_bundle: WorkOrderPlanBundle,
) -> None:
    importlib.reload(main)
    client = TestClient(main.app)
    monkeypatch.setattr(main, "authenticate_user", lambda *a, **kw: _planner())
    monkeypatch.setattr(
        main,
        "load_work_order_plan",
        lambda *a, **kw: (planner_stub_bundle, {}),
    )

    res = client.post(
        "/schedule",
        json={"workorder": "WO-STUB"},
        headers={"Authorization": "Bearer x"},
    )
    assert res.status_code == 202
    job = res.json()["job_id"]
    data = wait_for_job(client, job)["result"]

    assert data["status"] == "feasible"
    assert data["p10"] <= data["p50"] <= data["p90"]
    assert data["provenance"]["plan_id"] == "stub-plan-3a"
    assert data["provenance"]["plan_actions"] == ",".join(
        ["steam:S1->V1:lock", "steam:V1->D1:lock", "steam:D1->sink:tag"]
    )
    assert data["provenance"]["random_seed"] == "0"
    assert data["provenance"]["sample_count"] == "200"
    assert data["provenance"]["resource_profile"] == "mech:2"
    assert data["provenance"]["simulation_config_id"] == "default-des-montecarlo"
    assert data["provenance"]["simulation_config_version"] == "1.0"


def test_schedule_honors_request_overrides(
    monkeypatch: MonkeyPatch,
    planner_stub_bundle: WorkOrderPlanBundle,
) -> None:
    importlib.reload(main)
    client = TestClient(main.app)
    monkeypatch.setattr(main, "authenticate_user", lambda *a, **kw: _planner())
    monkeypatch.setattr(
        main,
        "load_work_order_plan",
        lambda *a, **kw: (planner_stub_bundle, {}),
    )

    res = client.post(
        "/schedule",
        json={
            "workorder": "WO-STUB",
            "runs": 17,
            "resource_caps": {"elec": 1, "mech": 3},
            "seed": 42,
        },
        headers={"Authorization": "Bearer x"},
    )
    assert res.status_code == 202
    job = res.json()["job_id"]
    data = wait_for_job(client, job)["result"]
    assert data["provenance"]["random_seed"] == "42"
    assert data["provenance"]["sample_count"] == "17"
    assert data["provenance"]["resource_profile"] == "elec:1,mech:3"


def test_schedule_feasible_returns_ordered_percentiles_from_mc(
    monkeypatch: MonkeyPatch,
    planner_stub_bundle: WorkOrderPlanBundle,
) -> None:
    importlib.reload(main)
    client = TestClient(main.app)
    monkeypatch.setattr(main, "authenticate_user", lambda *a, **kw: _planner())
    monkeypatch.setattr(
        main,
        "load_work_order_plan",
        lambda *a, **kw: (planner_stub_bundle, {}),
    )

    res = client.post(
        "/schedule",
        json={"workorder": "WO-STUB", "seed": 21},
        headers={"Authorization": "Bearer x"},
    )
    assert res.status_code == 202
    job = res.json()["job_id"]
    data = wait_for_job(client, job)["result"]

    assert data["status"] == "feasible"
    assert len(data["schedule"]) >= 1
    assert data["p10"] <= data["p50"] <= data["p90"]
    assert data["expected_makespan"] > 0


def test_schedule_knob_change_shifts_p50(
    monkeypatch: MonkeyPatch,
    planner_stub_bundle: WorkOrderPlanBundle,
) -> None:
    importlib.reload(main)
    client = TestClient(main.app)
    monkeypatch.setattr(main, "authenticate_user", lambda *a, **kw: _planner())
    monkeypatch.setattr(
        main,
        "load_work_order_plan",
        lambda *a, **kw: (planner_stub_bundle, {}),
    )
    monkeypatch.setattr(
        main,
        "assemble_tasks",
        lambda *a, **kw: {
            "tasks": {
                "a": Task(duration=10, resources={"mech": 1}),
                "b": Task(duration=10, resources={"mech": 1}),
            },
            "parts_gate": {"blocked": False},
        },
    )

    base_payload = {"workorder": "WO-STUB", "seed": 42, "runs": 200}
    low_cap = client.post(
        "/schedule",
        json={**base_payload, "resource_caps": {"mech": 1}},
        headers={"Authorization": "Bearer x"},
    )
    assert low_cap.status_code == 202
    low_data = wait_for_job(client, low_cap.json()["job_id"])["result"]

    high_cap = client.post(
        "/schedule",
        json={**base_payload, "resource_caps": {"mech": 3}},
        headers={"Authorization": "Bearer x"},
    )
    assert high_cap.status_code == 202
    high_data = wait_for_job(client, high_cap.json()["job_id"])["result"]

    assert low_data["p50"] != high_data["p50"]
    assert low_data["p50"] > high_data["p50"]


def test_schedule_blocked_with_stubbed_parts_check(
    monkeypatch: MonkeyPatch,
    planner_stub_bundle: WorkOrderPlanBundle,
) -> None:
    importlib.reload(main)
    client = TestClient(main.app)
    monkeypatch.setattr(main, "authenticate_user", lambda *a, **kw: _planner())
    blocked_bundle = WorkOrderPlanBundle(
        work_order=planner_stub_bundle.work_order,
        inv_status=InventoryStatus(
            blocked=True,
            missing=[Reservation(item_id="P-200", quantity=1, critical=True)],
        ),
        parts_status={"P-200": "short"},
        missing_part_details=[
            {
                "item": "P-200",
                "required": 1,
                "available": 0,
                "shortfall": 1,
                "reason": "insufficient_available",
            }
        ],
        plan=planner_stub_bundle.plan,
        impact=planner_stub_bundle.impact,
        provenance=planner_stub_bundle.provenance,
    )
    monkeypatch.setattr(
        main, "load_work_order_plan", lambda *a, **kw: (blocked_bundle, {})
    )

    res = client.post(
        "/schedule?parts_block_policy=A",
        json={"workorder": "WO-STUB"},
        headers={"Authorization": "Bearer x"},
    )
    assert res.status_code == 202
    job = res.json()["job_id"]
    job_data = wait_for_job(client, job)
    assert job_data["status"] == "failed"
    assert job_data["result"]["status"] == "failed"
    assert job_data["result"]["error_code"] == "PARTS_BLOCKED"
    assert job_data["result"]["provenance"]["plan_id"] == "stub-plan-3a"
    assert job_data["result"]["missing_parts"] == [
        {
            "item": "P-200",
            "required": 1,
            "available": 0,
            "shortfall": 1,
            "reason": "insufficient_available",
        }
    ]
    assert "p10" not in job_data["result"]
    assert "p50" not in job_data["result"]
    assert "p90" not in job_data["result"]


def test_schedule_blocked_policy_a_skips_monte_carlo(
    monkeypatch: MonkeyPatch,
    planner_stub_bundle: WorkOrderPlanBundle,
) -> None:
    importlib.reload(main)
    client = TestClient(main.app)
    monkeypatch.setattr(main, "authenticate_user", lambda *a, **kw: _planner())
    blocked_bundle = WorkOrderPlanBundle(
        work_order=planner_stub_bundle.work_order,
        inv_status=InventoryStatus(
            blocked=True,
            missing=[Reservation(item_id="P-200", quantity=1, critical=True)],
        ),
        parts_status={"P-200": "short"},
        missing_part_details=[
            {
                "item": "P-200",
                "required": 1,
                "available": 0,
                "shortfall": 1,
                "reason": "insufficient_available",
            }
        ],
        plan=planner_stub_bundle.plan,
        impact=planner_stub_bundle.impact,
        provenance=planner_stub_bundle.provenance,
    )
    monkeypatch.setattr(
        main, "load_work_order_plan", lambda *a, **kw: (blocked_bundle, {})
    )

    def _unexpected_mc(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("monte_carlo_schedule should not run for policy A blocks")

    monkeypatch.setattr(main, "monte_carlo_schedule", _unexpected_mc)

    res = client.post(
        "/schedule?parts_block_policy=A",
        json={"workorder": "WO-STUB"},
        headers={"Authorization": "Bearer x"},
    )
    assert res.status_code == 202
    job = res.json()["job_id"]
    job_data = wait_for_job(client, job)
    assert job_data["status"] == "failed"
    assert job_data["result"]["error_code"] == "PARTS_BLOCKED"


def test_blueprint_and_schedule_share_plan_identity_and_actions(
    monkeypatch: MonkeyPatch,
) -> None:
    importlib.reload(main)
    client = TestClient(main.app)
    monkeypatch.setattr(main, "authenticate_user", lambda *a, **kw: _planner())

    blueprint_res = client.post("/blueprint", json={"workorder_id": "WO-1"})
    assert blueprint_res.status_code == 202
    blueprint_job = blueprint_res.json()["job_id"]
    blueprint_data = wait_for_job(client, blueprint_job)["result"]
    expected_actions = ",".join(
        f"{step['component_id']}:{step['method']}" for step in blueprint_data["steps"]
    )

    schedule_res = client.post(
        "/schedule",
        json={"workorder": "WO-1"},
        headers={"Authorization": "Bearer x"},
    )
    assert schedule_res.status_code == 202
    schedule_job = schedule_res.json()["job_id"]
    schedule_data = wait_for_job(client, schedule_job)["result"]
    provenance = schedule_data["provenance"]

    assert provenance["plan_id"] == "UA"
    assert provenance["plan_actions"] == expected_actions
    assert provenance["plan_version"]


def test_schedule_schema_requires_provenance_and_status_contract() -> None:
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        ScheduleResponse.model_validate(
            {
                "status": "feasible",
                "provenance": {"plan_id": "WO-1"},
                "schedule": [],
                "rulepack_sha256": "abc",
            }
        )


def test_schedule_inventory_gating_strict_forces_policy_a(
    monkeypatch: MonkeyPatch,
) -> None:
    importlib.reload(main)
    client = TestClient(main.app)
    monkeypatch.setattr(main, "authenticate_user", lambda *a, **kw: _planner())
    original = DemoStoresAdapter._INVENTORY["P-200"]["reorder_point"]
    try:
        DemoStoresAdapter._INVENTORY["P-200"]["reorder_point"] = 2
        res = client.post(
            "/schedule?strict=true&parts_block_policy=B",
            json={"workorder": "WO-1"},
            headers={"Authorization": "Bearer x"},
        )
        assert res.status_code == 202
        job = res.json()["job_id"]
        job_data = wait_for_job(client, job)
        assert job_data["status"] == "failed"
        assert job_data["result"]["error_code"] == "PARTS_BLOCKED"
    finally:
        DemoStoresAdapter._INVENTORY["P-200"]["reorder_point"] = original


def test_fixed_durations_are_seeded_and_spread_under_resource_constraints(
    constrained_duration_tasks: dict[str, Task],
) -> None:
    importlib.reload(main)

    wrapped = apply_duration_variability(constrained_duration_tasks)
    assert all(task.distribution is not None for task in wrapped.values())

    mc_a = monte_carlo_schedule(wrapped, {"crew": 1}, runs=300, seed=123)
    mc_b = monte_carlo_schedule(wrapped, {"crew": 1}, runs=300, seed=123)

    assert mc_a == mc_b
    assert (
        mc_a.makespan_percentiles["P10"]
        < mc_a.makespan_percentiles["P50"]
        < mc_a.makespan_percentiles["P90"]
    )


def test_duration_wrapper_preserves_existing_callable_tasks() -> None:
    importlib.reload(main)

    tasks = {
        "callable": Task(duration=lambda rng: rng.randint(1, 2)),
        "fixed": Task(duration=5),
    }

    wrapped = apply_duration_variability(tasks)

    assert wrapped["callable"] is tasks["callable"]
    assert wrapped["fixed"].distribution is not None
    assert wrapped["fixed"].base_duration == 5
