#!/usr/bin/env python3
"""Export PPTX slides to PNG images for demo assets.

Usage:
    python scripts/export_pptx_slides_to_png.py path/to/deck.pptx --output-dir demo/pids

Optional external dependencies:
- LibreOffice (`soffice`) available on PATH. This script shells out to:
      soffice --headless --convert-to png --outdir <dir> <deck.pptx>
- If LibreOffice is unavailable, install it first (for example via apt/homebrew)
  and rerun the script.

Output files follow LibreOffice naming (`<deck_name>.png` or numbered variants
for multi-slide exports), and are placed in the provided output directory.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pptx", type=Path, help="Path to source PPTX file")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("demo/pids"),
        help="Directory where PNG files will be written (default: demo/pids)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if not args.pptx.exists():
        raise FileNotFoundError(f"PPTX not found: {args.pptx}")
    if args.pptx.suffix.lower() != ".pptx":
        raise ValueError(f"Expected a .pptx file, got: {args.pptx.name}")

    soffice = shutil.which("soffice")
    if not soffice:
        raise RuntimeError(
            "LibreOffice `soffice` was not found on PATH. Install LibreOffice to use this exporter."
        )

    args.output_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        soffice,
        "--headless",
        "--convert-to",
        "png",
        "--outdir",
        str(args.output_dir),
        str(args.pptx),
    ]
    subprocess.run(cmd, check=True)
    print(f"Export complete: {args.pptx} -> {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
