from loto.inventory import InventoryStatus
from loto.models import IsolationAction, IsolationPlan
from loto.scheduling.assemble import from_work_order
from loto.scheduling.des_engine import run


class _WO:
    def __init__(self, wo_id: str) -> None:
        self.id = wo_id
        self.reservations: list[object] = []


def test_tasks_wait_for_inventory_gate():
    wo = _WO("wo-1")
    plan = IsolationPlan(
        plan_id="p1",
        actions=[IsolationAction(component_id="c", method="lock", duration_s=1)],
    )

    status = InventoryStatus(blocked=True)

    def check_parts(_: object) -> InventoryStatus:
        return status

    tasks = from_work_order(wo, plan, check_parts)
    assert tasks["p1-0"].gate is not None

    state = {"parts": set()}
    if check_parts(wo).ready:
        state["parts"].add(wo.id)
    result = run(tasks, {}, state)
    assert "p1-0" not in result.starts

    status.blocked = False
    if check_parts(wo).ready:
        state["parts"].add(wo.id)
    result = run(tasks, {}, state)
    assert result.starts == {"p1-0": 0}
