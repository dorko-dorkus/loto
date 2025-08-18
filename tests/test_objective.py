import pytest

from loto.scheduling.des_engine import Task
from loto.scheduling.monte import bands
from loto.scheduling.objective import integrate_cost, integrate_mwh, objective


def test_integrate_mwh_edge_cases():
    # empty and degenerate curves should integrate to zero
    assert integrate_mwh([]) == 0.0
    assert integrate_mwh([(0.0, 5.0)]) == 0.0

    # a single linear segment integrates to its rectangular area
    single = [(0.0, 4.0), (1.0, 4.0)]
    assert integrate_mwh(single) == pytest.approx(4.0)

    # also confirm behaviour on known non-trivial curves
    tri = [(0.0, 0.0), (1.0, 1.0), (2.0, 0.0)]
    step = [(0.0, 2.0), (3.0, 2.0)]
    assert integrate_mwh(tri) == pytest.approx(1.0)
    assert integrate_mwh(step) == pytest.approx(6.0)


def test_integrate_cost_edge_cases():
    price_const = [(0.0, 2.0), (1.0, 2.0)]

    # empty or underspecified curves yield zero cost
    assert integrate_cost([], price_const) == 0.0
    assert integrate_cost([(0.0, 1.0)], price_const) == 0.0
    assert integrate_cost([(0.0, 1.0), (1.0, 1.0)], [(0.0, 5.0)]) == 0.0

    # single segment with constant price
    curve = [(0.0, 2.0), (1.0, 2.0)]
    assert integrate_cost(curve, price_const) == pytest.approx(4.0)

    # interpolation across mismatched breakpoints
    curve_const = [(0.0, 1.0), (2.0, 1.0)]
    price_ramp = [(0.0, 1.0), (1.0, 2.0), (2.0, 3.0)]
    assert integrate_cost(curve_const, price_ramp) == pytest.approx(4.0)


def test_objective_weighted_and_penalty():
    curve = [(0.0, 1.0), (1.0, 1.0)]
    price = [(0.0, 2.0), (1.0, 2.0)]
    lam = 3.0
    rho = 4.0
    makespan = 1.0
    deadline = 0.5

    cost = integrate_cost(curve, price)
    expected = makespan + lam * cost + rho  # late penalty triggered
    assert objective(makespan, curve, lam, rho, deadline, price) == pytest.approx(
        expected
    )

    # when curve or price are empty the objective reduces to makespan + penalty
    assert objective(0.5, [], lam, rho, 1.0, price) == pytest.approx(0.5)
    assert objective(0.5, curve, lam, rho, 1.0, []) == pytest.approx(0.5 + lam * 0.0)


def test_bands_deterministic_schedule():
    tasks = {
        "a": Task(duration=2),
        "b": Task(duration=3, predecessors=["a"]),
    }
    price = [(0.0, 2.0), (10.0, 2.0)]
    result = bands(tasks, {}, runs=10, price_curve=price, seed=1)
    assert (
        result.finish_times["P10"]
        == result.finish_times["P50"]
        == result.finish_times["P90"]
        == 5.0
    )
    expected = integrate_cost([(0.0, 1.0), (5.0, 1.0)], price)
    assert result.expected_cost == pytest.approx(expected)


def test_bands_stable_with_seed():
    tasks = {
        "a": Task(duration=lambda rng: rng.randint(1, 3)),
        "b": Task(duration=(4, 1), predecessors=["a"]),
    }
    price = [(0.0, 1.0), (10.0, 1.0)]
    r1 = bands(tasks, {}, runs=50, price_curve=price, seed=42)
    r2 = bands(tasks, {}, runs=50, price_curve=price, seed=42)
    assert r1.finish_times == r2.finish_times
    assert r1.expected_cost == pytest.approx(r2.expected_cost)
    assert r1.finish_times["P10"] < r1.finish_times["P50"] < r1.finish_times["P90"]
