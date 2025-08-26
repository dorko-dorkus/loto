from pathlib import Path

import yaml

from loto.integrations.hats_adapter import DemoHatsAdapter, HatsAdapter


def test_demo_hats_adapter_get_profile_keys() -> None:
    adapter: HatsAdapter = DemoHatsAdapter()
    profile = adapter.get_profile("DEMO-1")
    assert {"inductions", "competencies", "roster"} <= set(profile)


def test_hats_permit_map_loads() -> None:
    cfg = yaml.safe_load(Path("config/hats_permit_map.yaml").read_text())
    assert "ConfinedSpace" in cfg


def test_demo_hats_adapter_has_required() -> None:
    adapter: HatsAdapter = DemoHatsAdapter()
    ok, missing = adapter.has_required(["DEMO-1"], ["Electrical", "HighVoltage"])
    assert ok and not missing
    ok, missing = adapter.has_required(["DEMO-1"], ["ConfinedSpace"])
    assert not ok and missing == ["DEMO-1"]
