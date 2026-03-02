import pytest

from loto.scheduling.des_engine import Task, run
from loto.scheduling.monte_carlo import (
    CalendarSpec,
    DurationDistribution,
    RunConfig,
    SimulationInput,
    SimulationTaskInput,
    simulate,
    simulate_input_model,
)


def test_percentiles_deterministic_schedule() -> None:
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


def test_percentiles_reflect_variability() -> None:
    tasks = {
        "a": Task(duration=lambda rng: rng.randint(1, 3)),
        "b": Task(duration=lambda rng: rng.randint(1, 4), predecessors=["a"]),
    }
    mc = simulate(tasks, {}, runs=200)

    assert mc.task_percentiles["a"]["P90"] > mc.task_percentiles["a"]["P50"]
    assert mc.task_percentiles["b"]["P90"] > mc.task_percentiles["b"]["P50"]
    assert mc.makespan_percentiles["P90"] > mc.makespan_percentiles["P50"]


def test_criticality_probability_on_dominant_path() -> None:
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


def test_simulate_seed_controls_repeatability() -> None:
    tasks = {
        "a": Task(duration=lambda rng: rng.randint(1, 3)),
        "b": Task(duration=lambda rng: rng.randint(1, 4), predecessors=["a"]),
    }

    result_a = simulate(tasks, {}, runs=100, seed=123)
    result_b = simulate(tasks, {}, runs=100, seed=123)
    result_c = simulate(tasks, {}, runs=100, seed=456)

    expected_makespans = [
        max(run(tasks, {}, seed=123 + i).ends.values()) for i in range(100)
    ]

    assert result_a == result_b
    assert result_a != result_c
    assert result_a.expected_makespan == pytest.approx(
        sum(expected_makespans) / len(expected_makespans)
    )


def test_input_model_aggregates_and_provenance_with_seed() -> None:
    sim_input = SimulationInput(
        tasks={
            "a": SimulationTaskInput(
                base_duration=4,
                distribution=DurationDistribution(kind="uniform", low=0.5, high=1.5),
                cost_per_time=10.0,
            ),
            "b": SimulationTaskInput(
                base_duration=2,
                predecessors=("a",),
                distribution=DurationDistribution(kind="uniform", low=0.8, high=1.2),
                cost_per_time=5.0,
            ),
        },
        resource_capacities={"mechanical": 1},
        calendars={"always_on": CalendarSpec(kind="always_on")},
        run_config=RunConfig(N=250, seed=42),
    )

    result_a = simulate_input_model(sim_input)
    result_b = simulate_input_model(sim_input)

    assert result_a.p10 <= result_a.p50 <= result_a.p90
    assert result_a.expected_makespan >= result_a.p10
    assert result_a.expected_cost is not None
    assert result_a.provenance["random_seed"] == "42"
    assert result_a.provenance["sample_count"] == "250"
    assert len(result_a.run_metrics) == 250
    assert result_a.p50 == result_b.p50
    assert result_a.expected_makespan == result_b.expected_makespan


def test_monotonic_lower_labor_capacity_worsens_p50() -> None:
    base_tasks = {
        "a": SimulationTaskInput(base_duration=3, resources={"labor": 1}),
        "b": SimulationTaskInput(base_duration=3, resources={"labor": 1}),
        "c": SimulationTaskInput(base_duration=3, predecessors=("a", "b")),
    }
    low_cap = SimulationInput(
        tasks=base_tasks,
        resource_capacities={"labor": 1},
        calendars={"always_on": CalendarSpec(kind="always_on")},
        run_config=RunConfig(N=220, seed=7),
    )
    high_cap = SimulationInput(
        tasks=base_tasks,
        resource_capacities={"labor": 2},
        calendars={"always_on": CalendarSpec(kind="always_on")},
        run_config=RunConfig(N=220, seed=7),
    )

    p50_low = simulate_input_model(low_cap).p50
    p50_high = simulate_input_model(high_cap).p50
    assert p50_low >= p50_high


def test_monotonic_more_plan_actions_worsens_p50() -> None:
    few_actions = SimulationInput(
        tasks={
            "a": SimulationTaskInput(base_duration=2),
            "b": SimulationTaskInput(base_duration=2, predecessors=("a",)),
        },
        resource_capacities={"labor": 2},
        calendars={"always_on": CalendarSpec(kind="always_on")},
        run_config=RunConfig(N=220, seed=11),
    )
    more_actions = SimulationInput(
        tasks={
            "a": SimulationTaskInput(base_duration=2),
            "b": SimulationTaskInput(base_duration=2, predecessors=("a",)),
            "c": SimulationTaskInput(base_duration=2, predecessors=("b",)),
            "d": SimulationTaskInput(base_duration=2, predecessors=("c",)),
        },
        resource_capacities={"labor": 2},
        calendars={"always_on": CalendarSpec(kind="always_on")},
        run_config=RunConfig(N=220, seed=11),
    )

    p50_few = simulate_input_model(few_actions).p50
    p50_more = simulate_input_model(more_actions).p50
    assert p50_more >= p50_few


def test_input_model_rejects_non_positive_sample_count() -> None:
    sim_input = SimulationInput(
        tasks={"a": SimulationTaskInput(base_duration=1)},
        resource_capacities={"labor": 1},
        calendars={"always_on": CalendarSpec(kind="always_on")},
        run_config=RunConfig(N=0, seed=1),
    )

    with pytest.raises(ValueError, match="run_config.N"):
        simulate_input_model(sim_input)
