"""Pytest configuration for the loto package."""

import sys
from pathlib import Path


# Ensure project root is on the import path so ``import loto`` works during
# test collection even when ``pytest`` changes the working directory.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
