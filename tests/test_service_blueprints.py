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
