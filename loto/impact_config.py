from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Set

import yaml


@dataclass
class ImpactConfig:
    """Configuration for :class:`loto.impact.ImpactEngine`.

    Attributes
    ----------
    asset_units:
        Mapping of asset identifier to unit name.
    unit_data:
        Per-unit information including rating and redundancy scheme.
    unit_areas:
        Mapping of unit name to area.
    penalties:
        Mapping of asset identifier to MW penalty applied when unavailable.
    asset_areas:
        Mapping of penalty asset to area.
    unknown_units:
        Set of unit names with missing or inconsistent data.
    unknown_penalties:
        Set of penalty asset identifiers with missing information.
    """

    asset_units: Dict[str, str]
    unit_data: Dict[str, Dict[str, Any]]
    unit_areas: Dict[str, str]
    penalties: Dict[str, float]
    asset_areas: Dict[str, str]
    unknown_units: Set[str]
    unknown_penalties: Set[str]


def load_impact_config(
    unit_map: str | Path, redundancy_map: str | Path
) -> ImpactConfig:
    """Load impact configuration from YAML files.

    Parameters
    ----------
    unit_map:
        Path to the unit map describing units, their ratings, areas and
        asset membership.  The file is expected to have the following
        structure::

            units:
              <unit_name>:
                rated: <MW>
                area: <area_name>
                assets: [<asset_id>, ...]
            penalties:
              <asset_id>:
                mw: <MW>
                area: <area_name>

    redundancy_map:
        Path to the redundancy map describing redundancy schemes per
        unit.  The value for each unit can either be a simple string such
        as ``"SPOF"`` or a mapping with ``scheme`` and ``nplus`` keys for
        ``N+1`` configurations.

    Returns
    -------
    ImpactConfig
        Parsed configuration along with sets of unknown units or penalty
        assets that were missing required information.
    """

    unit_map_path = Path(unit_map)
    redundancy_map_path = Path(redundancy_map)

    with unit_map_path.open() as f:
        um_data = yaml.safe_load(f) or {}

    units_info = um_data.get("units", {})
    penalties_info = um_data.get("penalties", {})

    asset_units: Dict[str, str] = {}
    unit_data: Dict[str, Dict[str, Any]] = {}
    unit_areas: Dict[str, str] = {}
    penalties: Dict[str, float] = {}
    asset_areas: Dict[str, str] = {}
    unknown_units: Set[str] = set()
    unknown_penalties: Set[str] = set()

    # ------------------------------------------------------------------
    # Units and their assets
    # ------------------------------------------------------------------
    for unit, info in units_info.items():
        rated = info.get("rated")
        area = info.get("area")
        assets = info.get("assets", [])
        if rated is None or area is None:
            unknown_units.add(unit)
            continue
        unit_data[unit] = {"rated": float(rated)}
        unit_areas[unit] = str(area)
        for asset in assets:
            asset_units[str(asset)] = unit

    # ------------------------------------------------------------------
    # Penalty assets not tied to units
    # ------------------------------------------------------------------
    for asset, info in penalties_info.items():
        mw = info.get("mw")
        area = info.get("area")
        if mw is None or area is None:
            unknown_penalties.add(asset)
            continue
        penalties[asset] = float(mw)
        asset_areas[asset] = str(area)

    # ------------------------------------------------------------------
    # Redundancy / derate scheme
    # ------------------------------------------------------------------
    with redundancy_map_path.open() as f:
        red_data = yaml.safe_load(f) or {}

    for unit, info in red_data.items():
        if isinstance(info, str):
            scheme = info
            nplus = None
        else:
            scheme = info.get("scheme")
            nplus = info.get("nplus")
        if unit not in unit_data:
            unknown_units.add(unit)
            continue
        scheme = str(scheme).upper() if scheme is not None else None
        if scheme is None:
            unknown_units.add(unit)
            continue
        unit_data[unit]["scheme"] = scheme
        if scheme == "N+1":
            unit_data[unit]["nplus"] = int(nplus or 1)

    # units defined without redundancy scheme
    missing_scheme = set(unit_data) - set(red_data)
    unknown_units.update(missing_scheme)

    return ImpactConfig(
        asset_units=asset_units,
        unit_data=unit_data,
        unit_areas=unit_areas,
        penalties=penalties,
        asset_areas=asset_areas,
        unknown_units=unknown_units,
        unknown_penalties=unknown_penalties,
    )


__all__ = ["ImpactConfig", "load_impact_config"]
