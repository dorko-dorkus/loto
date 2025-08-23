import importlib
import os

from fastapi.testclient import TestClient


def test_disallowed_origin(monkeypatch):
    original = os.getenv("CORS_ORIGINS", "")
    monkeypatch.setenv("CORS_ORIGINS", "https://allowed.example.com")
    import apps.api.main as main

    importlib.reload(main)
    client = TestClient(main.app)

    response = client.options(
        "/healthz",
        headers={
            "Origin": "https://evil.example.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers

    monkeypatch.setenv("CORS_ORIGINS", original)
    importlib.reload(main)
