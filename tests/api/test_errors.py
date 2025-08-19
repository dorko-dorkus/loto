import logging

from fastapi.testclient import TestClient

from apps.api.main import app


@app.get("/force_error")
def force_error() -> None:
    raise RuntimeError("boom")


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
