import pytest

from loto.impact import unit_derate_curve
from loto.scheduling.objective import integrate_mwh


def test_unit_derate_curve_integral():
    start = 1.0
    end = 3.5
    mw = 20.0
    curve = unit_derate_curve(start, end, mw)
    assert integrate_mwh(curve) == pytest.approx(mw * (end - start))
