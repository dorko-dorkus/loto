from loto.models import IsolationAction, IsolationPlan
from loto.scheduling.assemble import (
    DEFAULT_BASELINE_DURATION_MIN,
    DEFAULT_RESOURCE_BUCKET,
    MappedTask,
    map_plan_tasks,
)


def _plan() -> IsolationPlan:
    return IsolationPlan(
        plan_id="plan-1",
        actions=[
            IsolationAction(component_id="A", method="lock", duration_s=None),
            IsolationAction(component_id="B", method="test", duration_s=1800),
            IsolationAction(component_id="C", method="verify", duration_s=None),
        ],
    )


def _is_acyclic(tasks: list[MappedTask]) -> bool:
    ids = {task.id for task in tasks}
    indegree: dict[str, int] = {task.id: 0 for task in tasks}
    graph: dict[str, list[str]] = {task.id: [] for task in tasks}

    for task in tasks:
        for dep in task.dependencies:
            if dep in ids:
                graph[dep].append(task.id)
                indegree[task.id] += 1

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
    assert all(task.resources == (DEFAULT_RESOURCE_BUCKET,) for task in tasks)


def test_mapping_dependencies_are_acyclic() -> None:
    tasks = map_plan_tasks(_plan())

    assert _is_acyclic(tasks)


def test_mapping_is_deterministic_for_same_input() -> None:
    plan = _plan()

    first = map_plan_tasks(plan)
    second = map_plan_tasks(plan)

    assert first == second
    assert first[0].baseline_duration_min == DEFAULT_BASELINE_DURATION_MIN
    assert first[1].baseline_duration_min == 30
