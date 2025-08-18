from loto.models import IsolationAction, IsolationPlan
from loto.pid import build_overlay
from loto.pid import overlay as overlay_mod


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


def test_overlay_map_cached(tmp_path):
    pid_map = tmp_path / "pid_map.yaml"
    pid_map.write_text("A-201: '#A201'\n")

    plan = IsolationPlan(plan_id="p1", actions=[])

    overlay_mod._load_map_cached.cache_clear()
    overlay_mod._MAP_PARSES = 0

    build_overlay(
        sources=[],
        asset="A-201",
        plan=plan,
        sim_fail_paths=[],
        map_path=pid_map,
    )
    build_overlay(
        sources=[],
        asset="A-201",
        plan=plan,
        sim_fail_paths=[],
        map_path=pid_map,
    )

    assert overlay_mod._MAP_PARSES == 1
