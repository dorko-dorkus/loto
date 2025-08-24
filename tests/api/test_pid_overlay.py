import importlib

from fastapi.testclient import TestClient


def test_overlay_returns_validation_warnings(tmp_path):
    svg = tmp_path / "doc.svg"
    svg.write_text("<svg xmlns='http://www.w3.org/2000/svg'><g id='a'/></svg>")

    import apps.api.main as main

    importlib.reload(main)

    client = TestClient(main.app)

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
