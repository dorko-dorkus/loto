import importlib

from fastapi.testclient import TestClient


def test_version_endpoint():
    import apps.api.main as main

    importlib.reload(main)
    client = TestClient(main.app)
    res = client.get("/version")
    assert res.status_code == 200
    data = res.json()
    assert data["version"] == main.APP_VERSION
    assert res.headers["X-Env"] == main.ENV_BADGE


def test_openapi_includes_health_and_version():
    import apps.api.main as main

    client = TestClient(main.app)
    spec = client.get("/openapi.json").json()
    assert "/healthz" in spec["paths"]
    assert "/version" in spec["paths"]
