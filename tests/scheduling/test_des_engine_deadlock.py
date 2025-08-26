from loto.scheduling.des_engine import Task, run


def test_stalemate_cycle_detection() -> None:
    tasks = {
        "a": Task(duration=1, predecessors=["b"], resources={"crew": 1}),
        "b": Task(duration=1, predecessors=["a"], resources={"crew": 1}),
    }
    result = run(tasks, {"crew": 1})
    assert result.starts == {}
    assert result.ends == {}
    assert result.violations and "cycle detected" in result.violations[0]


def test_idle_limit_break() -> None:
    tasks = {"a": Task(duration=1, calendar=lambda t: False)}
    result = run(tasks, {}, idle_limit=5)
    assert result.starts == {}
    assert result.ends == {}
    assert result.violations and "idle limit" in result.violations[0]
