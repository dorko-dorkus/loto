from fastapi.testclient import TestClient

from apps.api.main import app
from loto.errors import AssetTagNotFoundError, GenerationError
from loto.errors import ImportError as LotoImportError
from loto.errors import UnisolatablePathError, ValidationError


@app.get("/test/validation")
def _raise_validation() -> None:  # pragma: no cover - endpoint for testing
    raise ValidationError("bad input")


@app.get("/test/asset-tag-not-found")
def _raise_asset_tag_not_found() -> None:  # pragma: no cover - endpoint for testing
    raise AssetTagNotFoundError("UA-404", hint="graph contains 5 nodes")


@app.get("/test/unisolatable")
def _raise_unisolatable() -> None:  # pragma: no cover - endpoint for testing
    raise UnisolatablePathError(
        target_identifier="UA-500",
        reason="no isolation points on any source→target path",
        hint="add an inline valve on each source-to-target path",
    )


@app.get("/test/import")
def _raise_import() -> None:  # pragma: no cover - endpoint for testing
    raise LotoImportError("failed import")


@app.get("/test/generation")
def _raise_generation() -> None:  # pragma: no cover - endpoint for testing
    raise GenerationError("cannot generate")


def test_validation_error_handler() -> None:
    client = TestClient(app)
    res = client.get("/test/validation")
    assert res.status_code == 400
    assert res.json() == {"code": "VALIDATION_ERROR", "message": "bad input"}


def test_asset_tag_not_found_error_handler() -> None:
    client = TestClient(app)
    res = client.get("/test/asset-tag-not-found")
    assert res.status_code == 400
    assert res.json() == {
        "code": "ASSET_TAG_NOT_FOUND",
        "message": "asset_tag 'UA-404' not found in graph",
        "hint": "graph contains 5 nodes",
    }


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


def test_unisolatable_error_handler() -> None:
    client = TestClient(app)
    res = client.get("/test/unisolatable")
    assert res.status_code == 422
    assert res.json() == {
        "code": "UNISOLATABLE_PATH",
        "message": "unable to isolate target 'UA-500': no isolation points on any source→target path",
        "target": "UA-500",
        "reason": "no isolation points on any source→target path",
        "hint": "add an inline valve on each source-to-target path",
    }
