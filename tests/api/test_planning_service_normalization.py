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
