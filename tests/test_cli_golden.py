from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def test_demo_command_creates_doclinks(tmp_path: Path) -> None:
    env = {**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1])}
    result = subprocess.run(
        [sys.executable, "-m", "loto.cli", "demo"],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    doclinks_dir = tmp_path / "out" / "doclinks"
    assert doclinks_dir.is_dir()
    pdfs = list(doclinks_dir.glob("*.pdf"))
    jsons = list(doclinks_dir.glob("*.json"))
    assert len(pdfs) == 1
    assert len(jsons) == 1
    assert pdfs[0].stem == jsons[0].stem
    with jsons[0].open() as f:
        data = json.load(f)
    assert data.get("category") == "Permit/LOTO"
