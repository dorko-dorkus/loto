from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field


class OverlayRequest(BaseModel):
    """Request body for generating PID overlay."""

    workorder_id: str = Field(..., description="Identifier of the work order")
    plan: Dict[str, Any] = Field(default_factory=dict, description="Isolation plan")
    simulation: Dict[str, Any] = Field(
        default_factory=dict, description="Simulation results"
    )

    class Config:
        extra = "forbid"


class OverlayResponse(BaseModel):
    """Overlay payload merging plan and simulation data."""

    overlay: Dict[str, Any] = Field(default_factory=dict, description="Overlay JSON")

    class Config:
        extra = "forbid"


router = APIRouter()


@router.get("/{drawing_id}/svg")
async def get_pid_svg(drawing_id: str) -> StreamingResponse:
    """Stream the SVG drawing for the given identifier."""

    base = Path(__file__).resolve().parents[2] / "demo"
    file_path = base / f"{drawing_id}.svg"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Drawing not found")

    return StreamingResponse(open(file_path, "rb"), media_type="image/svg+xml")


@router.post("/overlay", response_model=OverlayResponse)
async def post_pid_overlay(payload: OverlayRequest) -> OverlayResponse:
    """Return overlay data for the provided work order, plan and simulation."""

    overlay = {
        "workorder_id": payload.workorder_id,
        "plan": payload.plan,
        "simulation": payload.simulation,
    }
    return OverlayResponse(overlay=overlay)
