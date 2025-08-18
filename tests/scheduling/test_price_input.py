from pathlib import Path

import pytest

from loto.scheduling.price_input import load_price_curve
from loto.scheduling.objective import integrate_cost


def test_csv_loader_produces_expected_cost(tmp_path: Path) -> None:
    csv_path = tmp_path / "price.csv"
    csv_path.write_text(
        "timestamp,price\n"
        "2024-01-01T00:00:00,10\n"
        "2024-01-01T01:00:00,20\n"
        "2024-01-01T02:00:00,30\n"
    )

    price_curve = load_price_curve(csv_path)
    # constant 1 MW power over two hours
    power_curve = [(0.0, 1.0), (2.0, 1.0)]

    assert price_curve == [(0.0, 10.0), (1.0, 20.0), (2.0, 30.0)]
    cost = integrate_cost(power_curve, price_curve)
    assert cost == pytest.approx(40.0)
