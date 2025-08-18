from loto.scheduling import roster_input
from loto.scheduling.des_engine import Task, run


def test_calendar_respects_shift(tmp_path):
    csv_path = tmp_path / "hats.csv"
    csv_path.write_text("hat,start,stop,breaks,ot\ncrew,5,10,,false\n")

    roster = roster_input.read_hat_roster(csv_path)
    cal = roster_input.calendar_adapter(roster["crew"])

    # closes outside the shift
    assert not cal(4)
    assert cal(5)
    assert cal(9)
    assert not cal(10)

    tasks = {"a": Task(duration=2, calendar=cal)}
    result = run(tasks, {})
    assert result.starts == {"a": 5}
    assert result.ends == {"a": 7}
