"""Pytest configuration for the loto package."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure the project root is on ``sys.path`` so that ``import loto`` works when
# tests are executed without installing the package.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
