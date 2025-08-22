"""Pytest configuration for the loto package."""

import sys
from pathlib import Path

from dotenv import load_dotenv

# Ensure project root is on the import path so ``import loto`` works during
# test collection even when ``pytest`` changes the working directory.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load default environment variables for tests.
load_dotenv(PROJECT_ROOT / ".env.example", override=False)
