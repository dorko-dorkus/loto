import json
from pathlib import Path

from PyPDF2 import PdfReader
from typer.testing import CliRunner

from loto.cli import cli


def test_demo_command_creates_outputs(tmp_path: Path) -> None:
    runner = CliRunner()
    out_dir = tmp_path / "out"
    result = runner.invoke(cli, ["demo", "--out", str(out_dir)])

    assert result.exit_code == 0
    assert "PDF + JSON saved" in result.stdout
    assert (out_dir / "LOTO_A.pdf").exists()
    assert (out_dir / "LOTO_A.json").exists()

    with (out_dir / "LOTO_A.json").open("r", encoding="utf-8") as f:
        payload = json.load(f)
    assert payload["plan"]["hazards"] == ["Radiation", "Asphyxiation"]
    assert payload["plan"]["controls"] == ["Shielding", "Ventilation"]

    reader = PdfReader(out_dir / "LOTO_A.pdf")
    text = "".join(page.extract_text() for page in reader.pages)
    assert "Radiation" in text
    assert "Shielding" in text
