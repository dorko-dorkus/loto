from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List

import yaml
from pydantic import RootModel, ValidationError, field_validator, model_validator

SELECTOR_RE = re.compile(r"^#?[A-Za-z0-9_.:-]+$")


class TagSelectors(RootModel[List[str]]):
    """List of CSS selectors for a single tag."""

    @model_validator(mode="before")
    @classmethod
    def _coerce(cls, value: object) -> List[str]:
        if isinstance(value, str):
            value = [value]
        elif isinstance(value, list):
            value = list(value)
        else:
            raise ValueError("selector must be string or list of strings")
        if not value:
            raise ValueError("selector must not be empty")
        return value

    @field_validator("root")
    @classmethod
    def _validate_selector(cls, selectors: List[str]) -> List[str]:
        for selector in selectors:
            if not SELECTOR_RE.fullmatch(selector):
                raise ValueError("invalid selector")
        return selectors


class PidTagMap(RootModel[Dict[str, TagSelectors]]):
    """Mapping of tag identifiers to CSS selectors."""


class _TagMapLoader(yaml.SafeLoader):
    """YAML loader that records line numbers and rejects duplicate keys."""

    def __init__(self, stream) -> None:
        super().__init__(stream)
        self.tag_lines: Dict[str, int] = {}


def _construct_mapping(loader: _TagMapLoader, node, deep=False):  # type: ignore[override]
    mapping = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if not isinstance(key, str):
            raise ValueError(
                f"{loader.name}:{key_node.start_mark.line + 1}: tag must be a string"
            )
        if key in mapping:
            raise ValueError(
                f"{loader.name}:{key_node.start_mark.line + 1}: duplicate tag '{key}'"
            )
        loader.tag_lines[key] = value_node.start_mark.line + 1
        value = loader.construct_object(value_node, deep=deep)
        if not isinstance(value, (str, list)):
            raise ValueError(
                f"{loader.name}:{value_node.start_mark.line + 1}: selector must be string or list of strings"
            )
        mapping[key] = value
    return mapping


_TagMapLoader.add_constructor(  # type: ignore[attr-defined]
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping
)


def load_tag_map(path: str | Path) -> PidTagMap:
    """Load and validate a tag map from ``path``."""

    path = Path(path)
    with path.open("r") as fh:
        loader = _TagMapLoader(fh)
        loader.name = str(path)
        try:
            data = loader.get_single_data() or {}
        finally:
            loader.dispose()
        line_map = loader.tag_lines

    if not isinstance(data, dict):
        raise ValueError(f"{path}:1: expected mapping of tags to selectors")

    try:
        return PidTagMap.model_validate(data)
    except ValidationError as exc:  # pragma: no cover - re-raise with line info
        err = exc.errors()[0]
        loc = err.get("loc", ())
        if loc:
            tag = loc[0]
            line = line_map.get(str(tag), 1)
        else:
            line = 1
        raise ValueError(f"{path}:{line}: {err['msg']}") from None
