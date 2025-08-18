from typing import Optional

from fastapi import FastAPI, File, UploadFile

app = FastAPI(title="loto API")


@app.get("/healthz", include_in_schema=False)
async def healthz() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/blueprint")
async def post_blueprint(
    csv: Optional[UploadFile] = File(default=None),
    workorder_id: Optional[str] = None,
) -> dict[str, str]:
    """Placeholder for blueprint upload or work order reference."""
    return {"detail": "Not implemented"}


@app.post("/schedule")
async def post_schedule(payload: dict) -> dict[str, str]:
    """Placeholder for schedule creation."""
    _ = payload  # suppress unused variable warning
    return {"detail": "Not implemented"}


@app.get("/workorders/{workorder_id}")
async def get_workorder(workorder_id: str) -> dict[str, str]:
    """Mock work order fetch."""
    return {"workorder_id": workorder_id, "status": "mocked"}
