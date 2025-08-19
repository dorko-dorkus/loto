import datetime

from loto.roster.metrics import KpiEvent, safety_rank


def test_clamp_and_demotion():
    now = datetime.datetime.utcnow()
    events = [KpiEvent(timestamp=now, incidents=10, total=1)]
    rank = safety_rank(events)
    assert rank.band == "red"
    assert rank.score == 0.0


def test_min_samples_neutral_rank():
    now = datetime.datetime.utcnow()
    events = [KpiEvent(timestamp=now, incidents=0, total=2)]
    rank = safety_rank(events, min_samples=5)
    assert rank.band == "amber"
    assert rank.score == 0.5


def test_cooldown_before_rank_lifts():
    start = datetime.datetime(2024, 1, 1)
    events = [
        KpiEvent(timestamp=start, incidents=1, total=10),
        KpiEvent(timestamp=start + datetime.timedelta(hours=1), incidents=0, total=10),
    ]
    rank = safety_rank(
        events, now=start + datetime.timedelta(hours=2), cooldown_hours=24
    )
    assert rank.band == "red"
    assert rank.score == 0.0

    rank_after = safety_rank(
        events, now=start + datetime.timedelta(days=2), cooldown_hours=24
    )
    assert rank_after.band == "green"
    assert rank_after.score > 0.8
