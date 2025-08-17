import random

from loto.scheduling.expectation import estimate


def test_ci_shrinks_with_n():
    def sampler(seed: int) -> float:
        return random.Random(seed).random()

    small = estimate(sampler, max_runs=20, ci_threshold=0, p_targets=[0.5])
    large = estimate(sampler, max_runs=200, ci_threshold=0, p_targets=[0.5])

    assert small.samples == 20
    assert large.samples == 200
    assert large.ci_width < small.ci_width
    # P50 around median 0.5
    assert 0.25 < large.percentiles["P50"] < 0.75


def test_early_stopping_reported():
    def sampler(seed: int) -> float:
        return 5.0  # deterministic

    res = estimate(sampler, max_runs=100, ci_threshold=0.1)

    assert res.stopped_early
    assert res.samples < 100
    assert res.ci_width < 0.1
