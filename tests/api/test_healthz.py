import importlib

from fastapi.testclient import TestClient


def test_healthz_reports_components(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_CAPACITY", "5")
    monkeypatch.setenv("RATE_LIMIT_INTERVAL", "30")
    import apps.api.main as main

    importlib.reload(main)

    client = TestClient(main.app)
    res = client.get("/healthz")
    assert res.status_code == 200
    data = res.json()
    assert data["rate_limit"]["capacity"] == 5
    assert data["rate_limit"]["interval"] == 30.0
    assert data["adapters"]["maximo"]["status"] == "mock"
    assert data["adapters"]["coupa"]["status"] == "mock"
    assert data["db"]["head"] == "0002"
    assert data["integrity"]["missing_assets"] == 0
    assert data["integrity"]["missing_locations"] == 0

    monkeypatch.setenv("RATE_LIMIT_CAPACITY", "100000")
    monkeypatch.setenv("RATE_LIMIT_INTERVAL", "60")
    importlib.reload(main)


def test_healthz_fails_on_missing_demo_data(monkeypatch):
    import apps.api.main as main

    importlib.reload(main)
    monkeypatch.setattr(
        main.demo_data,
        "validate",
        lambda: {
            "missing_assets": [{"workorder": "1", "assetnum": None}],
            "missing_locations": [],
        },
    )
    client = TestClient(main.app)
    res = client.get("/healthz")
    assert res.status_code == 503
    data = res.json()
    assert data["missing_assets"] == 1
    assert data["missing_locations"] == 0
