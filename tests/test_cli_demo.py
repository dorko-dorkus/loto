from pathlib import Path

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
