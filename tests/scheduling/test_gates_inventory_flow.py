from loto.inventory import InventoryStatus
from loto.models import IsolationAction, IsolationPlan
from loto.service import scheduling
from loto.service.blueprints import inventory_state


class _WO:
    def __init__(self, wo_id: str) -> None:
        self.id = wo_id
        self.reservations: list[object] = []


def test_inventory_gate_flow() -> None:
    wo = _WO("wo-1")
    plan = IsolationPlan(
        plan_id="p1",
        actions=[IsolationAction(component_id="c", method="lock", duration_s=1)],
    )

    status = InventoryStatus(blocked=True)

    def check_parts(_: object) -> InventoryStatus:
        return status

    assembled = scheduling.assemble_tasks(wo, plan, check_parts)
    tasks = assembled["tasks"]
    state = inventory_state(wo, check_parts)
    result = scheduling.run_schedule(tasks, {}, state=state)
    assert "p1-iso-0" not in result.starts

    status.blocked = False
    state = inventory_state(wo, check_parts, state)
    result = scheduling.run_schedule(tasks, {}, state=state)
    assert result.starts.get("p1-iso-0") == 0
    assert "wo-1-work-0" in result.starts
    assert "wo-1-restore-0" in result.starts
