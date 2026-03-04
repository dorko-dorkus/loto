from __future__ import annotations

from typing import Any

import pytest

from apps.api import planning_service


def test_load_work_order_plan_mixed_case_asset_tag_yields_same_plan(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "loto.service.blueprints.validate_fk_integrity", lambda *a, **k: None
    )

    baseline_bundle, _ = planning_service.load_work_order_plan(
        "WO-1", strict_pre_applied_isolations=False, state={}
    )

    original_load_context = planning_service.DemoMaximoAdapter.load_context

    def _mixed_case_context(self: Any, workorder_id: str) -> dict[str, Any]:
        ctx = original_load_context(self, workorder_id)
        ctx["asset_tag"] = "  uA  "
        return ctx

    monkeypatch.setattr(
        planning_service.DemoMaximoAdapter, "load_context", _mixed_case_context
    )

    mixed_bundle, _ = planning_service.load_work_order_plan(
        "WO-1", strict_pre_applied_isolations=False, state={}
    )

    assert baseline_bundle.plan_action_set == mixed_bundle.plan_action_set
    assert baseline_bundle.plan_version == mixed_bundle.plan_version


def test_load_work_order_plan_infers_and_canonicalizes_policy_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "loto.service.blueprints.validate_fk_integrity", lambda *a, **k: None
    )

    class _PermitAdapter:
        def fetch_permit(self, workorder_id: str) -> dict[str, Any]:
            return {
                "description": "Hot Work on pressure line",
                "callback_time_min": 5,
                "applied_isolations": [],
            }

    captured: dict[str, Any] = {}

    def _capturing_plan_and_evaluate(*args: Any, **kwargs: Any) -> Any:
        captured.update(kwargs)
        from loto.service.blueprints import plan_and_evaluate as real_plan_and_evaluate

        return real_plan_and_evaluate(*args, **kwargs)

    monkeypatch.setattr(
        planning_service, "get_permit_adapter", lambda: _PermitAdapter()
    )
    monkeypatch.setattr(
        planning_service, "plan_and_evaluate", _capturing_plan_and_evaluate
    )

    planning_service.load_work_order_plan(
        "WO-1",
        strict_pre_applied_isolations=False,
        state={},
        work_type=" Intrusive-Mech ",
        hazard_class=[" Pressure ", "CHEMICAL"],
        exposure_mode=" RELEASE-POSSIBLE ",
    )

    assert captured["work_type"] == "intrusive_mech"
    assert captured["hazard_class"] == ["pressure", "chemical"]
    assert captured["exposure_mode"] == "release_possible"


def test_load_work_order_plan_legacy_defaults_from_permit_and_description(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "loto.service.blueprints.validate_fk_integrity", lambda *a, **k: None
    )

    class _PermitAdapter:
        def fetch_permit(self, workorder_id: str) -> dict[str, Any]:
            return {
                "description": "Hot work with pressure boundary",
                "hazard_class": [" Temperature ", "Pressure"],
                "callback_time_min": 5,
                "applied_isolations": [],
            }

    captured: dict[str, Any] = {}

    def _capturing_plan_and_evaluate(*args: Any, **kwargs: Any) -> Any:
        captured.update(kwargs)
        from loto.service.blueprints import plan_and_evaluate as real_plan_and_evaluate

        return real_plan_and_evaluate(*args, **kwargs)

    monkeypatch.setattr(
        planning_service, "get_permit_adapter", lambda: _PermitAdapter()
    )
    monkeypatch.setattr(
        planning_service, "plan_and_evaluate", _capturing_plan_and_evaluate
    )

    planning_service.load_work_order_plan(
        "WO-1", strict_pre_applied_isolations=False, state={}
    )

    assert captured["work_type"] == "hot_work"
    assert captured["hazard_class"] == ["temperature", "pressure"]
    assert captured["exposure_mode"] == "ignition_possible"


def test_load_work_order_plan_infers_exposure_from_scope_terms(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "loto.service.blueprints.validate_fk_integrity", lambda *a, **k: None
    )

    class _PermitAdapter:
        def fetch_permit(self, workorder_id: str) -> dict[str, Any]:
            return {
                "description": "Support replacement and insulation touch-up",
                "callback_time_min": 5,
                "applied_isolations": [],
            }

    monkeypatch.setattr(
        planning_service, "get_permit_adapter", lambda: _PermitAdapter()
    )

    bundle, _ = planning_service.load_work_order_plan(
        "WO-1", strict_pre_applied_isolations=False, state={}
    )

    assert bundle.provenance.context is not None
    assert bundle.provenance.context["exposure_mode"]["final"] == "thermal_only"
    assert bundle.provenance.context["exposure_mode"]["source"] == "inferred"


def test_load_work_order_plan_boundary_open_escalates_when_work_type_not_provided(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "loto.service.blueprints.validate_fk_integrity", lambda *a, **k: None
    )

    class _PermitAdapter:
        def fetch_permit(self, workorder_id: str) -> dict[str, Any]:
            return {
                "description": "Hot work with open boundary for tie-in",
                "callback_time_min": 5,
                "applied_isolations": [],
            }

    captured: dict[str, Any] = {}

    def _capturing_plan_and_evaluate(*args: Any, **kwargs: Any) -> Any:
        captured.update(kwargs)
        from loto.service.blueprints import plan_and_evaluate as real_plan_and_evaluate

        return real_plan_and_evaluate(*args, **kwargs)

    monkeypatch.setattr(
        planning_service, "get_permit_adapter", lambda: _PermitAdapter()
    )
    monkeypatch.setattr(
        planning_service, "plan_and_evaluate", _capturing_plan_and_evaluate
    )

    bundle, _ = planning_service.load_work_order_plan(
        "WO-1",
        strict_pre_applied_isolations=False,
        state={},
        work_type="hot_work",
        exposure_mode="none",
    )

    assert captured["work_type"] == "hot_work"
    assert captured["exposure_mode"] == "none"
    assert bundle.provenance.context is not None
    assert (
        bundle.provenance.context["work_type"]["escalated_to_intrusive_mech"] is False
    )
    assert bundle.provenance.context["exposure_mode"]["source"] == "request"


def test_load_work_order_plan_boundary_open_escalates_to_intrusive_mech(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "loto.service.blueprints.validate_fk_integrity", lambda *a, **k: None
    )

    class _PermitAdapter:
        def fetch_permit(self, workorder_id: str) -> dict[str, Any]:
            return {
                "description": "Hot work with open boundary for tie-in",
                "callback_time_min": 5,
                "applied_isolations": [],
            }

    captured: dict[str, Any] = {}

    def _capturing_plan_and_evaluate(*args: Any, **kwargs: Any) -> Any:
        captured.update(kwargs)
        from loto.service.blueprints import plan_and_evaluate as real_plan_and_evaluate

        return real_plan_and_evaluate(*args, **kwargs)

    monkeypatch.setattr(
        planning_service, "get_permit_adapter", lambda: _PermitAdapter()
    )
    monkeypatch.setattr(
        planning_service, "plan_and_evaluate", _capturing_plan_and_evaluate
    )

    bundle, _ = planning_service.load_work_order_plan(
        "WO-1",
        strict_pre_applied_isolations=False,
        state={},
    )

    assert captured["work_type"] == "intrusive_mech"
    assert captured["exposure_mode"] == "release_possible"
    assert bundle.provenance.context is not None
    assert bundle.provenance.context["work_type"]["escalated_to_intrusive_mech"] is True
