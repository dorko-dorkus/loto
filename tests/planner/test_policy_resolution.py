import networkx as nx
import pytest

from loto.errors import UnisolatablePathError
from loto.isolation_planner import IsolationPlanner
from loto.models import (
    ExposureMode,
    IsolationPolicyEntry,
    IsolationPolicyWorkTypeMatrix,
    RequiredActions,
    RulePack,
    WorkType,
)


def test_require_ddbb_policy_enforced(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PLANNER_NODE_SPLIT", "0")
    g = nx.MultiDiGraph()
    g.add_node("s", is_source=True)
    g.add_node("t", tag="asset")
    g.add_edge("s", "t", is_isolation_point=True)

    planner = IsolationPlanner()
    pack = RulePack(risk_policies=None)

    with pytest.raises(UnisolatablePathError, match="mandatory DDBB"):
        planner.compute(
            {"p": g},
            asset_tag="asset",
            rule_pack=pack,
            config={"work_type": "intrusive_mech", "hazard_class": ["pressure"]},
        )


def test_policy_outputs_verifications_and_controls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PLANNER_NODE_SPLIT", "0")
    g = nx.MultiDiGraph()
    g.add_node("s", is_source=True)
    g.add_node("v1")
    g.add_node("v2")
    g.add_node("t", tag="asset")
    g.add_node("sink", safe_sink=True)
    g.add_edge("s", "v1", is_isolation_point=True)
    g.add_edge("v1", "v2", is_isolation_point=True)
    g.add_edge("v2", "t")
    g.add_edge("v1", "sink", is_bleed=True)

    custom_matrix = {
        WorkType.EXTERNAL_MAINTENANCE: IsolationPolicyWorkTypeMatrix(
            pressure=IsolationPolicyEntry(
                default=RequiredActions(
                    block_sources=True,
                    depressurize_to_sink=True,
                    prove_zero=True,
                    add_barriers=True,
                    require_ddbb=False,
                )
            )
        )
    }
    planner = IsolationPlanner()
    pack = RulePack(risk_policies=None, isolation_policy_matrix=custom_matrix)
    plan = planner.compute(
        {"p": g},
        asset_tag="asset",
        rule_pack=pack,
        config={"work_type": "external_maintenance", "hazard_class": ["pressure"]},
    )

    assert plan.actions
    assert any("depressurize_to_sink" in item for item in plan.verifications)
    assert "path-check: depressurization path to safe sink" in plan.verifications
    assert any("temporary barriers installed" in item for item in plan.controls)


def test_external_maintenance_prefers_closest_cut(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PLANNER_NODE_SPLIT", "0")
    g = nx.MultiDiGraph()
    g.add_node("s", is_source=True)
    g.add_node("u")
    g.add_node("n")
    g.add_node("t", tag="asset")
    g.add_edge("s", "u", is_isolation_point=True, op_cost_min=1.0)
    g.add_edge("u", "n")
    g.add_edge("n", "t", is_isolation_point=True, op_cost_min=1.3)

    planner = IsolationPlanner()
    pack = RulePack(risk_policies=None)

    baseline = planner.compute({"p": g}, asset_tag="asset", rule_pack=pack)
    assert baseline.actions[0].component_id.endswith("s->u")

    local = planner.compute(
        {"p": g},
        asset_tag="asset",
        rule_pack=pack,
        config={
            "work_type": "external_maintenance",
            "hazard_class": ["mechanical"],
        },
    )
    assert local.actions[0].component_id.endswith("n->t")


def test_external_maintenance_pressure_thermal_only_does_not_require_intrusive_boundary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PLANNER_NODE_SPLIT", "0")
    g = nx.MultiDiGraph()
    g.add_node("s", is_source=True)
    g.add_node("u")
    g.add_node("n")
    g.add_node("t", tag="asset")
    g.add_edge("s", "u", is_isolation_point=True, op_cost_min=1.0)
    g.add_edge("u", "n")
    g.add_edge("n", "t", is_isolation_point=True, op_cost_min=1.3)

    planner = IsolationPlanner()
    pack = RulePack(risk_policies=None)
    plan = planner.compute(
        {"steam": g},
        asset_tag="asset",
        rule_pack=pack,
        config={
            "work_type": "external_maintenance",
            "hazard_class": ["pressure"],
            "exposure_mode": "thermal_only",
        },
    )

    assert plan.actions[0].component_id.endswith("n->t")
    assert not any("DDBB" in item for item in plan.verifications)


def test_external_maintenance_release_possible_requires_local_block_depressurize_and_prove(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PLANNER_NODE_SPLIT", "0")
    g = nx.MultiDiGraph()
    g.add_node("s", is_source=True)
    g.add_node("u")
    g.add_node("n")
    g.add_node("t", tag="asset")
    g.add_node("sink", safe_sink=True)
    g.add_edge("s", "u", is_isolation_point=True, op_cost_min=1.0)
    g.add_edge("u", "n")
    g.add_edge("n", "t", is_isolation_point=True, op_cost_min=1.3)
    g.add_edge("n", "sink", is_bleed=True)

    custom_matrix = {
        WorkType.EXTERNAL_MAINTENANCE: IsolationPolicyWorkTypeMatrix(
            pressure=IsolationPolicyEntry(
                default=RequiredActions(block_sources=True, prove_zero=True),
                exposure_overrides={
                    ExposureMode.RELEASE_POSSIBLE: RequiredActions(
                        block_sources=True,
                        depressurize_to_sink=True,
                        prove_zero=True,
                    )
                },
            )
        )
    }

    planner = IsolationPlanner()
    pack = RulePack(risk_policies=None, isolation_policy_matrix=custom_matrix)
    plan = planner.compute(
        {"steam": g},
        asset_tag="asset",
        rule_pack=pack,
        config={
            "work_type": "external_maintenance",
            "hazard_class": ["pressure"],
            "exposure_mode": "release_possible",
        },
    )

    assert plan.actions[0].component_id.endswith("n->t")
    assert any("PT=0" in item for item in plan.verifications)
    assert "path-check: depressurization path to safe sink" in plan.verifications
    assert any("depressurize_to_sink verified" in item for item in plan.verifications)


def test_intrusive_mech_outputs_action_category_strings_for_boundary_open_work(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PLANNER_NODE_SPLIT", "0")
    g = nx.MultiDiGraph()
    g.add_node("s", is_source=True)
    g.add_node("v1")
    g.add_node("v2")
    g.add_node("t", tag="asset")
    g.add_node("sink", safe_sink=True)
    g.add_edge("s", "v1", is_isolation_point=True)
    g.add_edge("v1", "v2", is_isolation_point=True)
    g.add_edge("v2", "t")
    g.add_edge("v1", "sink", is_bleed=True)

    planner = IsolationPlanner()
    pack = RulePack(risk_policies=None)
    plan = planner.compute(
        {"steam": g},
        asset_tag="asset",
        rule_pack=pack,
        config={
            "work_type": "intrusive_mech",
            "hazard_class": ["pressure"],
            "exposure_mode": "release_possible",
        },
    )

    assert any("PT=0" in item for item in plan.verifications)
    assert any("DDBB" in item for item in plan.verifications)
    assert "path-check: depressurization path to safe sink" in plan.verifications
    assert any("pressure relief routed to safe sink" in item for item in plan.controls)
