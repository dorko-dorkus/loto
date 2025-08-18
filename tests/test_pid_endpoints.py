from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.api.pid_endpoints import OverlayResponse
from apps.api.pid_endpoints import router as pid_router

app = FastAPI()
app.include_router(pid_router, prefix="/pid")
client = TestClient(app)


def test_get_pid_svg_serves_svg():
    response = client.get("/pid/sample/svg")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/svg+xml"
    assert response.text.startswith("<svg")


def test_post_overlay_matches_schema():
    payload = {
        "workorder_id": "WO123",
        "plan": {"step": 1},
        "simulation": {"result": "ok"},
    }
    response = client.post("/pid/overlay", json=payload)
    assert response.status_code == 200
    data = OverlayResponse(**response.json())
    assert data.overlay["workorder_id"] == "WO123"
    assert data.overlay["plan"] == {"step": 1}
    assert data.overlay["simulation"] == {"result": "ok"}
