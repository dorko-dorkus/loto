from collections.abc import Mapping

from loto.inventory import InventoryStatus, Reservation
from loto.models import IsolationAction, IsolationPlan
from loto.scheduling.des_engine import DurationDistribution, Task
from loto.service import scheduling


def test_run_schedule_deterministic() -> None:
    tasks = {"t": Task(duration=lambda rng: rng.randint(1, 3))}
    res1 = scheduling.run_schedule(tasks, {}, seed=7)
    res2 = scheduling.run_schedule(tasks, {}, seed=7)
    assert res1 == res2


def test_monte_carlo_deterministic() -> None:
    tasks = {
        "a": Task(duration=lambda rng: rng.randint(1, 3)),
        "b": Task(duration=lambda rng: rng.randint(1, 3), predecessors=["a"]),
    }
    mc1 = scheduling.monte_carlo_schedule(tasks, {}, runs=5, seed=10)
    mc2 = scheduling.monte_carlo_schedule(tasks, {}, runs=5, seed=10)
    mc3 = scheduling.monte_carlo_schedule(tasks, {}, runs=5, seed=11)
    assert mc1 == mc2
    assert mc1 != mc3


class _WO:
    def __init__(self, wo_id: str) -> None:
        self.id = wo_id
        self.reservations: list[object] = []


def test_assemble_tasks_feasible_gate_and_tasks() -> None:
    wo = _WO("wo-1")
    plan = IsolationPlan(
        plan_id="p1",
        actions=[IsolationAction(component_id="c", method="lock", duration_s=1)],
    )

    assembled = scheduling.assemble_tasks(
        wo,
        plan,
        check_parts=lambda _: InventoryStatus(blocked=False),
    )

    assert assembled["parts_gate"] == {"blocked": False, "status": "feasible"}
    assert assembled["missing_parts"] == []
    assert {"p1-iso-0", "wo-1-work-0", "wo-1-restore-0"}.issubset(assembled["tasks"])


def test_assemble_tasks_blocked_gate_and_missing_parts() -> None:
    wo = _WO("wo-1")
    plan = IsolationPlan(
        plan_id="p1",
        actions=[IsolationAction(component_id="c", method="lock", duration_s=1)],
    )
    status = InventoryStatus(
        blocked=True, missing=[Reservation(item_id="P-1", quantity=2)]
    )

    assembled = scheduling.assemble_tasks(wo, plan, check_parts=lambda _: status)

    assert assembled["parts_gate"] == {"blocked": True, "status": "blocked_by_parts"}
    assert assembled["missing_parts"] == [{"item_id": "P-1", "quantity": 2}]


def test_assemble_tasks_supports_optional_ddbb_verification_hook() -> None:
    wo = _WO("wo-1")
    plan = IsolationPlan(
        plan_id="p1",
        actions=[IsolationAction(component_id="c", method="lock", duration_s=1)],
        verifications=["Branch A DDBB cert"],
    )

    def verification_builder(
        _wo: object, _plan: IsolationPlan, tasks: Mapping[str, Task]
    ) -> Mapping[str, Task]:
        return {"p1-verify": Task(duration=1, predecessors=list(tasks))}

    assembled = scheduling.assemble_tasks(
        wo,
        plan,
        check_parts=lambda _: InventoryStatus(blocked=False),
        verification_task_builder=verification_builder,
    )

    assert "Branch A DDBB cert" in assembled["conditional"]["ddbb_candidates"]
    assert assembled["conditional"]["applied_verification_tasks"] == ["p1-verify"]
    assert "p1-verify" in assembled["tasks"]


def test_monte_carlo_two_isolation_plan_percentiles_ordered_with_seed() -> None:
    wo = _WO("wo-2")
    plan = IsolationPlan(
        plan_id="SH_2",
        actions=[
            IsolationAction(component_id="c1", method="lock", duration_s=1200),
            IsolationAction(component_id="c2", method="lock", duration_s=1800),
        ],
    )

    assembled = scheduling.assemble_tasks(wo, plan, duration_variability_ratio=0.2)
    result = scheduling.monte_carlo_schedule(assembled["tasks"], {}, runs=200, seed=42)

    assert result.makespan_percentiles["P10"] < result.makespan_percentiles["P50"]
    assert result.makespan_percentiles["P50"] < result.makespan_percentiles["P90"]


def test_monte_carlo_deterministic_distribution_can_collapse_percentiles() -> None:
    wo = _WO("wo-3")
    plan = IsolationPlan(
        plan_id="SH_2",
        actions=[
            IsolationAction(component_id="c1", method="lock", duration_s=1200),
            IsolationAction(component_id="c2", method="lock", duration_s=1800),
        ],
    )

    assembled = scheduling.assemble_tasks(wo, plan, duration_variability_ratio=0.0)
    fixed_tasks = {
        task_id: Task(
            duration=task.base_duration
            or (task.duration if isinstance(task.duration, int) else 1),
            predecessors=task.predecessors,
            resources=task.resources,
            calendar=task.calendar,
            gate=task.gate,
            base_duration=task.base_duration,
            distribution=DurationDistribution(kind="fixed"),
        )
        for task_id, task in assembled["tasks"].items()
    }

    result = scheduling.monte_carlo_schedule(fixed_tasks, {}, runs=20, seed=7)

    assert result.makespan_percentiles["P10"] == result.makespan_percentiles["P50"]
    assert result.makespan_percentiles["P50"] == result.makespan_percentiles["P90"]
