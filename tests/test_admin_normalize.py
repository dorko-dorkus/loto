from fastapi.testclient import TestClient

from apps.api.main import app


def test_admin_normalize_endpoint():
    client = TestClient(app)
    items = [
        {
            "description": "M12x35 bolt 8.8",
            "unit": "L",
            "qty_onhand": 5,
            "reorder_point": 0,
        }
    ]
    res = client.post(
        "/admin/normalize", params={"dry_run": "true"}, json={"items": items}
    )
    assert res.status_code == 200
    assert res.json()["diffs"] == [
        {"description": "M12x35 bolt 8.8", "from": "L", "to": "ea"}
    ]

    res = client.post(
        "/admin/normalize", params={"dry_run": "false"}, json={"items": items}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["anomalies"] == 0
    assert data["items"][0]["unit"] == "ea"
