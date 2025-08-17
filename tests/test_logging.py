import json

from loto.logging_setup import get_logger, init_logging


def test_json_log_contains_context(capsys):
    init_logging(verbosity=1)
    logger = get_logger().bind(wo="WO-1", asset="A-1", rule_hash="deadbeef")
    logger.info("planning start")

    captured = capsys.readouterr().out.strip()
    assert captured, "No log output captured"
    data = json.loads(captured)
    assert data["wo"] == "WO-1"
    assert data["asset"] == "A-1"
    assert data["rule_hash"] == "deadbeef"
    assert data["message"] == "planning start"
    assert data["level"] == "INFO"


def test_verbosity_respected(capsys):
    # Verbosity 0 should suppress INFO
    init_logging(verbosity=0)
    log = get_logger()
    log.info("info message")
    assert capsys.readouterr().out == ""

    # Verbosity 2 should show DEBUG
    init_logging(verbosity=2)
    log = get_logger()
    log.debug("debug message")
    out = capsys.readouterr().out.strip()
    data = json.loads(out)
    assert data["message"] == "debug message"
    assert data["level"] == "DEBUG"
