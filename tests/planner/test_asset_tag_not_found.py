from __future__ import annotations

import networkx as nx
import pytest

from loto.errors import AssetTagNotFoundError
from loto.isolation_planner import IsolationPlanner
from loto.models import RulePack


def test_compute_raises_asset_tag_not_found_with_normalized_message() -> None:
    graph = nx.MultiDiGraph()
    graph.add_node("S", is_source=True, tag="S")
    graph.add_node("A", is_isolation_point=True, tag="A")
    graph.add_edge("S", "A", is_isolation_point=True)

    planner = IsolationPlanner()
    with pytest.raises(AssetTagNotFoundError) as excinfo:
        planner.compute(
            {"process": graph},
            asset_tag="  MISSING ",
            rule_pack=RulePack(risk_policies=None),
        )

    exc = excinfo.value
    assert exc.code == "ASSET_TAG_NOT_FOUND"
    assert exc.hint == "asset_tag 'MISSING' not found in graph"
    assert exc.public_hint == "graph contains 2 nodes"
