import json

from loto.models import IsolationPlan, SimReport
from loto.renderer import Renderer


def test_to_json_round_trip_and_optional_impact():
    plan = IsolationPlan(plan_id="p", actions=[])
    sim_report = SimReport(results=[], total_time_s=0.0)
    renderer = Renderer()

    base_payload = renderer.to_json(plan, sim_report)
    assert list(base_payload.keys()) == ["plan", "simulation"]
    assert "impact" not in base_payload
    rt_base = json.loads(json.dumps(base_payload))
    assert list(rt_base.keys()) == ["plan", "simulation"]

    impact_data = {"b": 2, "a": 1}
    impact_payload = renderer.to_json(plan, sim_report, impact=impact_data)
    assert list(impact_payload.keys()) == ["plan", "simulation", "impact"]
    assert list(impact_payload["impact"].keys()) == ["a", "b"]
    rt_impact = json.loads(json.dumps(impact_payload))
    assert list(rt_impact.keys()) == ["plan", "simulation", "impact"]
    assert list(rt_impact["impact"].keys()) == ["a", "b"]


def test_to_json_with_bundling():
    plan = IsolationPlan(plan_id="p", actions=[])
    sim_report = SimReport(results=[], total_time_s=0.0)
    renderer = Renderer()

    bundling = {
        "picks": ["b", "a"],
        "params": {"y": 2, "x": 1},
    }

    payload = renderer.to_json(
        plan,
        sim_report,
        bundling_picks=bundling["picks"],
        bundling_params=bundling["params"],
    )

    assert list(payload.keys()) == ["plan", "simulation", "bundling"]
    assert payload["bundling"]["picks"] == ["a", "b"]
    assert list(payload["bundling"]["params"].keys()) == ["x", "y"]

    rt_payload = json.loads(json.dumps(payload))
    assert rt_payload["bundling"]["picks"] == ["a", "b"]
    assert list(rt_payload["bundling"]["params"].keys()) == ["x", "y"]
