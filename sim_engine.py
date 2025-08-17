"""Simulation engine for the LOTO planner.

The simulation engine applies an isolation plan to domain graphs and
executes predefined stimuli (remote commands, local toggles, air
restores, etc.) to verify that isolated assets remain de-energized.
It also checks invariants such as unreachable energy paths and can be
extended to evaluate simple cause & effect logic.

This module defines basic class stubs; real implementations must be
provided by developers. The simulation engine should be deterministic
and must not control real hardware.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Any

import networkx as nx  # type: ignore

from .isolation_planner import IsolationPlan
from .rule_engine import RulePack


@dataclass
class Stimulus:
    """Represents a stimulus applied during simulation testing.

    Attributes
    ----------
    id: str
        A unique identifier for the stimulus (e.g., 'REMOTE_OPEN').
    parameters: Dict[str, Any]
        Optional parameters required for the stimulus (e.g., which
        actuator to toggle). The structure is currently undefined.
    """

    id: str
    parameters: Dict[str, Any] | None = None


@dataclass
class StimulusResult:
    """Holds the result of applying a stimulus during simulation."""

    stimulus_id: str
    result: str  # expected values: 'PASS' or 'FAIL'
    details: Dict[str, Any] | None = None


class SimReport:
    """Represents the outcome of a simulation run."""

    def __init__(self, results: List[StimulusResult], unknowns: List[str]):
        self.results = results
        self.unknowns = unknowns


class SimEngine:
    """Apply isolation plans and run stimulus tests."""

    def apply(self, plan: IsolationPlan, graphs: Dict[str, nx.MultiDiGraph]) -> Dict[str, nx.MultiDiGraph]:
        """Return a new set of graphs with isolation edges removed.

        Parameters
        ----------
        plan: IsolationPlan
            The isolation plan produced by the planner.
        graphs: Dict[str, nx.MultiDiGraph]
            The original domain graphs.

        Returns
        -------
        Dict[str, nx.MultiDiGraph]
            A copy of the graphs with isolation actions applied.

        Notes
        -----
        This stub does not implement the actual edge removal. A real
        implementation should iterate over isolation actions and remove
        the corresponding edges or mark nodes/edges inactive.
        """
        raise NotImplementedError("SimEngine.apply() is not implemented yet")

    def run_stimuli(
        self,
        applied_graphs: Dict[str, nx.MultiDiGraph],
        stimuli: List[Stimulus],
        rule_pack: "RulePack" | None = None,
    ) -> SimReport:
        """Run stimuli on the isolated graphs and check invariants.

        Parameters
        ----------
        applied_graphs: Dict[str, nx.MultiDiGraph]
            The graphs after isolation actions have been applied.
        stimuli: List[Stimulus]
            A list of stimuli to apply (remote commands, local toggles, etc.).
        rule_pack: RulePack | None
            Optional rule pack for domain-specific behaviour; may not be
            necessary for simple reachability checks.

        Returns
        -------
        SimReport
            The simulation report containing results per stimulus and
            a list of unknowns encountered during the process.

        Notes
        -----
        This stub does not implement any simulation logic. Developers
        should add reachability checks and, optionally, simple cause &
        effect evaluation.
        """
        raise NotImplementedError("SimEngine.run_stimuli() is not implemented yet")