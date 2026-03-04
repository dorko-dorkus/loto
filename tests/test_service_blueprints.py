import io

import pandas as pd
import pytest

from loto.inventory import InventoryStatus
from loto.models import RulePack
from loto.service import scheduling
from loto.service.blueprints import plan_and_evaluate


def test_plan_and_evaluate_deterministic(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "loto.service.blueprints.validate_fk_integrity", lambda *a, **k: None
    )
    monkeypatch.setenv("PLANNER_NODE_SPLIT", "0")
    line_df = pd.DataFrame(
        [
            {"domain": "steam", "from_tag": "S", "to_tag": "V"},
            {"domain": "steam", "from_tag": "V", "to_tag": "DEMO_ASSET_1"},
            {"domain": "steam", "from_tag": "DEMO_ASSET_1", "to_tag": "D"},
        ]
    )
    valve_df = pd.DataFrame(
        [
            {"domain": "steam", "tag": "V", "fail_state": "FC", "kind": "MV"},
        ]
    )
    drain_df = pd.DataFrame(
        [
            {"domain": "steam", "tag": "D", "kind": "drain"},
        ]
    )
    source_df = pd.DataFrame(
        [
            {"domain": "steam", "tag": "S", "kind": "source"},
        ]
    )

    plan, report, impact, prov = plan_and_evaluate(
        io.StringIO(line_df.to_csv(index=False)),
        io.StringIO(valve_df.to_csv(index=False)),
        io.StringIO(drain_df.to_csv(index=False)),
        io.StringIO(source_df.to_csv(index=False)),
        asset_tag="DEMO_ASSET_1",
        rule_pack=RulePack(risk_policies=None),
        stimuli=[],
        asset_units={"DEMO_ASSET_1": "U1"},
        unit_data={"U1": {"rated": 5.0, "scheme": "SPOF"}},  # type: ignore[dict-item]
        unit_areas={"U1": "Area1"},
    )

    assert [a.component_id for a in plan.actions] == ["steam:V->DEMO_ASSET_1"]
    assert report.results == []
    assert impact.unavailable_assets == {"DEMO_ASSET_1"}
    assert impact.unit_mw_delta == {"U1": 5.0}
    assert impact.area_mw_delta == {"Area1": 5.0}
    assert prov.seed is None
    assert len(prov.rule_hash) == 64


def test_plan_and_evaluate_with_pre_applied_isolations(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "loto.service.blueprints.validate_fk_integrity", lambda *a, **k: None
    )
    monkeypatch.setenv("PLANNER_NODE_SPLIT", "0")
    line_df = pd.DataFrame(
        [
            {"domain": "steam", "from_tag": "S", "to_tag": "V"},
            {"domain": "steam", "from_tag": "V", "to_tag": "DEMO_ASSET_1"},
            {"domain": "steam", "from_tag": "DEMO_ASSET_1", "to_tag": "D"},
        ]
    )
    valve_df = pd.DataFrame(
        [
            {"domain": "steam", "tag": "V", "fail_state": "FC", "kind": "MV"},
        ]
    )
    drain_df = pd.DataFrame(
        [
            {"domain": "steam", "tag": "D", "kind": "drain"},
        ]
    )
    source_df = pd.DataFrame(
        [
            {"domain": "steam", "tag": "S", "kind": "source"},
        ]
    )

    plan, report, impact, _ = plan_and_evaluate(
        io.StringIO(line_df.to_csv(index=False)),
        io.StringIO(valve_df.to_csv(index=False)),
        io.StringIO(drain_df.to_csv(index=False)),
        io.StringIO(source_df.to_csv(index=False)),
        asset_tag="DEMO_ASSET_1",
        rule_pack=RulePack(risk_policies=None),
        stimuli=[],
        asset_units={"DEMO_ASSET_1": "U1"},
        unit_data={"U1": {"rated": 5.0, "scheme": "SPOF"}},  # type: ignore[dict-item]
        unit_areas={"U1": "Area1"},
        pre_applied_isolations=["steam:V->DEMO_ASSET_1"],
    )

    assert plan.actions == []
    assert report.results == []
    assert impact.unavailable_assets == {"DEMO_ASSET_1"}


def test_plan_and_evaluate_pre_applied_becomes_base_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "loto.service.blueprints.validate_fk_integrity", lambda *a, **k: None
    )
    monkeypatch.setenv("PLANNER_NODE_SPLIT", "0")
    line_df = pd.DataFrame(
        [
            {"domain": "process", "from_tag": "S", "to_tag": "A"},
            {"domain": "process", "from_tag": "A", "to_tag": "B"},
            {"domain": "process", "from_tag": "S", "to_tag": "B"},
        ]
    )
    valve_df = pd.DataFrame(
        [
            {"domain": "process", "tag": "B", "fail_state": "FC", "kind": "MV"},
        ]
    )
    drain_df = pd.DataFrame(
        [
            {"domain": "process", "tag": "D", "kind": "drain"},
        ]
    )
    source_df = pd.DataFrame(
        [
            {"domain": "process", "tag": "S", "kind": "source"},
        ]
    )

    plan, _, _, _ = plan_and_evaluate(
        io.StringIO(line_df.to_csv(index=False)),
        io.StringIO(valve_df.to_csv(index=False)),
        io.StringIO(drain_df.to_csv(index=False)),
        io.StringIO(source_df.to_csv(index=False)),
        asset_tag="B",
        rule_pack=RulePack(risk_policies=None),
        stimuli=[],
        asset_units={"B": "U1"},
        unit_data={"U1": {"rated": 5.0, "scheme": "SPOF"}},  # type: ignore[dict-item]
        unit_areas={"U1": "Area1"},
    )

    initial_edges = [action.component_id for action in plan.actions]
    assert "process:A->B" in initial_edges

    plan_with_pre_applied, _, _, _ = plan_and_evaluate(
        io.StringIO(line_df.to_csv(index=False)),
        io.StringIO(valve_df.to_csv(index=False)),
        io.StringIO(drain_df.to_csv(index=False)),
        io.StringIO(source_df.to_csv(index=False)),
        asset_tag="B",
        rule_pack=RulePack(risk_policies=None),
        stimuli=[],
        asset_units={"B": "U1"},
        unit_data={"U1": {"rated": 5.0, "scheme": "SPOF"}},  # type: ignore[dict-item]
        unit_areas={"U1": "Area1"},
        pre_applied_isolations=["process:A->B"],
    )

    selected_edges = [action.component_id for action in plan_with_pre_applied.actions]
    assert "process:A->B" not in selected_edges
    assert "process:S->B" in selected_edges


def test_plan_and_evaluate_strict_pre_applied_raises_on_malformed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "loto.service.blueprints.validate_fk_integrity", lambda *a, **k: None
    )
    monkeypatch.setenv("PLANNER_NODE_SPLIT", "0")
    line_df = pd.DataFrame(
        [
            {"domain": "steam", "from_tag": "S", "to_tag": "V"},
            {"domain": "steam", "from_tag": "V", "to_tag": "DEMO_ASSET_1"},
        ]
    )
    valve_df = pd.DataFrame(
        [
            {"domain": "steam", "tag": "V", "fail_state": "FC", "kind": "MV"},
        ]
    )
    drain_df = pd.DataFrame([{"domain": "steam", "tag": "D", "kind": "drain"}])
    source_df = pd.DataFrame(
        [
            {"domain": "steam", "tag": "S", "kind": "source"},
        ]
    )

    with pytest.raises(ValueError, match="Malformed component_id 'ISO-1'"):
        plan_and_evaluate(
            io.StringIO(line_df.to_csv(index=False)),
            io.StringIO(valve_df.to_csv(index=False)),
            io.StringIO(drain_df.to_csv(index=False)),
            io.StringIO(source_df.to_csv(index=False)),
            asset_tag="DEMO_ASSET_1",
            rule_pack=RulePack(risk_policies=None),
            stimuli=[],
            asset_units={"DEMO_ASSET_1": "U1"},
            unit_data={"U1": {"rated": 5.0, "scheme": "SPOF"}},  # type: ignore[dict-item]
            unit_areas={"U1": "Area1"},
            pre_applied_isolations=["ISO-1", "steam:V->DEMO_ASSET_1"],
            strict_pre_applied_isolations=True,
        )


def test_plan_and_evaluate_non_strict_pre_applied_skips_malformed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "loto.service.blueprints.validate_fk_integrity", lambda *a, **k: None
    )
    monkeypatch.setenv("PLANNER_NODE_SPLIT", "0")
    events: list[tuple[str, dict[str, str]]] = []

    def fake_warning(event: str, **kw: str) -> None:
        events.append((event, kw))

    monkeypatch.setattr("loto.service.blueprints.logger.warning", fake_warning)

    line_df = pd.DataFrame(
        [
            {"domain": "steam", "from_tag": "S", "to_tag": "V"},
            {"domain": "steam", "from_tag": "V", "to_tag": "DEMO_ASSET_1"},
        ]
    )
    valve_df = pd.DataFrame(
        [
            {"domain": "steam", "tag": "V", "fail_state": "FC", "kind": "MV"},
        ]
    )
    drain_df = pd.DataFrame([{"domain": "steam", "tag": "D", "kind": "drain"}])
    source_df = pd.DataFrame(
        [
            {"domain": "steam", "tag": "S", "kind": "source"},
        ]
    )

    plan, report, impact, _ = plan_and_evaluate(
        io.StringIO(line_df.to_csv(index=False)),
        io.StringIO(valve_df.to_csv(index=False)),
        io.StringIO(drain_df.to_csv(index=False)),
        io.StringIO(source_df.to_csv(index=False)),
        asset_tag="DEMO_ASSET_1",
        rule_pack=RulePack(risk_policies=None),
        stimuli=[],
        asset_units={"DEMO_ASSET_1": "U1"},
        unit_data={"U1": {"rated": 5.0, "scheme": "SPOF"}},  # type: ignore[dict-item]
        unit_areas={"U1": "Area1"},
        pre_applied_isolations=["ISO-1", "steam:V->DEMO_ASSET_1"],
        strict_pre_applied_isolations=False,
    )

    assert plan.actions == []
    assert report.results == []
    assert impact.unavailable_assets == {"DEMO_ASSET_1"}
    assert events == [("invalid_component_id", {"component_id": "ISO-1"})]


def test_plan_and_evaluate_strict_pre_applied_normalizes_component_variants(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "loto.service.blueprints.validate_fk_integrity", lambda *a, **k: None
    )
    monkeypatch.setenv("PLANNER_NODE_SPLIT", "0")
    line_df = pd.DataFrame(
        [
            {"domain": "steam", "from_tag": "SRC", "to_tag": "V_1"},
            {"domain": "steam", "from_tag": "V_1", "to_tag": "ASSET_1"},
        ]
    )
    valve_df = pd.DataFrame(
        [{"domain": "steam", "tag": "V_1", "fail_state": "FC", "kind": "MV"}]
    )
    drain_df = pd.DataFrame([{"domain": "steam", "tag": "D", "kind": "drain"}])
    source_df = pd.DataFrame([{"domain": "steam", "tag": "SRC", "kind": "source"}])

    plan, _, _, _ = plan_and_evaluate(
        io.StringIO(line_df.to_csv(index=False)),
        io.StringIO(valve_df.to_csv(index=False)),
        io.StringIO(drain_df.to_csv(index=False)),
        io.StringIO(source_df.to_csv(index=False)),
        asset_tag="ASSET_1",
        rule_pack=RulePack(risk_policies=None),
        stimuli=[],
        asset_units={"ASSET_1": "U1"},
        unit_data={"U1": {"rated": 5.0, "scheme": "SPOF"}},  # type: ignore[dict-item]
        unit_areas={"U1": "Area1"},
        pre_applied_isolations=["StEaM: v-1 -> asset-1"],
        strict_pre_applied_isolations=True,
    )

    assert plan.actions == []


def test_plan_and_evaluate_non_strict_pre_applied_normalizes_component_variants(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "loto.service.blueprints.validate_fk_integrity", lambda *a, **k: None
    )
    monkeypatch.setenv("PLANNER_NODE_SPLIT", "0")
    events: list[tuple[str, dict[str, str]]] = []

    def fake_warning(event: str, **kw: str) -> None:
        events.append((event, kw))

    monkeypatch.setattr("loto.service.blueprints.logger.warning", fake_warning)

    line_df = pd.DataFrame(
        [
            {"domain": "steam", "from_tag": "SRC", "to_tag": "V_1"},
            {"domain": "steam", "from_tag": "V_1", "to_tag": "ASSET_1"},
        ]
    )
    valve_df = pd.DataFrame(
        [{"domain": "steam", "tag": "V_1", "fail_state": "FC", "kind": "MV"}]
    )
    drain_df = pd.DataFrame([{"domain": "steam", "tag": "D", "kind": "drain"}])
    source_df = pd.DataFrame([{"domain": "steam", "tag": "SRC", "kind": "source"}])

    plan, _, _, _ = plan_and_evaluate(
        io.StringIO(line_df.to_csv(index=False)),
        io.StringIO(valve_df.to_csv(index=False)),
        io.StringIO(drain_df.to_csv(index=False)),
        io.StringIO(source_df.to_csv(index=False)),
        asset_tag="ASSET_1",
        rule_pack=RulePack(risk_policies=None),
        stimuli=[],
        asset_units={"ASSET_1": "U1"},
        unit_data={"U1": {"rated": 5.0, "scheme": "SPOF"}},  # type: ignore[dict-item]
        unit_areas={"U1": "Area1"},
        pre_applied_isolations=["bad-id", "StEaM: v-1 -> asset-1"],
        strict_pre_applied_isolations=False,
    )

    assert plan.actions == []
    assert events == [("invalid_component_id", {"component_id": "bad-id"})]


class _WO:
    def __init__(self, wo_id: str) -> None:
        self.id = wo_id
        self.reservations: list[object] = []


def test_pre_applied_permit_isolation_reduces_schedule_workload_and_makespan(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "loto.service.blueprints.validate_fk_integrity", lambda *a, **k: None
    )
    monkeypatch.setenv("PLANNER_NODE_SPLIT", "0")

    line_df = pd.DataFrame(
        [
            {"domain": "steam", "from_tag": "S", "to_tag": "V"},
            {"domain": "steam", "from_tag": "V", "to_tag": "DEMO_ASSET_1"},
        ]
    )
    valve_df = pd.DataFrame(
        [{"domain": "steam", "tag": "V", "fail_state": "FC", "kind": "MV"}]
    )
    drain_df = pd.DataFrame([{"domain": "steam", "tag": "D", "kind": "drain"}])
    source_df = pd.DataFrame([{"domain": "steam", "tag": "S", "kind": "source"}])

    base_plan, _, _, _ = plan_and_evaluate(
        io.StringIO(line_df.to_csv(index=False)),
        io.StringIO(valve_df.to_csv(index=False)),
        io.StringIO(drain_df.to_csv(index=False)),
        io.StringIO(source_df.to_csv(index=False)),
        asset_tag="DEMO_ASSET_1",
        rule_pack=RulePack(risk_policies=None),
        stimuli=[],
        asset_units={"DEMO_ASSET_1": "U1"},
        unit_data={"U1": {"rated": 5.0, "scheme": "SPOF"}},  # type: ignore[dict-item]
        unit_areas={"U1": "Area1"},
        seed=7,
    )
    with_permit_plan, _, _, _ = plan_and_evaluate(
        io.StringIO(line_df.to_csv(index=False)),
        io.StringIO(valve_df.to_csv(index=False)),
        io.StringIO(drain_df.to_csv(index=False)),
        io.StringIO(source_df.to_csv(index=False)),
        asset_tag="DEMO_ASSET_1",
        rule_pack=RulePack(risk_policies=None),
        stimuli=[],
        asset_units={"DEMO_ASSET_1": "U1"},
        unit_data={"U1": {"rated": 5.0, "scheme": "SPOF"}},  # type: ignore[dict-item]
        unit_areas={"U1": "Area1"},
        pre_applied_isolations=["steam:V->DEMO_ASSET_1"],
        seed=7,
    )

    wo = _WO("WO-CONCURRENT-PERMIT")
    base_assembled = scheduling.assemble_tasks(
        wo,
        base_plan,
        check_parts=lambda _: InventoryStatus(blocked=False),
    )
    permit_assembled = scheduling.assemble_tasks(
        wo,
        with_permit_plan,
        check_parts=lambda _: InventoryStatus(blocked=False),
    )

    base_run = scheduling.run_schedule(base_assembled["tasks"], {}, seed=7)
    permit_run = scheduling.run_schedule(permit_assembled["tasks"], {}, seed=7)

    base_task_count = len(base_assembled["tasks"])
    permit_task_count = len(permit_assembled["tasks"])
    base_makespan = max(base_run.ends.values()) if base_run.ends else 0
    permit_makespan = max(permit_run.ends.values()) if permit_run.ends else 0

    assert permit_task_count < base_task_count, (
        "Expected concurrent permit benefit: pre-applied permit isolations should reduce "
        f"assembled scheduling tasks (baseline={base_task_count}, with_permit={permit_task_count})."
    )
    assert permit_makespan < base_makespan, (
        "Expected concurrent permit benefit: pre-applied permit isolations should improve "
        f"deterministic p50 makespan proxy (baseline={base_makespan}, with_permit={permit_makespan})."
    )


def test_plan_and_evaluate_canonicalizes_policy_context_for_planner(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "loto.service.blueprints.validate_fk_integrity", lambda *a, **k: None
    )
    monkeypatch.setenv("PLANNER_NODE_SPLIT", "0")

    line_df = pd.DataFrame(
        [
            {"domain": "steam", "from_tag": "S", "to_tag": "V"},
            {"domain": "steam", "from_tag": "V", "to_tag": "DEMO_ASSET_1"},
        ]
    )
    valve_df = pd.DataFrame(
        [{"domain": "steam", "tag": "V", "fail_state": "FC", "kind": "MV"}]
    )
    drain_df = pd.DataFrame([{"domain": "steam", "tag": "D", "kind": "drain"}])
    source_df = pd.DataFrame([{"domain": "steam", "tag": "S", "kind": "source"}])

    captured: dict[str, object] = {}

    from loto.models import IsolationPlan

    def fake_compute(self, graphs, asset_tag, rule_pack, config=None):  # type: ignore[no-untyped-def]
        captured.update(config or {})
        return IsolationPlan(
            plan_id=asset_tag, actions=[], verifications=[], hazards=[], controls=[]
        )

    monkeypatch.setattr(
        "loto.service.blueprints.IsolationPlanner.compute", fake_compute
    )

    plan_and_evaluate(
        io.StringIO(line_df.to_csv(index=False)),
        io.StringIO(valve_df.to_csv(index=False)),
        io.StringIO(drain_df.to_csv(index=False)),
        io.StringIO(source_df.to_csv(index=False)),
        asset_tag="DEMO_ASSET_1",
        rule_pack=RulePack(risk_policies=None),
        stimuli=[],
        asset_units={"DEMO_ASSET_1": "U1"},
        unit_data={"U1": {"rated": 5.0, "scheme": "SPOF"}},  # type: ignore[dict-item]
        unit_areas={"U1": "Area1"},
        work_type=" External-Maintenance ",
        hazard_class=[" Pressure ", "CHEMICAL"],
        exposure_mode=" RELEASE-POSSIBLE ",
    )

    assert captured["work_type"] == "external_maintenance"
    assert captured["hazard_class"] == ["pressure", "chemical"]
    assert captured["exposure_mode"] == "release_possible"


def test_plan_and_evaluate_defaults_empty_policy_context_for_planner(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "loto.service.blueprints.validate_fk_integrity", lambda *a, **k: None
    )
    monkeypatch.setenv("PLANNER_NODE_SPLIT", "0")

    line_df = pd.DataFrame(
        [
            {"domain": "steam", "from_tag": "S", "to_tag": "V"},
            {"domain": "steam", "from_tag": "V", "to_tag": "DEMO_ASSET_1"},
        ]
    )
    valve_df = pd.DataFrame(
        [{"domain": "steam", "tag": "V", "fail_state": "FC", "kind": "MV"}]
    )
    drain_df = pd.DataFrame([{"domain": "steam", "tag": "D", "kind": "drain"}])
    source_df = pd.DataFrame([{"domain": "steam", "tag": "S", "kind": "source"}])

    captured: dict[str, object] = {}
    from loto.models import IsolationPlan

    def fake_compute(self, graphs, asset_tag, rule_pack, config=None):  # type: ignore[no-untyped-def]
        captured.update(config or {})
        return IsolationPlan(
            plan_id=asset_tag, actions=[], verifications=[], hazards=[], controls=[]
        )

    monkeypatch.setattr(
        "loto.service.blueprints.IsolationPlanner.compute", fake_compute
    )

    plan_and_evaluate(
        io.StringIO(line_df.to_csv(index=False)),
        io.StringIO(valve_df.to_csv(index=False)),
        io.StringIO(drain_df.to_csv(index=False)),
        io.StringIO(source_df.to_csv(index=False)),
        asset_tag="DEMO_ASSET_1",
        rule_pack=RulePack(risk_policies=None),
        stimuli=[],
        asset_units={"DEMO_ASSET_1": "U1"},
        unit_data={"U1": {"rated": 5.0, "scheme": "SPOF"}},  # type: ignore[dict-item]
        unit_areas={"U1": "Area1"},
    )

    assert captured["work_type"] is None
    assert captured["hazard_class"] == []
    assert captured["exposure_mode"] is None
