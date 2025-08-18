from fastapi.testclient import TestClient

from apps.api.main import app


def test_schedule_endpoint():
    client = TestClient(app)
    payload = {
        "tasks": {
            "a": {"duration": 4},
            "b": {"duration": 2, "predecessors": ["a"]},
        },
        "runs": 5,
        "seed": 42,
        "power_curve": [[0, 1], [6, 1]],
        "price_curve": [[0, 5], [6, 5]],
    }
    res = client.post("/schedule", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["p10"] == data["p50"] == data["p90"] == 6
    assert data["expected_cost"] == 30.0
    assert data["violations"] == []
    assert data["seed"] == 42
