from loto.service import scheduling
from loto.scheduling.des_engine import Task


def test_run_schedule_deterministic():
    tasks = {"t": Task(duration=lambda rng: rng.randint(1, 3))}
    res1 = scheduling.run_schedule(tasks, {}, seed=7)
    res2 = scheduling.run_schedule(tasks, {}, seed=7)
    assert res1 == res2


def test_monte_carlo_deterministic():
    tasks = {
        "a": Task(duration=lambda rng: rng.randint(1, 3)),
        "b": Task(duration=lambda rng: rng.randint(1, 3), predecessors=["a"]),
    }
    mc1 = scheduling.monte_carlo_schedule(tasks, {}, runs=5)
    mc2 = scheduling.monte_carlo_schedule(tasks, {}, runs=5)
    assert mc1 == mc2
