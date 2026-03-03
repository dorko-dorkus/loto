import importlib
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
DEMO_DIR = ROOT / "demo"


def _load_client() -> TestClient:
    import apps.api.main as main

    importlib.reload(main)
    return TestClient(main.app)


def test_get_pid_svg_prefers_svg_when_present() -> None:
    drawing_id = "test_pid_svg_preferred"
    svg_path = DEMO_DIR / f"{drawing_id}.svg"
    png_path = DEMO_DIR / f"{drawing_id}.png"
    svg_path.write_text("<svg xmlns='http://www.w3.org/2000/svg'></svg>")
    png_path.write_bytes(b"\x89PNG\r\n\x1a\n")

    try:
        client = _load_client()
        res = client.get(f"/pid/{drawing_id}/svg")
        assert res.status_code == 200
        assert res.headers["content-type"].startswith("image/svg+xml")
        assert b"<svg" in res.content
    finally:
        svg_path.unlink(missing_ok=True)
        png_path.unlink(missing_ok=True)


def test_get_pid_svg_falls_back_to_png() -> None:
    drawing_id = "test_pid_png_fallback"
    png_path = DEMO_DIR / f"{drawing_id}.png"
    png_payload = b"\x89PNG\r\n\x1a\n\x00\x00\x00\x00"
    png_path.write_bytes(png_payload)

    try:
        client = _load_client()
        res = client.get(f"/pid/{drawing_id}/svg")
        assert res.status_code == 200
        assert res.headers["content-type"].startswith("image/png")
        assert res.content == png_payload
    finally:
        png_path.unlink(missing_ok=True)


def test_get_pid_svg_returns_404_when_missing() -> None:
    client = _load_client()
    res = client.get("/pid/does-not-exist-for-test/svg")
    assert res.status_code == 404
    assert "Drawing not found" in res.text


def test_overlay_rejects_non_svg_source(tmp_path: Path) -> None:
    png = tmp_path / "doc.png"
    png.write_bytes(b"\x89PNG\r\n\x1a\n")

    client = _load_client()

    payload = {
        "sources": [],
        "asset": "A-100",
        "plan": {"plan_id": "P1", "actions": [], "verifications": []},
        "sim_fail_paths": [],
        "pid_map": {"__svg__": str(png), "T1": "#a"},
    }

    res = client.post("/pid/overlay", json=payload)
    assert res.status_code == 422
    assert "requires an SVG input" in res.text


def test_overlay_returns_validation_warnings(tmp_path: Path) -> None:
    svg = tmp_path / "doc.svg"
    svg.write_text("<svg xmlns='http://www.w3.org/2000/svg'><g id='a'/></svg>")

    client = _load_client()

    payload = {
        "sources": [],
        "asset": "A-100",
        "plan": {"plan_id": "P1", "actions": [], "verifications": []},
        "sim_fail_paths": [],
        "pid_map": {"__svg__": str(svg), "T1": "#a", "T2": "#missing"},
    }

    res = client.post("/pid/overlay", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "missing selector '#missing'" in data["warnings"]
