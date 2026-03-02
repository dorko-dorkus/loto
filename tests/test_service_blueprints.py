import io

import pandas as pd
import pytest

from loto.models import RulePack
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
            {"domain": "steam", "from_tag": "V", "to_tag": "asset"},
            {"domain": "steam", "from_tag": "asset", "to_tag": "D"},
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
        asset_tag="ASSET",
        rule_pack=RulePack(risk_policies=None),
        stimuli=[],
        asset_units={"ASSET": "U1"},
        unit_data={"U1": {"rated": 5.0, "scheme": "SPOF"}},  # type: ignore[dict-item]
        unit_areas={"U1": "Area1"},
    )

    assert [a.component_id for a in plan.actions] == ["steam:V->ASSET"]
    assert report.results == []
    assert impact.unavailable_assets == {"ASSET"}
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
            {"domain": "steam", "from_tag": "V", "to_tag": "asset"},
            {"domain": "steam", "from_tag": "asset", "to_tag": "D"},
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
        asset_tag="ASSET",
        rule_pack=RulePack(risk_policies=None),
        stimuli=[],
        asset_units={"ASSET": "U1"},
        unit_data={"U1": {"rated": 5.0, "scheme": "SPOF"}},  # type: ignore[dict-item]
        unit_areas={"U1": "Area1"},
        pre_applied_isolations=["steam:V->ASSET"],
    )

    assert plan.actions == []
    assert report.results == []
    assert impact.unavailable_assets == {"ASSET"}


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
            {"domain": "steam", "from_tag": "V", "to_tag": "asset"},
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
            asset_tag="ASSET",
            rule_pack=RulePack(risk_policies=None),
            stimuli=[],
            asset_units={"ASSET": "U1"},
            unit_data={"U1": {"rated": 5.0, "scheme": "SPOF"}},  # type: ignore[dict-item]
            unit_areas={"U1": "Area1"},
            pre_applied_isolations=["ISO-1", "steam:V->ASSET"],
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
            {"domain": "steam", "from_tag": "V", "to_tag": "asset"},
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
        asset_tag="ASSET",
        rule_pack=RulePack(risk_policies=None),
        stimuli=[],
        asset_units={"ASSET": "U1"},
        unit_data={"U1": {"rated": 5.0, "scheme": "SPOF"}},  # type: ignore[dict-item]
        unit_areas={"U1": "Area1"},
        pre_applied_isolations=["ISO-1", "steam:V->ASSET"],
        strict_pre_applied_isolations=False,
    )

    assert plan.actions == []
    assert report.results == []
    assert impact.unavailable_assets == {"ASSET"}
    assert events == [("invalid_component_id", {"component_id": "ISO-1"})]
