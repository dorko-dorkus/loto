from __future__ import annotations

import json
from pathlib import Path

import pytest

from loto.roster.ranking import update_ranking


@pytest.fixture
def golden(request):
    path = Path(request.node.fspath).with_suffix(".golden.json")
    expected = json.loads(path.read_text())

    def check(data: object) -> None:
        assert data == expected

    return check


def test_update_ranking(golden):
    ledger = {
        "alice": [(0.7, 0.8), (0.8, 0.9), (0.9, 1.0)],
        "bob": [(0.5, 0.4), (0.4, 0.5), (0.6, 0.5)],
        "carol": [(0.2, 0.1), (0.3, 0.2), (0.4, 0.3)],
    }

    snapshot = update_ranking(ledger)
    golden(snapshot)
