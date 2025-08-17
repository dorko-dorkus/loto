"""Top-level package for the LOTO planner.

This package contains the core components needed to compute lockout–tagout
plans, run simulation tests, and integrate with external systems like
Maximo, WAPR and Coupa. Only class and method stubs are defined here.

Each module exposes a primary class responsible for a distinct concern:

* :mod:`loto.rule_engine` – Loading and validating rule packs.
* :mod:`loto.graph_builder` – Building connectivity graphs from raw data.
* :mod:`loto.isolation_planner` – Computing isolation plans using cut-set algorithms.
* :mod:`loto.sim_engine` – Applying isolation plans and running stimulus tests.
* :mod:`loto.integrations` – Adapters for external systems (CMMS, permit, procurement).
* :mod:`loto.renderer` – Generating human‐readable plan documents.
* :mod:`loto.cli` – Command line entry points (not implemented yet).
"""

__all__ = [
    "RuleEngine",
    "GraphBuilder",
    "IsolationPlanner",
    "SimEngine",
    "IntegrationAdapter",
    "Renderer",
]

# Import statements are deferred until runtime to avoid circular imports
