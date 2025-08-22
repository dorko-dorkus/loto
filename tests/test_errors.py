from typing import Any, Type

import pytest

from loto.errors import (
    ConfigError,
    GenerationError,
    GraphError,
    ImportError,
    IntegrationError,
    LotoError,
    PlanError,
    RenderError,
    RulesError,
    ValidationError,
)


@pytest.mark.parametrize(
    "exc_cls",
    [ConfigError, RulesError, GraphError, PlanError, IntegrationError, RenderError],
)
def test_error_subclassing(exc_cls: type[LotoError]) -> None:
    err = exc_cls("E001", "something went wrong")
    assert isinstance(err, LotoError)
    assert err.code == "E001"
    assert err.hint == "something went wrong"
    # The string representation should include both the code and hint
    msg = str(err)
    assert "E001" in msg and "something went wrong" in msg


@pytest.mark.parametrize(
    "exc_cls, code",
    [
        (ValidationError, "VALIDATION_ERROR"),
        (ImportError, "IMPORT_ERROR"),
        (GenerationError, "GENERATION_ERROR"),
    ],
)
def test_fixed_code_errors(exc_cls: Type[Any], code: str) -> None:
    err = exc_cls("something went wrong")
    assert err.code == code
    assert err.hint == "something went wrong"
    msg = str(err)
    assert code in msg and "something went wrong" in msg


def test_loto_error_str_contains_code() -> None:
    err = LotoError("X99", "oops")
    assert err.code == "X99"
    assert err.hint == "oops"
    assert "X99" in str(err)
    assert "oops" in str(err)


def test_demo_adapter_used_when_env_missing(monkeypatch, tmp_path) -> None:
    from pathlib import Path

    from loto.integrations import DemoIntegrationAdapter, get_integration_adapter
    from loto.models import IsolationAction, IsolationPlan, SimReport

    for key in [
        "MAXIMO_BASE_URL",
        "MAXIMO_APIKEY",
        "MAXIMO_OS_WORKORDER",
        "MAXIMO_OS_ASSET",
    ]:
        monkeypatch.delenv(key, raising=False)

    monkeypatch.chdir(tmp_path)

    adapter = get_integration_adapter()
    assert isinstance(adapter, DemoIntegrationAdapter)

    work_order = adapter.fetch_work_order("WO-1")
    assert work_order["id"] == "WO-1"

    plan = IsolationPlan(
        plan_id="P1",
        actions=[IsolationAction(component_id="C1", method="lock")],
    )
    child_ids = adapter.create_child_work_orders("WO-1", plan)
    assert child_ids and child_ids[0].startswith("WO-1")

    sim_report = SimReport(results=[], total_time_s=0.0)
    adapter.attach_artifacts("WO-1", plan, sim_report, {"k": "v"}, b"pdf")
    doc_dir = Path("out") / "doclinks"
    assert (doc_dir / "WO-1.json").exists()
    assert (doc_dir / "WO-1.pdf").exists()
