import pytest

from loto.models import IsolationAction, IsolationPlan
from loto.scheduling.assemble import (
    DEFAULT_BASELINE_DURATION_MIN,
    DEFAULT_RESOURCE_BUCKET,
    LOTO_COMPLETE_TASK_ID,
    RETURN_TO_SERVICE_COMPLETE_TASK_ID,
    WORK_COMPLETE_TASK_ID,
    build_isolation_tasks,
    build_job_dag,
    build_restoration_tasks,
    build_work_tasks,
    map_plan_tasks,
    planning_to_scheduler_tasks,
    validate_dag_acyclic,
)
from loto.scheduling.task_model import (
    DeterministicDurationSpec,
    PlanningTask,
    TriangularDurationSpec,
)


class _WO:
    def __init__(
        self,
        wo_id: str,
        tasks: list[dict[str, object]] | None = None,
        *,
        description: str | None = None,
        trade: str | None = None,
        job_steps: list[dict[str, object]] | None = None,
    ) -> None:
        self.id = wo_id
        self.tasks = tasks or []
        self.description = description
        self.trade = trade
        self.job_steps = job_steps


def _plan() -> IsolationPlan:
    return IsolationPlan(
        plan_id="plan-1",
        actions=[
            IsolationAction(component_id="A", method="lock", duration_s=None),
            IsolationAction(component_id="B", method="test", duration_s=1800),
            IsolationAction(component_id="C", method="verify", duration_s=None),
        ],
    )


def test_mapping_has_one_task_per_action() -> None:
    plan = _plan()
    tasks = map_plan_tasks(plan)

    assert len(tasks) == len(plan.actions)


def test_mapping_populates_resources_on_all_tasks() -> None:
    tasks = build_isolation_tasks(_plan())

    assert all(task.resources for task in tasks)
    assert all(task.resources == {DEFAULT_RESOURCE_BUCKET: 1} for task in tasks)


def test_mapping_dependencies_are_acyclic() -> None:
    dag = build_job_dag(_WO("wo-1"), _plan())

    validate_dag_acyclic(dag)


def test_validate_dag_acyclic_raises_for_cycle() -> None:
    tasks = [
        PlanningTask(
            task_id="a",
            kind="work",
            name="a",
            resources={"Mechanical": 1},
            duration=DeterministicDurationSpec(minutes=1),
            depends_on=["b"],
        ),
        PlanningTask(
            task_id="b",
            kind="work",
            name="b",
            resources={"Mechanical": 1},
            duration=DeterministicDurationSpec(minutes=1),
            depends_on=["a"],
        ),
    ]

    with pytest.raises(ValueError, match="contains a cycle"):
        validate_dag_acyclic(tasks)


def test_mapping_is_deterministic_for_same_input() -> None:
    plan = _plan()

    first = build_isolation_tasks(plan)
    second = build_isolation_tasks(plan)

    assert first == second
    assert isinstance(first[0].duration, TriangularDurationSpec)
    assert isinstance(first[1].duration, TriangularDurationSpec)
    assert first[0].duration.mode == DEFAULT_BASELINE_DURATION_MIN
    assert first[1].duration.mode == 30
    assert first[0].task_id == "plan-1-iso-0"


def test_planning_tasks_map_to_scheduler_tasks() -> None:
    scheduler_tasks = planning_to_scheduler_tasks(build_isolation_tasks(_plan()))

    assert set(scheduler_tasks) == {"plan-1-iso-0", "plan-1-iso-1", "plan-1-iso-2"}
    assert scheduler_tasks["plan-1-iso-1"].predecessors == ("plan-1-iso-0",)


def test_mapping_places_isolation_details_in_meta() -> None:
    tasks = build_isolation_tasks(_plan())

    assert tasks[0].name == "isolation-0"
    assert tasks[0].meta == {
        "action_index": 0,
        "method": "lock",
        "component_id": "A",
        "valve_tag": "A",
    }
    assert tasks[1].meta["valve_tag"] == "B"


def test_build_work_tasks_uses_single_fallback_for_empty_job_steps() -> None:
    tasks = build_work_tasks(
        _WO("wo-9", description="Replace pump seal", trade="mechanical", job_steps=[])
    )

    assert len(tasks) == 1
    assert tasks[0].task_id == "wo-9-work-0"
    assert tasks[0].name == "Replace pump seal"
    assert tasks[0].resources == {"mech": 1}
    assert tasks[0].duration.kind == "triangular"
    assert tasks[0].duration.min == 30
    assert tasks[0].duration.mode == 120
    assert tasks[0].duration.max == 360
    assert tasks[0].meta["default_work_task"] is True


def test_build_work_tasks_creates_one_task_per_job_step() -> None:
    tasks = build_work_tasks(
        _WO(
            "wo-11",
            job_steps=[
                {"description": "remove", "duration_s": 600},
                {"description": "install", "duration_s": 900},
            ],
        )
    )

    assert [task.task_id for task in tasks] == ["wo-11-work-0", "wo-11-work-1"]
    assert [task.name for task in tasks] == ["remove", "install"]


def test_build_restoration_tasks_mirror_actions() -> None:
    tasks = build_restoration_tasks(_plan(), _WO("wo-8"))

    assert [task.meta["restoration_component_id"] for task in tasks] == ["C", "B", "A"]


def test_build_job_dag_orders_phases() -> None:
    wo = _WO("wo-7", tasks=[{"description": "replace", "duration_s": 120}])
    dag = build_job_dag(wo, _plan())

    assert dag[0].kind == "isolation"
    assert any(task.kind == "work" for task in dag)
    assert dag[-1].task_id == RETURN_TO_SERVICE_COMPLETE_TASK_ID
    first_work = next(task for task in dag if task.kind == "work")
    assert LOTO_COMPLETE_TASK_ID in first_work.depends_on


def test_build_job_dag_includes_milestones_and_phase_dependencies() -> None:
    wo = _WO(
        "wo-10",
        tasks=[
            {"description": "replace", "duration_s": 120},
            {"description": "inspect", "duration_s": 180},
        ],
    )
    dag = build_job_dag(wo, _plan())

    by_id = {task.task_id: task for task in dag}
    loto_complete = by_id[LOTO_COMPLETE_TASK_ID]
    work_complete = by_id[WORK_COMPLETE_TASK_ID]
    return_to_service_complete = by_id[RETURN_TO_SERVICE_COMPLETE_TASK_ID]

    assert loto_complete.kind == "milestone"
    assert loto_complete.resources == {}
    assert loto_complete.duration.kind == "deterministic"
    assert loto_complete.duration.minutes == 1
    assert loto_complete.depends_on == [
        task.task_id for task in dag if task.kind == "isolation"
    ]

    work_tasks = [task for task in dag if task.kind == "work"]
    restoration_tasks = [task for task in dag if task.kind == "restoration"]
    assert all(LOTO_COMPLETE_TASK_ID in task.depends_on for task in work_tasks)
    assert work_complete.kind == "milestone"
    assert work_complete.depends_on == [task.task_id for task in work_tasks]
    assert all(WORK_COMPLETE_TASK_ID in task.depends_on for task in restoration_tasks)
    assert return_to_service_complete.depends_on == [
        task.task_id for task in restoration_tasks
    ]


def test_mapping_with_variability_uses_triangular_duration_spec_and_sampler() -> None:
    tasks = build_isolation_tasks(_plan(), duration_variability_ratio=0.2)

    assert tasks[0].duration.kind == "triangular"
    scheduler_task = planning_to_scheduler_tasks(tasks)["plan-1-iso-0"]
    assert callable(scheduler_task.duration)
    assert scheduler_task.distribution is not None
    assert scheduler_task.distribution.kind == "triangular"


def test_build_job_dag_has_stable_task_ids_and_barrier_dependencies() -> None:
    wo = _WO(
        "wo-12",
        job_steps=[
            {"description": "remove", "duration_s": 120},
            {"description": "replace", "duration_s": 180},
        ],
    )

    first = build_job_dag(wo, _plan())
    second = build_job_dag(wo, _plan())

    assert [task.task_id for task in first] == [task.task_id for task in second]

    by_id = {task.task_id: task for task in first}
    assert by_id["wo-12-work-0"].depends_on == [LOTO_COMPLETE_TASK_ID]
    assert by_id["wo-12-work-1"].depends_on == ["wo-12-work-0", LOTO_COMPLETE_TASK_ID]
    assert by_id[WORK_COMPLETE_TASK_ID].depends_on == ["wo-12-work-0", "wo-12-work-1"]
    assert by_id["wo-12-restore-0"].depends_on == [WORK_COMPLETE_TASK_ID]
