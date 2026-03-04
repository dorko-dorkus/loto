from loto.models import IsolationAction, IsolationPlan
from loto.scheduling.assemble import (
    DEFAULT_BASELINE_DURATION_MIN,
    DEFAULT_RESOURCE_BUCKET,
    build_isolation_tasks,
    build_job_dag,
    build_restoration_tasks,
    build_work_tasks,
    map_plan_tasks,
    planning_to_scheduler_tasks,
)
from loto.scheduling.task_model import PlanningTask


class _WO:
    def __init__(
        self, wo_id: str, tasks: list[dict[str, object]] | None = None
    ) -> None:
        self.id = wo_id
        self.tasks = tasks or []


def _plan() -> IsolationPlan:
    return IsolationPlan(
        plan_id="plan-1",
        actions=[
            IsolationAction(component_id="A", method="lock", duration_s=None),
            IsolationAction(component_id="B", method="test", duration_s=1800),
            IsolationAction(component_id="C", method="verify", duration_s=None),
        ],
    )


def _is_acyclic(tasks: list[PlanningTask]) -> bool:
    ids = {task.task_id for task in tasks}
    indegree: dict[str, int] = {task.task_id: 0 for task in tasks}
    graph: dict[str, list[str]] = {task.task_id: [] for task in tasks}

    for task in tasks:
        for dep in task.depends_on:
            if dep in ids:
                graph[dep].append(task.task_id)
                indegree[task.task_id] += 1

    queue: list[str] = [tid for tid, deg in indegree.items() if deg == 0]
    visited = 0
    while queue:
        node = queue.pop(0)
        visited += 1
        for nxt in graph[node]:
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                queue.append(nxt)

    return visited == len(tasks)


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

    assert _is_acyclic(dag)


def test_mapping_is_deterministic_for_same_input() -> None:
    plan = _plan()

    first = build_isolation_tasks(plan)
    second = build_isolation_tasks(plan)

    assert first == second
    assert first[0].duration.baseline_min == DEFAULT_BASELINE_DURATION_MIN
    assert first[1].duration.baseline_min == 30
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


def test_build_work_tasks_uses_default_when_no_details() -> None:
    tasks = build_work_tasks(_WO("wo-9"))

    assert len(tasks) == 1
    assert tasks[0].task_id == "wo-9-work-0"
    assert tasks[0].meta["default_work_task"] is True


def test_build_restoration_tasks_mirror_actions() -> None:
    tasks = build_restoration_tasks(_plan(), _WO("wo-8"))

    assert [task.meta["restoration_component_id"] for task in tasks] == ["C", "B", "A"]


def test_build_job_dag_orders_phases() -> None:
    wo = _WO("wo-7", tasks=[{"description": "replace", "duration_s": 120}])
    dag = build_job_dag(wo, _plan())

    assert dag[0].kind == "isolation"
    assert any(task.kind == "work" for task in dag)
    assert dag[-1].kind == "restoration"
    first_work = next(task for task in dag if task.kind == "work")
    assert first_work.depends_on == ["plan-1-iso-2"]
