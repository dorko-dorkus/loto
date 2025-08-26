from loto.scheduling.assign import Hat, coalesce_slots, is_available


def test_coalesce_slots_merges_ranges() -> None:
    assert coalesce_slots([0, 1, 2, 4, 5, 7]) == [(0, 2), (4, 5), (7, 7)]


def test_hat_calendar_coalesces() -> None:
    hat = Hat(id="h", skills={"w"}, calendar=[0, 1, 2, 4], rank=1)
    assert hat.calendar == [(0, 2), (4, 4)]


def test_is_available() -> None:
    ranges = [(0, 2), (4, 4)]
    assert is_available(1, ranges)
    assert not is_available(3, ranges)
    hat = Hat(id="h", skills={"w"}, calendar=ranges, rank=1)
    assert is_available(4, hat.calendar)
    assert not is_available(3, hat.calendar)
