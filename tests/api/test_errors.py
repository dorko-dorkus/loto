import logging

from fastapi import HTTPException
from fastapi.testclient import TestClient

from apps.api.main import app


@app.get("/force_error")
def force_error() -> None:
    raise RuntimeError("boom")


@app.get("/force_http_error")
def force_http_error() -> None:
    raise HTTPException(status_code=418, detail="teapot")


def test_error_envelope_and_logging(caplog) -> None:
    client = TestClient(app)
    with caplog.at_level(logging.ERROR):
        response = client.get("/force_error")
    assert response.status_code == 500
    payload = response.json()
    assert payload["error"]["code"] == 500
    assert payload["error"]["message"] == "Internal Server Error"
    assert "boom" in payload["error"]["details"]
    assert any("request_id=" in record.message for record in caplog.records)


def test_http_exception_envelope_and_logging(caplog) -> None:
    client = TestClient(app)
    with caplog.at_level(logging.WARNING):
        response = client.get("/force_http_error")
    assert response.status_code == 418
    payload = response.json()
    assert payload["error"]["code"] == 418
    assert payload["error"]["message"] == "teapot"
    assert payload["error"]["details"] == "teapot"
    assert any("request_id=" in record.message for record in caplog.records)
