from pathlib import Path
import json

import pytest

from loto.config import ConfigError, validate_env_vars
from loto.loggers import configure_logging


def test_validate_env_vars_reports_missing(monkeypatch, capsys):
    """Ensure missing env vars are reported with a table."""
    # pick a known key from the example file
    example = Path(__file__).resolve().parent.parent / ".env.example"
    key = "DATA_IN"
    assert any(line.startswith(f"{key}=") for line in example.read_text().splitlines())
    monkeypatch.delenv(key, raising=False)

    configure_logging()
    with pytest.raises(ConfigError):
        validate_env_vars(example)

    captured = capsys.readouterr()
    lines = (captured.out + captured.err).strip().splitlines()
    msgs = [json.loads(json.loads(line)["msg"])["msg"] for line in lines if line]
    assert any(key in msg and msg.rstrip().endswith("N") for msg in msgs)
