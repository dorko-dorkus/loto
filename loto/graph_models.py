from __future__ import annotations

import math
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, validator

MEDIUM_WHITELIST = {"STEAM", "WATER", "AIR", "OIL", "NITROGEN"}


class Domain(str, Enum):
    STEAM = "steam"
    WATER = "water"
    PROCESS = "process"
    ELECTRICAL = "electrical"
    INSTRUMENT_AIR = "instrument_air"
    CONDENSATE = "condensate"


def _normalise_tag(cls: type[Any], value: Any) -> Any:
    if value is None:
        return value
    if isinstance(value, float) and math.isnan(value):
        return None
    if isinstance(value, str):
        return value.strip().replace("-", "_").upper()
    return value


def _normalise_domain(cls: type[Any], value: Any) -> Any:
    if isinstance(value, str):
        return value.strip().replace("-", "_").lower()
    return value


def _validate_medium(cls: type[Any], value: Any) -> Any:
    if value is None:
        return value
    if isinstance(value, float) and math.isnan(value):
        return None
    if isinstance(value, str):
        norm = value.strip().replace("-", "_").upper()
        if norm not in MEDIUM_WHITELIST:
            raise ValueError(f"medium '{norm}' not permitted")
        return norm
    return value


class LineRow(BaseModel):
    domain: Domain
    from_tag: str
    to_tag: str
    line_tag: Optional[str] = None
    isolation_cost: Optional[float] = None
    medium: Optional[str] = None
    op_cost_min: Optional[float] = None
    reset_time_min: Optional[float] = None
    risk_weight: Optional[float] = None
    travel_time_min: Optional[float] = None
    elevation_penalty: Optional[float] = None
    outage_penalty: Optional[float] = None

    _normalise_domain = validator("domain", pre=True, allow_reuse=True)(
        _normalise_domain
    )
    _normalise_tags = validator("from_tag", "to_tag", pre=True, allow_reuse=True)(
        _normalise_tag
    )
    _validate_medium = validator("medium", pre=True, allow_reuse=True)(_validate_medium)

    class Config:
        extra = "forbid"


class ValveRow(BaseModel):
    domain: Domain
    tag: str
    fail_state: Optional[str] = None
    kind: Optional[str] = None
    isolation_cost: Optional[float] = None
    medium: Optional[str] = None
    op_cost_min: Optional[float] = None
    reset_time_min: Optional[float] = None
    risk_weight: Optional[float] = None
    travel_time_min: Optional[float] = None
    elevation_penalty: Optional[float] = None
    outage_penalty: Optional[float] = None

    _normalise_domain = validator("domain", pre=True, allow_reuse=True)(
        _normalise_domain
    )
    _normalise_tag = validator("tag", pre=True, allow_reuse=True)(_normalise_tag)
    _validate_medium = validator("medium", pre=True, allow_reuse=True)(_validate_medium)

    class Config:
        extra = "forbid"


class DrainRow(BaseModel):
    domain: Domain
    tag: str
    kind: Optional[str] = None
    medium: Optional[str] = None

    _normalise_domain = validator("domain", pre=True, allow_reuse=True)(
        _normalise_domain
    )
    _normalise_tag = validator("tag", pre=True, allow_reuse=True)(_normalise_tag)
    _validate_medium = validator("medium", pre=True, allow_reuse=True)(_validate_medium)

    class Config:
        extra = "forbid"


class SourceRow(BaseModel):
    domain: Domain
    tag: str
    kind: Optional[str] = None
    medium: Optional[str] = None

    _normalise_domain = validator("domain", pre=True, allow_reuse=True)(
        _normalise_domain
    )
    _normalise_tag = validator("tag", pre=True, allow_reuse=True)(_normalise_tag)
    _validate_medium = validator("medium", pre=True, allow_reuse=True)(_validate_medium)

    class Config:
        extra = "forbid"
