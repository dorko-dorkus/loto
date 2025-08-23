import copy
import json

import pytest
from pydantic import ValidationError

from loto.models import (
    ArtifactBundle,
    DomainRule,
    Edge,
    GraphBundle,
    ImpactReport,
    IsolationAction,
    IsolationPlan,
    Node,
    RiskPolicies,
    RulePack,
    SimReport,
    SimResultItem,
    Stimulus,
    VerificationRule,
)

# Example instances for round-trip tests
MODEL_DATA = [
    (
        DomainRule,
        {
            "name": "r1",
            "expression": "x > 0",
            "statutory": ["HSWA"],
            "evidence": ["record"],
        },
    ),
    (
        VerificationRule,
        {
            "name": "v1",
            "check": "x < 1",
            "statutory": ["HSWA"],
            "evidence": ["record"],
        },
    ),
    (RiskPolicies, {"levels": {"low": 0.1, "high": 0.9}}),
    (Node, {"id": "n1", "label": "Node 1"}),
    (Edge, {"source": "n1", "target": "n2", "weight": 1.0}),
    (
        GraphBundle,
        {
            "nodes": [{"id": "n1"}, {"id": "n2"}],
            "edges": [{"source": "n1", "target": "n2"}],
            "metadata": {"type": "simple"},
        },
    ),
    (
        IsolationAction,
        {"component_id": "valve1", "method": "lock", "duration_s": 5.0},
    ),
    (
        IsolationPlan,
        {
            "plan_id": "planA",
            "actions": [
                {"component_id": "valve1", "method": "lock", "duration_s": 5.0}
            ],
            "verifications": [],
            "hazards": [],
            "controls": [],
        },
    ),
    (Stimulus, {"name": "pulse", "magnitude": 3.0, "duration_s": 1.0}),
    (
        SimResultItem,
        {
            "stimulus": {"name": "pulse", "magnitude": 3.0, "duration_s": 1.0},
            "success": True,
            "impact": 0.5,
        },
    ),
    (
        SimReport,
        {
            "results": [
                {
                    "stimulus": {
                        "name": "pulse",
                        "magnitude": 3.0,
                        "duration_s": 1.0,
                    },
                    "success": True,
                    "impact": 0.5,
                }
            ],
            "total_time_s": 1.0,
        },
    ),
    (
        ImpactReport,
        {"component_id": "valve1", "severity": 0.7, "description": "minor"},
    ),
    (
        ArtifactBundle,
        {"artifacts": {"log": "path/to/log"}, "metadata": {"creator": "tester"}},
    ),
    (
        RulePack,
        {
            "domain_rules": [
                {
                    "name": "r1",
                    "expression": "x > 0",
                    "statutory": ["HSWA"],
                    "evidence": ["record"],
                }
            ],
            "verification_rules": [
                {
                    "name": "v1",
                    "check": "x < 1",
                    "statutory": ["HSWA"],
                    "evidence": ["record"],
                }
            ],
            "risk_policies": {"levels": {"low": 0.1}},
            "metadata": {},
            "policy": {},
            "governance": {},
            "datasets": {},
        },
    ),
]


@pytest.mark.parametrize("model_cls,data", MODEL_DATA)
def test_json_round_trip(model_cls, data):
    """Objects should be serialisable to JSON and back without loss."""

    obj = model_cls(**data)
    dumped = json.loads(obj.model_dump_json(exclude_none=True))
    assert dumped == data
    obj2 = model_cls(**dumped)
    assert obj2 == obj


@pytest.mark.parametrize("model_cls,data", MODEL_DATA)
def test_rejects_extra_fields(model_cls, data):
    """All models use ``extra='forbid'`` and should reject additional fields."""

    bad = copy.deepcopy(data)
    bad["unexpected"] = 123
    with pytest.raises(ValidationError):
        model_cls(**bad)


def test_invalid_type_raises_error():
    """Invalid field types should raise clear validation errors."""

    with pytest.raises(ValidationError):
        Node(id=1, label="A")  # id must be a string
