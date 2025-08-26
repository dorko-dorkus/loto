"""Project-wide constants."""

from __future__ import annotations

import os

DOC_CATEGORY = "Permit/LOTO"
DOC_CATEGORY_DIR = DOC_CATEGORY.replace("/", "_")

# Checklist item verifying the permit has been closed and uploaded.
CHECKLIST_HAND_BACK = "Permit Closed & Hand-back uploaded"


def _env_flag(name: str, default: bool) -> bool:
    """Return a boolean environment flag with ``default`` fallback."""

    return os.getenv(name, str(default)).lower() in {"1", "true", "yes"}


# Feature flags for HATS compliance checks.
HATS_FAILCLOSE_CRITICAL = _env_flag("HATS_FAILCLOSE_CRITICAL", True)
HATS_WARN_ONLY_MECH = _env_flag("HATS_WARN_ONLY_MECH", False)

# Work order status domain descriptions
WOSTATUS_DESCRIPTIONS = {
    "SCHED": "Scheduled",
    "INPRG": "In Progress",
    "HOLD": "On Hold",
    "COMP": "Completed",
}
