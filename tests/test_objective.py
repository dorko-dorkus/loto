import pytest

from loto.scheduling.objective import integrate_mwh, integrate_cost, objective


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
    assert objective(makespan, curve, lam, rho, deadline, price) == pytest.approx(expected)

    # when curve or price are empty the objective reduces to makespan + penalty
    assert objective(0.5, [], lam, rho, 1.0, price) == pytest.approx(0.5)
    assert objective(0.5, curve, lam, rho, 1.0, []) == pytest.approx(0.5 + lam * 0.0)

