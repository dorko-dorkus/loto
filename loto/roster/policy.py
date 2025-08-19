from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

_DEFAULT_PATH = Path(__file__).resolve().parents[2] / "config" / "hats_policy.yaml"


def load_policy(path: str | Path = _DEFAULT_PATH) -> dict[str, Any]:
    """Return policy configuration from *path*.

    The file is expected to contain YAML with keys defining ranking and chooser
    behaviour.  The returned mapping is normalised to the keys used by the
    ranking and scheduling helpers.
    """

    data = yaml.safe_load(Path(path).read_text()) or {}
    policy: dict[str, Any] = {
        "weights": data.get("weights"),
        "half_life": data.get("half_life"),
        "pseudo_count": data.get("pseudo_count"),
        "incident_cap": data.get("incident_cap"),
        "rotation_limit": data.get("rotation_window"),
        "utilization_cap": data.get("daily_utilization_cap"),
    }
    return policy
