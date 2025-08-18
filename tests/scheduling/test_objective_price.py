import pytest

from loto.scheduling.objective import integrate_cost, objective


def test_cost_integral_known_curves():
    tri = [(0.0, 0.0), (1.0, 1.0), (2.0, 0.0)]
    price_const = [(0.0, 2.0), (2.0, 2.0)]
    assert integrate_cost(tri, price_const) == pytest.approx(2.0)

    step = [(0.0, 2.0), (3.0, 2.0)]
    price_ramp = [(0.0, 0.0), (3.0, 6.0)]
    assert integrate_cost(step, price_ramp) == pytest.approx(18.0)


def test_objective_uses_delta_cost():
    curve = [(0.0, 1.0), (1.0, 1.0)]
    price_lo = [(0.0, 1.0), (1.0, 1.0)]
    price_hi = [(0.0, 2.0), (1.0, 2.0)]
    lam = 4.0
    rho = 0.0
    base = objective(1.0, curve, lam, rho, price=price_lo)
    high = objective(1.0, curve, lam, rho, price=price_hi)
    delta_cost = integrate_cost(curve, price_hi) - integrate_cost(curve, price_lo)
    assert high - base == pytest.approx(lam * delta_cost)
