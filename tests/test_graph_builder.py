import pandas as pd

from loto.graph_builder import GraphBuilder


def test_build_graphs_from_demo_csvs(tmp_path):
    line_df = pd.DataFrame(
        [
            {"domain": "steam", "from_tag": "S1", "to_tag": "V1"},
            {"domain": "steam", "from_tag": "V1", "to_tag": "D1"},
            {"domain": "water", "from_tag": "S2", "to_tag": "V2"},
            {"domain": "water", "from_tag": "V2", "to_tag": "D2"},
        ]
    )
    valve_df = pd.DataFrame(
        [
            {"domain": "steam", "tag": "V1", "fail_state": "CLOSED", "kind": "MV"},
            {"domain": "water", "tag": "V2", "fail_state": "OPEN", "kind": "GV"},
        ]
    )
    drain_df = pd.DataFrame(
        [
            {"domain": "steam", "tag": "D1", "kind": "drain"},
            {"domain": "water", "tag": "D2", "kind": "drain"},
        ]
    )
    source_df = pd.DataFrame(
        [
            {"domain": "steam", "tag": "S1", "kind": "source"},
            {"domain": "water", "tag": "S2", "kind": "source"},
        ]
    )

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

    assert set(graphs.keys()) == {"steam", "water"}

    steam = graphs["steam"]
    water = graphs["water"]

    assert steam.number_of_nodes() == 3
    assert steam.number_of_edges() == 2
    assert water.number_of_nodes() == 3
    assert water.number_of_edges() == 2

    assert steam.nodes["S1"]["is_source"] is True
    assert steam.nodes["V1"]["is_isolation_point"] is True
    assert steam.nodes["V1"]["fail_state"] == "CLOSED"
    assert steam.nodes["V1"]["kind"] == "MV"
