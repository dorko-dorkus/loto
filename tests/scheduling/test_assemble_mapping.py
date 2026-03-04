from loto.models import IsolationAction, IsolationPlan
from loto.scheduling.assemble import (
    DEFAULT_BASELINE_DURATION_MIN,
    DEFAULT_RESOURCE_BUCKET,
    map_plan_tasks,
    planning_to_scheduler_tasks,
)
from loto.scheduling.task_model import PlanningTask


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
    tasks = map_plan_tasks(_plan())

    assert all(task.resources for task in tasks)
    assert all(task.resources == {DEFAULT_RESOURCE_BUCKET: 1} for task in tasks)


def test_mapping_dependencies_are_acyclic() -> None:
    tasks = map_plan_tasks(_plan())

    assert _is_acyclic(tasks)


def test_mapping_is_deterministic_for_same_input() -> None:
    plan = _plan()

    first = map_plan_tasks(plan)
    second = map_plan_tasks(plan)

    assert first == second
    assert first[0].duration.baseline_min == DEFAULT_BASELINE_DURATION_MIN
    assert first[1].duration.baseline_min == 30
    assert first[0].task_id == "plan-1-iso-0"


def test_planning_tasks_map_to_scheduler_tasks() -> None:
    scheduler_tasks = planning_to_scheduler_tasks(map_plan_tasks(_plan()))

    assert set(scheduler_tasks) == {"plan-1-iso-0", "plan-1-iso-1", "plan-1-iso-2"}
    assert scheduler_tasks["plan-1-iso-1"].predecessors == ("plan-1-iso-0",)
