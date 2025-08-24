from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

DATA_DIR = Path(__file__).with_name("demo_data")


class DemoDataSource:
    """Load demo data from JSON files on startup."""

    def __init__(self) -> None:
        self.work_orders: List[Dict[str, Any]] = self._load_list("workorders.json")
        self.assets: List[Dict[str, Any]] = self._load_list("assets.json")
        self.locations: List[Dict[str, Any]] = self._load_list("locations.json")
        self.inventory: List[Dict[str, Any]] = self._load_list("inventory.json")
        self.blueprints: Dict[str, Dict[str, Any]] = self._load_dict("blueprints.json")
        self.boms: List[Dict[str, Any]] = self._load_list("bom.json")
        self._work_orders_by_id = {wo["id"]: wo for wo in self.work_orders}
        self._bom_by_wo: Dict[str, List[Dict[str, Any]]] = {}
        for line in self.boms:
            self._bom_by_wo.setdefault(line["workorder"], []).append(line)
        self.asset_ids = {asset["id"] for asset in self.assets}
        self.location_ids = {loc["id"] for loc in self.locations}

    def _load_list(self, filename: str) -> List[Dict[str, Any]]:
        path = DATA_DIR / filename
        if path.exists():
            return json.loads(path.read_text())
        return []

    def _load_dict(self, filename: str) -> Dict[str, Dict[str, Any]]:
        path = DATA_DIR / filename
        if path.exists():
            return json.loads(path.read_text())
        return {}

    def list_work_orders(self) -> List[Dict[str, Any]]:
        return list(self._work_orders_by_id.values())

    def get_work_order(self, work_order_id: str) -> Dict[str, Any]:
        return self._work_orders_by_id[work_order_id]

    def get_blueprint(self, work_order_id: str) -> Dict[str, Any] | None:
        return self.blueprints.get(work_order_id)

    def get_bom(self, work_order_id: str) -> List[Dict[str, Any]]:
        """Return bill-of-material lines for ``work_order_id``."""

        return list(self._bom_by_wo.get(work_order_id, []))

    def validate(self) -> Dict[str, List[Dict[str, str | None]]]:
        """Check referential integrity of work orders.

        Returns a mapping with lists of missing assets and locations.
        """
        missing_assets: List[Dict[str, str | None]] = []
        missing_locations: List[Dict[str, str | None]] = []
        for wo in self.work_orders:
            asset = wo.get("assetnum")
            if not asset or asset not in self.asset_ids:
                missing_assets.append(
                    {"workorder": wo.get("id", ""), "assetnum": asset}
                )
            location = wo.get("location")
            if not location or location not in self.location_ids:
                missing_locations.append(
                    {"workorder": wo.get("id", ""), "location": location}
                )
        return {
            "missing_assets": missing_assets,
            "missing_locations": missing_locations,
        }


demo_data = DemoDataSource()
