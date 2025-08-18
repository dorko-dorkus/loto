from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Dict, Iterable, List, cast

import yaml
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from loto.models import IsolationPlan
from loto.pid import build_overlay

router = APIRouter(prefix="/pid", tags=["pid"])


class OverlayRequest(BaseModel):
    """Request model for the /pid/overlay endpoint."""

    sources: List[str] = Field(default_factory=list, description="Energy sources")
    asset: str = Field(..., description="Asset tag under isolation")
    plan: IsolationPlan
    sim_fail_paths: List[List[str]] = Field(
        default_factory=list,
        description="Paths that still allow energy flow after simulation",
    )
    pid_map: Dict[str, object] = Field(
        default_factory=dict,
        description="Mapping of component tags to CSS selectors",
    )

    class Config:
        extra = "forbid"


class OverlayBadge(BaseModel):
    selector: str
    type: str

    class Config:
        extra = "forbid"


class OverlayPath(BaseModel):
    id: str
    selectors: List[str]

    class Config:
        extra = "forbid"


class OverlayResponse(BaseModel):
    highlight: List[str] = Field(default_factory=list)
    badges: List[OverlayBadge] = Field(default_factory=list)
    paths: List[OverlayPath] = Field(default_factory=list)

    class Config:
        extra = "forbid"


@router.get("/{drawing_id}/svg")
async def get_pid_svg(drawing_id: str) -> StreamingResponse:
    """Stream the raw SVG for a given drawing identifier."""

    base = Path(__file__).resolve().parents[2] / "demo"
    svg_path = base / f"{drawing_id}.svg"
    if not svg_path.exists():
        raise HTTPException(status_code=404, detail="Drawing not found")
    return StreamingResponse(svg_path.open("rb"), media_type="image/svg+xml")


@router.post("/overlay", response_model=OverlayResponse)
async def post_overlay(payload: OverlayRequest) -> OverlayResponse:
    """Return overlay JSON for a work order, plan, and simulation results."""

    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as fh:
        yaml.safe_dump(payload.pid_map, fh)
        map_path = Path(fh.name)
    try:
        data = build_overlay(
            sources=payload.sources,
            asset=payload.asset,
            plan=payload.plan,
            sim_fail_paths=cast(List[Iterable[str]], payload.sim_fail_paths),
            map_path=map_path,
        )
    finally:
        map_path.unlink(missing_ok=True)

    return OverlayResponse(**data)
