"""Core data models for lock-out/tag-out planning utilities.

This module defines strict Pydantic models used throughout the project.  All
models forbid extra fields to help surface typing mistakes early and include
basic metadata/units for numeric values.
"""

from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DomainRule(BaseModel):
    """Represents a rule describing domain-specific constraints."""

    name: str = Field(..., description="Rule name")
    expression: str = Field(..., description="Expression used to evaluate the rule")
    statutory: List[str] = Field(
        ..., description="Statutory references supporting the rule"
    )
    evidence: List[str] = Field(..., description="Evidence requirements for compliance")

    class Config:
        extra = "forbid"


class VerificationRule(BaseModel):
    """Represents a rule verifying an expected condition."""

    name: str = Field(..., description="Verification rule name")
    check: str = Field(..., description="Expression or callable for verification")
    statutory: List[str] = Field(
        ..., description="Statutory references supporting the rule"
    )
    evidence: List[str] = Field(..., description="Evidence requirements for compliance")

    class Config:
        extra = "forbid"


class RiskPolicies(BaseModel):
    """Policy thresholds for different risk levels.

    The ``levels`` mapping associates a textual risk level with a probability
    threshold in the range ``[0, 1]`` (unit: probability).
    """

    levels: Dict[str, float] = Field(
        default_factory=dict,
        description="Mapping of risk level to probability threshold [0-1]",
    )

    class Config:
        extra = "forbid"


class Node(BaseModel):
    """A node within a graph structure."""

    id: str = Field(..., description="Unique node identifier")
    label: Optional[str] = Field(None, description="Human readable label")

    class Config:
        extra = "forbid"


class Edge(BaseModel):
    """An edge connecting two nodes within a graph."""

    source: str = Field(..., description="Identifier of the source node")
    target: str = Field(..., description="Identifier of the target node")
    weight: Optional[float] = Field(None, description="Edge weight (unitless)")

    class Config:
        extra = "forbid"


class GraphBundle(BaseModel):
    """Group of graph components accompanied by metadata."""

    nodes: List[Node] = Field(
        default_factory=list, description="Nodes comprising the graph"
    )
    edges: List[Edge] = Field(
        default_factory=list, description="Edges comprising the graph"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Arbitrary graph metadata"
    )

    class Config:
        extra = "forbid"


class IsolationAction(BaseModel):
    """Action executed to isolate a component."""

    component_id: str = Field(..., description="Identifier of the component")
    method: str = Field(..., description="Isolation method such as 'lock' or 'tag'")
    duration_s: Optional[float] = Field(
        None, description="Expected duration in seconds"
    )

    class Config:
        extra = "forbid"


class IsolationPlan(BaseModel):
    """Plan made up of a sequence of isolation actions."""

    plan_id: str = Field(..., description="Unique identifier for the plan")
    actions: List[IsolationAction] = Field(
        default_factory=list, description="Ordered isolation actions"
    )
    verifications: List[str] = Field(
        default_factory=list, description="Optional verification checks"
    )
    hazards: List[str] = Field(
        default_factory=list, description="Identified hazards associated with the plan"
    )
    controls: List[str] = Field(
        default_factory=list, description="Controls implemented to mitigate hazards"
    )

    class Config:
        extra = "forbid"


class Stimulus(BaseModel):
    """Input stimulus used for simulation."""

    name: str = Field(..., description="Stimulus name")
    magnitude: float = Field(..., description="Stimulus magnitude (unitless)")
    duration_s: float = Field(..., description="Stimulus duration in seconds")

    class Config:
        extra = "forbid"


class SimResultItem(BaseModel):
    """Result produced from simulating a single stimulus."""

    stimulus: Stimulus = Field(..., description="Stimulus that was simulated")
    success: bool = Field(..., description="Whether the simulation succeeded")
    impact: float = Field(..., description="Impact score (unitless)")
    domain: Optional[str] = Field(
        None, description="Domain containing any invariant violation"
    )
    path: Optional[List[str]] = Field(
        None, description="Shortest offending path if a violation occurred"
    )
    hint: Optional[str] = Field(
        None, description="Suggested remediation for the violation"
    )

    class Config:
        extra = "forbid"


class SimReport(BaseModel):
    """Collection of simulation results."""

    results: List[SimResultItem] = Field(
        default_factory=list, description="Individual simulation results"
    )
    total_time_s: float = Field(..., description="Total simulation time in seconds")

    class Config:
        extra = "forbid"


class ImpactReport(BaseModel):
    """Quantified impact report for a component or system."""

    component_id: str = Field(..., description="Component identifier")
    severity: float = Field(..., description="Severity score (unitless)")
    description: Optional[str] = Field(
        None, description="Human readable description of the impact"
    )

    class Config:
        extra = "forbid"


class ArtifactBundle(BaseModel):
    """Bundle of generated artifacts."""

    artifacts: Dict[str, str] = Field(
        default_factory=dict,
        description="Mapping of artifact name to path or URI",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional artifact metadata"
    )

    class Config:
        extra = "forbid"


class RulePackReview(BaseModel):
    """Record of a governance review for a rule pack."""

    version: str = Field(..., description="Reviewed rule pack version")
    date: datetime.date = Field(..., description="Date of the review")
    reviewer: str = Field(..., description="Person who performed the review")
    outcome: str = Field(..., description="Outcome of the review")

    class Config:
        extra = "forbid"


class RulePack(BaseModel):
    """Collection of domain and verification rules with optional risk policies."""

    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Informational metadata about the rules"
    )
    policy: Dict[str, Any] = Field(
        default_factory=dict, description="Policy settings influencing execution"
    )
    governance: Dict[str, Any] = Field(
        default_factory=dict, description="Governance stamping information"
    )
    datasets: Dict[str, Any] = Field(
        default_factory=dict, description="Dataset references used by rules"
    )
    domain_rules: List[DomainRule] = Field(
        default_factory=list, description="Rules describing domain constraints"
    )
    verification_rules: List[VerificationRule] = Field(
        default_factory=list, description="Rules verifying expected conditions"
    )
    risk_policies: Optional[RiskPolicies] = Field(
        None, description="Associated risk policies"
    )
    review: Optional[List[RulePackReview]] = Field(
        default=None, description="Review history for the rule pack"
    )

    class Config:
        extra = "forbid"
