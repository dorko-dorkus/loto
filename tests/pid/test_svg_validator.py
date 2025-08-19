from loto.pid.validator import validate_svg_map


def test_validator_reports_warnings(tmp_path):
    svg = tmp_path / "d.svg"
    svg.write_text(
        "<svg xmlns='http://www.w3.org/2000/svg'>"
        "<g id='a'/>"
        "<g id='b'/>"
        "<g class='foo bar'/>"
        "</svg>"
    )
    pid_map = tmp_path / "pid_map.yaml"
    pid_map.write_text(
        "\n".join(
            [
                "tag1: '#a'",
                "tag2: '#missing'",
                "tag3: '.foo'",
                "dup1: '#dup'",
                "dup2: '#dup'",
            ]
        )
    )

    report = validate_svg_map(svg, pid_map)
    warnings = report.warnings

    assert "missing selector '#missing'" in warnings
    assert "missing selector '#dup'" in warnings
    assert any("duplicate tag '#dup'" in w for w in warnings)
    assert "unmapped tag '#b'" in warnings
    assert "unmapped tag '.bar'" in warnings
