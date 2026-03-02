import pytest

from loto.service import blueprints


def test_parse_component_ids_strict_raises_on_malformed() -> None:
    with pytest.raises(ValueError, match="Malformed component_id 'steam:src-VALVE'"):
        blueprints.parse_component_ids(["steam:src-VALVE"], strict=True)


def test_parse_component_ids_non_strict_skips_and_warns(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[tuple[str, dict[str, str]]] = []

    def fake_warning(event: str, **kw: str) -> None:
        events.append((event, kw))

    monkeypatch.setattr(blueprints.logger, "warning", fake_warning)

    parsed = blueprints.parse_component_ids(
        ["steam:src->V1", "bad", "air:A->B"],
        strict=False,
    )

    assert parsed == [("steam", "src", "V1"), ("air", "A", "B")]
    assert events == [("invalid_component_id", {"component_id": "bad"})]


def test_parse_component_ids_defaults_to_env_setting(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(blueprints, "STRICT_PERMIT_ISOLATIONS", True)

    with pytest.raises(ValueError, match="Malformed component_id 'steam:src-VALVE'"):
        blueprints.parse_component_ids(["steam:src-VALVE"])
