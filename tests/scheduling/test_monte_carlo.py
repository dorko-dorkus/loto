import pytest

from loto.scheduling.des_engine import Task, run
from loto.scheduling.monte_carlo import simulate


def test_percentiles_deterministic_schedule():
    tasks = {
        "t1": Task(duration=4),
        "t2": Task(duration=3, predecessors=["t1"]),
        "t3": Task(duration=2, predecessors=["t1"]),
    }
    mc = simulate(tasks, {}, runs=20)

    # percentiles collapse to single deterministic value
    for tid, pct in mc.task_percentiles.items():
        vals = set(pct.values())
        assert len(vals) == 1
        # Compare against single deterministic run
        end = run(tasks, {}).ends[tid]
        assert vals.pop() == end

    vals = set(mc.makespan_percentiles.values())
    assert len(vals) == 1
    assert vals.pop() == run(tasks, {}).ends["t2"]


def test_percentiles_reflect_variability():
    tasks = {
        "a": Task(duration=lambda rng: rng.randint(1, 3)),
        "b": Task(duration=lambda rng: rng.randint(1, 4), predecessors=["a"]),
    }
    mc = simulate(tasks, {}, runs=200)

    assert mc.task_percentiles["a"]["P90"] > mc.task_percentiles["a"]["P50"]
    assert mc.task_percentiles["b"]["P90"] > mc.task_percentiles["b"]["P50"]
    assert mc.makespan_percentiles["P90"] > mc.makespan_percentiles["P50"]


def test_criticality_probability_on_dominant_path():
    tasks = {
        "start": Task(duration=1),
        "b": Task(duration=2, predecessors=["start"]),
        "c": Task(duration=3, predecessors=["start"]),
        "end": Task(duration=1, predecessors=["b", "c"]),
    }
    mc = simulate(tasks, {}, runs=10)

    assert mc.criticality["start"] == pytest.approx(1.0)
    assert mc.criticality["c"] == pytest.approx(1.0)
    assert mc.criticality["end"] == pytest.approx(1.0)
    assert mc.criticality["b"] == pytest.approx(0.0)
