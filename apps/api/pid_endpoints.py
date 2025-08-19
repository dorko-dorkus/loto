from __future__ import annotations

import tempfile
from functools import lru_cache
from pathlib import Path
from typing import Dict, Iterable, List, cast

import yaml
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from loto.models import IsolationPlan
from loto.pid import build_overlay
from loto.pid.validator import validate_svg_map

router = APIRouter(prefix="/pid", tags=["pid"])


def _stat_path(path: Path) -> tuple[float, bool]:
    try:
        stat = path.stat()
        return stat.st_mtime, True
    except FileNotFoundError:
        return -1.0, False


@lru_cache(maxsize=128)
def _svg_exists_cached(path: Path, mtime: float, exists: bool) -> bool:
    return exists


def _svg_exists(path: Path) -> bool:
    mtime, exists = _stat_path(path)
    return _svg_exists_cached(path, mtime, exists)


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
    warnings: List[str] = Field(default_factory=list)

    class Config:
        extra = "forbid"


@router.get("/{drawing_id}/svg")
async def get_pid_svg(drawing_id: str) -> StreamingResponse:
    """Stream the raw SVG for a given drawing identifier."""

    base = Path(__file__).resolve().parents[2] / "demo"
    svg_path = base / f"{drawing_id}.svg"
    if not _svg_exists(svg_path):
        raise HTTPException(status_code=404, detail="Drawing not found")
    return StreamingResponse(svg_path.open("rb"), media_type="image/svg+xml")


@router.post("/overlay", response_model=OverlayResponse)
async def post_overlay(payload: OverlayRequest) -> OverlayResponse:
    """Return overlay JSON for a work order, plan, and simulation results."""

    pid_map = dict(payload.pid_map)
    svg_obj = pid_map.pop("__svg__", None)
    svg_path_raw: str | None
    if isinstance(svg_obj, str):
        svg_path_raw = svg_obj
    else:
        svg_path_raw = None

    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as fh:
        yaml.safe_dump(pid_map, fh)
        map_path = Path(fh.name)
    try:
        data = build_overlay(
            sources=payload.sources,
            asset=payload.asset,
            plan=payload.plan,
            sim_fail_paths=cast(List[Iterable[str]], payload.sim_fail_paths),
            map_path=map_path,
        )
        warnings: List[str] = []
        if svg_path_raw:
            svg_path = Path(svg_path_raw)
            if not svg_path.is_absolute():
                base = Path(__file__).resolve().parents[2]
                svg_path = base / svg_path
            report = validate_svg_map(svg_path, map_path)
            warnings.extend(report.warnings)
    finally:
        map_path.unlink(missing_ok=True)

    return OverlayResponse(**data, warnings=warnings)
