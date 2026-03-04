from loto.inventory import InventoryStatus
from loto.models import IsolationAction, IsolationPlan
from loto.scheduling.des_engine import run
from loto.service import scheduling


class _WO:
    def __init__(self, wo_id: str) -> None:
        self.id = wo_id
        self.reservations: list[object] = []


def test_tasks_wait_for_inventory_gate() -> None:
    wo = _WO("wo-1")
    plan = IsolationPlan(
        plan_id="p1",
        actions=[IsolationAction(component_id="c", method="lock", duration_s=1)],
    )

    status = InventoryStatus(blocked=True)

    def check_parts(_: object) -> InventoryStatus:
        return status

    assembled = scheduling.assemble_tasks(wo, plan, check_parts=check_parts)
    tasks = assembled["tasks"]
    assert all(task.gate is not None for task in tasks.values())

    state: dict[str, set[str]] = {"parts": set()}
    if check_parts(wo).ready:
        state["parts"].add(wo.id)
    result = run(tasks, {}, state)
    assert not result.starts

    status.blocked = False
    if check_parts(wo).ready:
        state["parts"].add(wo.id)
    result = run(tasks, {}, state)
    assert result.starts
