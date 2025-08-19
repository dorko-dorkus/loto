from loto.scheduling.assign import Hat, Task, simulate


class _Bias:
    """Deterministic rank bias for testing."""

    def duration_with_rank(self, duration_s: float, rank: int) -> float:
        # Increase the objective by the rank value so lower rank numbers are preferred
        return duration_s + rank


def test_prefers_higher_rank():
    hats = [
        Hat(id="h1", skills={"w"}, calendar={0}, rank=2),
        Hat(id="h2", skills={"w"}, calendar={0}, rank=1),
    ]
    task = Task(skill="w", start=0, duration_s=1)
    chosen = simulate(task, hats, _Bias())
    assert chosen is not None
    assert chosen.id == "h2"


def test_respects_calendar():
    hats = [
        Hat(id="h1", skills={"w"}, calendar={1}, rank=1),
        Hat(id="h2", skills={"w"}, calendar={0}, rank=2),
    ]
    task = Task(skill="w", start=0, duration_s=1)
    chosen = simulate(task, hats, _Bias())
    assert chosen is not None
    assert chosen.id == "h2"
