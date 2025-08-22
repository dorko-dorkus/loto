from fastapi.testclient import TestClient

from apps.api.main import app
from loto.errors import GenerationError
from loto.errors import ImportError as LotoImportError
from loto.errors import ValidationError


@app.get("/test/validation")
def _raise_validation():  # pragma: no cover - endpoint for testing
    raise ValidationError("bad input")


@app.get("/test/import")
def _raise_import():  # pragma: no cover - endpoint for testing
    raise LotoImportError("failed import")


@app.get("/test/generation")
def _raise_generation():  # pragma: no cover - endpoint for testing
    raise GenerationError("cannot generate")


def test_validation_error_handler() -> None:
    client = TestClient(app)
    res = client.get("/test/validation")
    assert res.status_code == 400
    assert res.json() == {"code": "VALIDATION_ERROR", "message": "bad input"}


def test_import_error_handler() -> None:
    client = TestClient(app)
    res = client.get("/test/import")
    assert res.status_code == 500
    assert res.json() == {"code": "IMPORT_ERROR", "message": "failed import"}


def test_generation_error_handler() -> None:
    client = TestClient(app)
    res = client.get("/test/generation")
    assert res.status_code == 500
    assert res.json() == {"code": "GENERATION_ERROR", "message": "cannot generate"}
