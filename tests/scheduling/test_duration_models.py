import math

import numpy as np
import pytest

from loto.scheduling.duration_models import Lognormal, Triangular, make_sampler

N = 50_000


def _stats(sampler, seed=0):
    rng = np.random.default_rng(seed)
    samples = [sampler(rng) for _ in range(N)]
    return float(np.mean(samples)), float(np.std(samples))


def test_triangular_distribution_stats():
    a, m, b = 10.0, 20.0, 30.0
    sampler = Triangular(a, m, b)
    mean, stdev = _stats(sampler, seed=1)
    expected_mean = (a + m + b) / 3
    expected_var = (a * a + m * m + b * b - a * m - a * b - m * b) / 18
    expected_std = math.sqrt(expected_var)
    assert mean == pytest.approx(expected_mean, rel=0.02)
    assert stdev == pytest.approx(expected_std, rel=0.02)


def test_lognormal_distribution_stats():
    mu, sigma = 1.0, 0.5
    sampler = Lognormal(mu, sigma)
    mean, stdev = _stats(sampler, seed=2)
    expected_mean = math.exp(mu + sigma**2 / 2)
    expected_var = (math.exp(sigma**2) - 1) * math.exp(2 * mu + sigma**2)
    expected_std = math.sqrt(expected_var)
    assert mean == pytest.approx(expected_mean, rel=0.02)
    assert stdev == pytest.approx(expected_std, rel=0.02)


def test_make_sampler_scales_by_context():
    baseline = make_sampler("A", {"health": 1.0, "access": 1.0, "experience": 1.0})
    slowed = make_sampler("A", {"health": 0.5, "access": 1.0, "experience": 1.0})
    mean_base, _ = _stats(baseline, seed=3)
    mean_slowed, _ = _stats(slowed, seed=4)
    assert mean_slowed == pytest.approx(mean_base * 2.0, rel=0.05)
