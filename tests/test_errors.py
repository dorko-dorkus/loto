import pytest

from loto.errors import (
    ConfigError,
    GraphError,
    IntegrationError,
    LotoError,
    PlanError,
    RenderError,
    RulesError,
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


def test_loto_error_str_contains_code() -> None:
    err = LotoError("X99", "oops")
    assert err.code == "X99"
    assert err.hint == "oops"
    assert "X99" in str(err)
    assert "oops" in str(err)
