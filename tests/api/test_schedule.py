from fastapi.testclient import TestClient

from apps.api.main import app


def test_schedule_endpoint():
    client = TestClient(app)
    payload = {"workorder": "WO-1"}
    res = client.post("/schedule", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "schedule" in data
    assert len(data["schedule"]) > 0
    first = data["schedule"][0]
    assert {"date", "p10", "p50", "p90", "price", "hats"} <= first.keys()
    assert data["seed"] == "0"
