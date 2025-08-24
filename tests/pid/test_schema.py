from pathlib import Path

import pytest

from loto.pid.registry import load_registry
from loto.pid.schema import load_tag_map


def _write(tmp_path: Path, name: str, content: str) -> Path:
    path = tmp_path / name
    path.write_text(content)
    return path


def test_load_tag_map_valid(tmp_path: Path) -> None:
    path = _write(tmp_path, "map.yaml", "T1: '#a'\nT2:\n  - '#b'\n")
    tag_map = load_tag_map(path)
    assert tag_map.model_dump() == {"T1": ["#a"], "T2": ["#b"]}


def test_load_tag_map_duplicate_tag(tmp_path: Path) -> None:
    path = _write(tmp_path, "map.yaml", "T1: '#a'\nT1: '#b'\n")
    with pytest.raises(ValueError) as exc:
        load_tag_map(path)
    assert f"{path}:2" in str(exc.value)
    assert "duplicate tag" in str(exc.value)


def test_load_tag_map_empty_selector(tmp_path: Path) -> None:
    path = _write(tmp_path, "map.yaml", "T1: ''\n")
    with pytest.raises(ValueError) as exc:
        load_tag_map(path)
    assert f"{path}:1" in str(exc.value)
    assert "selector" in str(exc.value)


def test_load_tag_map_wrong_type(tmp_path: Path) -> None:
    path = _write(tmp_path, "map.yaml", "T1: [1, 2]\n")
    with pytest.raises(ValueError) as exc:
        load_tag_map(path)
    assert f"{path}:1" in str(exc.value)


def test_load_registry_validates_tag_map(tmp_path: Path) -> None:
    tag_map = _write(tmp_path, "map.yaml", "T1: '#a'\n")
    registry = _write(
        tmp_path,
        "registry.yaml",
        """
        pids:
          test:
            svg: doc.svg
            tag_map: map.yaml
        """.strip(),
    )
    loaded = load_registry(registry)
    assert loaded.pids["test"].tag_map == tag_map


def test_load_registry_invalid_tag_map(tmp_path: Path) -> None:
    tag_map = _write(tmp_path, "map.yaml", "T1: 123\n")
    registry = _write(
        tmp_path,
        "registry.yaml",
        """
        pids:
          test:
            svg: doc.svg
            tag_map: map.yaml
        """.strip(),
    )
    with pytest.raises(ValueError) as exc:
        load_registry(registry)
    assert str(tag_map) in str(exc.value)


def test_load_registry_reports_warnings(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "doc.svg",
        "<svg xmlns='http://www.w3.org/2000/svg'><g id='a'/></svg>",
    )
    _write(tmp_path, "map.yaml", "T1: '#a'\nT2: '#missing'\n")
    registry = _write(
        tmp_path,
        "registry.yaml",
        """
        pids:
          demo:
            svg: doc.svg
            tag_map: map.yaml
        """.strip(),
    )
    loaded = load_registry(registry)
    warnings = loaded.pids["demo"].warnings
    assert "missing selector '#missing'" in warnings
