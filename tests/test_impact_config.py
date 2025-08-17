from pathlib import Path

from loto.impact_config import load_impact_config


def test_load_demo_config():
    cfg = load_impact_config(
        Path("demo/unit_map.yaml"), Path("demo/redundancy_map.yaml")
    )
    assert cfg.asset_units == {"uA": "UnitA", "uB1": "UnitB", "uB2": "UnitB"}
    assert cfg.unit_data == {
        "UnitA": {"rated": 100.0, "scheme": "SPOF"},
        "UnitB": {"rated": 90.0, "scheme": "N+1", "nplus": 2},
    }
    assert cfg.unit_areas == {"UnitA": "North", "UnitB": "North"}
    assert cfg.penalties == {"local1": 5.0}
    assert cfg.asset_areas == {"local1": "South"}
    assert cfg.unknown_units == set()
    assert cfg.unknown_penalties == set()


def test_missing_redundancy_flagged(tmp_path):
    tmp_redundancy = tmp_path / "redundancy.yaml"
    tmp_redundancy.write_text("UnitA: SPOF\n")
    cfg = load_impact_config(Path("demo/unit_map.yaml"), tmp_redundancy)
    assert "UnitB" in cfg.unknown_units
