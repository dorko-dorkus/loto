from pathlib import Path

import pytest

from loto.config import ConfigError, validate_env_vars


def test_validate_env_vars_reports_missing(monkeypatch, capsys):
    """Ensure missing env vars are reported with a table."""
    # pick a known key from the example file
    example = Path(__file__).resolve().parent.parent / ".env.example"
    key = "DATA_IN"
    assert any(line.startswith(f"{key}=") for line in example.read_text().splitlines())
    monkeypatch.delenv(key, raising=False)

    with pytest.raises(ConfigError):
        validate_env_vars(example)

    out = capsys.readouterr().out
    assert key in out
    lines = out.strip().splitlines()
    row = next(line for line in lines if key in line)
    assert row.rstrip().endswith("N")
