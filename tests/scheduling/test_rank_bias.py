import pytest

from loto.scheduling.rank_bias import duration_with_rank


@pytest.mark.parametrize(
    "rank,multiplier",
    [
        (1, 1.0),
        (2, 1.025),
        (5, 1.1),
        (6, 1.1),  # cap reached
        (10, 1.1),  # cap maintained
    ],
)
def test_duration_with_rank(rank, multiplier):
    base = 10.0
    assert duration_with_rank(base, rank) == base * multiplier


def test_max_multiplier():
    base = 10.0
    assert duration_with_rank(base, 999) <= base * 1.1
