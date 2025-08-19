import pytest

from loto.scheduling.rank_bias import duration_with_rank


@pytest.mark.parametrize(
    "rank,multiplier",
    [
        (1, 1.0),
        (2, 1.1),
        (5, 1.4),
        (6, 1.5),  # cap reached
        (10, 1.5),  # cap maintained
    ],
)
def test_duration_with_rank(rank, multiplier):
    base = 10.0
    assert duration_with_rank(base, rank) == base * multiplier
