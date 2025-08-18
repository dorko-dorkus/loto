from loto.models import IsolationAction, IsolationPlan
from loto.pid import build_overlay


def test_overlay_highlights_isolations_and_sim_fail(tmp_path):
    pid_map = tmp_path / "pid_map.yaml"
    pid_map.write_text(
        "\n".join(
            [
                "V-201A: '#V201A'",
                "V-201B: '#V201B'",
                "BL-201: '#BL201'",
                "A-201: '#A201'",
                "src: '#SRC'",
            ]
        )
    )

    plan = IsolationPlan(
        plan_id="p1",
        actions=[
            IsolationAction(component_id="process:src->V-201A", method="lock"),
            IsolationAction(component_id="process:src->V-201B", method="lock"),
            IsolationAction(component_id="process:src->BL-201", method="lock"),
        ],
    )

    overlay = build_overlay(
        sources=["src"],
        asset="A-201",
        plan=plan,
        sim_fail_paths=[["src", "V-201A", "A-201"]],
        map_path=pid_map,
    )

    highlights = overlay["highlight"]
    assert "#V201A" in highlights
    assert "#V201B" in highlights
    assert "#BL201" in highlights

    path0 = overlay["paths"][0]
    assert path0["id"] == "path0"
    assert "#V201A" in path0["selectors"]
    assert "#V201A" in highlights


def test_overlay_dedup_and_warnings(tmp_path):
    pid_map = tmp_path / "pid_map.yaml"
    pid_map.write_text(
        "\n".join(
            [
                "V-201A: '#DUP'",
                "V-201B: '#DUP'",
                "A-201: '#A201'",
                "src: '#SRC'",
            ]
        )
    )

    plan = IsolationPlan(
        plan_id="p2",
        actions=[
            IsolationAction(component_id="process:src->V-201A", method="lock"),
            IsolationAction(component_id="process:src->V-201B", method="lock"),
            IsolationAction(component_id="process:src->MISSING", method="lock"),
        ],
    )

    overlay = build_overlay(
        sources=["src", "UNKNOWN_SRC"],
        asset="A-201",
        plan=plan,
        sim_fail_paths=[["src", "V-201A", "V-201B", "A-201", "UNKNOWN"]],
        map_path=pid_map,
    )

    assert overlay["highlight"].count("#DUP") == 1
    path0 = overlay["paths"][0]
    assert path0["selectors"].count("#DUP") == 1
    assert {"selector": "#A201", "type": "warning"} in overlay["badges"]
