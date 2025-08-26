from pathlib import Path

import pandas as pd

from loto.graph_builder import GraphBuilder
from loto.isolation_planner import IsolationPlanner
from loto.rule_engine import RulePack  # type: ignore[attr-defined]


def test_check_valve_excluded_from_plan(tmp_path: Path) -> None:
    line_df = pd.DataFrame(
        [
            {"domain": "steam", "from_tag": "S1", "to_tag": "V1"},
            {"domain": "steam", "from_tag": "V1", "to_tag": "N1"},
            {"domain": "steam", "from_tag": "N1", "to_tag": "V2"},
            {"domain": "steam", "from_tag": "V2", "to_tag": "A1"},
        ]
    )
    valve_df = pd.DataFrame(
        [
            {"domain": "steam", "tag": "V1", "kind": "NRV", "direction": "forward"},
            {"domain": "steam", "tag": "V2", "kind": "GV"},
        ]
    )
    drain_df = pd.DataFrame(columns=["domain", "tag", "kind"])
    source_df = pd.DataFrame([{"domain": "steam", "tag": "S1", "kind": "source"}])

    line_path = tmp_path / "lines.csv"
    valve_path = tmp_path / "valves.csv"
    drain_path = tmp_path / "drains.csv"
    source_path = tmp_path / "sources.csv"
    line_df.to_csv(line_path, index=False)
    valve_df.to_csv(valve_path, index=False)
    drain_df.to_csv(drain_path, index=False)
    source_df.to_csv(source_path, index=False)

    builder = GraphBuilder()
    graphs = builder.from_csvs(line_path, valve_path, drain_path, source_path)
    planner = IsolationPlanner()
    pack = RulePack(risk_policies=None)
    plan = planner.compute(graphs, asset_tag="A1", rule_pack=pack)

    edges = [action.component_id.split(":", 1)[1] for action in plan.actions]
    assert all("V1" not in e for e in edges)
    assert any("V2" in e for e in edges)
