from pathlib import Path

from loto.pid.validator import validate_svg_map


def _write_svg(path: Path) -> Path:
    svg_path = path / "doc.svg"
    svg_path.write_text(
        "<svg xmlns='http://www.w3.org/2000/svg'>\n"
        "        <rect id='a'/>\n"
        "        <circle class='foo bar'/>\n"
        "        </svg>"
    )
    return svg_path


def _write_map(path: Path) -> Path:
    map_path = path / "map.yaml"
    map_path.write_text(
        "\n".join(
            [
                "T1: '#a'",
                "T2: '.foo'",
                "T3: '#missing'",
                "T4: '.missing'",
            ]
        )
    )
    return map_path


def test_validate_svg_map_reports_missing(tmp_path: Path) -> None:
    svg = _write_svg(tmp_path)
    mapping = _write_map(tmp_path)
    report = validate_svg_map(svg, mapping)
    assert report.missing_selectors == ["#missing", ".missing"]
