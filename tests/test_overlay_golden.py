from __future__ import annotations

import json
from pathlib import Path

import pytest

from loto.models import IsolationAction, IsolationPlan
from loto.pid import build_overlay


@pytest.fixture
def golden(request):
    path = Path(request.node.fspath).with_suffix(".golden.json")
    expected = json.loads(path.read_text())

    def check(data: object) -> None:
        assert data == expected

    return check


def test_overlay_golden(golden) -> None:
    """Ensure overlay generation matches expected demo output."""

    map_path = Path(__file__).resolve().parent.parent / "demo/pids/pid_map.yaml"

    plan = IsolationPlan(
        plan_id="P1",
        actions=[
            IsolationAction(component_id="process:src->V-101", method="lock"),
            IsolationAction(component_id="process:src->V-102", method="lock"),
        ],
    )

    overlay = build_overlay(
        sources=["src"],
        asset="A-100",
        plan=plan,
        sim_fail_paths=[["src", "V-101", "A-100"]],
        map_path=map_path,
    )

    golden(overlay)
