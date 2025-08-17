"""Core data models for lock-out/tag-out planning utilities.

This module defines strict Pydantic models used throughout the project.  All
models forbid extra fields to help surface typing mistakes early and include
basic metadata/units for numeric values.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DomainRule(BaseModel):
    """Represents a rule describing domain-specific constraints."""

    name: str = Field(..., description="Rule name")
    expression: str = Field(..., description="Expression used to evaluate the rule")

    class Config:
        extra = "forbid"


class VerificationRule(BaseModel):
    """Represents a rule verifying an expected condition."""

    name: str = Field(..., description="Verification rule name")
    check: str = Field(..., description="Expression or callable for verification")

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
    weight: Optional[float] = Field(
        None, description="Edge weight (unitless)")

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
    method: str = Field(
        ..., description="Isolation method such as 'lock' or 'tag'"
    )
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

    class Config:
        extra = "forbid"


class SimReport(BaseModel):
    """Collection of simulation results."""

    results: List[SimResultItem] = Field(
        default_factory=list, description="Individual simulation results"
    )
    total_time_s: float = Field(
        ..., description="Total simulation time in seconds"
    )

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


class RulePack(BaseModel):
    """Collection of domain and verification rules with optional risk policies."""

    domain_rules: List[DomainRule] = Field(
        default_factory=list, description="Rules describing domain constraints"
    )
    verification_rules: List[VerificationRule] = Field(
        default_factory=list, description="Rules verifying expected conditions"
    )
    risk_policies: Optional[RiskPolicies] = Field(
        None, description="Associated risk policies"
    )

    class Config:
        extra = "forbid"
