from loto.scheduling.des_engine import Task, run
from loto.scheduling.gates import parts_available


def test_task_waits_for_parts_gate():
    gate = parts_available("wo-1")
    tasks = {
        "prep": Task(duration=3),
        "aux": Task(duration=2),
        "main": Task(duration=1, predecessors=["prep"], gate=gate),
    }

    state = {"parts": set()}
    result = run(tasks, {}, state)
    assert result.starts == {"prep": 0, "aux": 0}
    assert result.ends == {"aux": 2, "prep": 3}
    assert result.violations == ["main"]
    assert "main" not in result.starts

    state["parts"].add("wo-1")
    result = run(tasks, {}, state)
    assert result.starts == {"prep": 0, "aux": 0, "main": 3}
    assert result.ends == {"aux": 2, "prep": 3, "main": 4}
    assert result.violations == []
