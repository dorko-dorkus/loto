import math
from datetime import datetime

from loto.roster.metrics import HatRank, HatScore, KpiEvent, ewma, rank_bands, shrink


def test_ewma_half_life():
    """After one half-life the previous value contributes half the weight."""
    result = ewma(previous=0.0, observation=1.0, dt=2.0, half_life=2.0)
    assert math.isclose(result, 0.5, rel_tol=1e-9)


def test_shrink_and_cap():
    """Shrinkage moves extreme rates toward the prior and respects caps."""
    # Without cap the incident rate would be 1.0
    shrunk = shrink(incidents=5, total=5, prior=0.5, weight=1.0)
    assert 0.5 < shrunk < 1.0

    capped = shrink(incidents=10, total=10, prior=0.5, weight=1.0, cap=5)
    assert math.isclose(capped, shrink(5, 10, prior=0.5, weight=1.0))


def test_rank_bands():
    bands = [(0.8, "green"), (0.5, "amber"), (0.0, "red")]
    assert rank_bands(0.9, bands) == "green"
    assert rank_bands(0.7, bands) == "amber"
    assert rank_bands(0.2, bands) == "red"


def test_models_instantiation():
    now = datetime.utcnow()
    evt = KpiEvent(timestamp=now, incidents=1, total=10)
    score = HatScore(value=0.8, incidents=1, total=10)
    rank = HatRank(band="green", score=0.8)
    assert evt.timestamp == now
    assert score.value == 0.8
    assert rank.band == "green"
