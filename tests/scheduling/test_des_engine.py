from loto.scheduling.des_engine import Task, run


def test_deterministic_schedule_with_precedence():
    tasks = {
        "t1": Task(duration=4),
        "t2": Task(duration=3, predecessors=["t1"]),
        "t3": Task(duration=2, predecessors=["t1"]),
    }
    result = run(tasks, {})
    assert result.starts == {"t1": 0, "t2": 4, "t3": 4}
    assert result.ends == {"t1": 4, "t2": 7, "t3": 6}
    assert result.queues == {}
    assert result.violations == []


def test_queues_form_under_contention():
    tasks = {
        "a": Task(duration=3, resources={"crew": 1}),
        "b": Task(duration=2, resources={"crew": 1}),
        "c": Task(duration=1, resources={"crew": 1}),
    }
    result = run(tasks, {"crew": 1})
    assert result.starts == {"a": 0, "b": 3, "c": 5}
    assert result.ends == {"a": 3, "b": 5, "c": 6}
    assert result.queues == {"crew": ["b", "c"]}


def test_calendar_blocks_outside_work_windows():
    def cal(t: int) -> bool:
        return 5 <= t < 10

    tasks = {"a": Task(duration=2, calendar=cal)}
    result = run(tasks, {})
    assert result.starts == {"a": 5}
    assert result.ends == {"a": 7}
