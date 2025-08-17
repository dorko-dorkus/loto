import pytest

from loto.scheduling.objective import integrate_mwh, objective


def test_integral_toy_curves():
    tri = [(0.0, 0.0), (1.0, 1.0), (2.0, 0.0)]
    step = [(0.0, 2.0), (3.0, 2.0)]
    assert integrate_mwh(tri) == pytest.approx(1.0)
    assert integrate_mwh(step) == pytest.approx(6.0)


def test_penalty_toggle():
    curve = [(0.0, 0.0), (1.0, 0.0)]
    lam = 0.0
    rho = 5.0
    deadline = 5.0
    assert objective(4.0, curve, lam, rho, deadline) == pytest.approx(4.0)
    assert objective(6.0, curve, lam, rho, deadline) == pytest.approx(6.0 + rho)
