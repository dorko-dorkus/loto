"""Rule engine for the LOTO planner.

The rule engine is responsible for loading configuration files (e.g.
YAML/JSON rule packs) that define isolation standards for each energy
domain (steam, condensate, instrument air, electrical, etc.). It also
performs static validation on the rule data and exposes it to other
components via a simple API. Only method signatures are provided here.

Example usage::

    from loto.rule_engine import RuleEngine

    engine = RuleEngine()
    rule_pack = engine.load("/config/rules.yml")
    current_hash = engine.hash(rule_pack)

Note that in this stub implementation, method bodies are intentionally
left blank (using ``pass``) because the user requested only class and
method stubs. Detailed logic will be implemented in future iterations.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml
from pydantic import ValidationError

from .models import RulePack


class RuleEngine:
    """Load and validate rule packs for the LOTO planner.

    This class encapsulates the logic for reading rule files from disk
    (typically YAML or JSON), validating their contents, and computing a
    reproducible hash of the loaded rules. The hash can be used to
    detect changes to the rule pack and to include version information
    in generated isolation plans.
    """

    def load(self, filepath: str | Path) -> RulePack:
        """Load a rule pack from the given file path.

        Parameters
        ----------
        filepath: str | Path
            The path to the rule file (YAML, JSON, etc.).

        Returns
        -------
        RulePack
            A parsed rule pack object.

        Notes
        -----
        The function supports both YAML and JSON files.  The top level of the
        parsed document must contain the keys ``domain_rules`` and
        ``verification_rules``.  ``risk_policies`` is optional.  A ``ValueError``
        is raised if the file cannot be parsed or the expected keys are
        missing.
        """

        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(path)

        suffix = path.suffix.lower()
        text = path.read_text(encoding="utf-8")
        if suffix in {".yaml", ".yml"}:
            data = yaml.safe_load(text)
        elif suffix == ".json":
            data = json.loads(text)
        else:
            raise ValueError(f"Unsupported rule file format: {suffix}")

        if not isinstance(data, dict):
            raise ValueError("Rule pack file must contain a mapping/object")

        required_keys = {"domain_rules", "verification_rules"}
        missing = required_keys - set(data)
        if missing:
            raise ValueError(
                "Missing required keys in rule pack: " + ", ".join(sorted(missing))
            )

        try:
            return RulePack(**data)
        except ValidationError as exc:  # pragma: no cover - propagated as ValueError
            raise ValueError("Invalid rule pack") from exc

    def hash(self, rule_pack: RulePack) -> str:
        """Compute a stable hash for the given rule pack.

        Parameters
        ----------
        rule_pack: RulePack
            The rule pack to hash.

        Returns
        -------
        str
            A hexadecimal digest representing the contents of the rule pack.

        Notes
        -----
        The hash is computed using SHA-256 over a canonical JSON
        representation of the rule pack.  Keys are sorted to ensure that
        semantically equivalent rule packs produce identical hashes
        regardless of dictionary key order.
        """

        data = rule_pack.model_dump(exclude_none=True)
        canonical = json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
